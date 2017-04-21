---
layout: post
title:  "iSync文件管理服务器版本"
author: Terry
date:   2017-04-18 11:14
categories: python
excerpt: iSync iPrivate 文件管理 同步 云盘
---

* content
{:toc}

# 目标与简单说明

文件管理系统.
目标是安装在[树莓派](https://www.raspberrypi.org/)上,提供家庭媒体文件的操作,包含同步,浏览等操作

1. 服务器实现: flask + python.
    以HTTP协议实现JSON数据格式的API接口
    若服务端需要扫描已有数据,则需要安装库: ffmpeg, Pillow
        ffmpeg: 用于获取媒体的信息,生成视频缩略图
        Pillow: 用于生成图片的缩略图(用ffmepg来生成图片的缩略图,某些图片格式生成的图片与原图不一致)

2. 客户端需要实现下文相关接口


# 安装
后续再作说明

# App配置文件
若没有配置文件,则使用默认值
**appConfigs.json**: 配置整个服务器的变量.以下内容有效

**logFileName**: 日志存在路径,默认是 ./building/appLog.log
**thumbPath**: 生成缩略图时存放的总路径,默认 ./building/thumbs
**defaultUserPath**: 默认的用户路径,只有当创建了用户,但此用户还没有一个目录时有效,默认 ./building/users
**shareUrlThreshold**: 分享URL的最大数量,默认1000,
**shareUrlTimeout**: 分享URL的最大缓存时间,默认1800, 单位:秒
**onlineTimeout**: 在线人数极值,超过此值,则会进行超时处理,默认100
**onlineTimeout**: 在线用户无活动保持的最大时间,默认 3600, 单位: 秒

# 扫描数据(附加功能)
如果不想将已有文件加入到系统,可不理会此功能
为方便处理磁盘数据,提供了 **scanDisk.py** 来扫描数据,具体参数见下表

|参数名| 作用|
|----- | ----|
| 不带参数 | 根据同目录下的**scanConfig.json**文件来扫描数据|
| -i(fileName) | 提供指定格式的 JSON 文件,这是最全面的方式 |
使用例子:

```bash
#根据同目录下 scanConfig.json 来扫描数据
python scanDisk.py

#使用配置文件 sd.json 来扫描数据
python scanDisk.py -i sd.json
```

### 配置文件例子

```json
[
    {
        "paths":["~/work/temp/sharePath", "~/Downloads/APPicon"],
        "users":[
            {"name": "terry", "password": "123"},
            {"name": "terry2", "password": "333"}
        ],
        "mergeRootPaths": 1
    },
    {
        "paths":["/User/Terry/syncFiles/t1"],
        "users":[
            {"name": "terry"}
        ]
    },
    {
        "paths":["/User/Terry/syncFiles/t2"],
        "users":[
            {"name": "terry2"}
        ]
    }
]
```

PS:
配置文件外层是一个数组,每个对象拥有 **paths** 和 **users** 两个属性
**users**: 定义用户名与密码
**paths**: 定义要扫描的路径信息
**mergeRootPaths**: 对已经加入到数据库中的路径进行判断,将数据库中的 RootPath 与计算机文件系统路径相一致.默认为 True

# 服务端数据结构说明
服务端只用了4张表来对数据做记录,具体定义,可参考源代码.这里只做了简单说明
1. User: 用户表
2. Catalog: 目录表,记录目录的相关信息
3. Files: 文件表,记录文件的相关信息
4. UserAssociate: 用户与目录的关系表,记录用户对拥有读写操作的根目录信息

对于前三个表,都有 "HelpInfo" 的信息,这些字段对服务端来说是没有意义的.只负责保存.
只对客户端有意义,客户端可以根据需求赋不同含义.如我在 "iPrivate" 客户端,定义它是同步ID


# 接口描述

定义接口的请求与响应,若无说明,则
1. 请求与响应都是通过**JSON**格式进行交互
2. 接口都需要**登陆**后才能使用

## 命令响应返回格式：

```json
{
    "code": 0,
    "msg": "error message",
    "data": 不同的命令有不同的结构
}
```

## 类型定义

<span id="datetime">**datetime**</span>:包含日期与时间的类型. 
1970到现在的秒数,如 2017-04-19 03:06:44 +0000  表示为: 1492571204.221604
```json
typedef datetime float
```

<span id="fileType">**fileType**</span>: 媒体类型定义

```basic
    Image   = 1 << 0;
    Gif     = 1 << 1;
    Video   = 1 << 2;
    Audio   = 1 << 3;
    File    = 1 << 4;
```

<span id="helpInfo">HelpInfo</span>定义: 记录自带的辅助信息,这些信息对服务器没有意义,只负责保存
```json
{
    "helpInt": 12,
    "helpText": "xxxx",
    "lastModifyTime": 1480665083.080785
}
```

<span id="userInfo">**UserInfo**</span>: 用户信息
```json
{
    "name": "displayName",
    "createTime": 123123123.00,
    "lastLoginDate": 1480665083.080785,
    "rootids": "1,5,10"
    "helpInt": 20,
    "helpText": "only for client"
}
```

<span id="catalogInfo">**CatalogInfo**</span>: 目录信息
```json
{
    "id": 123,
    "rootId": 1,
    "parentId": 1,
    "name": "display name",
    "createTime": 123123.123,
    "lastModifyTime": 12312312.123,
    "memo": "xxx",
    "subCatalogCount": 0,
    "fileCount": 100,
    "helpInt": 123,
    "helpText": "only for client"
}
```

<span id="fileInfo">**FileInfo**</span>: 文件信息
```json
{
    "id": 123,
    "catalogId": 1,
    "name": "display name",
    "createTime": 123123,
    "uploadTime": 3243423,
    "importTime": 98123,
    "lastModifyTime": 1231.12,
    "size": 123123,
    "type": 0,
    "duration": 1231.12,
    "width": 300,
    "height": 400,
    "orientation": 0,
    "memo": "jjjj",
    "helpInt": 12,
    "helpText": "XXXX"
}
```

<span id="pageInfo">**PageInfo**</span>: 分页信息
```json
{
    "pageIndex": 0,
    "maxPerPage": 10,
    "pageCount": 100
}
```

## 帐户相关接口

### login.icc 登陆
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| userName | string | 登陆名,区分大小写 |
| password | string | 登陆密码 |
|||
| 响应Data | **[UserInfo](#userInfo)** |

### logout.icc 退出
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| 不需要 | ||
|||
| 响应Data | 无 |

## HelpInfo 相关接口

### helpInfo.icc 获取指定记录的辅助信息

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| type | int | 类型,在指定表查询, 0->用户表; 1->目录表; 2->文件表
| id | int | 相关类型的id,用户表时不需要此值
|||
| 响应Data | **[HelpInfo](#helpInfo)** |

### updateHelpInfo.icc 设置指定记录的辅助信息

| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| type | int | 类型,与getHelpInfo接口参数一致 |
| id | int | 相关类型的id
| helpInt | int | 辅助值(可选) |
| helpText | string | 辅助值(可选) |
|||
| 响应Data | 无 |

## 目录相关接口

### catalogs.icc 获取指定目录下的信息

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| pids | string | 请求指定父类下所有目录的信息, 多个以","分隔, -1表示获取所有的根目录
|||
| 响应Data | array of **[CatalogInfo](#catalogInfo)** |

### createCatalog.icc 创建目录
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| parentId | int | 父类Id |
| name | string | 目录名称, 长度限制( 1 <= len < 100) |
| createTime | [datetime](#datetime) | 创建时间,可选 |
| lastModifyTime | [datetime](datetime) | 最后修改时间,可选 |
| memo | string | 备注,可选 |
| helpInt | int | 辅助信息,可选 |
| helpText | string | 辅助信息,可选 |
|||
| 响应Data | **[CatalogInfo](#catalogInfo)** |

### deleteCatalog.icc 删除目录
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| ids | string | 要删除的目录Id,以","分隔.不支持删除根目录.此操作会直接将指定目录下的所有文件,子目录都进行删除 |
|||
| 响应Data | "提示信息" |

### updateCatalog.icc 更新目录信息
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| id | int | 将被更新目录 |
| parentId | int | 目录移动到指定目录,此操作只修改数据库,不修改实际文件位置 |
| name | string | 目录名称, 长度限制( 1 <= len < 100)(可选) |
| memo | string | 备注,可选 |
| helpInt | int | 辅助信息,可选 |
| helpText | string | 辅助信息,可选 |
|||
| 响应Data | "提示信息" |











## 请求指定目录下的数据: files.icc

| 请求方法 | GET |
| -------- | -----|
| 请求参数 | pids | pageIndex | maxPerPage | types(可选) | sort(可选) |
| 参数类型 | string | int | int | int | int |
| 响应Data | 见下表 |

参数说明
**pids**: 所属目录ID.如 "1,2,3"
**types**: 数据类型, 具体值可参考fileType的定义.可传入多个类型如: "1,2,4", 也可以不传,表示所有
**pageIndex**: 请求的页序号
**maxPerPage**: 每页数量
**sort**: 排序方式: **>0** ==> 升序, **<0** 降序, 默认为0

| sort 值 | 含义 |
| ---- | ---- |
| 0 | 不对结果进行排序 |
| 1, -1 | 文件创建时间 |
| 2, -2 | 上传时间 |
| 3, -3 | 文件大小 |
| 4, -4 | 持续时间 |
| 5, -5 | 文件尺寸 |

```json
{
    "page": {pageInfo object},
    "list": [fileInfo object]
}
```

## 请求指定文件的缩略图: thumbnail.icc

只对MediaType为 Image, Gif 或 Video 的文件有效

| 请求方法 | GET |
| -------- | -----|
| 请求参数 | id | forScreen |
| 参数类型 | int | BOOL |
| 范围 | > 0 | 0 表示获取最小的缩略图, 其它表示获取更大的缩略图 |
| 响应Data | 图片数据或JSON数据(出错) |

参数说明
**id**: 文件 ID
**forScreen**: 只有视频文件需要生成更大的缩略图.

## 请求指定的文件: downFile.icc
下载指定的资源

| 请求方法 | GET |
| -------- | --- |
| 请求参数 | id |
| 参数类型 | int |
| 响应内容 | 文件内容 |


## 请求指定的文件地址: shareFileUrl.icc

获取指定资源的分享HTTP 地址

| 请求方法 | GET |
| -------- | --- |
| 请求参数 | id |
| 参数类型 | int |
| 响应内容 | 资源地址(有效时间由appConfig.json配置) |

```json
{
    "分享标志shareKey,用于 shareFile.icc ";
}
```


## 获取用户分享的文件: shareFile.icc

此接口**不需要**用户已经**登录**,只要共享标志已经缓存在服务器就可以下载
支持Http的单Range协议

| 请求方法 | GET |
| -------- | --- |
| 请求参数 | shareKey |
| 参数类型 | string |
| 响应内容 | 资源内容 |



## 上传文件信息
 
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| cid | int | 文件存在的路径ID |
| name | string | 文件显示名称 |
| size | int | 文件大小 |
| type | int | 文件类型 |
| createTime | double | 可选, 创建时间 |
| importTime | double | 可选, 导入时间 |
| duration | double | 可选,持续时间,视频与GIF有效 |
| width | int | 可选,宽度 |
| height | int |  可选,高度 |
| orientation | int |  可选,方向,图片有效 |
| memo | string |  可选,备注,最长 1024 |
| helpInt | int | 可选,辅助信息 |
| helpText | string | 可选, 辅助信息 |
|||
| 响应Data | **FileInfo**|

## 获取上传文件当前进度
| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| fid | int | 文件ID,-1表示所有上传中的文件 |
|||
| 响应Data | **CatalogInfo** |



