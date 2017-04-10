#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "terry<jxd524@163.com>"

from time import time
from werkzeug.contrib.cache import BaseCache

"""
缓存对象
"""

class JxdObjectCache(BaseCache):

    """与 SimpleCache 的操作类似,只是直接缓存对象    """

#lifecycle
    def __init__(self, threshold=500, default_timeout=300):
        "初始化"
        BaseCache.__init__(self, default_timeout)
        self._cache = {}
        self.clear = self._cache.clear
        self._threshold = threshold

#public function
    def get(self, key, autoUpdateExpires=True):
        "获取数据"
        self._prune();
        try:
            expires, value = self._cache[key];
            if expires == 0 or expires > time():
                if autoUpdateExpires:
                    timeout = 0 if expires == 0 else time();
                    expires = self._get_expiration(timeout);
                    self._cache[key] = (expires, value);
                return value
            else:
                self._cache.pop(key, None);
        except Exception as e:
            return None

    def set(self, key, value, timeout=None):
        "设置数据"
        self._prune();
        expires = self._get_expiration(timeout);
        self._cache[key] = (expires,value);
        return True;

    def delete(self, key):
        return self._cache.pop(key, None) is not None;

#private function
    def _prune(self):
        "压缩,当缓存数据大于指定要求时,删除超时"
        if len(self._cache) > self._threshold:
            now = time()
            toremove = []
            for idx, (key, (expires, _)) in enumerate(self._cache.items()):
                if (expires != 0 and expires <= now) or idx % 3 == 0:
                    toremove.append(key)
            for key in toremove:
                v = self._cache.pop(key, None);

    def _get_expiration(self, timeout):
        "生成过期时间"
        if timeout is None:
            timeout = self.default_timeout
        if timeout > 0:
            timeout = time() + timeout
        return timeout

