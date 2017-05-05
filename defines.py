#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
有关数据类型的定义
"""

__author__="Terry<jxd524@163.com>"

# 文件状态
kFileStatusFromLocal        = 0 # 来自本地
kFileStatusBuildError       = 1 # 本地生成时出错
kFileStatusFromUploading    = 2 # 来自上传
kFileStatusFromUploaded     = 3 # 来自上传,并且已经上传完成

# 媒体类型
kFileTypeImage      = 1 << 0
kFileTypeGif        = 1 << 1
kFileTypeVideo      = 1 << 2
kFileTypeAudio      = 1 << 3
kFileTypeFile       = 1 << 4

# 生成等比例缩略图时,最大长度(宽度或长度)
kThumbnailImageMaxSize = 160

# 生成等比例屏幕大小缩略图时,最大长度,只有视频文件需要
kScreenThumbnailImageMaxSize = 800

kAppSecretKey = "sjjdicjLKDI(*&%#_)^!BJsdj182312Jippxmw[OP]12><MK>"

#登录用户有权限的目录ID
kSessionUserKey = "Session_UserKey"
