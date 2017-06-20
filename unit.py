#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目中用到的一些辅助函数
必须安装库: ffmpeg, PIL
"""

__author__="Terry<jxd524@163.com>"

import os, subprocess, json
import datetime, time
import hashlib
import base64
import defines, configs

def _getOrientationFromFFprobeStream(aStream):
    try:
        rotate = int(aStream["tags"]["rotate"])
        if rotate < 0:
            rotate = 360 + rotate
        if rotate == 90:
            return 8
        elif rotate == 180:
            return 3
        elif rotate == 270:
            return 6
        else:
            #其它情况不做处理
            return None
    except Exception as e:
        return None

def _getMediaInfoByFFprobe(aInputFile):
    """返回图片的 width, height, type, orientation
        可能存在: duration 
    """
    strCmd = "ffprobe -v quiet -print_format json -show_format -show_streams -i \"" + \
            aInputFile + "\""
    p = subprocess.Popen(strCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdOut = p.communicate()[0]
    if p.returncode != 0:
        return None

    mediaInfo = json.loads(stdOut.decode("utf-8"))
    if mediaInfo is None or len(mediaInfo) <= 1:
        return None
    try:
        streams = mediaInfo["streams"]
        bHasAudioStream = False
        bHasVideoStream = False
        result = {}
        for item in streams:
            codecType = item["codec_type"].lower()
            if not bHasVideoStream and codecType == "video":
                bHasVideoStream = True
                result["width"] = item["width"]
                result["height"] = item["height"]
                result["orientation"] = _getOrientationFromFFprobeStream(item)
            elif not bHasAudioStream and codecType == "audio":
                bHasAudioStream = True

        if bHasAudioStream:
            nFileType = defines.kFileTypeVideo if bHasVideoStream else defines.kFileTypeAudio
        else:
            # 不存在音频时,可能是视频,可能是图片,可能是文本或其它
            if not bHasVideoStream:
                return None
            fName = mediaInfo["format"]["format_name"].lower()
            nCount = len(fName.split(","))
            if nCount > 1:
                # 只有视频,没有音频,未测试过这种文件
                nFileType = defines.kFileTypeVideo
            else:
                if fName == "gif":
                    nFileType = defines.kFileTypeGif
                elif fName == "tty":
                    nFileType = defines.kFileTypeFile
                else:
                    nFileType = defines.kFileTypeImage
        result["type"] = nFileType

        if nFileType == defines.kFileTypeAudio or nFileType == defines.kFileTypeVideo:
            result["duration"] = mediaInfo["format"]["duration"]
        elif nFileType == defines.kFileTypeFile:
            result["width"] = None
            result["height"] = None
            result["orientation"] = None

        return result
    except Exception as e:
        print("Error: parse json dat(getFileMediaInfo result data): ", aInputFile, e)
        return None


def _getImageInfoByPIL(aInputFile):
    """返回图片的 width, height, type, orientation
        可能存在: duration 
    """
    try:
        from PIL import Image, GifImagePlugin
        img = Image.open(aInputFile, "r")
        result = {"width": img.width, "height": img.height, "ext": img.format}
        nOrientation = None
        if hasattr(img, "_getexif"):
            exif = img._getexif()
            if exif != None:
                try:
                    # 从 from PIL.ExifTags import TAGS 中获取到 0x0112 表示 Orientation
                    nOrientation = int(exif.get(0x0112))
                except Exception as e:
                    pass
        result["orientation"] = nOrientation

        if isinstance(img, GifImagePlugin.GifImageFile):
            nFileType = defines.kFileTypeGif
            try:
                result["duration"] = img.info["duration"] * img.n_frames / 1000
            except Exception as e:
                pass
        else:
            nFileType = defines.kFileTypeImage
        result["type"] = nFileType

        return result
    except Exception as e:
        return None

def getMediaFileInfo(aInputFile, aFileSize):
    """获取媒体文件的 width, height, type, orientation
        可能存在: duration 
    根据 aFileSize 优先调用相关函数
    """
    if aFileSize > 1024 * 1024 * 5:
        # > 5M 优化使用 ffprobe, 音视频文件可能比较大
        result = _getMediaInfoByFFprobe(aInputFile)
        if result and result["type"] in (defines.kFileTypeGif, defines.kFileTypeImage):
            # Gif为了获取duration, Image为了更精确的orientation
            r = _getImageInfoByPIL(aInputFile)
            if r:
                result = r
    else:
        result = _getImageInfoByPIL(aInputFile)
        if not result:
            result = _getMediaInfoByFFprobe(aInputFile)
    if result:
        nOrientation = result.get("orientation")
        if nOrientation and nOrientation in (5,6,7,8):
            nTemp = result["width"]
            result["width"] = result["height"]
            result["height"] = nTemp
    return result


def _buildImageThumbnail(aInputFile, aOutFileName, aOrientation, aWidth, aHeight):
    """生成图片的缩略图

    :aInputFile: 文件全路径
    :aOutFileName: 要输出的文件全路径
    :aOrientation: 方向
    :aWidth: 宽度
    :aHeight: 高度
    :returns: Bool 成功与否

    """
    #使用PIL库生成缩略图
    try:
        from PIL import Image
        img = Image.open(aInputFile)
        img.thumbnail((aWidth, aHeight))

        if aOrientation and aOrientation != 1:
            if aOrientation == 3:
                img = img.transpose(Image.ROTATE_180)
            elif aOrientation == 6:
                img = img.transpose(Image.ROTATE_270)
            elif aOrientation == 8:
                img = img.transpose(Image.ROTATE_90)
            elif aOrientation == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif aOrientation == 4:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            elif aOrientation == 5:
                img = img.transpose(Image.ROTATE_270)
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif aOrientation == 7:
                img = img.transpose(Image.ROTATE_270)
                img = img.transpose(image.FLIP_TOP_BOTTOM)

        ext = "PNG" if img.mode in ("P", "RGBA") else "JPEG"
        img.save(aOutFileName, ext)
        return True
    except Exception as e:
        print("build thumbanil image error: ", e)
        return False


def _buildVideoThumbnail(aInputFile, aOutFileName, aWidth, aHeight, aStrTimePos="00:00:01"):
    """生成视频文件的缩略图

    :aInputFile: 文件全路径
    :aOutFileName: 输出路径
    :aWidth: 要生成缩略图的宽度
    :aHeight: 高度
    :aStrTimePos: 截取的时间位置
    :returns: BOOL 是否成功
    """
    strCmd = "ffmpeg -ss {startPos} -i \"{inputFile}\" -f image2 -s {width}*{height} -y \"{outFile}\"".\
            format(inputFile=aInputFile, outFile=aOutFileName, width=aWidth, height=aHeight, startPos=aStrTimePos)
    p = subprocess.Popen(strCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    return os.path.isfile(aOutFileName)


def generateThumbailImage(aCatalogId, aFileId, aInputFile, aOrientation, aOrgWidth, aOrgHeight, aFileType, aLevel):
    """为数据库中的媒体生成指定类型的缩略图,若文件已存在,则直接返回路径
    
    :aCatalogId: 文件对应的路径ID
    :aFileId: 文件Id, 参与生成文件名
    :aInputFile: 输入文件
    :aOrientation: 方向,具体可参考 ReadMe.md
    :aOrgWidth: 原始媒体宽度
    :aOrgHeight: 原始媒体高度
    :aFileType: 文件类型
    :aLevel: 生成类型
    :returns: 成功时返回文件路径,失败则返回None

    """
    nMaxSize = defines.kThumbnailImageMaxSize if aLevel == 0 else defines.kScreenThumbnailImageMaxSize
    strOutFile = getFileThumbFullFileName(aCatalogId, aFileId, aLevel)
    if os.path.isfile(strOutFile):
        return strOutFile

    if defines.kFileTypeImage == aFileType and nMaxSize >= aOrgWidth and nMaxSize >= aOrgHeight:
        return aInputFile

    #生成大小
    if aOrgWidth < aOrgHeight:
        nH, f = (aOrgHeight, 1) if aOrgHeight < nMaxSize else (nMaxSize, nMaxSize / aOrgHeight)
        nW = f * aOrgWidth
    else:
        nW, f = (aOrgWidth, 1) if aOrgWidth < nMaxSize else (nMaxSize, nMaxSize / aOrgWidth)
        nH = f * aOrgHeight
    nW = int(nW)
    nH = int(nH)
    if defines.kFileTypeVideo == aFileType:
        bOK = _buildVideoThumbnail(aInputFile, strOutFile, nW, nH)
    else:
        bOK = _buildImageThumbnail(aInputFile, strOutFile, aOrientation, nW, nH)
    if not bOK:
        print("error")
    return strOutFile if bOK else ""


def filterNullValue(aDict):
    "过滤空值"
    removeKeys = []
    for key,value in aDict.items():
        if value is None:
            removeKeys.append(key)
    for key in removeKeys:
        aDict.pop(key)


def buildFormatString(aRows, aIndex, aSpace=",", aFormat="{}"):
    "将二维数组中的指定列数据格式指定形式"
    result = None
    if aRows and len(aRows) > 0:
        for item in aRows:
            cid = item if isinstance(item, str) else item[aIndex]
            s = aFormat.format(cid)
            if result:
                result += aSpace + s
            else:
                result = s
    return result if result else ""



def checkParamForInt(aParam):
    "检查是否为Int"
    return int(aParam)

def checkParamForDouble(aParam):
    return double(aparam)

def checkParamForFileType(aParam):
    t = int(aParam)
    return t if t in (defines.kFileTypeImage, defines.kFileTypeGif, 
            defines.kFileTypeVideo, defines.kFileTypeAudio, defines.kFileTypeFile) else None

def checkParamForLess100(aParam):
    return aParam if len(aParam) <= 100 else None


def checkParamForLess1024(aParam):
    return aParam if len(aParam) <= 1024 else None


def checkParamForIntList(aParam):
    "检查是否为一个Int的列表: 1, 2, 4"
    intList = list(map(int, aParam.split(",")))
    return aParam if len(intList) > 0 else None


def checkParamForTimestamp(aParam):
    "检查是否可转成Datetime对象"
    dt = datetime.datetime.fromtimestamp(float(aParam))
    return int(dt.timestamp())


def judgeIntStringsInList(aIntStrings, aList):
    "判断类型 1,2,5 之类的字符串是否都存在于AList中"
    intList = list(map(int, aIntStrings.split(",")))
    if len(intList) > 0:
        for item in intList:
            if item not in aList:
                return False
        return True
    else:
        return False


def makeUserCreateCatalogPath(aParentPath, aName):
    "用户创建目录时生成路径"
    if aName:
        from werkzeug.utils import secure_filename
        aName = secure_filename(aName)
    aName = aName if aName and len(aName) > 0 else ""
    while True:
        nTime = ((int)(time.time() * 1000000)) % 10000000000
        strName = "{}_{}_{}".format(aName, datetime.date.today(), nTime)
        strPath = os.path.join(aParentPath, strName)
        if not os.path.isdir(strPath):
            try:
                os.makedirs(strPath)
                return strPath
            except Exception as e:
                pass


def formatInField(aName, aValue):
    "格式SQL的in查询字段"
    return (lambda :"{} in ({})".format(aName, aValue)) if aValue != None else None

def formatNotInField(aName, aValue):
    "格式SQL的not in查询字段"
    return (lambda :"{} not in ({})".format(aName, aValue)) if aValue != None else None



def makeValue(aDict, aKey, aDefaultValue):
    "确保容器存在指定key,value"
    v = aDict.get(aKey)
    if v == None:
        if callable(aDefaultValue):
            aDict[aKey] = aDefaultValue()
        else:
            aDict[aKey] = aDefaultValue

def removePath(aPath):
    "删除指定路径或文件,可为字符串或数组"
    import subprocess
    strCmd = "rm -rf {}"
    if isinstance(aPath, str):
        strPath = "'{}'".format(aPath)
        subprocess.Popen(strCmd.format(strPath), shell=True)
    else:
        nCount = 0
        strPath = None
        for item in aPath:
            strTemp = "'{}'".format(item)
            if nCount == 0:
                strPath = strTemp
            else:
                strPath = "{} {}".format(strPath, strTemp)
            nCount += 1
            if nCount == 5:
                subprocess.Popen(strCmd.format(strPath), shell=True)
                strPath = None
                nCount = 0
        if strPath:
            subprocess.Popen(strCmd.format(strPath), shell=True)

def moveFile(aFileName, aPath):
    "将指定文件移动到指定目录下, 指定目录下不存在对应文件才能成功"
    import shutil
    try:
        shutil.move(aFileName, aPath)
        return True
    except Exception as e:
        return False


def getFileThumbFullFileName(aCatalogId, aFileId, aLevel):
    "根据目录,文件,生成对应的缩略图位置"
    strRootPath = configs.thumbPath()
    result = os.path.join(strRootPath, "{}".format(aCatalogId))
    if not os.path.isdir(result):
        try:
            os.makedirs(result)
        except Exception as e:
            return None, 0
    name = "thumb_{}".format(aFileId) if aLevel == 0 else "thumbScreen_{}".format(aFileId)
    return os.path.join(result, name)


def buildOriginFileName(aCatalogPath, aExt):
    "在指定目录下生成文件名,并自动生成一个空文件用于占位"
    if aExt:
        from werkzeug.utils import secure_filename
        aExt = secure_filename(aExt)
    strExt = ("." + aExt) if aExt and len(aExt) > 0 else ""
    while True:
        nTime = ((int)(time.time() * 1000000)) % 10000000000
        strFileName = "{}_{}{}".format(datetime.date.today(), nTime, strExt)
        strFullFileName = os.path.join(aCatalogPath, strFileName)
        try:
            with open(strFullFileName, "x") as f:
                return strFileName
        except Exception as e:
            pass

def SHA1FileWithName(aFileName, aMaxBlockSize = 1024 * 64):
    "文件SHA1值"
    print("SHA1:", aFileName)
    with open(aFileName, 'rb') as f:
        sha1 = hashlib.sha1()
        while True:
            data = f.read(aMaxBlockSize)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def MD5FileWithName(aFileName, aMaxBlockSize=1024 * 64):
    "文件MD5值"
    print("MD5:", aFileName)
    with open(aFileName, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(aMaxBlockSize)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def getTimeInt():
    "获取1970到现在的秒数"
    return int( time.time() )


if __name__ == "__main__":
    print("begin")
    # print( judgeIntStringsInList("1, 2", [1, 3]))
    print(getTimeInt())
    print("finished")
