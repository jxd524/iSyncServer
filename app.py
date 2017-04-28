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
def _getDbManager():
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
def _getFileInfo(aOtherParams, aValideFileTypes):
    """获取指定文件资源,返回值参考 checkApiParam, 若成功时,返回值result[kParamForRequestParams]会加上
        "_x_file": 资源对应的全路径
        "_x_fileInfo": 在数据库中对应的Row信息

    :aOtherParam: 除了"id"之后的其它信息,必须为一个可变数组[]
    :aValideFileTypes: 有效的文件类型,一个list(int),None 表示不判断
    :returns: 参考 checkApiParam
    """
    param = aOtherParams if aOtherParams else []
    param.append({"name": "id", "checkfunc": unit.checkParamForInt})

    result = checkApiParam(True, param)
    if not result[kParamForResult]:
        return result

    loginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]

    nId = param["id"]

    #获取文件信息
    db = _getDbManager();
    dbFile = db.getFileByIdAndRootIds(nId, loginInfo.rootIdsString)
    if dbFile is None:
        return False, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_NotResource), 301


    #文件类型判断
    if aValideFileTypes:
        nType = dbFile[dataManager.kFileFieldType];
        if nType not in aValideFileTypes:
            return False, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ErrorFileTypeForOpt), 416

    #获取文件位置
    nCatalog = dbFile[dataManager.kFileFieldRealCatalogId]
    dbCatalog = db.getCatalogByIdAndRootIds(nCatalog, loginInfo.rootIdsString);
    if dbCatalog is None:
        appLog.logObject().error("数据库中的数据有误,找不到对应的路径信息=> 文件ID=%d" % nId);
        return False, responseHelp.buildErrorResponseData(responseHelp.kCmdServerError_DbDataError), 500

    #文件判断
    strFileName = os.path.join(dbCatalog[dataManager.kCatalogFieldPath], \
            dbFile[dataManager.kFileFieldFileName]);
    if not os.path.isfile(strFileName):
        appLog.logObject().error("找不到文件=> 文件ID=%d" % nId);
        return False, responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_ResourceHasBeenRemove), 500

    param["_x_file"] = strFileName
    param["_x_fileInfo"] = dbFile
    return result


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
    db = _getDbManager()
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
    db = _getDbManager()
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
        db = _getDbManager()
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
    db = _getDbManager()
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
    db = _getDbManager()
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
    db = _getDbManager()
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
    db = _getDbManager()
    bOk = db.updateCatalog(nId, param, loginInfo.rootIdsString)
    if bOk:
        return responseHelp.buildSuccessResponseData("OK") 
    else:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param)


@app.route("/files.icc", methods=["GET"])
def appGetFiles():
    "获取指定目录下的文件"

    result = checkApiParam(True, [
        {"name": "pids", "checkfunc": unit.checkParamForIntList},
        {"name": "pageIndex", "checkfunc": unit.checkParamForInt},
        {"name": "maxPerPage", "checkfunc": lambda v: int(v) if int(v) > 0 and int(v) < 10000 else 100,
            "default": 100},
        {"name": "types", "checkfunc": unit.checkParamForIntList, "default": None},
        {"name": "sort", "checkfunc": unit.checkParamForInt, "default": 0}])

    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    loginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]

    # 查询数据
    db = _getDbManager();
    fileRows, pageInfo = db.getFiles(param["pids"], loginInfo.rootIdsString, param["pageIndex"], param["maxPerPage"], param["types"], param["sort"])

    #生成数据
    ltData = dataManager.buildFileInfoList(fileRows, None)
    return responseHelp.buildSuccessResponseData({"list": ltData, "page": pageInfo});


@app.route("/thumbnail.icc", methods=["GET"])
def appGetThumb():
    "获取文件的缩略图"
    result = _getFileInfo(
            [{"name": "level", "checkfunc": unit.checkParamForInt, "default": 0}],
            (defines.kFileTypeImage, defines.kFileTypeGif, defines.kFileTypeVideo))
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    param = result[kParamForRequestParams]
    nLevel = param["level"]
    strFile = param["_x_file"]
    dbFile = param["_x_fileInfo"]

    nErrorCode = None
    nOrigFileStatus = dbFile[dataManager.kFileFieldStatusForOrigin]
    nStatus = dbFile[dataManager.kFileFieldStatusForThumb] if nLevel == 0 else\
            dbFile[dataManager.kFileFieldStatusForScreen]
    if nStatus == defines.kFileStatusFromLocal:
        #本地生成缩略图
        if nOrigFileStatus in (defines.kFileStatusFromLocal, defines.kFileStatusFromUploaded):
            #根据参数生成缩略图
            nId = dbFile[dataManager.kFileFieldId]
            nWidth = dbFile[dataManager.kFileFieldWidth]
            nHeight = dbFile[dataManager.kFileFieldHeight]
            nType = dbFile[dataManager.kFileFieldType]
            nCatalogId = dbFile[dataManager.kFileFieldRealCatalogId]
            nOrientation = dbFile[dataManager.kFileFieldOrientation]
            strFileOut = unit.generateThumbailImage(nCatalogId, nId, strFile, nOrientation, nWidth, nHeight, nType, nLevel)
            if not strFileOut or not os.path.isfile(strFileOut):
                #无法生成缩略图
                nErrorCode = responseHelp.kCmdUserError_BuildThumbFailed
                field = "statusForThumb" if nLevel == 0 else "statusForScreen"
                _getDbManager().updateFile(nId, {field: defines.kFileStatusBuildError})
        else:
            nErrorCode = kCmdUserError_WaitUploading
    elif nStatus == defines.kFileStatusFromUploaded:
        #客户端上传,直接发送
        nCatalogId = dbFile[dataManager.kFileFieldRealCatalogId]
        nId = dbFile[dataManager.kFileFieldId]
        strFileOut = unit.getFileThumbFullFileName(nCatalogId, nId, nLevel)
    elif nStatus == defines.kFileStatusBuildError:
        #本地生成错误
        nErrorCode = responseHelp.kCmdUserError_BuildThumbFailed
    elif nStatus == defines.kFileStatusFromUploading:
        nErrorCode = responseHelp.kCmdUserError_WaitUploading

    #发送数据
    if nErrorCode != None:
        return responseHelp.buildErrorResponseData(nErrorCode, 404)
    return responseHelp.sendFile(strFileOut);


@app.route("/downFile.icc")
def appDownFile():
    "下载指定ID的资源"
    result = _getFileInfo(None, None)
    if not result[kParamForResult]:
        errResponse = result[kParamForErrorResponse]
        errResponse.status_code = result[kParamForErrorRealCode]
        return errResponse

    param = result[kParamForRequestParams]
    strFile = param["_x_file"]
    return responseHelp.sendFile(strFile, 404);


@app.route("/shareFileUrl.icc")
def appShareFileUrl():
    "获取指定资源的分享KEY"
    result = _getFileInfo(None, None)
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    param = result[kParamForRequestParams]
    strFile = param["_x_file"]
    key = hashlib.md5(strFile.encode("utf8")).hexdigest()
    cache.getAppFileCache().set(key, strFile)
    return responseHelp.buildSuccessResponseData(key)


@app.route("/shareFile.icc")
def appGetShareFile():
    "根据分享的KEY获取文件内容"
    result = checkApiParam(False, ("shareKey",))
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    param = result[kParamForRequestParams]
    strFileName = cache.getAppFileCache().get(param["shareKey"])
    print(strFileName)
    return responseHelp.sendFile(strFileName) if strFileName else \
            responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param);


@app.route("/uploadFileInfo.icc", methods=["POST"])
def appUploadFileInfo():
    "上传文件信息"
    funcCheckStatus = lambda v: int(v) if int(v) in (defines.kFileStatusFromLocal, defines.kFileStatusFromUploading) else defines.kFileStatusFromLocal
    curDateTime = datetime.datetime.now()
    result = checkApiParam(True, (
        {"name": "cid", "checkfunc": unit.checkParamForInt},
        {"name": "name", "checkfunc": lambda v: v if len(v) > 0 and len(v) <= 100 else None},
        {"name": "size", "checkfunc": unit.checkParamForInt},
        {"name": "type", "checkfunc": unit.checkParamForFileType},
        {"name": "statusForThumb", "checkfunc": funcCheckStatus, "default": defines.kFileStatusFromLocal},
        {"name": "statusForScreen", "checkfunc": funcCheckStatus, "default": defines.kFileStatusFromLocal},
        {"name": "createTime", "checkfunc": unit.checkParamForDatetime, "default": curDateTime},
        {"name": "importTime", "checkfunc": unit.checkParamForDatetime, "default": curDateTime},
        {"name": "lastModifyTime", "checkfunc": unit.checkParamForDatetime, "default": curDateTime},
        {"name": "duration", "checkfunc": lambda v: float(v), "default": None},
        {"name": "width", "checkfunc": unit.checkParamForInt, "default": None},
        {"name": "height", "checkfunc": unit.checkParamForInt, "default": None},
        {"name": "orientation", "checkfunc": unit.checkParamForInt, "default": None},
        {"name": "memo", "checkfunc": unit.checkParamForLess1024, "default": None},
        {"name": "helpInt", "checkfunc": unit.checkParamForInt, "default": None},
        {"name": "helpText", "default": None},))

    if not result[kParamForResult]:
        return result[kParamForErrorResponse]

    loginInfo = result[kParamForLoginInfo]
    param = result[kParamForRequestParams]
    nCatalogId = param.pop("cid")
    #目录信息
    db = _getDbManager()
    catalogRow = db.getCatalogByIdAndRootIds(nCatalogId, loginInfo.rootIdsString)
    if not catalogRow:
        return responseHelp.buildErrorResponseData(responseHelp.kCmdUserError_Param)

    strFileName = unit.buildOriginFileName(catalogRow[dataManager.kCatalogFieldPath], param["name"])
    param["uploadUserId"] = loginInfo.userId
    param["fileName"] = strFileName
    param["statusForOrigin"] = defines.kFileStatusFromUploading
    nNewFileId = db.addFile(catalogRow[dataManager.kCatalogFieldRootId], nCatalogId, param)
    fileRow = db.getFileByIdAndRootIds(nNewFileId, None)
    return responseHelp.buildSuccessResponseData(dataManager.buildFileInfo(fileRow))


@app.route("/uploadingInfo.icc", methods=["GET"])
def appUploadingInfo():
    "获取所有正在上传的文件"
    result = checkApiParam(True, ())
    if not result[kParamForResult]:
        return result[kParamForErrorResponse]
    loginInfo = result[kParamForLoginInfo]
    # 查询数据
    db = _getDbManager();
    fileRows = db.getFileByUploading(loginInfo.userId)

    #生成数据
    ltData = dataManager.buildFileInfoList(fileRows, db)
    return responseHelp.buildSuccessResponseData(ltData)


@app.route("/uploadFile.icc", methods=["POST"])
def appUploadFile():
    print('new request')
    print(request.args)
    return "xxxxx"

    def custom_stream_factory(total_content_length, content_type, filename, content_length=None):
        print("total_content_length: ", total_content_length);
        print("filename: ", filename);
        print("content_type: ", content_type);
        tmpfile = open("/Users/terry/Downloads/myTest.xd", "a+b");
        print("start receiving file ... filename => " + str(tmpfile.name))
        return tmpfile


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
