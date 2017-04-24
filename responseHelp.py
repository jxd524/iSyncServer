#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Terry<jxd524@163.com>"

"""
辅助生成 API 响应数据
"""

import mimetypes, json, os
from flask import make_response, request, send_file, abort, Response, session
from werkzeug import http
import logging
import log, defines, dataManager, unit
from cache import LoginInfo


#success
kCmdSuccess = 0;

#Check api result index
kParamForResult = 0
kParamForLoginInfo = 1
kParamForErrorResponse = 1
kParamForErrorRealCode = 2
kParamForRequestParams = 2

#Server error: -1000 以下
kCmdServerError_NotSetRootPath          = -100
kCmdServerError_FormatData              = -101
kCmdServerError_DbDataError             = -102
kCmdServerError_DeleteError             = -103

#User error: -10000 以上
kCmdUserError_LoginNamePassword         = -10000
kCmdUserError_NeedLogin                 = -10001
kCmdUserError_NotAccessRight            = -10002
kCmdUserError_Param                     = -10003
kCmdUserError_NotResource               = -10004
kCmdUserError_ErrorFileTypeForOpt       = -10005
kCmdUserError_ResourceHasBeenRemove     = -10006
kCmdUserError_CatalogIdInValid          = -10007


kCmdErrorMessags = {
        kCmdUserError_LoginNamePassword: "用户名或密码错误",
        kCmdUserError_NeedLogin: "你需要登录后才能访问内容",
        kCmdUserError_NotAccessRight: "无访问权限",
        kCmdUserError_Param: "参数不正确",
        kCmdUserError_NotResource: "找不到指定资源",
        kCmdUserError_ErrorFileTypeForOpt: "文件类型无法执行此操作",
        kCmdUserError_ResourceHasBeenRemove: "指定资源已经被删除",
        kCmdUserError_CatalogIdInValid: "无效的目录Id",

        kCmdServerError_NotSetRootPath: "服务端必须设置根目录",
        kCmdServerError_FormatData: "服务器对数据格式时出错",
        kCmdServerError_DbDataError: "数据库有错误",
        kCmdServerError_DeleteError: "删除操作失败"
        };

def buildResponseData(aCode, aData=None, aMessage=None, aStatusCode=200):
    """生成响应的 JSON 数据

    :aCode: TODO
    :aMessage: TODO
    :aData: TODO
    :returns: TODO

    """
    r = {"code": aCode};
    if aMessage is not None:
        r["msg"] = aMessage;
    if aData is not None:
        r["data"] = aData;

    try:
        r = json.dumps(r);
    except Exception as e:
        log.logoutError("code: {0} formatDataError:{1}".format(aCode, aData));
        return buildErrorResponseData(kCmdServerError_FormatData);

    return r, aStatusCode, {"Content-Type": "application/json"};


def buildSuccessResponseData(aData):
    "生成响应成功的数据"
    return buildResponseData(kCmdSuccess, aData=aData);

def buildErrorResponseData(aCode, statusCode=200):
    "生成响应错误的数据"
    msg = kCmdErrorMessags.get(aCode);
    if msg is None or len(msg) <= 0:
        msg = "未定义错误信息内容: %d" % aCode;
    return make_response(buildResponseData(aCode, aMessage=msg, aStatusCode = statusCode));

def sendFile(aStrFileName, aErrorStatusCode=200):
    """发送文件到客户端,支持单 Range 请求

    :aStrFileName: 文件名称
    :returns: Response

    """

    if not os.path.isfile(aStrFileName):
        log.logObject().error("找不到文件=%s" % aStrFileName)
        return buildErrorResponseData(kCmdUserError_NotResource, statusCode=aErrorStatusCode)


    try:
        httpHeaderRange = request.headers.get("Range")
        r = http.parse_range_header(httpHeaderRange)
        bHasRange = r is not None and len(r.ranges) == 1 and r.ranges[0][0] is not None
    except Exception as e:
        bHasRange = False

    #发送整个文件
    if not bHasRange:
        return send_file(aStrFileName)

    #发送部分文件
    nFileSize = os.path.getsize(aStrFileName)
    beginPos, stopPos = r.range_for_length(nFileSize)
    with open(aStrFileName, "rb") as f:
        f.seek(beginPos)
        byteContens = f.read(stopPos - beginPos)

    strMimeType = mimetypes.guess_type(aStrFileName)[0]
    if strMimeType is None:
        strMimeType = "application/octet-stream"
    resp = Response(byteContens, 206, mimetype = strMimeType, 
            headers={"Content-Range": r.make_content_range(nFileSize),
                "Accept-Ranges": r.units,
                "Etag": "%d" % nFileSize});
    return resp

def checkApiParam(aNeedLogin, aParams):
    """判断Api参数信息是否正确

    :aNeedLogin: 是否需要登陆才能使用
    :aParams: API请求的参数,是一个list,
        元素为dict: 有以下可用内容
             name: 请求参数名; 
             checkfunc: 从request获取到的数据后进行检查,返回None表示此参数不正确
             default: 当提供此值时,说明这是个可选参数,当参数不正确或没有时,将使用此值代替
        元素为string: 
            表示name
    :returns: (bSuccess, 成功时: loginInfo(当aNeedLogin时,否则为None), {key, value}
                         失败时: response, realStatusCode(实际上的错误码)

    """

    # 判断是否需要登陆, 失败实际Code: 403
    loginInfo = None;
    if aNeedLogin:
        key = session.get(defines.kSessionUserKey);
        loginInfo = LoginInfo.GetObject(key);
        if loginInfo is None:
            return False, buildErrorResponseData(kCmdUserError_NeedLogin), 403

    # 参数判断, 失败实际Code: 416
    try:
        result = [];
        result.append(True);
        result.append(loginInfo)
        params = {}

        requestValue = request.get_json(True, True, False) if request.is_json else request.values
        # begin for
        for item in aParams:
            if isinstance(item, str):
                key = item
                bHasDefaultValue = False
                bHasCheckFunc = False
            else:
                key = item["name"]
                bHasDefaultValue = "default" in item.keys()
                defaultValue = item["default"] if bHasDefaultValue else None
                bHasCheckFunc = "checkfunc" in item.keys()
                checkFunc = item["checkfunc"] if bHasCheckFunc else None

            value = requestValue.get(key)
            if bHasCheckFunc:
                try:
                    value = checkFunc(value)
                except Exception as e:
                    value = None
            bParamOK = value != None
            if not bParamOK and bHasDefaultValue:
                value = defaultValue
                bParamOK = True

            if not bParamOK:
                log.logObject().info("parse not ok: {}, value: {}".format(item, value))
                return False, buildErrorResponseData(kCmdUserError_Param), 416
            params[key] = value
        # end for
        result.append(params)
        return result 
    except Exception as e:
        log.logObject().error("parse param error: {}".format(e))
        return False, buildErrorResponseData(kCmdUserError_Param), 417


if __name__ == "__main__":
    s = [];
    l = None;
    s.append(100);
    s.insert(0, l);
    print(s);
