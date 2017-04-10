#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
根据参数对磁盘进入扫描,并将其添加到指定数据库中
描述期间,最好不要启动服务,以免相关根目录被修改后,不能及时通知到用户
"""

__author__="Terry<jxd524@163.com>"

import os,sys, getopt, json
import time, datetime
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
        self.__rootPaths = [];
        self.__dbManager = aDataBase;
        self.__scaning = False;
        self.__rootIds = [];
        self.__ownerUserIds = aOwnerUserIds;
        for item in aRootPaths:
            path = os.path.abspath(os.path.expanduser(item));
            self.__rootPaths.append(path);

#property
    @property
    def rootPaths(self):
        return self.__rootPaths;

    @property
    def rootPathIds(self):
        return self.__rootIds;

    @property
    def dbManager(self):
        return self.__dbManager;

    @property
    def ownerUserIds(self):
        return self.__ownerUserIds;

#public function
    def startScan(self):
        "启动扫描"
        if self.__scaning:
            return True;
        self.__scaning = True;

        #处理根目录
        scanDirList = []; #元素: (rootId, pathId, fullPath)
        for path in self.rootPaths:
            nRootId = self.__makeCatelog(path, -1, -1, scanDirList);
            self.rootPathIds.append(nRootId);

        #扫描目录
        while len(scanDirList) > 0:
            subDirList = [];
            for item in scanDirList:
                nRootId = item[0];
                nPathId = item[1];
                strPath = item[2];
                self.__scanPath(nRootId, nPathId, strPath, subDirList);
            scanDirList = subDirList;

        #关联用户
        if self.ownerUserIds:
            for userId in self.ownerUserIds:
                for rootId in self.rootPathIds:
                    self.dbManager.makeUserAssociate(userId, rootId);

        self.__scaning = False;

#prinvate function
    def __makeCatelog(self, aPath, aRootId, aParentId, aDirList):
        "确保路径写入数据库,存在则查询,不存在则插入"
        info = self.dbManager.getCatalogByPath(aPath);
        if info is None:
            nId = self.dbManager.addCatelog(aPath, aRootId, aParentId);
            info = self.dbManager.getCatalogById(nId);
        nRootId = info[dataManager.kCatalogFieldRootId];
        nPathId = info[dataManager.kCatalogFieldId];
        if nRootId == -1:
            nRootId = nPathId;
        aDirList.append((nRootId, nPathId, aPath));
        return nRootId;

    #扫描指定目录下的文件及子目录,写入到数据库中
    def __scanPath(self, aRootId, aPathId, aPath, subDirs):
        """扫描指定的路径,此路径已经加入到数据中了

        :aPath: 路径
        :aPathId: 路径在数据库中的Id
        :returns: 子目录信息,{pathId, Path}

        """
        print("scaning: %s" % aPath);
        ls = os.listdir(aPath);
        for item in ls:
            strFullFileName = os.path.join(aPath, item);
            if os.path.isdir(strFullFileName):
                "文件夹"
                if not self.__filterPath(strFullFileName):
                    self.__makeCatelog(strFullFileName, aRootId, aPathId, subDirs);
            elif os.path.isfile(strFullFileName):
                "文件"
                if not self.__filterFile(strFullFileName):
                    self.__addFileToDb(strFullFileName, aRootId, aPathId);


    #过滤不需要加入数据库的文件
    def __filterPath(self, aPath):
        """过滤不扫描的路径

        :aPath: 路径
        :returns: True表示不扫描此目录

        """
        return self.__defaultFilter(aPath);

    def __filterFile(self, aFilePathName):
        """过滤不扫描的文件

        :aFilePathName: 文件名, 全路径
        :returns: True表示不处理此文件

        """
        return self.__defaultFilter(aFilePathName);

    def __defaultFilter(self, aPath):
        """默认过滤函数: 以.开头的不扫描入数据库

        :aPath: 路径
        :returns: True表示不扫描此目录

        """
        strName = os.path.split(aPath)[1];
        n = ord(strName[0]);
        if (n == ord('.')):
            return True;
        return False;


#DB operation
    #将文件添加到数据库, 无返回值
    def __addFileToDb(self, aFileName, aRootId, aPathId):
        strName = os.path.split(aFileName)[1];
        if self.dbManager.getFileByCatalogId(aPathId, strName):
            return;

        fStat = os.stat(aFileName);
        nFileSize = fStat.st_size;

        #Create time
        nCreateTime = fStat.st_ctime;
        if nCreateTime > fStat.st_mtime:
            nCreateTime = fStat.st_mtime;
        if nCreateTime > fStat.st_atime:
            nCreateTime = fStat.st_atime;

        #build media info and judge pprint
        nFileStyle = defines.kFileTypeFile;
        nWidth = nHeight = 0;
        nDuration = 0;
        mediaInfo = unit.getFileMediaInfo(aFileName);
        if mediaInfo is not None:
            bHasAudioStream = False;
            try:
                streams = mediaInfo["streams"];
                for item in streams:
                    ct = item["codec_type"];

                    if ct.lower() == "video":
                        nWidth = item["width"];
                        nHeight = item["height"];
                    else:
                        bHasAudioStream = True;

                if bHasAudioStream:
                    nDuration = mediaInfo["format"]["duration"];

                if nWidth > 0 and nHeight > 0:
                    if bHasAudioStream:
                        nFileStyle = defines.kFileTypeVideo;
                    elif mediaInfo["format"]["format_name"].lower() == "gif":
                        nFileStyle = kFileTypeGif;
                    else:
                        nFileStyle = kFileTypeImage;
                elif bHasAudioStream:
                    nFileStyle = kFileTypeFile;

                # Txt 文件
                if mediaInfo["format"]["format_long_name"] == "Tele-typewriter":
                    nFileStyle = kFileTypeFile;
            except Exception as e:
                #do not need handle
                print("Error: parse json dat(getFileMediaInfo result data)")
                pass;

        #add to db
        # strFileName = os.path.split(aFileName)[1];
        print("     %s" % strName);
        self.dbManager.addFile(aRootCatalogId=aRootId, aCatalogId=aPathId, aFileName=strName,
                aFileType= nFileStyle, aSize=nFileSize, aCreateTime=nCreateTime,
                aWidth=nWidth, aHeight=nHeight, aDuration=nDuration);

####################end ScanDisk####################





def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:");
    except Exception as e:
        print(e);
        return;

    if len(opts) == 0:
        strFileName = os.path.join(sys.path[0], "scanDiskConfig.json");
        scanByJsonFile(strFileName);
    else:
        for op, value in opts:
            if op == "-i":
                #根据配置文件来扫描数据
                scanByJsonFile(value);

def scanByJsonFile(aJsonFileName):
    "根据配置文件扫描数据"
    try:
        with open(aJsonFileName)as f:
            config = json.load(f);
    except Exception as e:
        print(e);
        return;

    if not isinstance(config, list):
        print("文件格式有误");
        return;

    dm = DataManager();
    for item in config:
        try:
            paths = item.get("paths");
            users = makeUsers(dm, item.get("users"));
            sd = ScanDisk(users, paths, dm);
            sd.startScan();
        except Exception as e:
            print(e);
    dm.save();

def makeUsers(aDataManager, aUsers):
    "处理配置文件中users对象,生成用户表数据,插入数据库"
    result = [];
    if aUsers is None:
        return result;
    for user in aUsers:
        strName = user.get("name");
        strPassword = user.get("password");
        if isinstance(strName, str) and len(strName) > 0:
            nId = aDataManager.makeUser(strName, strPassword);
            if nId:
                result.append(nId);

    return result;

if __name__ == "__main__":
    main();

