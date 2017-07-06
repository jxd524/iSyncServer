#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用程序配置

application configs
"""

__author__ = "Terry<jxd524@163.com>";

import json
import os,sys, getopt
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
def defaultUserPath(aUserId):
    """
    用户默认路径
    user default path
    """
    global __gDefaultUserPath
    if __gDefaultUserPath == "*":
        __gDefaultUserPath = AppConfig().defaultUserPath
    strPathName = "{}".format(aUserId)
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
    configs = AppConfig()
    return (configs.shareUrlThreshold, configs.shareUrlTimeout)

def onlineSetting():
    """
    在线人数缓存配置
    cache setting of online users count
    """
    configs = AppConfig()
    return (configs.onlineThreshold, configs.onlineTimeout)



"""
AppConfig 配置类
"""
class AppConfig(object):

#print lifecycle
    def __init__(self):
        try:
            with open(self.__configFileName(), "r") as f:
                self.__config = json.load(f);
        except Exception as e:
            print("没有配置文件,将使用默认值");
            self.__config = {}

# public function
    def save(self):
        s = json.dumps(self.__config)
        with open(self.__configFileName(), "w") as f:
            f.write(s)

#property
    # 日志文件
    @property
    def logFileName(self):
        "日志文件名"
        return self.__getPath("logFileName", "appLog.log", False)
    @logFileName.setter
    def logFileName(self, aValue):
        "设置日志输出路径"
        try:
            path, name = os.path.split(aValue)
            if not os.path.exists(path):
                os.makedirs(path)
            with open(aValue, "w+") as f:
                pass
        except Exception as e:
            aValue = self.logFileName
            print("设置日志路径失败")
        self.__config["logFileName"] = aValue


    @property
    def thumbPath(self):
        "缩略图总位置"
        return self.__getPath("thumbPath", "thumbs", True)
    @thumbPath.setter
    def thumbPath(self, aValue):
        "设置缩略图存放位置"
        try:
            if not os.path.exists(aValue):
                os.makedirs(aValue)
        except Exception as e:
            pass
        if not os.path.exists(aValue):
            print("设置缩略图位置失败")
            aValue = self.thumbPath
        self.__config["thumbPath"] = aValue


    @property
    def defaultUserPath(self):
        "用于创建默认的用户目录"
        return self.__getPath("defaultUserPath", "users", True)
    @defaultUserPath.setter
    def defaultUserPath(self, aValue):
        "设置缩默认的用户目录位置"
        try:
            if not os.path.exists(aValue):
                os.makedirs(aValue)
        except Exception as e:
            pass
        if not os.path.exists(aValue):
            print("设置默认用户目录失败")
            aValue = self.defaultUserPath
        self.__config["defaultUserPath"] = aValue


    @property
    def onlineThreshold(self):
        "在线极值人数,用于缓存在线用户的关键信息"
        return self.__getValue("onlineThreshold", 100)
    @onlineThreshold.setter
    def onlineThreshold(self, aValue):
        self.__setIntValue("onlineThreshold", aValue, self.onlineThreshold)

    @property
    def onlineTimeout(self):
        "在线用户最大无活动时间"
        return self.__getValue("onlineTimeout", 3600)
    @onlineTimeout.setter
    def onlineTimeout(self, aValue):
        "设置在线用户最大无活动时间"
        self.__setIntValue("onlineTimeout", aValue, self.onlineTimeout)

    @property
    def shareUrlThreshold(self):
        "分享URL最大极值"
        return self.__getValue("shareUrlThreshold", 100)
    @shareUrlThreshold.setter
    def shareUrlThreshold(self, aValue):
        self.__setIntValue("shareUrlThreshold", aValue, self.shareUrlThreshold)

    @property
    def shareUrlTimeout(self):
        "分享URL有效时间"
        return self.__getValue("shareUrlTimeout", 1800)
    @shareUrlTimeout.setter
    def shareUrlTimeout(self, aValue):
        self.__setIntValue("shareUrlTimeout", aValue, self.shareUrlTimeout)

#private function
    def __configFileName(self):
        return os.path.join(sys.path[0], "appConfigs.json")

    def __setIntValue(self, aKey, aValue, aDefaultValue):
        try:
            aValue = int(aValue)
        except Exception as e:
            aValue = aDefaultValue
        self.__config[aKey] = aValue

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
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["logFileName=", "thumbPath=", "defaultUserPath=", "shareUrlThreshold=", "shareUrlTimeout=", "onlineThreshold=", "onlineTimeout="])
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        print("请查阅: http://icc.one/")
        sys.exit(2)
    
    if len(opts) == 0:
        exit(0)
    
    ac = AppConfig()
    for opt, value in opts:
        if opt == "--logFileName":
            ac.logFileName = value
        elif opt == "--thumbPath":
            ac.thumbPath = value
        elif opt == "--defaultUserPath":
            ac.defaultUserPath = value
        elif opt == "--shareUrlThreshold":
            ac.shareUrlThreshold = value
        elif opt == "--shareUrlTimeout":
            ac.shareUrlTimeout = value
        elif opt == "--onlineThreshold":
            ac.onlineThreshold = value
        elif opt == "--onlineTimeout":
            ac.onlineTimeout = value
    ac.save()
