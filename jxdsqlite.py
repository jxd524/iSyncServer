#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理基本类
"""

__author__="Terry<jxd524@163.com>"

import sqlite3

class JxdSqlDataBasic(object):

#lifecycle
    def __init__(self, aFileName):
        "初始化" 
        self.__conn = sqlite3.connect(aFileName);

    def __del__(self):
        "释放"
        self.save();
        self.__conn.close();
        self.__conn = None;

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
            print(e);
        finally:
            cur.close();
        return None

    def select(self, aTableName, aWheres, aFields="*", aOneRecord=True):
        "查询数据"
        values = [];
        strWhere = self.FormatFieldValues(aWheres, values, "and");
        sql = "select %s from %s where %s" % (aFields, aTableName, strWhere);
        try:
            cur = self.cursor();
            cur.execute(sql, values);
            return cur.fetchone() if aOneRecord else cur.fetchall();
        except Exception as e:
            print(e);
        finally:
            cur.close();
        return None;

    def insert(self, aTableName, aFieldValues):
        "插入数据"
        values = [];
        strFields = self.FormatFieldValues(aFieldValues, values, aFormat="{aSign}{aKey}");
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
            #print(e);
            pass;
        finally:
            cur.close();
        return None;

    def update(self, aTableName, aWheres, aFieldValues):
        "更新数据"
        values = [];
        updateFields = self.FormatFieldValues(aFieldValues, values);
        if len(updateFields) == 0:
            return False;
        strWhere = self.FormatFieldValues(aWheres, values, "and");

        sql = "update %s set %s where %s" % (aTableName, updateFields, strWhere);
        try:
            cur = self.cursor();
            cur.execute(sql, values);
            return True;
        except Exception as e:
            raise e
        finally:
            cur.close();
        return False;

    @staticmethod
    def FormatFieldValues(aFieldValues, aAppendArray, aSpaceSign=",", aFormat="{aSign} {aKey}=?"):
        "将字段与值格式化为aFormat指定的类型.默认: name=?"
        strResult = "";
        for k in aFieldValues.keys():
            v = aFieldValues[k];
            if v:
                strSpaceSign = aSpaceSign if len(strResult) > 0 else "";
                strResult += aFormat.format(aSign=strSpaceSign, aKey=k);
                aAppendArray.append(v);
        return strResult;

if __name__ == "__main__":
    values = [];
    s = JxdSqlDataBasic.FormatFieldValues({"f1": 100, "name2": "this"}, values, aFormat="{aSign}{aKey}")
    print(s);
    print(values);
