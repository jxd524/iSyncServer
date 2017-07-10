#!/usr/bin/env bash


# 安装 iSyncServer 服务器
# 自动判断安装软件: git, ffmpeg, python 3.5.2, pyenv, Pillow, Flask 及有关依赖库
#
# 作者: Terry
# Email: jxd524@163.com
# Date: 2017-07-03 13:30
# LastModifyDate: 2017-07-05 13:00
#

# 错误时退出
set -e

# 判断是否要更新系统
bUpdateSystem=0
function checkToUpdateSystem()
{
    if [[ $bUpdateSystem == 0 ]]; then
        bUpdateSystem=1
        sudo apt-get update
        sudo apt-get upgrade -y
    fi
}

# git 下载项目
function checkout()
{
    [ -d "$2" ] || git clone --depth 1 "$1" "$2"
}

# 确保安装GIT
if ! command -v git 1>/dev/null 2>&1; then
    # 自动为树莓派安装GIT
    echo "install git"
    checkToUpdateSystem
    sudo apt-get install git -y
fi

#安装ffmpeg
if ! command -v ffmpeg 1>/dev/null 2>&1; then
    set +e
    echo "尝试安装ffmpeg"
    ffmpegSourcs=("deb http://mirrors.ustc.edu.cn/debian-multimedia/ jessie main non-free"
                  "deb-src http://mirrors.ustc.edu.cn/debian-multimedia/ jessie main non-free"
                  "deb http://mirrors.ustc.edu.cn/debian-multimedia/ jessie-backports main"
                  "deb-src http://mirrors.ustc.edu.cn/debian-multimedia/ jessie-backports main")
    sourceList=`cat /etc/apt/sources.list`
    for (( i = 0; i < ${#ffmpegSourcs[*]}; i++ )); do
        if [[ -z "`echo $sourceList | grep -o "${ffmpegSourcs[i]}"`" ]]; then
          echo ${ffmpegSourcs[i]} | sudo tee -a /etc/apt/sources.list
        fi
    done
    sudo apt-get update
    sudo apt-get install deb-multimedia-keyring -y
    sudo apt-get upgrade -y
    sudo apt-get install ffmpeg -y
    bUpdateSystem=1

    if [[ -z "`ffmpeg -version`" ]]; then
        echo "安装 ffmpeg 失败"
    fi

    set -e
fi

# 变量定义
PYENV_ROOT="${HOME}/.pyenv"
GITHUB="https://github.com"
PythonVersion="3.5.2"
iSyncName="iSyncServerEnv${PythonVersion}"
iSyncRoot="${HOME}/iSyncServer"

# checkout pyenv
checkout "${GITHUB}/yyuu/pyenv.git"            "${PYENV_ROOT}"
checkout "${GITHUB}/yyuu/pyenv-doctor.git"     "${PYENV_ROOT}/plugins/pyenv-doctor"
checkout "${GITHUB}/yyuu/pyenv-installer.git"  "${PYENV_ROOT}/plugins/pyenv-installer"
checkout "${GITHUB}/yyuu/pyenv-update.git"     "${PYENV_ROOT}/plugins/pyenv-update"
checkout "${GITHUB}/yyuu/pyenv-virtualenv.git" "${PYENV_ROOT}/plugins/pyenv-virtualenv"
checkout "${GITHUB}/yyuu/pyenv-which-ext.git"  "${PYENV_ROOT}/plugins/pyenv-which-ext"

# checkout iSyncServer
checkout "${GITHUB}/jxd524/iSyncServer.git" "${HOME}/iSyncServer"

# 确保将pyenv 添加到环境
if ! command -v pyenv 1>/dev/null; then
    if [ ! -f $profile ]; then
        touch ${profile}
    fi
    export PATH="${PYENV_ROOT}/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi

#确保已安装 iSyncServerEnv352 虚拟环境
if [ -z "`pyenv versions | awk '{if ( $1 == "'$iSyncName'" ){ print $1 }}'`" ];then
    if [ -z "`pyenv versions --skip-aliases | awk '{if ($1 == "'$PythonVersion'") {print $1}}'`" ]; then
        echo "need install python version: ${PythonVersion}"
        checkToUpdateSystem
        sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
            libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev
        pyenvCachePath="${PYENV_ROOT}/cache/"
        fileName="Python-${PythonVersion}.tar.xz"
        if [[ ! -r ${pyenvCachePath}${fileName} ]]; then
            # 使用镜像文件
            mirrorURL="http://mirrors.sohu.com/python/${PythonVersion}/${fileName}"
            wget $mirrorURL -P ${pyenvCachePath}
        fi
        pyenv install ${PythonVersion} -v
        rm -rf ${pyenvCachePath}
        pyenv rehash
    fi
    echo "install python virtual env: ${iSyncName}"
    pyenv virtualenv ${PythonVersion} ${iSyncName}
fi

#启动虚拟环境
pyenv activate ${iSyncName} 2>/dev/null

#加载PIP列表
piplistFile="${iSyncRoot}/piplist.temp"
if [[ -s $piplistFile ]]; then
    plugs=`cat $piplistFile`
else
    plugs=`pip freeze`
    echo $plugs > $piplistFile
fi

bNeedUpgradePip=0
bNeedUpPlugs=0

# 确保已安装 Pillow
if [[ -z "`echo $plugs | grep 'Pillow'`" ]]; then
    echo "install Pillow"
    bNeedUpgradePip=1
    pip install --upgrade pip
    checkToUpdateSystem
    sudo apt-get install -y libjpeg-dev zlib1g-dev tk-dev libopenjpeg-dev
    pip install Pillow
    bNeedUpPlugs=1
fi

# 确保已安装 Flask
if [[ -z "`pip freeze | grep 'Flask'`" ]]; then
    # 安装 Flask
    echo "install Flask"
    if [[ $bNeedUpgradePip == 0 ]]; then
        pip install --upgrade pip
    fi
    pip install Flask
    bNeedUpPlugs=1
fi

# 更新PIP列表
if [[ $bNeedUpPlugs == 1 ]]; then
    pip freeze > $piplistFile
fi

# 配置服务
cd $iSyncRoot
if [[ ! -s ${iSyncRoot}"/appConfigs.json" ]]; then
    source ./buildingConfig.sh
fi

if [[ ! -s ${iSyncRoot}"/scanDiskConfig.json" ]]; then
    source ./buildingScan.sh
fi

# 启动服务
python scanDisk.py

echo "准备启动服务"
python app.py &

echo "本地IP地址: "
echo "Local ip address"
ifconfig | grep "inet addr" | grep "Bcast" | awk -F: '{print $2}' | awk '{print $1}'

echo "所有操作已经完成,服务将在后台运行"
echo "All finished. Run iSyncServer in the background"

