# Intranet


Intranet —— 基于 VPSMate v1.0 b10 二次开发的开源 VPS 管理面板

官方网站：[intranet.pub](http://intranet.pub "Intranet")

#### 安装

```shell
curl -O https://raw.githubusercontent.com/crogram/intranet/master/install.py
python install.py
```

#### 卸载

```shell
service vpsmate stop
rm -rf /usr/local/vpsmate
rm -f /etc/init.d/vpsmate
```

#### 重置用户名或密码

```shell
/usr/local/vpsmate/config.py username '用户名'
/usr/local/vpsmate/config.py password '密码'
```

#### 功能

- 免费、简洁、开源
- 快速在线安装、小巧且节省资源
- 当前支持 CentOS/Redhat 5.4+、6.x
- 基于发行版软件源的软件管理机制
- 轻松构建 Linux + Nginx + MySQL + PHP 环境
- 强大的在线文件管理和回收站机制
- 快速创建和安装多种站点
- 丰富实用的系统工具

#### 从 VPSMate 到 Intranet

本管理面板只是在 UI 层面对系统服务及功能进行管理配置，并不会在系统中生成多余的依赖及配置文件，不管VPSMate 还是 Intranet，只是工具而已，卸载或安装，对系统已配置好的服务是没有影响的。

现阶段两者使用同一个进程服务文件，所以**只需要卸载 VPSMate ，再安装 Intranet 即可**。

> 希望你用得愉快 ！

