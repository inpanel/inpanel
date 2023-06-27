# InPanel

简体中文 | [English](./README.md)

## 介绍

InPanel 是一个开源的 Linux 服务器管理工具，为得使服务器的管理变得简单、快捷。

## 功能特性

- 免费、简洁、开源
- 快速在线安装、小巧且节省资源
- 当前支持 CentOS/Redhat 6.x、7.x、8.x
- 基于发行版软件源的软件管理机制
- 轻松构建 Linux + Nginx + MySQL + PHP 环境
- 强大的在线文件管理和回收站机制
- 快速创建和安装多种站点
- 丰富实用的系统工具

## 安装

```bash
# stable version
curl -O https://raw.githubusercontent.com/inpanel/inpanel/main/install.py
python install.py

# beta version
curl -O https://raw.githubusercontent.com/inpanel/inpanel/dev/install.py
python install.py --dev
```

## 卸载

在服务器上运行以下命令即可完成卸载：

```bash
service inpanel stop
rm -rf /usr/local/inpanel
rm -f /etc/init.d/inpanel
```

> 注意：卸载不会影响 InPanel 外的其它数据。InPanel 只是在 UI 层面对系统服务及功能进行管理配置，并不会在系统中生成多余的依赖及配置文件，无论卸载或安装，只会影响 InPanel 的数据，对系统已配置好的服务是没有影响的。

## 账号和密码

```bash
/usr/local/inpanel/config.py username '管理员账号'
/usr/local/inpanel/config.py password '管理员密码'
```

## 问题反馈

请到 [Issues](http://github.com/inpanel/inpanel/issues) 提交问题。

## 开源许可

InPanel 采用 [BSD](./LICENSE) 许可发布。

## 作者

[Jackson Dou](https://github.com/jksdou 'Jackson Dou')

## 信息

使用文档：[inpanel.org](https://inpanel.org 'InPanel Docs')

官方中文站：[inpanel.cn](http://inpanel.cn 'InPanel 官方中文站')
