#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Terry<jxd524@163.com>"

import hashlib
from functools import reduce
import configs
from jxdobjectCache import JxdObjectCache

#提供文件下载时标志缓存,md5(fileName): fullFileName
__appFileCache = None;
def getAppFileCache():
    global __appFileCache;
    if __appFileCache is None:
        nThreshold, nTimeOut = configs.shareUrlSetting();
        __appFileCache = JxdObjectCache(threshold=nThreshold, default_timeout=nTimeOut);
    return __appFileCache;


#应用程序用户缓存
_appCache = None;
def _getAppCache():
    global _appCache;
    if _appCache is None:
        threshold, timeout = configs.onlineSetting();
        _appCache = JxdObjectCache(threshold=threshold, default_timeout=timeout);
    return _appCache;

"""
缓存用户登陆之后的一些关键数据
"""
class LoginInfo(object):
#private
    def __init__(self, aUserId):
        "初始化"
        self._userId = aUserId;
    @property
    def userId(self):
        "用户ID"
        return self._userId;

    @property
    def rootIdList(self):
        "用户所拥有的根目录ID列表"
        return self._rootIdList;

    @rootIdList.setter
    def rootIdList(self, aNewValue):
        self._rootIdList = aNewValue;
        self._rootIdsString = None;

    @property
    def rootIdsString(self):
        "用户所拥有的根目录ID字符串"
        if self._rootIdsString is None and len(self.rootIdList) > 0:
            self._rootIdsString = reduce((lambda x,y:"{},{}".format(x, y)), self.rootIdList);
        return self._rootIdsString;

    @staticmethod
    def MakeObject(aUserId, aRootIdList):
        "生成登陆缓存信息"
        key = LoginInfo._UserKey(aUserId);
        u = _getAppCache().get(key);
        if u is None:
            u = LoginInfo(aUserId);
            _getAppCache().set(key, u);
        u.rootIdList = aRootIdList;
        return key;

    @staticmethod
    def GetObject(aKey):
        return _getAppCache().get(aKey) if aKey else None;

    @staticmethod
    def DeleteObject(aKey):
        "删除用户缓存信息"
        global _appCache
        if _appCache and aKey :
            _appCache.delete(aKey);

    @staticmethod
    def _UserKey(aUserId):
        "用户ID对应的KEY"
        strKey = "_{}_".format(aUserId);
        return hashlib.md5(strKey.encode("utf8")).hexdigest();


#end UserInfo class

if __name__ == "__main__":
    ls = [1, 100, 20, 34, 55];
    print(reduce((lambda x,y:"{},{}".format(x, y)), ls))
