#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理
db manager
"""

__author__="Terry<jxd524@163.com>"

import os, sys, time
from jxdsqlite import JxdSqlDataBasic
import defines, log, unit

"""
方便定义字段序号
for easily define db table field index
"""
__gFieldIndex = 0;
def __incFieldWithInit(aInit=None):
    global __gFieldIndex;
    if aInit:
        __gFieldIndex = 0;
    nResult = __gFieldIndex;
    __gFieldIndex += 1;
    return nResult;


"""
用户表
记录所有用户信息

user table
"""
_kUserTableName = "User";
kUserFieldId                        = __incFieldWithInit(True);   #ID
kUserFieldName                      = __incFieldWithInit(); #用户名
kUserFieldPassword                  = __incFieldWithInit(); #用户密码
kUserFieldCreateTime                = __incFieldWithInit(); #创建时间
kUserFieldLastLoginDate             = __incFieldWithInit(); #最后登陆时间
kUserFieldLastModifyTime            = __incFieldWithInit(); #针对HelpInfo,最后修改时间
kUserFieldHelpInt                   = __incFieldWithInit(); #辅助Int,只对客户端有意义,服务端只负责保存
kUserFieldHelpText                  = __incFieldWithInit(); #辅助信息,只对客户端有意思
def _UserCreateTableSQL():
    """
    创建用户表的SQL语句
    sql for create user table
    """
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                name varchar(100) collate nocase UNIQUE,
                password varchar(32),
                createTime timestamp default(0),
                lastLoginDate timestamp default(0),
                lastModifyTime timestamp default 0,
                helpInt integer,
                helpText text
            )""" % _kUserTableName;


"""
目录表
"""
_kCatalogTableName = "Catalog";
kCatalogFieldId             = __incFieldWithInit(True); #ID
kCatalogFieldPath           = __incFieldWithInit(); #具体全路径
kCatalogFieldRootId         = __incFieldWithInit(); #根路径ID
kCatalogFieldParentId       = __incFieldWithInit(); #父路径ID
kCatalogFieldName           = __incFieldWithInit(); #在客户端显示的名称
kCatalogFieldCreateTime     = __incFieldWithInit(); #记录创建时间
kCatalogFieldLastModifyTime = __incFieldWithInit(); #记录最后修改时间
kCatalogFieldMemo           = __incFieldWithInit(); #备注
kCatalogFieldHelpInt        = __incFieldWithInit(); #辅助信息,只为客户端保存
kCatalogFieldHelpText       = __incFieldWithInit(); #辅助信息,只为客户端保存
def _CatalogCreateTableSQL():
    "创建目录表SQL语句"
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                path varchar(200) collate nocase UNIQUE,
                rootId  integer,
                parentId integer,
                name varchar(100) collate nocase,
                createTime timestamp default 0,
                lastModifyTime timestamp default 0,
                memo varchar(1024),
                helpInt integer,
                helpText text
            )""" % _kCatalogTableName;


"""
文件表
"""
_kFileTableName = "Files";
kFileFieldId                    = __incFieldWithInit(True); #ID
kFileFieldRootCatalogId         = __incFieldWithInit(); #所属根目录ID
kFileFieldCatalogId             = __incFieldWithInit(); #对应的路径ID
kFileFieldFileName              = __incFieldWithInit(); #文件名称,不包括路径
kFileFieldName                  = __incFieldWithInit(); #显示名称,默认为空
kFileFieldCreateTime            = __incFieldWithInit(); #创建时间
kFileFieldUploadTime            = __incFieldWithInit(); #上传时间
kFileFieldImportTime            = __incFieldWithInit(); #导入时间
kFileFieldLastModifyTime        = __incFieldWithInit(); #最后更新时间
kFileFieldSize                  = __incFieldWithInit(); #文件大小
kFileFieldType                  = __incFieldWithInit(); #文件类型,定义为: FileType
kFileFieldDuration              = __incFieldWithInit(); #持续时间
kFileFieldWidth                 = __incFieldWithInit(); #宽度
kFileFieldHeight                = __incFieldWithInit(); #高度
kFileFieldThumbFileStatus       = __incFieldWithInit(); #缩略图状态, 参考 defines.FileStatus
kFileFieldScreenThumbFileStatus = __incFieldWithInit(); #更大的缩略图状态
kFileFieldOriginFileStatus      = __incFieldWithInit(); #原始文件状态
kFileFieldOrientation           = __incFieldWithInit(); #对于原始文件是图片的可能有效,表示图片方向
kFileFieldMemo                  = __incFieldWithInit(); #备注
kFileFieldHelpInt               = __incFieldWithInit(); #辅助信息,只为客户端保存
kFileFieldHelpText              = __incFieldWithInit(); #辅助信息,只为客户端保存
def _FileCreateTableSQL():
    "创建文件表SQL语句"
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                rootCatalogId integer,
                catalogId integer,
                fileName varchar(100) collate nocase,
                name varchar(100) collate nocase,
                createTime timestamp,
                uploadTime timestamp,
                importTime timestamp,
                lastModifyTime timestamp,
                size integer,
                type integer,
                duration double default 0,
                width integer,
                height integer,
                thumbFileStatus char DEFAULT(0),
                screenThumbFileStatus char DEFAULT(0),
                originFileStatus char,
                orientation char default(0),
                memo varchar(1024),
                helpInt integer,
                helpText text,
                unique(catalogId, fileName)
            )""" % _kFileTableName;


"""
用户的关联表
"""
_kUserAssociateTableName = "UserAssociate";
kUserAssociateFieldId               = __incFieldWithInit(True); #ID
kUserAssociateFieldUserId           = __incFieldWithInit(); #用户ID
kUserAssociateFieldRootCatalogId    = __incFieldWithInit(); #关联的
def _UserAssociateCreateTableSQL():
    "创建用户与目录的关联表"
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                userId integer not null,
                rootCatalogId integer not null,
                unique(userId, rootCatalogId)
            )""" % _kUserAssociateTableName;



"""

数据库管理类

"""
class DataManager(JxdSqlDataBasic):
    "数据库管理类"
#lifecycle
    def __init__(self, aFileName=None):
        "初始化"
        if aFileName is None:
            aFileName = os.path.join(sys.path[0], "dataManager.db");
        JxdSqlDataBasic.__init__(self, aFileName);
        cur = self.cursor();
        cur.execute(_UserCreateTableSQL());
        cur.execute(_CatalogCreateTableSQL());
        cur.execute(_UserAssociateCreateTableSQL());
        cur.execute(_FileCreateTableSQL());
        cur.close();


#public function -- User
    def makeUser(self, aUserName, aPassword):
        "若插入不成功,则判断修改密码,返回ID"
        fieldValues = {
                "name": aUserName,
                "password": aPassword,
                "createTime": time.time(), 
                "lastLoginDate": time.time()};
        nId = self.insert(_kUserTableName, fieldValues);
        if nId is None:
            #插入不成功,正常情况是数据已经存在
            row = self.select(_kUserTableName, {"name": aUserName});
            if row is None:
                log.logObject().log(logging.ERROR, "无法创建用户 %s" % aUserName);
                return None;
            nId = row[kUserFieldId];
            if aPassword and len(aPassword) > 0 and row[kUserFieldPassword] != aPassword:
                self.update(_kUserTableName, {"id": nId}, {"password": aPassword});
        return nId;

    def getUser(self, aUserName, aPassword):
        "根据用户跟密码查询,若成功,则更新登陆时间"
        row = self.select(_kUserTableName, {"name": aUserName, "password": aPassword});
        if row is None:
            #查询不到直接退出
            return None;

        #更新最后登陆时间
        self.update(_kUserTableName, {"id": row[kUserFieldId]}, {"lastLoginDate": time.time()});
        return row;


#public function - Catalog
    def getCatalogByPath(self, aPath):
        "根据路径,获取目录信息,不存在返回None"
        return self.select(_kCatalogTableName, {"path": os.path.abspath(aPath)});

    def getCatalogById(self, aId):
        "根据Id,获取目录信息,不存在返回None"
        return self.select(_kCatalogTableName, {"id": aId});

    def getCatalogByIdAndRootIds(self, aId, aRootIds):
        "获取指定 Id 的目录信息"
        return self.select(_kCatalogTableName, {"id": aId, (lambda :"rootId in ({})".format(aRootIds)): None})

    def getCatalogsByParentIds(self, aParentIds, aRootIds):
        "获取在RootIds下的所有aParentIds数据"
        where = {}
        if aRootIds != None:
            where[lambda :"rootId in ({})".format(aRootIds)] = None
        if aParentIds != None:
            where[lambda :"parentId in ({})".format(aParentIds)] = None
        return self.select(_kCatalogTableName, where, aOneRecord=False)

    def getCatalogState(self, aId):
        "获取指定目录的子目录数量,文件数量; 此SQL语句后续可优化,与getCatalogsByParentIds一起查询出来"
        return self.fetch("""select * from
                                (select count(1) from catalog where parentid==?),
                                (select count(1) from files where catalogid==?)
                """, (aId, aId));

    def makeCatalog(self, aCatalogInfo):
        """创建目录,aCatalogInfo["path"] 必须存在
        若已存在目录,只则更新更新
        若需要插入数据时:
            rootId与parentId存在,则直接插入.此时外部必须确定提供的数据有效
            否则,先查询其父目录,再根据情况插入
        :returns: 指定目录的信息

        """
        strPath = aCatalogInfo["path"]
        row = self.getCatalogByPath(strPath)
        nId = None
        if row:
            nId = row[kCatalogFieldId]
            aCatalogInfo.pop("path")
            aCatalogInfo.pop("rootId", None)
            aCatalogInfo.pop("parentId", None)
            self.updateCatalog(nId, aCatalogInfo, None)
        else:
            strPath = os.path.abspath(strPath)
            aCatalogInfo["path"] = strPath
            nParentId = aCatalogInfo.get("parentId")
            nRootId = aCatalogInfo.get("rootId")
            if nParentId == None or nRootId == None:
                pci = None
                if nParentId == None:
                    parentPath = os.path.dirname(strPath)
                    pci = self.getCatalogByPath(parentPath)
                else:
                    pci = self.getCatalogById(nParentId)
                aCatalogInfo["parentId"] = pci[kCatalogFieldId] if pci else -1
                aCatalogInfo["rootId"] = pci[kCatalogFieldRootId] if pci else -1

            nId = self.insert(_kCatalogTableName, aCatalogInfo)
        result = self.select(_kCatalogTableName, {"id": nId})
        if result and result[kCatalogFieldRootId] == -1:
            result = list(result)
            result[kCatalogFieldRootId] = nId
            self.update(_kCatalogTableName, {"id": nId}, {"rootId": nId})
        return result

    def updateCatalog(self, aId, aCatalogInfo, aRootIds):
        "更新目录信息, 若需要修改 parentId, 则可能需要修改rootId和所对应的File的rootCatalogId"
        bUpdateFileTable = False
        nNewRootId = None
        if aRootIds != None:
            # 只有传递 rootids 信息时,才进行修改(客户端才需要传递)
            nNewParentId = aCatalogInfo.get("parentId")
            if nNewParentId != None:
                row = self.select(_kCatalogTableName, {
                    (lambda :"id in ({},{})".format(aId, nNewParentId)): None,
                    (lambda :"rootId in ({})".format(aRootIds)): None}, aOneRecord=False)
                if row != None and len(row) == 2:
                    nOldRootId = row[0][kCatalogFieldRootId]
                    nNewRootId = row[1][kCatalogFieldRootId]
                    if nOldRootId != nNewRootId:
                        bUpdateFileTable = True
                        aCatalogInfo["rootId"] = nNewRootId
                else:
                    return False

        #更新Catalog表
        afv = None;
        if aCatalogInfo.get("lastModifyTime") == None:
            afv = {"lastModifyTime": time.time()};
        bOK = self.update(_kCatalogTableName, {"id": aId,
            (lambda :"rootId in ({})".format(aRootIds) if aRootIds != None else None): None}, aCatalogInfo, afv);

        #更新File表
        if bOK and bUpdateFileTable:
            bOK = self.update(_kFileTableName, {"catalogId": aId}, {"rootCatalogId": nNewRootId})
        return bOK

    def checkUpdateCatelogRootInfo(self, aUserId):
        "判断指定的用户的根目录是否需要更新"
        associateRootIds = self.getUserRootCatalogs(aUserId);
        for rootId in associateRootIds:
            catInfo = self.getCatalogById(rootId);
            parentPath = os.path.dirname(catInfo[kCatalogFieldPath]);
            parentCatInfo = self.getCatalogByPath(parentPath);
            if parentCatInfo:
                self.update(_kCatalogTableName, {"id": rootId}, 
                        {"rootId": parentCatInfo[kCatalogFieldRootId],
                         "parentId": parentCatInfo[kCatalogFieldId]});
                self.update(_kCatalogTableName, {"rootId": rootId}, 
                        {"rootId": parentCatInfo[kCatalogFieldRootId]});
                self.delete(_kUserAssociateTableName, {"rootCatalogId": rootId});
                self.update(_kFileTableName, {"rootCatalogId": rootId}, 
                        {"rootCatalogId": parentCatInfo[kCatalogFieldRootId]})

    def deleteCatalogs(self, aIds, aRootIds):
        "删除指定目录"
        if aIds == None or aRootIds == None:
            return
        rows = self.select(_kCatalogTableName, {(lambda :"rootId in ({})".format(aRootIds)): None,
            (lambda :"id in ({})".format(aIds)): None,
            (lambda :"parentId != -1"): None}, aOneRecord=False)

        self._loopDeleteCatalogRecords(rows)
        for item in rows:
            path = item[kCatalogFieldPath]
            # 使用 shell 删除
            import subprocess
            subprocess.Popen("rm -rf '{}'".format(path), shell=True)


    def _loopDeleteCatalogRecords(self, aParentRows):
        "递归删除指定目录的子目录与相关文件的数据库记录"
        if not aParentRows or len(aParentRows) == 0:
            return
        cids = ""
        for item in aParentRows:
            nid = item[kCatalogFieldId]
            if len(cids) > 0:
                cids += ",{}".format(nid)
            else:
                cids = "{}".format(nid)

        # 删除文件
        self.delete(_kFileTableName, {(lambda :"catalogId in ({})".format(cids)): None})

        # 删除信息
        self.delete(_kCatalogTableName, {(lambda :"id in ({})".format(cids)): None})

        # 删除子目录
        rows = self.select(_kCatalogTableName, {(lambda :"parentId in ({})".format(cids)): None}, aOneRecord=False)
        self._loopDeleteCatalogRecords(rows)


#public function - File
    def getFileByCatalogId(self, aCatalogId, aFileName):
        "根据指定目录 ID 和文件名获取文件信息"
        return self.select(_kFileTableName, {"catalogId": aCatalogId, "fileName": aFileName});

    def addFile(self, aRootCatalogId, aCatalogId, aFileName, aFileType, aSize, aCreateTime,\
            aWidth=None, aHeight=None, aName=None, aUploadTime=None, aImportTime=None, \
            aThumbFileStatus=defines.kFileStatusFormLocal, aScreenThumbFileStatus= defines.kFileStatusFormLocal,\
            aOriginFileStatus=defines.kFileStatusFormLocal, aOrientation=0,aMemo=None,  \
            aDuration=None, aHelpInt=None, aHelpText=None):
        "添加文件信息"
        fv = {"rootCatalogId": aRootCatalogId,
              "catalogId": aCatalogId,
              "fileName": aFileName,
              "name": aName,
              "createTime": aCreateTime,
              "uploadTime": aUploadTime,
              "importTime": aImportTime if aImportTime else time.time(),
              "lastModifyTime": time.time(),
              "size": aSize,
              "type": aFileType,
              "duration": aDuration,
              "width": aWidth,
              "height": aHeight,
              "thumbFileStatus": aThumbFileStatus,
              "screenThumbFileStatus": aScreenThumbFileStatus,
              "originFileStatus": aOriginFileStatus,
              "orientation": aOrientation,
              "memo": aMemo,
              "helpInt": aHelpInt,
              "helpText": aHelpText};
        return self.insert(_kFileTableName, fv);

    def updateFile(self, aId, aName=None, aHelpInt=None, aHelpText=None, \
            aUploadTime=None, aImportTime=None, aWidth=None, aHeight=None, aDuration=None, \
            aRootCatalogId=None, aCatalogId=None, aFileType=None, aSize=None, aFileName=None):
        "更新文件信息"
        fv = {"rootCatalogId": aRootCatalogId,
              "catalogId": aCatalogId,
              "fileName": aFileName,
              "name": aName,
              "uploadTime": aUploadTime,
              "importTime": aImportTime,
              "size": aSize,
              "type": aFileType,
              "duration": aDuration,
              "width": aWidth,
              "height": aHeight,
              "helpInt": aHelpInt,
              "helpText": aHelpText};
        afv = {"lastModifyTime": time.time()};
        return self.update(_kFileTableName, {"id": aId}, fv, afv);

    def getFileWithRootAndId(self, aStrRootIds, aFileId):
        """获取指定 Id 的文件信息

        :aStrRootIds: 所有目录 ID
        :aFileId: 文件 Id
        """
        sql = "select * from %s where id=? and rootCatalogId in(%s)" % (_kFileTableName, aStrRootIds);
        return self.fetch(sql, (aFileId,));

    def getFiles(self, aStrPathIds, aStrRootIds, aPageIndex, aMaxPerPage, aStrTypes, aSort):
        """查找指定路径下的文件内容

        :aStrPathIds: 所属目录ID
        :aStrRootIds: 根目录Id, 用于权限判断
        :aPageIndex: 第几页
        :aMaxPerPage: 每页最大数量
        :aStrTypes: 类型,详细见ReadMe.md文件
        :aSort: 排序的方式: 1->文件创建时间, 2->上传时间, 3->文件大小, 4->持续时间, 5->文件尺寸
                    >0表示升序, <0表示降序
        :returns: list
        """
        nLimitCount = aMaxPerPage if aMaxPerPage > 0 else 10;
        nLimitBegin =  aPageIndex * nLimitCount;

        strOrderMethod = "asc" if aSort > 0 else "desc";
        strOrder = "order by %s " + strOrderMethod;
        if aSort < 0:
            aSort = -aSort;
        if aSort == 1:
            # 文件创建时间
            strOrder = strOrder % "createTime";
        elif aSort == 2:
            #上传时间
            strOrder = strOrder % "uploadTime";
        elif aSort == 3:
            #文件大小
            strOrder = strOrder % "size";
        elif aSort == 4:
            #持续时间
            strOrder = strOrder % "duration";
        elif aSort == 5:
            #文件尺寸
            strOrder = strOrder % ("width %s, height" % strOrderMethod);
        else:
            strOrder = "";

        sqlTypes = "";
        if aStrTypes:
            sqlTypes = " and type in ({}) ".format(aStrTypes);

        #文件项内容
        sql = """select * from {table} where catalogId in ({pathIds}) and rootCatalogId in({rootId}) 
                    {types} {order} limit {begin},{count}
        """.format(table=_kFileTableName, pathIds=aStrPathIds, rootId=aStrRootIds, 
                    types=sqlTypes, order=strOrder, begin=nLimitBegin, count=nLimitCount);
        # print(sql);
        fileInfos = self.fetch(sql, None, False);

        #分页信息
        sql = """select count(1) from {table} where catalogId in ({pathIds}) and rootCatalogId in({rootId}) 
                    {types}
        """.format(table=_kFileTableName, pathIds=aStrPathIds, rootId=aStrRootIds, 
                    types=sqlTypes);
        # print(sql);
        dbCount = self.fetch(sql);
        nItemCount = dbCount[0] if dbCount else 0;
        return fileInfos, {"pageIndex": aPageIndex,
                            "maxPerPage": nLimitCount,
                            "pageCount": (nItemCount + nLimitCount - 1) // nLimitCount};



#public function - UserAssociate
    def makeUserAssociate(self, aUserId, aRootCatalogId):
        "插入一条关联数据"
        return self.insert(_kUserAssociateTableName, {"userId": aUserId, "rootCatalogId": aRootCatalogId});

    def getUserRootCatalogs(self, aUserId):
        "获取指定用户下所有的关联根目录ID"
        rows = self.select(_kUserAssociateTableName, {"userId": aUserId}, "rootCatalogId", False);
        if rows:
            result = [];
            for item in rows:
                result.append(item[0]);
            rows = result;
        return rows;

#public function - help info
    def _buildHelpQueryInfo(self, aTableType, aRecordId, aStrRootIds=None):
        where = {"id": aRecordId}
        strTableName = None
        if aTableType == 0:
            # 用户表
            strTableName = _kUserTableName
        elif aTableType == 1:
            # 目录表
            where[lambda :"rootId in (?)"] = aStrRootIds
            strTableName = _kCatalogTableName
        else:
            where[lambda :"rootCatalogId in (?)"] = aStrRootIds
            strTableName = _kFileTableName
        return strTableName, where

    def getHelpInfo(self, aTableType, aRecordId, aStrRootIds=None):
        "从不同的表中获取不同的HelpInfo信息"
        strTableName, where = self._buildHelpQueryInfo(aTableType, aRecordId, aStrRootIds)
        return self.select(strTableName, where, "helpInt, helpText, lastModifyTime")

    def setHelpInfo(self, aTableType, aRecordId, aHelpInt, aHelpText, aStrRootIds=None):
        "设置不同表记录的HelpInfo信息"
        strTableName, where = self._buildHelpQueryInfo(aTableType, aRecordId, aStrRootIds)
        self.update(strTableName, where, {"helpInt": aHelpInt, "helpText": aHelpText}, 
                {"lastModifyTime": time.time()})

#private function
    def _makeValue(self, aDict, aKey, aDefaultValue):
        v = aDict.get(aKey)
        if v == None:
            aDict[aKey] = aDefaultValue



#help function - global
def buildUserInfo(aUserRow):
    "根据用户表信息生成发送给客户端的userInfo"
    userInfo = {"name": aUserRow[kUserFieldName],
            "createTime": aUserRow[kUserFieldCreateTime],
            "lastLoginDate": aUserRow[kUserFieldLastLoginDate],
            "lastModifyTime": aUserRow[kUserFieldLastModifyTime],
            "helpInt": aUserRow[kUserFieldHelpInt],
            "helpText": aUserRow[kUserFieldHelpText]};
    unit.filterNullValue(userInfo)
    return userInfo

def buildCatalogInfo(aCatalogRow, aDbObject):
    "根据数据库查询到的信息生成发送给客户端的catalogInfo"
    strName = aCatalogRow[kCatalogFieldName]
    if strName is None:
        strName = aCatalogRow[kCatalogFieldPath]
        strName = os.path.basename(strName)
    cid = aCatalogRow[kCatalogFieldId]
    catalogInfo = {"id": cid,
        "rootId": aCatalogRow[kCatalogFieldRootId],
        "parentId": aCatalogRow[kCatalogFieldParentId],
        "name": strName,
        "createTime": aCatalogRow[kCatalogFieldCreateTime],
        "lastModifyTime": aCatalogRow[kCatalogFieldLastModifyTime],
        "memo": aCatalogRow[kCatalogFieldMemo],
        "helpInt": aCatalogRow[kCatalogFieldHelpInt],
        "helpText": aCatalogRow[kCatalogFieldHelpText]}
    if aDbObject:
        subStates = aDbObject.getCatalogState(cid)
        if subStates and len(subStates) > 1:
            catalogInfo["subCatalogCount"] = subStates[0]
            catalogInfo["fileCount"] = subStates[1]
    unit.filterNullValue(catalogInfo)
    return catalogInfo

if __name__ == "__main__":
    print("begin test")
    db = DataManager()
    db.updateCatalog(9, {"parentId": 1, "name": "moveTest"}, "1")
    # db.deleteCatalogs("3, 4,5", "1,2,3")
    # db.makeCatalog({"path": "/A/B/1"})
    # db.makeCatalog({"path": "/a/b/"})
    # print(db.makeCatalog({"path": "/A/c/a/b/c", "parentId":4, "helpInt": "123"}))
    print("finished")
