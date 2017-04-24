#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目中用到的一些辅助函数
必须安装库: ffmpeg, PIL
"""

__author__="Terry<jxd524@163.com>"

import os, subprocess, json
import datetime
import hashlib
from PIL import Image
import defines, configs

def getFileMediaInfo(aFileName):
    """获取文件的媒体信息
        成功,返回值用命令: ffprobe
        失败,返回None
       
       :aFileName: 文件全路径
    """
    strCmd = "ffprobe -v quiet -print_format json -show_format -show_streams -i \"" + \
            aFileName + "\"";
    p = subprocess.Popen(strCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True);
    stdOut = p.communicate()[0];
    if p.returncode == 0:
        return json.loads(stdOut.decode("utf-8"));
    return None;

def _buildImageThumbnail(aInputFile, aOutFileName, aWidth, aHeight):
    """生成图片的缩略图

    :aInputFile: 文件全路径
    :aOutFileName: 要输出的文件全路径
    :aWidth: 宽度
    :aHeight: 高度
    :returns: Bool 成功与否

    """
    # 用 FFmpeg 生成的图片有问题,暂时无法解决
    # strCmd = "ffmpeg -i \"{inputFile}\" -f image2 -s {width}*{height} -y \"{outFile}\"".\
            # format(inputFile=aInputFile, outFile=aOutFileName, width=aWidth, height=aHeight);
    # #print(strCmd);
    # p = subprocess.Popen(strCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True);
    # p.wait();
    # return;

    #使用PIL库生成缩略图
    try:
        img = Image.open(aInputFile);

        mode = img.mode;
        if mode not in ('L', 'RGB'):
            if mode == 'RGBA':
                # 透明图片需要加白色底
                alpha = img.split()[3]
                bgmask = alpha.point(lambda x: 255-x);
                img = img.convert('RGB');
                img.paste((255,255,255), None, bgmask);
            else:
                img = img.convert('RGB')

        img = img.resize((aWidth, aHeight), Image.ANTIALIAS);#.convert("RGB");
        img.save(aOutFileName);
        return True;
    except Exception as e:
        print("build thumbanil image error: ", e);
        return False;


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
            format(inputFile=aInputFile, outFile=aOutFileName, width=aWidth, height=aHeight, startPos=aStrTimePos);
    p = subprocess.Popen(strCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True);
    p.wait();
    return os.path.isfile(aOutFileName);

def generateThumbailImage(aCatalogId, aFileId, aInputFile, aOrgWidth, aOrgHeight, aFileType, aLevel):
    """为数据库中的媒体生成指定类型的缩略图,若文件已存在,则直接返回路径
    
    :aCatalogId: 文件对应的路径ID
    :aFileId: 文件Id, 参与生成文件名
    :aInputFile: 输入文件
    :aOrgWidth: 原始媒体宽度
    :aOrgHeight: 原始媒体高度
    :aFileType: 文件类型
    :aLevel: 生成类型
    :returns: 成功时返回文件路径,失败则返回None

    """
    strOutFile, nMaxSize = getFileThumbFileInfo(aCatalogId, aFileId, aLevel)
    if os.path.isfile(strOutFile):
        return strOutFile

    if defines.kFileTypeImage == aFileType and nMaxSize >= aOrgWidth and nMaxSize >= aOrgHeight:
        return aInputFile;

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
        bOK = _buildVideoThumbnail(aInputFile, strOutFile, nW, nH);
    else:
        bOK = _buildImageThumbnail(aInputFile, strOutFile, nW, nH);
    if not bOK:
        print("error")
    return strOutFile if bOK else "";

def filterNullValue(aDict):
    "过滤空值"
    removeKeys = [];
    for key,value in aDict.items():
        if value is None:
            removeKeys.append(key);
    for key in removeKeys:
        aDict.pop(key);


def checkParamForInt(aParam):
    "检查是否为Int"
    return int(aParam)


def checkParamForIntList(aParam):
    "检查是否为一个Int的列表: 1, 2, 4"
    intList = list(map(int, aParam.split(",")))
    return aParam if len(intList) > 0 else None


def checkParamForDatetime(aParam):
    "检查是否可转成Datetime对象"
    return datetime.datetime.fromtimestamp(float(aParam))


def makeUserCreateCatalogPath(aParentPath, aName):
    "用户创建目录时生成路径"
    nRandom = 123
    while True:
        nRandom += 8
        strDirName = "{}{}{}".format(datetime.datetime.now(), nRandom, aName)
        md5 = hashlib.md5()
        md5.update(strDirName.encode("utf8"))
        strDirName = md5.hexdigest()
        strPath = os.path.join(aParentPath, strDirName)
        if not os.path.isdir(strPath):
            break
    try:
        os.makedirs(strPath)
        return strPath
    except Exception as e:
        print(e)
    return None

def formatInField(aName, aValue):
    "格式SQL的in查询字段"
    return (lambda :"{} in ({})".format(aName, aValue)) if aValue != None else None

def makeValue(aDict, aKey, aDefaultValue):
    "确保容器存在指定key,value"
    v = aDict.get(aKey)
    if v == None:
        aDict[aKey] = aDefaultValue

def removePath(aPath):
    import subprocess
    subprocess.Popen("rm -rf '{}'".format(aPath), shell=True)

def getFileThumbFileInfo(aCatalogId, aFileId, aLevel):
    "根据目录,文件,生成对应的缩略图位和最大值"
    strRootPath = configs.thumbPath()
    result = os.path.join(strRootPath, "{}".format(aCatalogId))
    if not os.path.isdir(result):
        try:
            os.makedirs(result)
        except Exception as e:
            return None, 0
    if aLevel == 0:
        return os.path.join(result, "thumb_{}".format(aFileId)), defines.kThumbnailImageMaxSize
    else:
        return os.path.join(result, "thumbScreen_{}".format(aFileId)), defines.kScreenThumbnailImageMaxSize

if __name__ == "__main__":
    pass
    # generateThumbailImage(1, 1, None, 3030, 1030, 1, 1)
