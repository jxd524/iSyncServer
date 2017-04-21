#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用程序配置

application configs
"""

__author__ = "Terry<jxd524@163.com>";

import json
import os,sys
import log

__gLogFileName = None;
def logFileName():
    """
    日志文件名称,全路径
    log file name, full path
    """
    global __gLogFileName;
    if __gLogFileName is None:
        __gLogFileName = AppConfig().logFileName;
    return __gLogFileName;

__gThumbPath = None;
def thumbPath():
    """
    生成缩略图时的根目录
    The root directory when save building thumbnail image file
    """
    global __gThumbPath;
    if __gThumbPath is None:
        __gThumbPath = AppConfig().thumbPath;
    return __gThumbPath;

__gDefaultUserPath = "*";
def defaultUserPath(aUserName, aUserId):
    """
    用户默认路径
    user default path
    """
    global __gDefaultUserPath
    if __gDefaultUserPath == "*":
        __gDefaultUserPath = AppConfig().defaultUserPath
    strPathName = "{}_{}".format(aUserName, aUserId)
    defPath = os.path.join(__gDefaultUserPath, strPathName)
    if not os.path.isdir(defPath):
        log.logObject().info("create path: {}".format(defPath))
        os.makedirs(defPath)
    return defPath

def shareUrlSetting():
    """
    分享URL缓存配置
    cache setting of share url
    """
    configs = AppConfig();
    return (configs.shareUrlThreshold, configs.shareUrlTimeout);

def onlineSetting():
    """
    在线人数缓存配置
    cache setting of online users count
    """
    configs = AppConfig();
    return (configs.onlineThreshold, configs.onlineTimeout);



"""
AppConfig 配置类
"""
class AppConfig(object):

#print lifecycle
    def __init__(self):
        strFileName = os.path.join(sys.path[0], "appConfigs.json");
        try:
            with open(strFileName, "r") as f:
                self.__config = json.load(f);
        except Exception as e:
            print("没有配置文件,将使用默认值");

#property
    @property
    def logFileName(self):
        "日记位置"
        return self.__getPath("logFileName", "appLog.log", False)

    @property
    def thumbPath(self):
        "缩略图总位置"
        return self.__getPath("thumbPath", "thumbs", True)

    @property
    def defaultUserPath(self):
        "用于创建默认的用户目录"
        return self.__getPath("defaultUserPath", "users", True)

    @property
    def onlineThreshold(self):
        "在线极值人数,用于缓存在线用户的关键信息"
        return self.__getValue("onlineThreshold", 100)

    @property
    def onlineTimeout(self):
        "在线用户最大无活动时间"
        return self.__getValue("onlineTimeout", 3600)

    @property
    def shareUrlThreshold(self):
        "分享URL最大极值"
        return self.__getValue("shareUrlThreshold", 100)

    @property
    def shareUrlTimeout(self):
        "分享URL有效时间"
        return self.__getValue("shareUrlTimeout", 1800)

#private function
    def __getPath(self, aNodeName, aDefaultValue, aForPath):
        try:
            result = self.__config.get(aNodeName)
        except Exception as e:
            result = None

        if (result is None or len(result) == 0) and aDefaultValue:
            result = os.path.join(sys.path[0], "building")
            result = os.path.join(result, aDefaultValue)

        # make sure the path is exists
        strPath = result if aForPath else os.path.split(result)[0]
        if not os.path.isdir(strPath):
            os.makedirs(strPath)

        return result;

    def __getValue(self, aNodeName, aDefaultValue):
        try:
            result = self.__config.get(aNodeName)
        except Exception as e:
            result = None

        if result is None:
            result = aDefaultValue

        return result

if __name__ == "__main__":
    s = "/Users/terry/work/terry/iSyncServer/appConfig.json";
    print(os.path.split(s));
    print("logFileName: ", logFileName());
    print("thumbPath: ", thumbPath());
    print("shareUrlSetting: ", shareUrlSetting());
    print("onlineSetting: ", onlineSetting());
