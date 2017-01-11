VPSMate
=========
This is special edition (fork) of VPSMate with many features not existing on VPSMate official release (v1.0 b10).


#### 安装
    curl -O https://raw.githubusercontent.com/fanshengshuai/VPSMate/master/install.py
    python install.py
    

#### 卸载
    service vpsmate stop
    rm -rf /usr/local/vpsmate
    rm -f /etc/init.d/vpsmate

#### 忘记用户名或密码
    /usr/local/vpsmate/config.py username '用户名'
    /usr/local/vpsmate/config.py password '密码'

#### 功能

* 快速在线安装、小巧且节省资源
* 当前支持 CentOS/Redhat 5.4+、6.x
* 基于发行版软件源的软件管理机制
* 轻松构建 Linux + Nginx + MySQL + PHP 环境
* 强大的在线文件管理和回收站机制
* 快速创建和安装多种站点
* 丰富实用的系统工具
