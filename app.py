#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Terry<jxd524@163.com>"

"""
flask 框架处理
"""

import os
import werkzeug
from werkzeug import datastructures, secure_filename
from flask import Flask, request, session, g, abort
import json
import hashlib

import dataManager, responseHelp, defines, unit, cache, configs
from dataManager import DataManager
from cache import LoginInfo

#登录用户有权限的目录ID
kSessionUserKey = "Session_UserKey";

app = Flask(__name__);
app.secret_key = defines.kAppSecretKey;

#db manager
def getDbManager():
    "按需获取数据库对象"
    db = getattr(g, "__dataManager", None);
    if db is None:
        db = g.__dataManager = DataManager();
    return db;

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, "__dataManager"):
        g.__dataManager = None;

#help function
def getCurLoginInfo():
    "获取当前登陆的用户缓存信息,若为None,表示未登陆"
    key = session.get(kSessionUserKey);
    return LoginInfo.GetObject(key);

def getUserRootCatalogs(aUserId, aUserName):
    "获取用户默认路径,返回目录ID"
    db = getDbManager();
    rootList = db.getUserRootCatalogs(aUserId);
    if not rootList or len(rootList) == 0:
        #无根目录
        strPath = config.defaultUserPath();
        try:
            strPath = os.path.join(strPath, aUserName);
            if not os.path.isdir(strPath):
                os.makedirs(strPath);

            nRootId = db.addCatelog(strPath, -1, -1);
            if nRootId is not None:
                db.makeUserAssociate(aUserId, nRootId);
                rootList = (nRootId);
        except Exception as e:
            rootList = None;
    return rootList;

def getResOnResponse(aValideFileType, aForceStatusCode):
    """响应请求时调用,获取 id ,返回(fileName, errorResponse)

    :aValideFileType: 有效的文件类型,None 表示不判断
    :aForceStatusCode: 强制返回的状态码,None 表示根据不同状态返回不同状态码
    :returns: (fileName, dbFileInfo, errorResponse)
    """
    strFileName = None;
    # 登陆判断
    loginInfo = getCurLoginInfo();
    if loginInfo is None:
        nStatusCode = aForceStatusCode if aForceStatusCode else 403;
        return strFileName, None, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_NeedLogin, \
                statusCode=nStatusCode);

    #参数判断
    bParamOK = False;
    try:
        nId = int(request.args.get("id"));
        bParamOK = nId > 0;
    except Exception as e:
        bParamOK = False;
    if not bParamOK:
        nStatusCode = aForceStatusCode if aForceStatusCode else 416;
        return strFileName, None, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ParamType,\
                statusCode=nStatusCode);

    #获取文件信息
    db = getDbManager();
    dbFile = db.getFileWithRootAndId(loginInfo.rootIdsString, nId);
    if dbFile is None:
        nStatusCode = aForceStatusCode if aForceStatusCode else 301;
        return strFileName, None, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_NotResource,\
                statusCode=nStatusCode);

    #文件类型判断
    if aValideFileType:
        nType = dbFile[dataManager.kFileFieldType];
        if nType not in aValideFileType:
            nStatusCode = aForceStatusCode if aForceStatusCode else 416;
            return strFileName, None, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ErrorFileTypeForOpt,\
                    statusCode=nStatusCode);

    #获取文件位置
    nCatalog = dbFile[dataManager.kFileFieldCatalogId];
    dbCatalog = db.getCatalogWithRootAndId(loginInfo.rootIdsString, nCatalog);
    if dbCatalog is None:
        appLog.logObject().error("数据库中的数据有误,找不到对应的路径信息=> 文件ID=%d" % nId);
        nStatusCode = aForceStatusCode if aForceStatusCode else 500;
        return strFileName, None, responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_DbDataError,\
                statusCode=nStatusCode);

    #文件判断
    strFileName = os.path.join(dbCatalog[dataManager.kCatalogFieldPath], \
            dbFile[dataManager.kFileFieldFileName]);
    if not os.path.isfile(strFileName):
        appLog.logObject().error("找不到文件=> 文件ID=%d" % nId);
        nStatusCode = aForceStatusCode if aForceStatusCode else 500;
        return None, None, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ResourceHasBeenRemove,\
                statusCode=nStatusCode);

    return strFileName, dbFile, None;

# api define
@app.route("/", methods=["GET", "POST"])
def appHome():
    return("hello world");

@app.route("/login.icc", methods=["POST"])
def appLogin():
    "登陆"
    try:
        js = request.get_json();
        name = js["userName"];
        password = js["password"];
    except Exception as e:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ParamType);

    db = getDbManager();
    row = db.getUser(name, password);
    if row is None:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_LoginNamePassword);

    #查询根目录信息
    nUserId = row[dataManager.kUserFieldId];
    strUserName = row[dataManager.kUserFieldName];
    rootList = getUserRootCatalogs(nUserId, strUserName);
    if rootList is None:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_NotSetRootPath);


    #登录成功,写入session信息
    key = LoginInfo.MakeObject(nUserId, rootList);
    session[kSessionUserKey] = key;

    #返回用户信息
    ltData = {"name": strUserName,
            "createTime": row[dataManager.kUserFieldCreateTime],
            "lastLoginDate": row[dataManager.kUserFieldLastLoginDate]};
    return responseHelp.buildSuccessResponseData(ltData);

@app.route("/logout.icc", methods=["POST"])
def appLogout():
    "退出"
    loginInfo = getCurLoginInfo();
    if loginInfo:
        LoginInfo.DeleteObject(session[kSessionUserKey]);
        session.clear();
    return responseHelp.buildSuccessResponseData("");

@app.route("/catalogs.icc")
def appGetCatalogs():
    """app 获取指定目录下的子目录信息
    参数 :
    pids: 以","分隔的数字: 1,2,5之类的
    """

    # 登陆判断
    loginInfo = getCurLoginInfo();
    if loginInfo is None:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_NeedLogin);

    # 参数判断
    bParamOK = False;
    try:
        strIds = request.values["pids"];
        bParamOK = appUnit.checkMultiStrNumbers(strIds);
    except Exception as e:
        pass;
    if not bParamOK:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ParamType);

    # 查询数据
    db = getDbManager();
    dbItems = db.getCatalogs(loginInfo.rootIdsString, strIds);

    #生成数据
    ltData = [];
    for item in dbItems:
        strName = item[dataManager.kCatalogFieldName];
        if strName is None:
            strName = item[dataManager.kCatalogFieldPath];
            strName = os.path.basename(strName);
        cid = item[dataManager.kCatalogFieldId];
        # print(cid);
        subStates = db.getCatalogState(cid);
        catalogItem = {"id": cid,
            "rootId": item[dataManager.kCatalogFieldRootId],
            "parentId": item[dataManager.kCatalogFieldParentId],
            "name": strName,
            "createTime": item[dataManager.kCatalogFieldCreateTime],
            "lastModifyTime": item[dataManager.kCatalogFieldLastModifyTime],
            "helpInt": item[dataManager.kCatalogFieldHelpInt],
            "helpText": item[dataManager.kCatalogFieldHelpText],
            "subCatalogCount": subStates[0],
            "fileCount": subStates[1]};
        appUnit.filterNullValue(catalogItem);
        ltData.append(catalogItem);
    return responseHelp.buildSuccessResponseData(ltData);

@app.route("/files.icc", methods=["GET"])
def appGetFiles():
    "获取指定目录下的文件"

    # 登陆判断
    loginInfo = getCurLoginInfo();
    if loginInfo is None:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_NeedLogin);

    # 参数判断
    bParamOK = False;
    try:
        strPathIds = "{}".format(request.values["pids"]);
        nPageIndex = int(request.values["pageIndex"]);
        nMaxPerPage = int(request.values["maxPerPage"]);
        #可选参数
        strTypes = request.values.get("types");
        nSort = request.values.get("sort");
        try:
            nSort = int(nSort);
        except Exception as e:
            nSort = 0;

        bParamOK = appUnit.checkMultiStrNumbers(strPathIds) and nPageIndex >= 0 and nMaxPerPage > 0;
        if bParamOK:
            if not appUnit.checkMultiStrNumbers(strTypes):
                strTypes = None;
    except Exception as e:
        bParamOK = False;

    if not bParamOK:
        print(strPathIds, nPageIndex, nMaxPerPage, strTypes, nSort);
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ParamType);

    # 查询数据
    db = getDbManager();
    dbItems, pageInfo = db.getFiles(strPathIds, loginInfo.rootIdsString, nPageIndex, nMaxPerPage, strTypes, nSort);

    #生成数据
    ltData = [];
    for item in dbItems:
        strName = item[dataManager.kFileFieldName];
        if strName is None:
            strName = item[dataManager.kFileFieldFileName];
        catalogItem = {"id": item[dataManager.kFileFieldId],
            "catalogId": item[dataManager.kFileFieldCatalogId],
            "name": strName,
            "createTime": item[dataManager.kFileFieldCreateTime],
            "uploadTime": item[dataManager.kFileFieldUploadTime],
            "importTime": item[dataManager.kFileFieldImportTime],
            "lastModifyTime": item[dataManager.kFileFieldLastModifyTime],
            "size": item[dataManager.kFileFieldSize],
            "type": item[dataManager.kFileFieldType],
            "duration": item[dataManager.kFileFieldDuration],
            "width": item[dataManager.kFileFieldWidth],
            "height": item[dataManager.kFileFieldHeight],
            "helpInt": item[dataManager.kFileFieldHelpInt],
            "helpText": item[dataManager.kFileFieldHelpText]};
        appUnit.filterNullValue(catalogItem);
        ltData.append(catalogItem);
    return responseHelp.buildSuccessResponseData({"list": ltData, "page": pageInfo});

@app.route("/thumbnail.icc", methods=["GET"])
def appGetThumb():
    "获取文件的缩略图"

    #获取指定资源的具体位置
    validType = (appUnit.FileType.Image.value, appUnit.FileType.Gif.value, appUnit.FileType.Video.value);
    strFileName, dbFile, errResponse = getResOnResponse(validType, 200);
    if strFileName is None:
        return errResponse;

    #获取要生成的大小
    try:
        nMaxSize = int(request.args.get("maxSize"));
    except Exception as e:
        nMaxSize = 90
    if nMaxSize <= 0 or nMaxSize > 1000:
        nMaxSize = 90;

    #根据参数生成缩略图
    nId = dbFile[dataManager.kFileFieldId];
    nWidth = dbFile[dataManager.kFileFieldWidth];
    nHeight = dbFile[dataManager.kFileFieldHeight];
    nDuration = dbFile[dataManager.kFileFieldDuration];
    nCatalogId = dbFile[dataManager.kFileFieldCatalogId];
    strFileOut = appUnit.buildThumbFile(strFileName, nId, nWidth, nHeight, nDuration, nCatalogId, nMaxSize);

    #发送数据
    return responseHelp.sendFile(strFileOut);

@app.route("/downFile.icc")
def appDownFile():
    "下载指定ID的资源"
    strFileName, _, errResponse = getResOnResponse(None, None);
    if strFileName is None:
        return errResponse;
    return responseHelp.sendFile(strFileName);


@app.route("/shareFileUrl.icc")
def appShareFileUrl():
    "获取指定资源的分享KEY"
    strFileName, _, errResponse = getResOnResponse(None, 200);
    if strFileName is None:
        return errResponse;

    key = hashlib.md5(strFileName.encode("utf8")).hexdigest();
    appCache.getAppFileCache().set(key, strFileName);
    return responseHelp.buildSuccessResponseData(key);

@app.route("/shareFile.icc")
def appGetShareFile():
    "根据分享的KEY获取文件内容"
    try:
        strKey = request.values.get("shareKey");
    except Exception as e:
        strKey = None;

    if strKey:
        strFileName = appCache.getAppFileCache().get(strKey);
        if strFileName:
            #成功
            return responseHelp.sendFile(strFileName);

    return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ParamType);

@app.route("/uploadFile.icc", methods=["POST"])
def appUploadFile():
    print('new request')

    def custom_stream_factory(total_content_length, content_type, filename, content_length=None):
        print("total_content_length: ", total_content_length);
        print("filename: ", filename);
        print("content_type: ", content_type);
        tmpfile = open("/Users/terry/Downloads/myTest.xd", "a+b");
        print("start receiving file ... filename => " + str(tmpfile.name))
        return tmpfile

    loginInfo = getCurLoginInfo();
    if loginInfo:
        print("login ok")
    else:
        print("not login");
    print(1);
    stream,form,files = werkzeug.formparser.parse_form_data(request.environ, stream_factory=custom_stream_factory)
    total_size = 0

    print(stream);
    print(form);
    print(files);
    print(2);
    for fil in files.values():
        print(" ".join(["saved form name", fil.name, "submitted as", fil.filename, "to temporary file", fil.stream.name]))
        total_size += os.path.getsize(fil.stream.name)
    print(total_size);
    return "Hello World!"


    print(request.files);
    print(request.form);
    # return "finished";

    for fileName, fileObject in request.files.items():
        strFileName = secure_filename(fileName);
        strFullFileName = os.path.join("/Users/terry/Downloads",strFileName);
        fileObject.save(strFullFileName);
    return "finished"

if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True, debug=True);
    # app.run(debug=True);
