#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理基本类
"""

__author__="Terry<jxd524@163.com>"

import sqlite3

class JxdSqlDataBasic(object):
    _autoSave = True
#lifecycle
    def __init__(self, aFileName):
        "初始化" 
        self.__conn = sqlite3.connect(aFileName);

    def __del__(self):
        "释放"
        if self.autoSave:
            self.save();
        self.__conn.close();
        self.__conn = None;

    @property
    def autoSave(self):
        return self._autoSave
    @autoSave.setter
    def autoSave(self, aValue):
        self._autoSave = aValue

#public 
    def connect(self):
        "connect对象"
        return self.__conn;

    def cursor(self):
        "cursor对象"
        return self.connect().cursor();

    def save(self):
        "保存"
        self.connect().commit();

    def fetch(self, aSql, aArgs=None, fetchone=True):
        "获取结果的一条数据"
        try:
            cur = self.connect().cursor();
            if aArgs:
                cur.execute(aSql, aArgs);
            else:
                cur.execute(aSql);
            result = cur.fetchone() if fetchone else cur.fetchall();
            return result;
        except Exception as e:
            print(e, sql, aArgs)
        finally:
            cur.close();
        return None

    def execute(self, aSql, aArgs=None):
        "执行一条SQL语句"
        try:
            cur = self.connect().cursor();
            if aArgs:
                cur.execute(aSql, aArgs);
            else:
                cur.execute(aSql);
            return True;
        except Exception as e:
            print(e, sql, aArgs)
        finally:
            cur.close();
        return False;

    def select(self, aTableName, aWheres, aFields="*", aOneRecord=True):
        "查询数据"
        values = [];
        strWhere = self.FormatFieldValues(aWheres, values, "and");
        sql = "select {} from {} where {}".format(aFields, aTableName, strWhere);
        try:
            cur = self.cursor();
            cur.execute(sql, values);
            return cur.fetchone() if aOneRecord else cur.fetchall();
        except Exception as e:
            print(e, sql, values)
        finally:
            cur.close();
        return None;

    def insert(self, aTableName, aFieldValues):
        "插入数据"
        values = [];
        strFields = self.FormatFieldValues(aFieldValues, values, aFormat="{aKey}");
        if len(strFields) == 0:
            return None;

        sc = ",?" * len(values);
        sql = "insert into {}({})values({})".format(aTableName, strFields, sc[1:]);
        try:
            cur = self.cursor();
            cur.execute(sql, values);
            nID = cur.lastrowid;
            return nID;
        except Exception as e:
            print(e, sql, values)
        finally:
            cur.close();
        return None;

    def update(self, aTableName, aWheres, aFieldValues, aAdditionWhenNeedUpdate = None):
        "更新数据"
        values = [];
        updateFields = self.FormatFieldValues(aFieldValues, values);
        if len(updateFields) == 0:
            return False
        elif aAdditionWhenNeedUpdate:
            strAdditions = self.FormatFieldValues(aAdditionWhenNeedUpdate, values)
            if len(strAdditions) > 0:
                updateFields += "," + strAdditions
        strWhere = self.FormatFieldValues(aWheres, values, "and");

        sql = "update %s set %s where %s" % (aTableName, updateFields, strWhere);
        # print(sql, values)
        try:
            cur = self.cursor()
            cur.execute(sql, values)
            return True;
        except Exception as e:
            print(e, sql, values)
        finally:
            cur.close();
        return False;

    def delete(self, aTableName, aWheres):
        "删除指定的数据行"
        values = []
        strWhere = self.FormatFieldValues(aWheres, values, "and")

        sql = "delete from {} where {}".format(aTableName, strWhere)
        try:
            cur = self.cursor();
            cur.execute(sql, values);
            return True;
        except Exception as e:
            print(sql, values)
        finally:
            cur.close();
        return False;

    @staticmethod
    def FormatFieldValues(aFieldValues, aAppendArray, aSpaceSign=",", aFormat="{aKey}=?"):
        """将字段与值格式化为aFormat指定的类型.默认: name=?
        key: 支持
             1:字符串,使用aFormat,此时value必须存在,否则不生成
             2:函数类型为: string func(),直接使用返回值,此时value可以为None
        value: 存在时才会进行格式化
        """
        strResult = ""
        bAddSpaceSign = aSpaceSign and len(aSpaceSign) > 0
        for key, value in aFieldValues.items():
            r = None
            if callable(key):
                r = key()
            elif value != None:
                r = aFormat.format(aKey=key)

            if r != None and len(r) > 0:
                if bAddSpaceSign and len(strResult) > 0:
                    strResult += " " + aSpaceSign + " "
                strResult += r
                if value != None:
                    aAppendArray.append(value)

        return strResult;

if __name__ == "__main__":
    values = []
    s = JxdSqlDataBasic.FormatFieldValues({(lambda :"rootId in ({})".format(123)): None,
            (lambda :"id in ({})".format(11)): None,
            (lambda :"parentId != -1"): None}, values, "and")
    # s = JxdSqlDataBasic.FormatFieldValues({"f1": 100, "name2": "this", "p3": 23, 
        # (lambda : "p4 in (1, 3)"): None,
        # (lambda : "p5 < ?"): 800}, values, aFormat="{aKey}=?", aSpaceSign = "and")
    print(s)
    print(values);
