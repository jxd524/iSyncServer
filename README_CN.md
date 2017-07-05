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

# 简介
　　借助[树莓派](https://www.raspberrypi.org/),通过HTTP协议对移动硬盘进行操作。对指定路径的文件进行扫描后写入数据库,提供一系列的API对数据进行增删查改功能.方便家庭成员对其媒体文件的访问

　　**服务端**需要安装:python3, flask. 若需要对生成媒体文件的缩略图,采集媒体文件的信息,则需要再安装: ffmpeg, Pillow.


　　**客户端**需要根据需求,实现以下API接口.已提供的iOS客户端: [iPrivate](https://itunes.apple.com/us/app/iprivate-protect-your-privacy-photo-video/id992360900?l=zh&ls=1&mt=8)

# 安装

## 在树莓派上安装服务器

推荐下载[RASPBIAN LITE版本](https://www.raspberrypi.org/downloads/raspbian/),安装方式可参考[树莓派入门](http://icc.one/2017/06/20/%E6%A0%91%E8%8E%93%E6%B4%BE%E5%85%A5%E9%97%A8/#安装操作系统)

使用以下脚本自动安装**iSyncServer**

```shell
curl "" | bash
```

## 在iOS上安装客户端

使用[iPrivate](https://itunes.apple.com/us/app/iprivate-protect-your-privacy-photo-video/id992360900?l=zh&ls=1&mt=8)


# App配置文件

在根目录下创建名为 **appConfigs.json** 的配置文件.它将影响整个服务器.若没有配置文件,则使用默认值
以下字段有效
**logFileName**: 日志存在路径,默认是 ./building/appLog.log
**thumbPath**: 生成缩略图时存放的总路径,默认 ./building/thumbs
**defaultUserPath**: 默认的用户路径,只有当创建了用户,但此用户还没有一个目录时有效,默认 ./building/users
**shareUrlThreshold**: 分享URL的最大数量,默认1000,
**shareUrlTimeout**: 分享URL的最大缓存时间,默认1800, 单位:秒
**onlineTimeout**: 在线人数极值,超过此值,则会进行超时处理,默认100
**onlineTimeout**: 在线用户无活动保持的最大时间,默认 3600, 单位: 秒

eg:

```bash
{
"logFileName": "/app/iSyncServer/appLog.txt",
"thumbPath": "/app/iSyncServer/building/thumbs"
}
```

<span id="scanDisk"/>
# 扫描数据(附加功能)

为方便处理磁盘数据,提供了 **scanDisk.py** 来递归扫描指定的目录,将对应的文件和用户信息写入到数据库中
配置文件外层是一个数组,每个对象拥有 **paths** 和 **users** 属性
**users**: 字典类型,定义用户名与密码
**paths**: 包含字符串的数组,定义要扫描的路径信息
**mergeRootPaths**: 布尔类型, 对已经加入到数据库中的路径进行判断,将数据库中的 RootPath 与计算机文件系统路径相一致.默认为 True

具体参数见下表

|参数名  | 作用 |
|----- | ---- |
| 不带参数 | 根据同目录下的**scanConfig.json**文件来扫描数据 |
| -i(fileName) | 提供指定格式的JSON文件全路径 |



```bash
#根据同目录下 scanConfig.json 来扫描数据
python scanDisk.py

#使用配置文件 sd.json 来扫描数据
python scanDisk.py -i sd.json
```

eg:

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


# 数据库表结构说明

服务端使用python内建支持的数据库: sqlite3. 只用了4张表来对数据做记录,具体定义,可参考源代码.这里只做了简单说明
1. User: 用户表
2. Catalog: 目录表,记录目录的相关信息
3. Files: 文件表,记录文件的相关信息
4. UserAssociate: 用户与目录的关系表,记录用户对拥有读写操作的根目录信息

对于前三个表,都有[HelpInfo](#helpInfo)信息,这些字段对服务端来说是没有意义的.只负责保存.
只对客户端有意义,客户端可以根据需求赋不同含义.


# API接口描述

定义接口的请求与响应,若无说明,则
1. 请求与响应都是通过**JSON**格式进行交互
2. 接口都需要**登陆**后才能使用

## 命令响应返回格式

```json
{
    "code": 0,
    "msg": "error message",
    "data": 不同的命令有不同的结构 & Different commands have different structures
}
```

## 类型定义

<span id="datetime">**datetime**</span>:包含日期与时间的类型.
1970到现在的秒数,如 2017-04-19 03:06:44 +0000  表示为: 1492571204

```json
typedef datetime int
```

<span id="orientation">**orientation**</span>: 图片或视频的旋转方向
在扫描文件时会生成,在生成缩略图时会用到,数据库中记录着原始的方向,若为0,表示不需要旋转

与iOS中UIImageOrientation的具体对应关系表

| UIImageOrientation | 原始exif中Orientation 值 <br> The original exif in the orientation value | 生成缩略图时旋转 <br> Rotate when generating thumbnails |
| ------ | ------ | ------ |
| UIImageOrientationUp | 1 | 不需要旋转 |
| UIImageOrientationDown | 3 | 180° |
| UIImageOrientationLeft | 6 | 顺时针90° |
| UIImageOrientationRight | 8 | 逆时针90° |
| UIImageOrientationUpMirrored | 2 | 水平翻转|
| UIImageOrientationDownMirrored | 4 | 垂直翻转 |
| UIImageOrientationLeftMirrored | 5 | 顺时针90°+水平翻转 |
| UIImageOrientationRightMirrored | 7 | 顺时针90°+垂直翻转 |

<span id="fileStatus">**fileStatus**</span>: 文件状态
标志文件是否已经存在,使用[scanDisk](#scanDisk)时,使用的状态的:kFileStatusFromLocal
当需要服务端生成缩略图时,其相应字段需要设置为 kFileStatusFromLocal,否则不进行缩略图生成

```basic
kFileStatusFromLocal        = 0 # 来自本地
kFileStatusBuildError       = 1 # 本地生成时出错
kFileStatusFromUploading    = 2 # 来自上传
kFileStatusFromUploaded     = 3 # 来自上传,并且已经上传完成
```

数据库Files表字段说明: 
√ 表示可能的值

| 字段名 | 字段含义 | kFileStatusFromLocal | kFileStatusBuildError | kFileStatusFromUploading | kFileStatusFromUploaded |
| ------ | ------ | ------ | ------ | ------ | ------ |
| statusForOrigin | 原始文件 | √(已存在,一般由[scanDisk](#scanDis)设置) | | √(等待上传) | √(已经上传成功) |
| statusForThumb  | 小缩略图,[参考](#thumbnail) | √(服务端根据原始文件自动) | √(服务端生成失败)  | √(等待上传) | √(上传成功) |
| statusForScreen | 大缩略图,[参考](#thumbnail) | √ | √  | √ | √ |


<span id="fileType">**fileType**</span>: 媒体类型定义

```basic
kFileTypeImage      = 1 << 0
kFileTypeGif        = 1 << 1
kFileTypeVideo      = 1 << 2
kFileTypeAudio      = 1 << 3
kFileTypeFile       = 1 << 4
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
    "id": 12,
    "name": "displayName",
    "createTime": 123123123.00,
    "lastLoginDate": 1480665083.080785,
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
    "uploadUserId": 1,
    "catalogId": 1,
    "name": "display name",
    "ext": "mp4",
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
    "helpText": "XXXX",
    "uploadingThumbSize": 0,
    "uploadingScreenSize": 0,
    "uploadingOriginSize": 0
}
```

PS:
**uploadingThumbSize**: 表示当前已经上传的小缩略图大小
**uploadingScreenSize**: 大缩略图
**uploadingOriginSize**: 原始文件
以上三个参数,只有当文件还没有上传成功时才会返回.用于断点上传功能.
客户端在上传完文件信息之后,在每次上传文件内容之前,都可以先获取已上传字节数后,
再上传后续内容.参考Api: [uploadFileInfo](#uploadFileInfo), [uploadFile](#uploadFile)

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
| parentId | int | 父类Id,此ID必须存在 |
| name | string | 目录名称, 长度限制( 1 <= len < 100) |
| createTime | [datetime](#datetime) | 可选, 创建时间 |
| lastModifyTime | [datetime](datetime) | 可选, 最后修改时间 |
| memo | string | 可选, 备注 |
| helpInt | int | 可选, 辅助信息 |
| helpText | string | 可选, 辅助信息 |
|||
| 响应Data | **[CatalogInfo](#catalogInfo)** |


### deleteCatalog.icc 删除目录

| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| ids | string | 要删除的目录Id,以","分隔.不支持删除根目录.<br>此操作会直接将指定目录下的所有文件,子目录都进行删除 |
|||
| 响应Data | "提示信息" |


### updateCatalog.icc 更新目录信息

| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| id | int | 将被更新目录 |
| parentId | int | 可选, 目录移动到指定目录,此操作只修改数据库,不修改实际文件位置 |
| name | string | 可选, 目录名称, 长度限制( 1 <= len < 100) |
| memo | string | 可选, 备注 |
| helpInt | int | 可选, 辅助信息 |
| helpText | string | 可选, 辅助信息 |
|||
| 响应Data | **[CatalogInfo](#catalogInfo)** |


## 文件相关接口

### 请求指定目录下的数据: files.icc

此操作中会返回[fileStatus](#fileStatus)为 kFileStatusFromLocal 和 kFileStatusFromUploaded 的内容

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| pageIndex | int | 请求的页序号, 范围: >= 0 |
| maxPerPage | int | 可选, 每页数量.默认为100, 范围: 10 <= maxPerPage <= 10000 |
| rootIds | string | 可选,指定根目录,如"1,2",默认: 所有根目录下 |
| pids | string | 可选,指定目录,如"1,2,3",默认:所有目录下 |
| types | string | 可选,数据类型,具体值参考[fileType](#fileType),如"1,8,16".默认: 所有类型 |
| onlySelfUpload | int | 可选,是否只是要自己上传的信息,默认为: 0(表示False, 其它值为True) |
| sort | int | 可选,排序方式, **>0**: 升序, **<0**:降序,**0**:不排序, 默认: 不排序 参考:[sort](#sort) |
|||
| 响应Data | [fileResponse](#fileResponse) |

<span id="sort">**sort**</span>

| sort 值 | 含义 |
| ---- | ---- |
| 0 | 不对结果进行排序 |
| 1, -1 | 文件创建时间 |
| 2, -2 | 上传时间 |
| 3, -3 | 文件大小 |
| 4, -4 | 持续时间 |
| 5, -5 | 文件尺寸 |


<span id="fileResponse">**fileResponse**</span>

>{
    "list": [{[fileInfo](#fileInfo)}],
    "page": {[pageInfo](#pageInfo)}
}

<span id="thumbnail"/>

### 请求指定文件的缩略图: thumbnail.icc

此接口会判断相关[fileStatus](#fileStatus)来确认是否自动生成缩略图,
在[上传接口](#uploadFileInfo)上需要设置好 **statusForThumb**, **statusForScreen**

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| id | int | 文件Id, 只有[fileType](#fileType)为 Image, Gif 或 Video 时有效 |
| level | int | [缩略图等级](#thumbnailInfo),默认为: 0 |
|||
| 响应Data | 图片数据或JSON数据(出错) |

<span id="thumbnailInfo">缩略图说明</span>

| level 值 | 含义 | 服务端是否生成 |
| ---- | ---- | ------ |
| 0 | 最大为100*100的等比缩略图 | 根据[statusForThumb](#fileStatus)的值生成 |
| 1 | 最大为800*800的等比缩略图 | 根据[statusForScreen](#fileStatus)的值生成 |

<span id="fileStatus">fileStatus说明</span>

| fileStatus 值 | 含义 |
| ---- | ---- | ------ |
| 0 | 默认值,使用[scanDisk](#scanDisk)时使用,表示在需要时自动生成 |
| 1 | 服务器无法生成指定缩略图时标志 |
| 2 | 等待客户端上传 |
| 3 | 客户端上传完成 |


### 请求指定的文件: downFile.icc< ext >

** < ext > **: 表示扩展名,这是为了iOS在线播放而做的修改.它不参与计算,只是一个URL的表现形式
如下面两次方式都是可行的:
downFile.icc?id=12
downFile.icc.mp4?id=12

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| id | int | 文件Id |
|||
| 响应Data | 文件内容 |



### 请求指定的文件地址: shareFileUrl.icc

获取指定资源的分享HTTP 地址

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| id | int | 文件Id |
|||
| 响应Data | 资源地址(有效时间由appConfig.json配置) |

```json
{
    "分享标志shareKey,用于 shareFile.icc ";
}
```


### 获取用户分享的文件: shareFile.icc< ext >

此接口**不需要**用户已经**登录**,只要共享标志已经缓存在服务器就可以下载
支持Http的单Range协议

** < ext > **: 表示扩展名,这是为了iOS在线播放而做的修改.它不参与计算,只是一个URL的表现形式 
调用如: 
shareFile.icc.mp4?shareKey=xxxx
shareFile.icc.mov?shareKey=xxx

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| shareKey | string | 分享标志,由shareFileUrl.icc返回 |
|||
| 响应Data | 资源内容 |


<span id="uploadFileInfo"/>

### 上传文件信息: uploadFileInfo.icc

上传文件时,先上传其信息,再上传文件内容
服务端在需要时自动生成缩略图时的相关信息,请参考: [获取缩略图](#thumbnail)
 
| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| cid | int | 文件所属路径ID |
| name | string | 文件显示名称 |
| size | int | 文件大小 |
| type | [fileType](#fileType) | 文件类型 |
| ext | string | 文件扩展名, 长度范围: (0, 10) |
| [statusForThumb](#fileStatus) | int | 可选,缩略图生成方式,<br>默认值是kFileStatusFromLocal,表示由服务器从本地原文件自动生成<br>可选值为 kFileStatusFromUploading,表示后续由客户端[上传](#uploadFile) |
| [statusForScreen](#fileStatus) | int | 与 statusForThumb 含义相同 |
| createTime | [datetime](#datetime) | 可选, 创建时间 |
| importTime | [datetime](#datetime) | 可选, 导入时间 |
| lastModifyTime | [datetime](#datetime) | 可选, 最后修改时间 |
| duration | float | 可选,持续时间,视频与GIF有效 |
| width | int | 可选,宽度 |
| height | int |  可选,高度 |
| [orientation](#orientation) | int |  可选,媒体方向,若需要服务端生成缩略图,此值必须为有效值 |
| longitude | double | 可选,经度|
| latitude | double | 可选,纬度 |
| memo | string |  可选,备注,最长 1024 |
| helpInt | int | 可选,辅助信息 |
| helpText | string | 可选, 辅助信息 |
|||
| 响应Data | [FileInfo](#fileInfo) |


### 获取当前正在上传的信息: uploadingInfo.icc

| 请求方法 | GET |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| 无 | | |
|||
| 响应Data | array of [fileInfo](#fileInfo) |


<span id="uploadFile">

### 上传文件: uploadFile.icc

若 multidata 的 filename 不在以下定义中,则直接报错

| 请求方法 | POST |
| -------- | ----- |

|以下参数要与URL一起生成,如: uploadFile.icc?id=1&obp=82331&tbp=0&sbp=100&cm=sha1 |
|--- |

| 请求参数 | 类型 | 说明 |
| ---- | ---- | ---- |
| id | int | 文件ID |
| obp | int | 可选,默认为0;origin begin position, 此次上传的原始文件的开始位置,对应multidata中filename为"origin" |
| tbp | int | 可选,默认为0;小缩略图开始位置,对应"thumb" |
| sbp | int | 可选,默认为0;大缩略图开始位置, 对应"screen" |
| cm | string | 可选,默认为None, 返回上传文件的检验值,暂时支持:sha1, md5.若不是指定值,则不计算检验值,由客户端负责自行检验
| 以下参数为multipart/form-data, 具体作用请自行查阅 |
| origin | bin | filename为origin的部分代表原始文件|
| thumb | bin | 小缩略图 |
| screen | bin | 大缩略图 |
|||
| 响应Data | [Response](#uploadResponse) |

<span id="uploadResponse">**uploadResponse**</span>

>{
    "fileInfo": {[fileInfo](#fileInfo)},
    "check": {"origin": "sha1或md5或空值", "thumb": "xxx", "screen": "xxx"}
}


### 删除指定文件: deleteFiles.icc

| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| ids | string | 要删除文件的id,可多个 |
|||
| 响应Data | 无 |


### 更新文件信息: updateFile.icc

| 请求方法 | POST |
| -------- | --- |
|||
| 请求参数 | 类型 | 说明 |
| id | int | 将被更新文件ID |
| catalogId | int | 可选, 文件将被移动到指定目录,此操作只修改数据库,不修改实际文件位置 |
| name | string | 可选, 文件显示名称 |
| size | int | 可选, 文件大小 |
| type | [fileType](#fileType) | 可选, 文件类型 |
| ext | string | 可选,文件扩展名 |
| [statusForThumb](#fileStatus) | int | 可选,缩略图生成方式,<br>默认值是kFileStatusFromLocal,表示由服务器从本地原文件自动生成<br>可选值为 kFileStatusFromUploading,表示后续由客户端[上传](#uploadFile) |
| [statusForScreen](#fileStatus) | int | 可选, 与 statusForThumb 含义相同 |
| createTime | [datetime](#datetime) | 可选, 创建时间 |
| importTime | [datetime](#datetime) | 可选, 导入时间 |
| lastModifyTime | [datetime](#datetime) | 可选, 最后修改时间 |
| duration | float | 可选,持续时间,视频与GIF有效 |
| longitude | double | 可选,经度|
| latitude | double | 可选,纬度 |
| width | int | 可选,宽度 |
| height | int |  可选,高度 |
| [orientation](#orientation) | int |  可选,媒体方向,若需要服务端生成缩略图,此值必须为有效值 |
| memo | string |  可选,备注,最长 1024 |
| helpInt | int | 可选,辅助信息 |
| helpText | string | 可选, 辅助信息 |
|||
| 响应Data | [FileInfo](#fileInfo) |

