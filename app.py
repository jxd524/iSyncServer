#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Terry<jxd524@163.com>"

"""
flask 框架处理
"""

import os, datetime
import werkzeug
from werkzeug import datastructures, secure_filename
from flask import Flask, request, session, g, abort
import json
import hashlib

import dataManager, responseHelp, defines, unit, cache, configs
from dataManager import DataManager
from cache import LoginInfo
from responseHelp import checkApiParam
from responseHelp import kParamForResult, kParamForErrorResponse, kParamForErrorRealCode, \
        kParamForLoginInfo, kParamForRequestParams
# from log import logObject


app = Flask(__name__);
app.secret_key = defines.kAppSecretKey;

#db manager
def getDbManager():
    "按需获取数据库对象"
    db = getattr(g, "__dataManager", None);
    if db is None:
        db = DataManager()
        g.__dataManager = db
    return db

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, "__dataManager"):
        g.__dataManager = None;

#help function

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
        return strFileName, None, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param,\
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
@app.route("/", methods=["POST"])
def appHome():
    return("hello world");

@app.route("/login.icc", methods=["POST", "GET"])
def appLogin():
    "登陆"
    result = checkApiParam(False, ["userName", "password"])
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    param = result[kParamForRequestParams]
    db = getDbManager()
    row = db.getUser(param["userName"], param["password"])
    if row is None:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_LoginNamePassword)

    #查询根目录信息
    nUserId = row[dataManager.kUserFieldId]
    strUserName = row[dataManager.kUserFieldName]
    rootIdList = db.getUserRootCatalogs(nUserId);
    if not rootIdList or len(rootIdList) == 0:
        #无根目录
        strPath = configs.defaultUserPath(strUserName, nUserId)
        if not os.path.isdir(strPath):
            logObject().error("user: {} do not set root path".format(nUserId))
            return responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_NotSetRootPath)

        ci = db.makeCatalog({"path": strPath})
        nRootId = ci[dataManager.kCatalogFieldRootId] if ci else None
        if nRootId == None:
            logObject().error("can not add root catelog: {} for user: {}".format(strPath, nUserId))
            return responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_DbDataError)

        db.makeUserAssociate(nUserId, nRootId);
        rootIdList = (nRootId);


    #登录成功,写入session信息
    key = LoginInfo.MakeObject(nUserId, rootIdList);
    session[defines.kSessionUserKey] = key;

    return responseHelp.buildSuccessResponseData(dataManager.buildUserInfo(row))

@app.route("/logout.icc", methods=["POST"])
def appLogout():
    "退出"
    key = session.get(defines.kSessionUserKey)
    user = LoginInfo.GetObject(key)
    if user:
        LoginInfo.DeleteObject(key)
        session.clear();
    return responseHelp.buildSuccessResponseData("");

@app.route("/helpInfo.icc", methods=["GET"])
def appGetHelpInfo():
    "获取指定记录的辅助信息"

    # 参数判断
    result = checkApiParam(True, [
        {"name": "type", "checkfunc": unit.checkParamForInt},
        {"name": "id", "checkfunc": unit.checkParamForInt, "default": -1}])
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    userLoginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]
    nType = param["type"]
    nId = userLoginInfo.userId if nType == 0 else param["id"]
    if nType not in (0, 1, 2) or nId <= 0:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param)

    # 查询并返回数据
    db = getDbManager()
    hi = db.getHelpInfo(nType, nId, userLoginInfo.rootIdsString)
    nLen = len(hi) if hi else 0
    ltData = {"helpInt": hi[0] if nLen > 0 else None,
              "helpText": hi[1] if nLen > 1 else None,
              "lastModifyTime": hi[2] if nLen > 2 else None}
    unit.filterNullValue(ltData)
    return responseHelp.buildSuccessResponseData(ltData)

@app.route("/updateHelpInfo.icc", methods=["POST"])
def appSetHelpInfo():
    "设置指定记录的辅助信息"

    # 参数判断
    result = checkApiParam(True, [
        {"name": "type", "checkfunc": unit.checkParamForInt},
        {"name": "id", "checkfunc": unit.checkParamForInt, "default": -1},
        {"name": "helpInt", "checkfunc": unit.checkParamForInt, "default": None},
        {"name": "helpText", "default": None}])
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    userLoginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]
    nType = param["type"]
    nId = userLoginInfo.userId if nType == 0 else param["id"]
    if nType not in (0, 1, 2) or nId <= 0:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param)
    nHelpId = param["helpInt"]
    strHelpText = param["helpText"]

    # 设置
    if nHelpId != None or strHelpText != None:
        db = getDbManager()
        db.setHelpInfo(nType, nId, nHelpId, strHelpText, userLoginInfo.rootIdsString)
        return responseHelp.buildSuccessResponseData(None)
    return responseHelp.buildErrorResponseData(kCmdUserError_Param)


@app.route("/catalogs.icc", methods=["GET"])
def appGetCatalogs():
    "获取指定目录下的子目录信息"

    # 参数判断
    result = checkApiParam(True, [{"name": "pids", "checkfunc": unit.checkParamForIntList}])
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    loginInfo = result[kParamForLoginInfo]
    strParentIds = result[kParamForRequestParams]["pids"]

    # 查询数据 
    db = getDbManager()
    dbItems = db.getCatalogsByParentIds(strParentIds, loginInfo.rootIdsString)

    #生成数据
    ltData = [];
    for item in dbItems:
        ltData.append(dataManager.buildCatalogInfo(item, db))
    return responseHelp.buildSuccessResponseData(ltData)

@app.route("/createCatalog.icc", methods=["POST"])
def appCreateCatalog():
    "创建目录"
    curDateTime = datetime.datetime.now()
    result = checkApiParam(True, [
        {"name": "parentId", "checkfunc": unit.checkParamForInt},
        {"name": "name", "checkfunc": lambda v: v if len(v) >= 1 and len(v) < 100 else None},
        {"name": "createTime", "checkfunc": unit.checkParamForDatetime, "default": curDateTime},
        {"name": "lastModifyTime", "checkfunc": unit.checkParamForDatetime, "default": curDateTime},
        {"name": "memo", "default": None},
        {"name": "helpInt", "default": None},
        {"name": "helpText", "default": None}])
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    loginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]

    #查询数据
    db = getDbManager()
    parentItem = db.getCatalogByIdAndRootIds(param["parentId"], loginInfo.rootIdsString)
    if not parentItem:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_CatalogIdInValid)

    #创建路径
    strPath = unit.makeUserCreateCatalogPath(parentItem[dataManager.kCatalogFieldPath], param["name"])
    if not strPath:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_DbDataError)
    param["path"] = strPath

    item = db.makeCatalog(param)
    return responseHelp.buildSuccessResponseData(dataManager.buildCatalogInfo(item, db))

@app.route("/deleteCatalog.icc", methods=["POST"])
def appDeleteCatalog():
    "删除目录"
    result = checkApiParam(True, [{"name": "ids", "checkfunc": unit.checkParamForIntList}])
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    loginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]
    db = getDbManager()
    try:
        db.deleteCatalogs(param["ids"], loginInfo.rootIdsString)
        return responseHelp.buildSuccessResponseData("OK")
    except Exception as e:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_DeleteError)

@app.route("/updateCatalog.icc", methods=["POST"])
def appUpdateCatalog():
    result = checkApiParam(True, [
        {"name": "id", "checkfunc": unit.checkParamForInt},
        {"name": "parentId", "checkfunc": unit.checkParamForInt, "default": None},
        {"name": "name", "checkfunc": lambda v: v if len(v) >= 1 and len(v) < 100 else None, 
            "default": None},
        {"name": "memo", "default": None},
        {"name": "helpInt", "default": None},
        {"name": "helpText", "default": None}]) 

    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    loginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]
    nId = param["id"]
    param.pop("id")
    db = getDbManager()
    bOk = db.updateCatalog(nId, param, loginInfo.rootIdsString)
    if bOk:
        return responseHelp.buildSuccessResponseData("OK") 
    else:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param)




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
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param);

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

    return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param);

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

def myTest(aInput):
    return aInput
def checkTest(aInput):
    return True;

if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True, debug=True);
