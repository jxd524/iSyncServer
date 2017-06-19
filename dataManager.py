#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理
db manager
"""

__author__="Terry<jxd524@163.com>"

import os, sys
import shutil
from jxdsqlite import JxdSqlDataBasic
import defines, log, unit
from unit import formatInField
from unit import formatNotInField
from unit import makeValue

"""
方便定义字段序号
for easily define db table field index
"""
__gFieldIndex = 0
def __incFieldWithInit(aInit=None):
    global __gFieldIndex
    if aInit:
        __gFieldIndex = 0
    nResult = __gFieldIndex
    __gFieldIndex += 1
    return nResult


"""
用户表
记录所有用户信息

user table
"""
_kUserTableName = "User"
kUserFieldId                        = __incFieldWithInit(True)   #ID
kUserFieldName                      = __incFieldWithInit() #用户名
kUserFieldPassword                  = __incFieldWithInit() #用户密码
kUserFieldCreateTime                = __incFieldWithInit() #创建时间
kUserFieldLastLoginDate             = __incFieldWithInit() #最后登陆时间
kUserFieldLastModifyTime            = __incFieldWithInit() #针对HelpInfo,最后修改时间
kUserFieldHelpInt                   = __incFieldWithInit() #辅助Int,只对客户端有意义,服务端只负责保存
kUserFieldHelpText                  = __incFieldWithInit() #辅助信息,只对客户端有意思
def _UserCreateTableSQL():
    """
    创建用户表的SQL语句
    sql for create user table
    """
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                name varchar(100) collate nocase UNIQUE,
                password varchar(32),
                createTime integer,
                lastLoginDate integer,
                lastModifyTime integer,
                helpInt integer,
                helpText text
            )""" % _kUserTableName


"""
目录表
"""
_kCatalogTableName = "Catalog"
kCatalogFieldId             = __incFieldWithInit(True) #ID
kCatalogFieldPath           = __incFieldWithInit() #具体全路径
kCatalogFieldRootId         = __incFieldWithInit() #根路径ID
kCatalogFieldParentId       = __incFieldWithInit() #父路径ID
kCatalogFieldName           = __incFieldWithInit() #在客户端显示的名称
kCatalogFieldCreateTime     = __incFieldWithInit() #记录创建时间
kCatalogFieldLastModifyTime = __incFieldWithInit() #记录最后修改时间
kCatalogFieldMemo           = __incFieldWithInit() #备注
kCatalogFieldHelpInt        = __incFieldWithInit() #辅助信息,只为客户端保存
kCatalogFieldHelpText       = __incFieldWithInit() #辅助信息,只为客户端保存
def _CatalogCreateTableSQL():
    "创建目录表SQL语句"
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                path varchar(200) collate nocase UNIQUE,
                rootId  integer,
                parentId integer,
                name varchar(100) collate nocase,
                createTime integer,
                lastModifyTime integer,
                memo varchar(1024),
                helpInt integer,
                helpText text
            )""" % _kCatalogTableName


"""
文件表
"""
_kFileTableName = "Files"
kFileFieldId                    = __incFieldWithInit(True) #ID
kFileFieldUploadUserId          = __incFieldWithInit() #文件的上传者
kFileFieldRootCatalogId         = __incFieldWithInit() #所属根目录ID
kFileFieldCatalogId             = __incFieldWithInit() #对应的路径ID,此值可被修改
kFileFieldRealCatalogId         = __incFieldWithInit() #对应的路径ID,此值不被修改,指明实际的位置
kFileFieldFileName              = __incFieldWithInit() #文件名称,不包括路径
kFileFieldExt                   = __incFieldWithInit() #文件扩展名,不包括"."
kFileFieldName                  = __incFieldWithInit() #显示名称,默认为空
kFileFieldCreateTime            = __incFieldWithInit() #创建时间
kFileFieldUploadTime            = __incFieldWithInit() #上传时间
kFileFieldImportTime            = __incFieldWithInit() #导入时间
kFileFieldLastModifyTime        = __incFieldWithInit() #最后更新时间
kFileFieldSize                  = __incFieldWithInit() #文件大小
kFileFieldType                  = __incFieldWithInit() #文件类型,定义为: FileType
kFileFieldDuration              = __incFieldWithInit() #持续时间
kFileFieldWidth                 = __incFieldWithInit() #宽度
kFileFieldHeight                = __incFieldWithInit() #高度
kFileFieldStatusForThumb        = __incFieldWithInit() #缩略图状态, 参考 defines.FileStatus
kFileFieldStatusForScreen       = __incFieldWithInit() #更大的缩略图状态
kFileFieldStatusForOrigin       = __incFieldWithInit() #原始文件状态
kFileFieldOrientation           = __incFieldWithInit() #对于原始文件是图片的可能有效,表示图片方向
kFileFieldMemo                  = __incFieldWithInit() #备注
kFileFieldHelpInt               = __incFieldWithInit() #辅助信息,只为客户端保存
kFileFieldHelpText              = __incFieldWithInit() #辅助信息,只为客户端保存
def _FileCreateTableSQL():
    "创建文件表SQL语句"
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                uploadUserId integer,
                rootCatalogId integer,
                catalogId integer,
                realCatalogId integer,
                fileName varchar(100) collate nocase,
                ext varchar(10)  collate nocase,
                name varchar(100) collate nocase,
                createTime integer,
                uploadTime integer,
                importTime integer,
                lastModifyTime integer,
                size integer,
                type integer,
                duration float,
                width integer,
                height integer,
                statusForThumb integer,
                statusForScreen integer,
                statusForOrigin integer,
                orientation integer,
                memo varchar(1024),
                helpInt integer,
                helpText text,
                unique(realCatalogId, fileName)
            )""" % _kFileTableName


"""
用户的关联表
"""
_kUserAssociateTableName = "UserAssociate"
kUserAssociateFieldId               = __incFieldWithInit(True) #ID
kUserAssociateFieldUserId           = __incFieldWithInit() #用户ID
kUserAssociateFieldRootCatalogId    = __incFieldWithInit() #关联的
def _UserAssociateCreateTableSQL():
    "创建用户与目录的关联表"
    return """Create Table if not exists %s(
                id integer primary key autoIncrement,
                userId integer not null,
                rootCatalogId integer not null,
                unique(userId, rootCatalogId)
            )""" % _kUserAssociateTableName

# 后续不需要再使用此变量了
del __gFieldIndex

"""

数据库管理类

"""
class DataManager(JxdSqlDataBasic):
    "数据库管理类"
#lifecycle
    def __init__(self, aFileName=None):
        "初始化"
        if aFileName is None:
            aFileName = os.path.join(sys.path[0], "dataManager.db")
        JxdSqlDataBasic.__init__(self, aFileName)
        cur = self.cursor()
        cur.execute(_UserCreateTableSQL())
        cur.execute(_CatalogCreateTableSQL())
        cur.execute(_UserAssociateCreateTableSQL())
        cur.execute(_FileCreateTableSQL())
        cur.close()


#public function -- User
    def makeUser(self, aUserName, aPassword):
        "若插入不成功,则判断修改密码,返回ID"
        curTime = unit.getTimeInt()
        fieldValues = {
                "name": aUserName,
                "password": aPassword,
                "createTime": curTime,
                "lastLoginDate": curTime,
                "lastModifyTime": curTime}
        nId = self.insert(_kUserTableName, fieldValues)
        if nId is None:
            #插入不成功,正常情况是数据已经存在
            row = self.select(_kUserTableName, {"name": aUserName})
            if row is None:
                log.logObject().log(logging.ERROR, "无法创建用户 %s" % aUserName)
                return None
            nId = row[kUserFieldId]
            if aPassword and len(aPassword) > 0 and row[kUserFieldPassword] != aPassword:
                self.update(_kUserTableName, {"id": nId}, {"password": aPassword})
        return nId


    def getUser(self, aUserName, aPassword):
        "根据用户跟密码查询,若成功,则更新登陆时间"
        row = self.select(_kUserTableName, {"name": aUserName, "password": aPassword})
        if row is None:
            #查询不到直接退出
            return None

        #更新最后登陆时间
        self.update(_kUserTableName, {"id": row[kUserFieldId]}, {"lastLoginDate": unit.getTimeInt()})
        return row


#public function - Catalog
    def getCatalogByPath(self, aPath):
        "根据路径,获取目录信息,不存在返回None"
        return self.select(_kCatalogTableName, {"path": os.path.abspath(aPath)})


    def getCatalogById(self, aId):
        "根据Id,获取目录信息,不存在返回None"
        return self.select(_kCatalogTableName, {"id": aId})


    def getCatalogByIdAndRootIds(self, aId, aLimitStrRootIds):
        "获取指定 Id 的目录信息"
        return self.select(_kCatalogTableName, {"id": aId, formatInField("rootId", aLimitStrRootIds): None})


    def getCatalogsByParentIds(self, aParentIds, aLimitStrRootIds):
        "获取在RootIds下的所有aParentIds数据"
        return self.select(_kCatalogTableName, 
                {formatInField("rootId", aLimitStrRootIds): None,
                    formatInField("parentId", aParentIds): None},
                aOneRecord=False)


    def getCatalogState(self, aId):
        "获取指定目录的子目录数量,文件数量 此SQL语句后续可优化,与getCatalogsByParentIds一起查询出来"
        return self.fetch("""select * from
                                (select count(1) from catalog where parentid==?),
                                (select count(1) from files where catalogid==?)
                """, (aId, aId))


    def getCatalogIdRelatePathInfo(self, aStrIds):
        "获取指定id所对应的路径信息,组成 [id] = path 的格式"
        rows = self.select(_kCatalogTableName, {formatInField("id", aStrIds): None}, "id, path", False)
        result = {}
        for item in rows:
            result[item[0]] = item[1]
        return result


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

            aCatalogInfo["lastModifyTime"] = unit.getTimeInt()
            nId = self.insert(_kCatalogTableName, aCatalogInfo)
        # end if
        result = self.select(_kCatalogTableName, {"id": nId})
        if result and result[kCatalogFieldRootId] == -1:
            result = list(result)
            result[kCatalogFieldRootId] = nId
            self.update(_kCatalogTableName, {"id": nId}, {"rootId": nId})
        return result


    def updateCatalog(self, aId, aCatalogInfo, aLimitStrRootIds):
        "更新目录信息, 若需要修改 parentId, 则可能需要修改rootId和所对应的File的rootCatalogId"
        bUpdateFileTable = False
        nNewRootId = None
        if aLimitStrRootIds != None:
            # 只有传递 rootids 信息时,才进行修改(客户端才需要传递)
            nNewParentId = aCatalogInfo.get("parentId")
            if nNewParentId != None and nNewParentId > 0:
                sql = """select a.rootId as newRootId, b.rootId as curRootid, b.parentId
                    from {table} a, {table} b
                    where a.id = ? and a.rootid in ({limitIds}) and
                        b.id = ? and b.rootid in ({limitIds})
                """.format(table = _kCatalogTableName, limitIds = aLimitStrRootIds)
                # print(sql)
                row = self.fetch(sql, (nNewParentId, aId))
                if not row:
                    return False

                # 判断是否更新
                if nNewParentId == row[2]:
                    aCatalogInfo.pop("parentId")
                elif row[0] != row[1]:
                    bUpdateFileTable = True
                    nNewRootId = row[0]
                    aCatalogInfo["rootId"] = nNewRootId
            else:
                aCatalogInfo.pop("parentId", None)
        else:
            # 若没有rootIds,则不对parentId进行处理
            aCatalogInfo.pop("parentId", None)



        #更新Catalog表
        afv = None
        if not aCatalogInfo.get("lastModifyTime"):
            afv = {"lastModifyTime": unit.getTimeInt()}
        bOK = self.update(_kCatalogTableName, {
            "id": aId,
            formatInField("rootId", aLimitStrRootIds): None},
            aCatalogInfo, afv)

        #更新File表
        if bOK and bUpdateFileTable:
            bOK = self.update(_kFileTableName, {"realCatalogId": aId}, {"rootCatalogId": nNewRootId})
        return bOK


    def checkUpdateCatelogRootInfo(self, aUserId):
        "判断指定的用户的根目录是否需要更新,只在扫描磁盘时起作用"
        associateRootIds = self.getUserRootCatalogs(aUserId)
        for rootId in associateRootIds:
            catInfo = self.getCatalogById(rootId)
            parentPath = os.path.dirname(catInfo[kCatalogFieldPath])
            parentCatInfo = self.getCatalogByPath(parentPath)
            if parentCatInfo:
                self.update(_kCatalogTableName, {"id": rootId}, 
                        {"rootId": parentCatInfo[kCatalogFieldRootId],
                            "parentId": parentCatInfo[kCatalogFieldId]})
                self.update(_kCatalogTableName, {"rootId": rootId}, 
                        {"rootId": parentCatInfo[kCatalogFieldRootId]})
                self.delete(_kUserAssociateTableName, {"rootCatalogId": rootId})
                self.update(_kFileTableName, {"rootCatalogId": rootId}, 
                        {"rootCatalogId": parentCatInfo[kCatalogFieldRootId]})


    def deleteCatalogs(self, aDelCids, aLimitStrRootIds):
        "删除指定目录"
        if aDelCids == None or aLimitStrRootIds == None:
            return
        #递归查询所有将被删除的目录信息
        sql = """
            with recursive
                cids(x) AS(
                    select id from {table} 
                        where id in ({ids}) and rootId in ({limitIds})
                    union all
                    select id from {table}, cids
                        where {table}.parentid = cids.x
                )
            select * from {table} where {table}.id in cids
            """.format(table=_kCatalogTableName, ids=aDelCids, limitIds=aLimitStrRootIds)
        rows = self.fetch(sql, fetchone = False)
        if not rows or len(rows) == 0:
            return

        waitDeletePaths = []
        for item in rows:
            s = item[kCatalogFieldPath]
            s = s.lower()
            waitDeletePaths.append(s)

        #移动目录下的所有挂接到别的目录的子目录到实际位置
        self._copySubCatalogToRealPath(waitDeletePaths)

        #组合所有目录id
        cids = unit.buildFormatString(rows, kCatalogFieldId)

        #删除所有挂接在目录下的所有文件的缩略图
        self._clearAllBuildFiles(cids)

        #所有挂接到此目录下,但实际位置在其它目录的文件,删除之
        self._queryWaitDeleteFiles(cids, waitDeletePaths)

        #所有实际在此目录,但已经挂接到其它目录下的,移动文件并修改realCatalogId
        self._moveFilesToNewPath(cids)

        #删除记录
        self.delete(_kCatalogTableName, {formatInField("id",cids): None})
        self.delete(_kFileTableName, {formatInField("catalogId", cids): None})
        self.delete(_kUserAssociateTableName, {formatInField("rootCatalogId", aLimitStrRootIds): None})

        #删除文件
        unit.removePath(waitDeletePaths)


    def _clearAllBuildFiles(self, aCids):
        rows = self.select(_kFileTableName, {formatInField("catalogId", aCids): None}, aOneRecord = False)
        if rows and len(rows) > 0:
            self._defFilesRes(rows, 2)


    def _queryWaitDeleteFiles(self, aCids, aToList):
        deleteFileRows = self.select(_kFileTableName, {
            formatInField("catalogId", aCids): None,
            formatNotInField("realCatalogId", aCids): None}, aOneRecord = False)
        if deleteFileRows and len(deleteFileRows) > 0:
            self._defFilesRes(deleteFileRows, 1, aToList)

    def _moveFilesToNewPath(self, aCids):
        moveFileRows = self.select(_kFileTableName, {
            formatInField("realCatalogId", aCids): None,
            formatNotInField("catalogId", aCids): None}, aOneRecord = False)
        if moveFileRows and len(moveFileRows) > 0:
            srcIds = unit.buildFormatString(moveFileRows, kFileFieldRealCatalogId)
            destIds = unit.buildFormatString(moveFileRows, kFileFieldCatalogId)
            srcInfo = self.getCatalogIdRelatePathInfo(srcIds)
            destInfo = self.getCatalogIdRelatePathInfo(destIds)
            for item in moveFileRows:
                newInfo = {"realCatalogId": item[kFileFieldCatalogId]}
                newPath = destInfo[item[kFileFieldCatalogId]]
                srcPath = srcInfo[item[kFileFieldRealCatalogId]]
                srcName = item[kFileFieldFileName]
                srcFile = os.path.join(srcPath, srcName)
                if not unit.moveFile(srcFile, newPath):
                    if not item[kFileFieldName]:
                        newInfo["name"] = srcName

                    i = 1
                    newRenameFile = None
                    while True:
                        srcTempName = srcName
                        ls = srcTempName.split(".")
                        if ls and len(ls) > 1:
                            ls[-2] = ls[-2] + "_{}".format(i)
                            srcTempName = unit.buildFormatString(ls, 0, aSpace=".")
                        else:
                            srcTempName += "_{}".format(i)
                        i += 1
                        newRenameFile = os.path.join(newPath, srcTempName)
                        if not os.path.exists(newRenameFile):
                            if unit.moveFile(srcFile, newRenameFile):
                                newInfo["filename"] = srcTempName
                                break;
                    #end while
                #end if
                self.update(_kFileTableName, {"id": item[kFileFieldId]}, newInfo)
            #end for

    def _copySubCatalogToRealPath(self, aPaths):
        "将已挂靠在不需要删除的子目录下的所有文件,复制一份到指定目录"
        for item in aPaths:
            self._judgeToMove(item, aPaths)
    def _judgeToMove(self, aParentPath, aMovePaths):
        ls = os.listdir(aParentPath)
        for item in ls:
            strPath = os.path.join(aParentPath, item)
            if os.path.isdir(strPath):
                strPath = strPath.lower()
                if strPath not in aMovePaths:
                    # 需要移动
                    self._copyToRealPath(strPath)
                self._judgeToMove(strPath, aMovePaths)

    def _copyToRealPath(self, aPath):
        "指定路径,根据记录,移动所有文件到新的目录下,不包含其子目录"
        row = self.getCatalogByPath(aPath)
        if not row:
            return
        nId = row[kCatalogFieldId]
        param = {}
        strOldPath = row[kCatalogFieldPath]
        strCurDirName = row[kCatalogFieldName]
        if not strCurDirName:
            strCurDirName = os.path.basename(strOldPath)
            param["name"] = strCurDirName

        parentRow = self.getCatalogById(row[kCatalogFieldParentId])
        strParentPath = parentRow[kCatalogFieldPath]

        strNewPath = os.path.join(strParentPath, strCurDirName)
        i = 0
        while os.path.isdir(strNewPath):
            strName = "{}_{}".format(strCurDirName, i)
            i += 1
            strNewPath = os.path.join(strParentPath, strName)
        os.makedirs(strNewPath)
        param["path"] = strNewPath

        lsFiles = os.listdir(strOldPath)
        for item in lsFiles:
            strFile = os.path.join(strOldPath, item)
            if os.path.isfile(strFile):
                unit.moveFile(strFile, strNewPath)

        self.update(_kCatalogTableName, {"id": nId}, param)



#public function - File
    def getFileByRealCatalogId(self, aRealCatalogId, aFileName, aLimitStrRootIds = None):
        "根据指定目录 ID 和文件名获取文件信息"
        return self.select(_kFileTableName, 
                {"realCatalogId": aRealCatalogId,
                    "fileName": aFileName,
                    formatInField("rootCatalogId", aLimitStrRootIds): None})


    def addFile(self, aRootId, aRealCatalogId, aFileInfo):
        """添加文件信息
            直接添加,调用者必须确保键值的正确性
        """
        curTime = unit.getTimeInt()
        aFileInfo["rootCatalogId"] = aRootId
        aFileInfo["realCatalogId"] = aRealCatalogId
        makeValue(aFileInfo, "catalogId", aRealCatalogId)
        makeValue(aFileInfo, "createTime", curTime)
        makeValue(aFileInfo, "importTime", curTime)
        makeValue(aFileInfo, "lastModifyTime", curTime)
        makeValue(aFileInfo, "statusForThumb", defines.kFileStatusFromLocal)
        makeValue(aFileInfo, "statusForScreen", defines.kFileStatusFromLocal)
        makeValue(aFileInfo, "statusForOrigin", defines.kFileStatusFromLocal)
        return self.insert(_kFileTableName, aFileInfo)


    def updateFile(self, aFileId, aFileInfo, aLimitStrRootIds):
        """更新文件信息
            若存在aLimitStrRootIds和aFileInfo["catalogId"]有效时, 只修改数据信息,不会真正移动文件
        """
        if aLimitStrRootIds != None and aFileInfo.get("catalogId") != None:
            #新位置是否有效s
            nNewCatalogId = aFileInfo["catalogId"]
            sql = """select a.rootId        as newRootId, 
                            b.catalogId     as curCatalogId, 
                            b.rootCatalogId as curRootId
                from {catalogTable} a, {fileTable} b 
                where a.id = ? and a.rootId in ({limitIds}) 
                    and b.id = ? and b.rootCatalogid in ({limitIds})
            """.format(catalogTable = _kCatalogTableName, fileTable = _kFileTableName, 
                    limitIds = aLimitStrRootIds)
            row = self.fetch(sql, (nNewCatalogId, aFileId))
            if not row:
                return False

            #是否要修改 catalogId
            nNewRootId = row[0]
            nCurCatalogId = row[1]
            nCurRootId = row[2]
            if nNewRootId != nCurRootId:
                aFileInfo["rootCatalogId"] = nNewRootId
            if nNewCatalogId == nCurCatalogId:
                aFileInfo.pop("catalogId")

        # 更新数据
        afv = None
        if aFileInfo.get("lastModifyTime") == None:
            afv = {"lastModifyTime": unit.getTimeInt()}
        return self.update(_kFileTableName,
                {"id": aFileId,
                    formatInField("rootCatalogId", aLimitStrRootIds): None}, 
                aFileInfo, afv)


    def getFileByIdAndRootIds(self, aFileId, aLimitStrRootIds):
        """获取指定 Id 的文件信息

        :aFileId: 文件 Id
        :aLimitStrRootIds: 根目录IDs
        """
        return self.select(_kFileTableName, {"id": aFileId, formatInField("rootCatalogId", aLimitStrRootIds): None})


    def deleteFiles(self, aIds, aLimitStrRootIds):
        "删除指定的文件"
        where = {formatInField("id", aIds): None, 
                    formatInField("rootCatalogId", aLimitStrRootIds): None}
        rows = self.select(_kFileTableName, where, aOneRecord = False)
        self._defFilesRes(rows)
        self.delete(_kFileTableName, where)

    def _defFilesRes(self, aFileRows, aDeleteType=3, aOnlyToAddList=None):
        """删除指定文件记录所对应的资源,
        :aDeleteType: 1->只删除原文件
                      2->只删除生成的文件
                      3->删除所有
        :aOnlyToAddList: 若指定,则只将要删除的数据添加到数组
        """
        cids = unit.buildFormatString(aFileRows, kFileFieldRealCatalogId)
        irp = self.getCatalogIdRelatePathInfo(cids)

        removePaths = [];
        for item in aFileRows:
            nCatalogId = item[kFileFieldRealCatalogId]
            nFileId = item[kFileFieldId]
            #原文件
            if aDeleteType & 1:
                strFile = os.path.join(irp[nCatalogId], item[kFileFieldFileName])
                if os.path.isfile(strFile):
                    removePaths.append(strFile)

            #缩略图
            if aDeleteType & 2:
                strFile = unit.getFileThumbFullFileName(nCatalogId, nFileId, 0)
                if os.path.isfile(strFile):
                    removePaths.append(strFile)
                #大缩略图
                strFile = unit.getFileThumbFullFileName(nCatalogId, nFileId, 1)
                if os.path.isfile(strFile):
                    removePaths.append(strFile)

        if len(removePaths) > 0:
            if aOnlyToAddList:
                aOnlyToAddList.extend(removePaths)
            else:
                unit.removePath(removePaths)


    def getFileByUploading(self, aUploadUserId):
        """获取指定用户未上传成功的信息

        :aUploadUserId: 上传用户ID
        """
        values = []
        where = {"statusForOrigin": defines.kFileStatusFromUploading,
                "statusForThumb": defines.kFileStatusFromUploading,
                "statusForScreen": defines.kFileStatusFromUploading}
        values.append(aUploadUserId)
        strWhere = "uploadUserId = ? and ({})".format(self.FormatFieldValues(where, values, "or"))
        sql = "select * from {} where {}".format(_kFileTableName, strWhere)
        # print(sql)
        return self.fetch(sql, values, False)


    def getFiles(self, aRootIds, aPids, aTypes, aUploadUserId, aSort, aPageIndex, aMaxPerPage):
        """查找指定路径下的文件内容, 对应API: file.icc 

        :aRootIds: 根目录Id, 如: 1,2,3 
        :aPids: 所属目录ID, 可能为空
        :aTypes: 文件的类型
        :aUploadUserId: 上传用户Id, None表示不限定
        :aSort: 排序的方式: 1->文件创建时间, 2->上传时间, 3->文件大小, 4->持续时间, 5->文件尺寸
                    >0表示升序, <0表示降序
        :aPageIndex: 第几页
        :aMaxPerPage: 每页最大数量
        :returns: (datelist, pageInfo)
        """
        funcNotEqual = lambda v: lambda :"{} != {}".format(v, defines.kFileStatusFromUploading)
        where = {formatInField("rootCatalogId", aRootIds): None,
                funcNotEqual("statusForOrigin"): None,
                funcNotEqual("statusForThumb"): None,
                funcNotEqual("statusForScreen"): None}
        if aPids and len(aPids) > 0:
            where[formatInField("catalogId", aPids)] = None
        if aTypes and len(aTypes) > 0:
            where[formatInField("type", aTypes)] = None
        if aUploadUserId:
            where[lambda:"uploadUserId = {}".format(aUploadUserId)] = None
        strWhere = self.FormatFieldValues(where, None, "and")

        if aSort != None and aSort != 0:
            nAbsSort = aSort if aSort > 0 else -aSort
            if nAbsSort == 1:
                strSortFieldName = "createTime"
            elif nAbsSort == 2:
                strSortFieldName = "uploadTime"
            elif nAbsSort == 3:
                strSortFieldName = "size"
            elif nAbsSort == 4:
                strSortFieldName = "duration"
            elif nAbsSort == 5:
                strSortFieldName = "width {orderMethod}, height"
            else:
                return None, None
            strWhere += " order by " + strSortFieldName + " {orderMethod}"
            strWhere = strWhere.format(orderMethod = "asc" if aSort > 0 else "desc")

        nLimitCount = aMaxPerPage if aMaxPerPage > 0 else 100
        nLimitBegin =  aPageIndex * nLimitCount

        #查询内容
        strWhere += " limit {begin}, {count}".format(begin = nLimitBegin, count = nLimitCount)
        sql = "select * from {} where {}".format(_kFileTableName, strWhere)
        # print(sql)
        fileInfos = self.fetch(sql, fetchone = False)

        #分页信息
        dbCount = self.select(_kFileTableName, where, aFields = "count(1)")
        nItemCount = dbCount[0] if dbCount else 0
        return fileInfos, {"pageIndex": aPageIndex,
                            "maxPerPage": nLimitCount,
                            "pageCount": (nItemCount + nLimitCount - 1) // nLimitCount}


#public function - UserAssociate
    def makeUserAssociate(self, aUserId, aRootCatalogId):
        "插入一条关联数据"
        return self.insert(_kUserAssociateTableName, {"userId": aUserId, "rootCatalogId": aRootCatalogId})

    def getUserRootCatalogs(self, aUserId):
        "获取指定用户下所有的关联根目录ID"
        rows = self.select(_kUserAssociateTableName, {"userId": aUserId}, "rootCatalogId", False)
        if rows:
            result = []
            for item in rows:
                result.append(item[0])
            rows = result
        return rows

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
                {"lastModifyTime": unit.getTimeInt()})


#help function - global
def buildUserInfo(aUserRow):
    "根据用户表信息生成发送给客户端的userInfo"
    userInfo = {"id": aUserRow[kUserFieldId],
            "name": aUserRow[kUserFieldName],
            "createTime": aUserRow[kUserFieldCreateTime],
            "lastLoginDate": aUserRow[kUserFieldLastLoginDate],
            "lastModifyTime": aUserRow[kUserFieldLastModifyTime],
            "helpInt": aUserRow[kUserFieldHelpInt],
            "helpText": aUserRow[kUserFieldHelpText]}
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

def buildFileInfo(aFileRow, aFuncForPaths):
    """组建单个fileInfo信息, 
    aFuncForPaths: 是一个函数,返回 {catalogId: path} 对象
    或者直接就是一个 {catalogId: path} 对象
    """
    strName = aFileRow[kFileFieldName]
    if strName is None:
        strName = aFileRow[kFileFieldFileName]
    fileInfo = {
            "id": aFileRow[kFileFieldId],
            "uploadUserId": aFileRow[kFileFieldUploadUserId],
            "catalogId": aFileRow[kFileFieldCatalogId],
            "name": strName,
            "ext": aFileRow[kFileFieldExt],
            "createTime": aFileRow[kFileFieldCreateTime],
            "uploadTime": aFileRow[kFileFieldUploadTime],
            "importTime": aFileRow[kFileFieldImportTime],
            "lastModifyTime": aFileRow[kFileFieldLastModifyTime],
            "size": aFileRow[kFileFieldSize],
            "type": aFileRow[kFileFieldType],
            "duration": aFileRow[kFileFieldDuration],
            "width": aFileRow[kFileFieldWidth],
            "height": aFileRow[kFileFieldHeight],
            "orientation": aFileRow[kFileFieldOrientation],
            "memo": aFileRow[kFileFieldMemo],
            "helpInt": aFileRow[kFileFieldHelpInt],
            "helpText": aFileRow[kFileFieldHelpText]}

    def _addUploading(aFullFileName, aUpSizeName):
        nSize = os.stat(aFullFileName).st_size if os.path.isfile(aFullFileName) else 0
        fileInfo[aUpSizeName] = nSize

    if aFileRow[kFileFieldStatusForOrigin] == defines.kFileStatusFromUploading:
        #原始文件上传信息
        cp = aFuncForPaths() if callable(aFuncForPaths) else aFuncForPaths
        fn = os.path.join(cp[aFileRow[kFileFieldRealCatalogId]], aFileRow[kFileFieldFileName])
        _addUploading(fn, "uploadingOriginSize")

    if aFileRow[kFileFieldStatusForThumb] == defines.kFileStatusFromUploading:
        #小缩略图上传信息
        fn = unit.getFileThumbFullFileName(aFileRow[kFileFieldRealCatalogId], aFileRow[kFileFieldId], 0)
        _addUploading(fn, "uploadingThumbSize")

    if aFileRow[kFileFieldStatusForScreen] == defines.kFileStatusFromUploading:
        #大缩略图上传信息
        fn = unit.getFileThumbFullFileName(aFileRow[kFileFieldRealCatalogId], aFileRow[kFileFieldId], 1)
        _addUploading(fn, "uploadingScreenSize")

    unit.filterNullValue(fileInfo)
    return fileInfo


def buildFileInfoList(aFileRows, aDbObject):
    """组建多个fileInfo信息, 
    aFuncForPaths: 是一个函数,返回 {catalogId: path} 对象
    或者直接就是一个 {catalogId: path} 对象
    """
    result = []
    if not aFileRows:
        return result
    
    irp = None
    def _buildIdRelatePath():
        #嵌套函数实现一次查询,多次使用
        nonlocal irp
        if not irp:
            cids = unit.buildFormatString(aFileRows, kFileFieldRealCatalogId)
            irp = aDbObject.getCatalogIdRelatePathInfo(cids)
        return irp

    for item in aFileRows:
        fileInfo = buildFileInfo(item, _buildIdRelatePath)
        result.append(fileInfo)
    return result


if __name__ == "__main__":
    print("begin test")
    # db = DataManager()
    # db.makeUser("xx", "jddjd")
    # r = db.getUser("Terry", "123")
    # print( buildUserInfo(r) )
    # db.updateFile(30, {"catalogId": 8}, "1,2")
    # db.updateCatalog(9, {"parentId": 2}, "1, 2")
    # db.deleteCatalogs("1,2", "1,2")
    # db.deleteFiles("103, 104, 105, 106, 107", "1, 2")
    # rows = db.getFileByUploading(1)
    # print(buildFileInfoList(rows, db))
    # print(db.buildCatalogPathInfo("1, 3,6"))
    # print(db.getFileByUploading(1))
    # print(db.getFiles("1, 2", "1,2", 0, 10, None, 0))
    # db.updateFile(20, {"name": "myTest", "catalogId":5}, "1,2")
    # print(db.getFileByRealCatalogId(1, "a2.mp3"))
    # db.deleteCatalogs("3, 4,5", "1,2,3")
    # db.makeCatalog({"path": "/A/B/1"})
    # db.makeCatalog({"path": "/a/b/"})
    # print(db.makeCatalog({"path": "/A/c/a/b/c", "parentId":4, "helpInt": "123"}))
    print("finished")
