#!/usr/bin/env bash


echo -e "创建iSyncServer配置文件 \ncreate iSyncServer configuation file"

keys=("logFileName" "thumbPath" "defaultUserPath" "shareUrlThreshold" "shareUrlTimeout" "onlineThreshold" "onlineTimeout")
infos=("输入日志存在路径\nInput app log file full path name" 
       "输入生成缩略图时存放的根路径\nInput the root path where the thumbnails are generated" 
       "输入默认用户路径,只有当创建了用户,但此用户还没有一个目录时有效.\nInput The default user path is only required when creating a user, but this user does not have a directory" 
       "分享URL的最大数量,默认1000\nInput Share the maximum number of URLs. Default: 1000" 
       "分享URL的最大缓存时间,默认1800, 单位:秒\nInput Share the maximum cache time for the URL. Default: 1800. unit:second"
       "在线人数极值,超过此值,则会进行超时处理,默认100\nInput The number of online extreme value, exceeds this value, it will be time-out processing. Defalt: 100" 
       "在线用户无活动保持的最大时间,默认 3600, 单位: 秒\nInput Online users have no activity to keep the maximum time. Default: 3600, Unit: second")
values=()

nCount=${#keys[@]}
for (( i = 0; i < nCount; i++ )); do
    #statements
    echo -e ${infos[$i]}
    read -e v
    values[i]=$v
    echo ""
done

echo "生成以下JSON: "
str=""
space=""
for (( i = 0; i < nCount; i++ )); do
    if [[ -n "${values[$i]}" ]]; then
        str="${str}${space}\"${keys[$i]}\": \"${values[$i]}\""
        if [[ -z $space ]]; then
            space=",\n"
        fi
    fi
done
str="{\n$str\n}"
echo -e $str
echo -e $str > "./appConfigs.json"
