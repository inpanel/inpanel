#!/bin/sh
# InPanel 一键安装脚本

# 默认值
version="v1.1.1b25"
initd_script='/etc/init.d/inpanel'
work_path='/usr/local/inpanel'
work_port=8888
ipaddress="0.0.0.0"
username='admin'
password='admin'
repository='https://github.com/inpanel/inpanel'

# 安装依赖
function fun_dependent() {
    echo 'Install Dependents'
    yum install -y -q wget net-tools vim psmisc rsync libxslt-devel GeoIP GeoIP-devel gd gd-devel python3
}

# 下载安装包到指定位置
function fun_download() {
    echo "${DARK}"
    echo 'Download Archive'
    url="${repository}/archive/refs/tags/${version}.tar.gz"

    echo "Version:       ${version}"
    echo "Location:      ${url}"
    echo "Directory:     ${work_path}"

    # 检查文件夹/创建
    test ! -d "${work_path}" && mkdir "${work_path}"

    curl -o inpanel.tar.gz -L "${url}"
    tar zxmf inpanel.tar.gz -C /usr/local/inpanel --strip-components 1

    # 添加执行权限
    chmod +x "${work_path}/config.py"
    chmod +x "${work_path}/server.py"
    echo 'copy'
    echo "${NC}"
}

# 设置账号密码
function fun_set_username() {
    # 读取账号
    read -p "Enter Admin Username [default: ${username}]: " in_name
    if [ $in_name ]; then
        username=$in_name
    fi

    "${work_path}/config.py username ${username}"
    echo "The Admin Username is: ${username}"
}

# 设置密码
function fun_set_password() {
    echo -n "Enter Admin Password [default: ${password}]: "
    # 使用 while 循环隐式地从标准输入每次读取一个字符，且反斜杠不做转义字符处理
    # 然后将读取的字符赋值给变量 in_pwd
    while IFS= read -r -s -n1 in_pwd; do
        # 如果读入的字符为空，则退出 while 循环
        if [ -z $in_pwd ]; then
            echo
            break
        fi
        # 如果输入的是退格或删除键，则移除一个字符
        if [[ $in_pwd == $'\x08' || $in_pwd == $'\x7f' ]]; then
            [[ -n $password ]] && password=${password:0:${#password}-1}
            printf '\b \b'
        else
            password+=$in_pwd
            printf '*'
        fi
    done

    # echo "Admin Password is: $password"
    # 设置密码
    "${work_path}/config.py password ${password}"

    echo "Admin Password Saved."
}

# 设置端口
function fun_set_port() {
    read -p "Enter Panel Port [default: ${work_port}]: " in_port
    if [ $in_port ]; then
        work_port=$in_port
    fi

    "${work_path}/config.py port ${work_port}"

    echo "InPanel will work on port ${work_port}"
}

# 设置防火墙
function fun_set_firewall() {
    echo 'fun_set_firewall'
    if [ -f /etc/firewalld/firewalld.conf ]; then
        echo "Redhat Linux detected."
        "firewall-cmd --permanent --zone=public --add-port=${work_port}/tcp"
        systemctl restart firewalld.service
}

# 获取IP地址
function fun_set_ip() {
    ipaddress=$(curl -s http://ip.42.pl/raw)
    echo "IP Address is: ${ipaddress}"
}

# 成功
function fun_success() {
    echo ''
    echo '============================'
    echo '*                          *'
    echo '*     INSTALL_COMPLETED    *'
    echo '*                          *'
    echo '============================'
    echo ''
    echo "The URL of your InPanel is: http://${ipaddress}:${work_port}"
    echo ''
    echo 'Wish you a happy life !'
    echo ''
    echo ''
}

fun_dependent
fun_download
fun_set_username
fun_set_password
fun_set_port
fun_set_firewall
fun_set_ip
fun_success
