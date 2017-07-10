#!/usr/bin/env bash


echo -e "创建iSyncServer扫描配置 \ncreate iSyncServer scan configuation file\n"

strJson=""
strSpace=""
nIndex=1

while [[ true ]]; do
    userInfo=()
    n=0
    while [[ true ]]; do
        if [[ $n = 0 ]]; then
            echo "添加用户:"
            echo "Add new user name:"
        else
            nCount=$(( ${#userInfo[@]} / 2 + 1 ))
            echo "添加第${nCount}个用户(若为空,则表示不再新增用户):"
            echo "add the ${nCount}nd users(if input lenght is 0, then finished add user)"
        fi
        read u
        if [[ -z $u ]]; then
            if [[ $n -gt 0 ]]; then
                break
            else
                continue
            fi
        fi
        while [[ true ]]; do
            echo "输入用户 ${u} 的密码:"
            echo "input the password for user ${u}"
            read p
            if [[ -n $p ]]; then
                break
            else
                echo "用户密码不能为空"
                echo "password must not be empty"
            fi
        done
        echo ""

        userInfo[$n]=$u
        userInfo[$n + 1]=$p
        n=$(( n + 2 ))
    done

    usersJson=""
    space=""
    nCount=${#userInfo[@]}
    n=0
    while [[ $nCount -gt $n ]]; do
        usersJson="${usersJson}${space}{\"name\":\"${userInfo[$n]}\",\"password\":\"${userInfo[$n + 1]}\"}"
        n=$(( n + 2 ))
        if [[ $n -gt 0 && -z $space ]]; then
            space=",\n"
        fi
    done
    usersJson="\"users\":[${usersJson}]"
    echo -e $usersJson

    paths=()
    while [[ true ]]; do
        echo ""
        if [[ ${#paths[@]} = 0 ]]; then
            echo "添加要扫描的路径,可以使用TAB键进行路径提示"
            echo "Add the path to scan, you can use the TAB key to prompt the path"
        else
            nCount=$(( ${#paths[@]} + 1 ))
            echo "添加第${nCount}条路径,若输入长度为0,则表示结束路径输入"
            echo "Add the ${#nCount}nd paths(if input lenght is 0, then finished add path)"
        fi
        read -e p
        if [[ -n $p ]]; then
            # 输入长度不为0
            if [[ -d $p ]]; then
                paths[${#paths[@]}]=$p
            else
                echo "输入的路径无效, 请重试"
                echo "The input path is invalid. Please try again"
            fi
        else
            # 输入长度为 0
            if [[ ${#paths[@]} != 0 ]]; then
                break
            fi
        fi
    done
    echo ""

    pathsJson=""
    space=""
    nCount=${#paths[@]}
    n=0
    while [[ $nCount -gt $n ]]; do
        pathsJson="${pathsJson}${space}\"${paths[$n]}\""
        n=$(( n + 1 ))
        if [[ $n -gt 0 && -z $space ]]; then
            space=","
        fi
    done
    pathsJson="\"paths\":[${pathsJson}]"

    strJson="${strJson}${strSpace}{${pathsJson},${usersJson}}"

    bYes=0
    while [[ true ]]; do
        echo "是否继续添加新节点, yes or no?"
        echo "Continue to add new nodes, yes or no"
        read isYes
        if [[ $isYes == "yes" ]]; then
            bYes=1
            break
        elif [[ $isYes == "no" ]]; then
            break
        fi
    done

    if [[ $bYes = 0 ]]; then
        break
    fi
    strSpace=","
done

strJson="[$strJson]"
echo -e $strJson > "./scanDiskConfig.json"


