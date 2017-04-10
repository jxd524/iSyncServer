#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
有关数据类型的定义
"""

__author__="Terry<jxd524@163.com>"

# 文件状态
kFileStatusFormLocal        = 0 # 来自本地
kFileStatusFormUploading    = 1 # 来自上传
kFileStatusFormUploaded     = 2 # 来自上传,并且已经上传完成

# 媒体类型
kFileTypeImage      = 1 << 0
kFileTypeGif        = 1 << 1
kFileTypeVideo      = 1 << 2
kFileTypeAudio      = 1 << 3
kFileTypeFile       = 1 << 4


# 生成等比例缩略图时,最大长度(宽度或长度)
kThumbnailImageMaxSize = 200

# 生成等比例屏幕大小缩略图时,最大长度,只有视频文件需要
kScreenThumbnailImageMaxSize = 800


