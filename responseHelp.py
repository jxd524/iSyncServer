#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Terry<jxd524@163.com>"

"""
辅助生成 API 响应数据
"""

from flask import make_response, request, send_file, abort, Response
from werkzeug import http
import mimetypes
import json
import os
import log


#success
kCmdSuccess = 0;

#Server error
kCmdServerError_NotSetRootPath          = 10;
kCmdServerError_FormatData              = 11;
kCmdServerError_DbDataError             = 12;

#User error
kCmdUserError_LoginNamePassword         = 10000;
kCmdUserError_NeedLogin                 = 10001;
kCmdUserError_NotAccessRight            = 10002;
kCmdUserError_ParamType                 = 10003;
kCmdUserError_NotResource               = 10004;
kCmdUserError_ErrorFileTypeForOpt       = 10005;
kCmdUserError_ResourceHasBeenRemove     = 10006;


kCmdErrorMessags = {
        kCmdUserError_LoginNamePassword: "用户名或密码错误",
        kCmdUserError_NeedLogin: "你需要登录后才能访问内容",
        kCmdUserError_NotAccessRight: "无访问权限",
        kCmdUserError_ParamType: "参数类型不正确",
        kCmdUserError_NotResource: "找不到指定资源",
        kCmdUserError_ErrorFileTypeForOpt: "文件类型无法执行此操作",
        kCmdUserError_ResourceHasBeenRemove: "指定资源已经被删除",

        kCmdServerError_NotSetRootPath: "服务端必须设置根目录",
        kCmdServerError_FormatData: "服务器对数据格式时出错",
        kCmdServerError_DbDataError: "数据库有错误"
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

def sendFile(aStrFileName):
    """发送文件到客户端,支持单 Range 请求

    :aStrFileName: 文件名称
    :returns: Response

    """

    if not os.path.isfile(aStrFileName):
        log.logObject().error("找不到文件=%s" % aStrFileName);
        return buildErrorResponseData(kCmdUserError_NotResource);


    try:
        httpHeaderRange = request.headers.get("Range");
        r = http.parse_range_header(httpHeaderRange);
        bHasRange = r is not None and len(r.ranges) == 1 and r.ranges[0][0] is not None;
    except Exception as e:
        bHasRange = False;

    #发送整个文件
    if not bHasRange:
        return send_file(aStrFileName);

    #发送部分文件
    nFileSize = os.path.getsize(aStrFileName);
    beginPos, stopPos = r.range_for_length(nFileSize);
    with open(aStrFileName, "rb") as f:
        f.seek(beginPos);
        byteContens = f.read(stopPos - beginPos);

    strMimeType = mimetypes.guess_type(aStrFileName)[0];
    if strMimeType is None:
        strMimeType = "application/octet-stream";
    resp = Response(byteContens, 206, mimetype = strMimeType, 
            headers={"Content-Range": r.make_content_range(nFileSize),
                "Accept-Ranges": r.units,
                "Etag": "%d" % nFileSize});
    return resp;

if __name__ == "__main__":
    s = buildErrorResponseData(kCmdUserError_NeedLogin);
    print(s);
