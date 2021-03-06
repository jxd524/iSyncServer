#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
根据参数对磁盘进入扫描,并将其添加到指定数据库中
描述期间,最好不要启动服务,以免相关根目录被修改后,不能及时通知到用户
"""

__author__="Terry<jxd524@163.com>"

import os,sys, getopt, json
import datetime
import defines, unit
import dataManager
from dataManager import DataManager

####################begin ScanDisk####################
class ScanDisk(object):
    """扫描给定的目录文件,添加到数据库中
    """

#life cycle
    def __init__(self, aOwnerUserIds, aRootPaths, aDataBase):
        "初始化,传入扫描的路径列表,数据库对象"
        self.__rootPaths = []
        self.__dbManager = aDataBase
        self.__scaning = False
        self.__mergeRootPaths = True
        self.__rootIds = []
        self.__ownerUserIds = aOwnerUserIds
        for item in aRootPaths:
            path = os.path.abspath(os.path.expanduser(item))
            self.__rootPaths.append(path)

#property
    @property
    def rootPaths(self):
        return self.__rootPaths

    @property
    def rootPathIds(self):
        return self.__rootIds

    @property
    def dbManager(self):
        return self.__dbManager

    @property
    def ownerUserIds(self):
        return self.__ownerUserIds

    @property
    def mergeRootPaths(self):
        return self.__mergeRootPaths
    @mergeRootPaths.setter
    def mergeRootPaths(self, aValue):
        self.__mergeRootPaths = aValue

#public function
    def startScan(self):
        "启动扫描"
        if self.__scaning:
            return True
        self.__scaning = True

        #处理根目录
        scanDirList = [] #元素: (rootId, pathId, fullPath)
        for path in self.rootPaths:
            info = self._makeCatalog(path, scanDirList)
            if info[dataManager.kCatalogFieldParentId] == -1:
                self.rootPathIds.append(info[dataManager.kCatalogFieldRootId])

        #扫描目录
        while len(scanDirList) > 0:
            subDirList = []
            for item in scanDirList:
                nRootId = item[0]
                nPathId = item[1]
                strPath = item[2]
                self._scanPath(nRootId, nPathId, strPath, subDirList)
            scanDirList = subDirList

        #关联用户
        if self.ownerUserIds:
            for userId in self.ownerUserIds:
                for rootId in self.rootPathIds:
                    self.dbManager.makeUserAssociate(userId, rootId)

        # 根目录化子目录
        if self.mergeRootPaths and self.ownerUserIds:
            for userId in self.ownerUserIds:
                self.dbManager.checkUpdateCatelogRootInfo(userId)


        self.__scaning = False

#prinvate function
    def _makeCatalog(self, aPath, aDirList, aRootId = None, aParentId = None):
        "确保路径写入数据库,存在则查询,不存在则插入"
        fStat = os.stat(aPath)
        #Create time
        nCreateTime = fStat.st_ctime
        if nCreateTime > fStat.st_mtime:
            nCreateTime = fStat.st_mtime
        if nCreateTime > fStat.st_atime:
            nCreateTime = fStat.st_atime
        info = self.dbManager.makeCatalog({"path": aPath, "rootId": aRootId, "parentId": aParentId, "createTime": int(nCreateTime)})
        nRootId = info[dataManager.kCatalogFieldRootId]
        nPathId = info[dataManager.kCatalogFieldId]
        aPath = info[dataManager.kCatalogFieldPath]
        aDirList.append((nRootId, nPathId, aPath))
        return info

    #扫描指定目录下的文件及子目录,写入到数据库中
    def _scanPath(self, aRootId, aPathId, aPath, aSubDirs):
        """扫描指定的路径,此路径已经加入到数据中了

        :aPath: 路径
        :aPathId: 路径在数据库中的Id
        :returns: 子目录信息,{pathId, Path}

        """
        print("scaning: %s" % aPath)
        ls = os.listdir(aPath)
        for item in ls:
            strFullFileName = os.path.join(aPath, item)
            if os.path.isdir(strFullFileName):
                "文件夹"
                if not self._filterPath(strFullFileName):
                    self._makeCatalog(strFullFileName, aSubDirs, aRootId, aPathId)
            elif os.path.isfile(strFullFileName):
                "文件"
                if not self._filterFile(strFullFileName):
                    self._addFileToDb(strFullFileName, aRootId, aPathId)


    #过滤不需要加入数据库的文件
    def _filterPath(self, aPath):
        """过滤不扫描的路径

        :aPath: 路径
        :returns: True表示不扫描此目录

        """
        return self._defaultFilter(aPath)

    def _filterFile(self, aFilePathName):
        """过滤不扫描的文件

        :aFilePathName: 文件名, 全路径
        :returns: True表示不处理此文件

        """
        return self._defaultFilter(aFilePathName)

    def _defaultFilter(self, aPath):
        """默认过滤函数: 以.开头的不扫描入数据库

        :aPath: 路径
        :returns: True表示不扫描此目录

        """
        strName = os.path.split(aPath)[1]
        n = ord(strName[0])
        if (n == ord('.')):
            return True
        return False

    @staticmethod
    def _tryGetValue(aDict, aNames, aDefaultValue):
        try:
            if isinstance(aNames, str):
                return aDict[aNames]
            else:
                for item in aNames:
                    aDict = aDict[item]
                return aDict
        except Exception as e:
            return aDefaultValue

#DB operation
    #将文件添加到数据库, 无返回值
    def _addFileToDb(self, aFileName, aRootId, aPathId):
        strName = os.path.split(aFileName)[1]
        if self.dbManager.getFileByRealCatalogId(aPathId, strName):
            return

        fStat = os.stat(aFileName)
        nFileSize = fStat.st_size

        #Create time
        nCreateTime = fStat.st_ctime
        if nCreateTime > fStat.st_mtime:
            nCreateTime = fStat.st_mtime
        if nCreateTime > fStat.st_atime:
            nCreateTime = fStat.st_atime

        fileInfo = unit.getMediaFileInfo(aFileName, nFileSize)
        if not fileInfo:
            fileInfo = {}

        fileInfo["fileName"] = strName
        fileInfo["size"] = nFileSize
        fileInfo["createTime"] = nCreateTime
        try:
            if len(fileInfo["ext"]) <= 0:
                fileInfo["ext"] = os.path.splitext(aFileName)[1][1:]
        except Exception as e:
            fileInfo["ext"] = os.path.splitext(aFileName)[1][1:]

        unit.makeValue(fileInfo, "type", defines.kFileTypeFile)
        print("     %s" % strName)
        self.dbManager.addFile(aRootId, aPathId, fileInfo)

####################end ScanDisk####################





def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:p:")
    except Exception as e:
        print(e)
        return

    if len(opts) == 0:
        strFileName = os.path.join(sys.path[0], "scanDiskConfig.json")
        scanByJsonFile(strFileName)
    else:
        for op, value in opts:
            if op == "-i":
                #根据配置文件来扫描数据
                scanByJsonFile(value)
                return
            elif op == "-p":
                #扫描指定路径,一般用于增量扫描
                beginScan((value,), None)


def scanByJsonFile(aJsonFileName):
    "根据配置文件扫描数据"
    try:
        with open(aJsonFileName)as f:
            config = json.load(f)
    except Exception as e:
        print(e)
        return

    if not isinstance(config, list):
        print("文件格式有误")
        return

    dm = DataManager()
    for item in config:
        try:
            beginScan(item.get("paths"), item.get("users"), dm, item.get("merge"))
        except Exception as e:
            print(e)

def beginScan(aPaths, aUsers, aDM = None, aMergeRootPath = True):
    if aDM is None:
        aDM = DataManager()
    users = makeUsers(aDM, aUsers)
    sd = ScanDisk(users, aPaths, aDM)
    if aMergeRootPath is not None:
        sd.mergeRootPaths = aMergeRootPath
    sd.startScan()
    aDM.save()

def makeUsers(aDataManager, aUsers):
    "处理配置文件中users对象,生成用户表数据,插入数据库"
    result = []
    if aUsers is None:
        return result
    for user in aUsers:
        strName = user.get("name")
        strPassword = user.get("password")
        if isinstance(strName, str) and len(strName) > 0:
            nId = aDataManager.makeUser(strName, strPassword)
            if nId:
                result.append(nId)

    return result

if __name__ == "__main__":
    print("准备扫描...")
    main()
    print("扫描结束")


