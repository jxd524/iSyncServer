#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目中用到的一些辅助函数
必须安装库: ffmpeg, PIL
"""

__author__="Terry<jxd524@163.com>"

import os, subprocess, json
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

def buildImageThumbnail(aInputFile, aOutFileName, aWidth, aHeight):
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


def buildVideoThumbnail(aInputFile, aOutFileName, aWidth, aHeight, aStrTimePos="00:00:01"):
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

def generateThumbailImage(aRootId, aPathId, aFileId, aInputFile, aOrgWidth, aOrgHeight, aFileType, aForScreenThumb):
    """为数据库中的媒体生成指定类型的缩略图,若文件已存在,则直接返回文体
    生成的缩略图分两种: 1-> 用于在列表中显示的小图,最大不超过 defines.kThumbnailImageMaxSize
                        2-> 用于全屏显示的图,最大不超过 defines.kScreenThumbnailImageMaxSize

    :aRootId: 根目录Id, 参与生成输出路径
    :aPathId: 父目录Id, 参与生成输出路径
    :aFileId: 文件Id, 参与生成文件名
    :aInputFile: 输入文件
    :aOrgWidth: 原始媒体宽度
    :aOrgHeight: 原始媒体高度
    :aFileType: 文件类型
    :aForScreenThumb: 生成类型
    :returns: 成功时返回文件路径,失败则返回None

    """
    strPath = os.path.join(configs.thumbPath(), "{0}".format(aRootId));
    strPath = os.path.join(strPath, "{0}".format(aPathId));
    if not os.path.isdir(strPath):
        os.makedirs(strPath);

    strFileName = "{0}_{1}.jpg".format(aFileId, "screenThumb" if aForScreenThumb else "thumb" );
    strOutFile = os.path.join(strPath, strFileName);
    if os.path.isfile(strOutFile):
        return strOutFile;

    nMaxSize = defines.kScreenThumbnailImageMaxSize if aForScreenThumb else defines.kThumbnailImageMaxSize
    if defines.kFileTypeImage == aFileType and nSize >= aOrgWidth and nMaxSize >= aOrgHeight:
        return aInputFile;

    #生成大小
    f = aWidth / aHeight;
    if aWidth < aHeight:
        #设置高度
        if aMaxSize < aHeight:
            aHeight = aMaxSize;
            aWidth = aHeight * f;
    else:
        #设置宽度
        if aMaxSize < aWidth:
            aWidth = aMaxSize;
            aHeight = aWidth // f;
    aWidth = int(aWidth);
    aHeight = int(aHeight);

    if defines.kFileTypeVideo == aFileType:
        bOK = mediaHelp.buildVideoThumbnail(aInputFile, strOutFile, aWidth, aHeight);
    else:
        bOK = mediaHelp.buildImageThumbnail(aInputFile, strOutFile, aWidth, aHeight);
    if not bOK:
        strOutFile = None;
    return strOutFile;

if __name__ == "__main__":
    print("finished");
