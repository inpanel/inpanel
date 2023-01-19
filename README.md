# InPanel

> InPanel 是一个开源的 Linux 服务器管理工具，为得使服务器的管理变得简单、快捷。
>
> 后端采用 Python 语言编写，采用 [BSD](https://github.com/inpanel/inpanel/blob/main/LICENSE) 许可证。项目于 2017 年 1 月 11 日启动。

官方中文站：[inpanel.cn](http://inpanel.cn 'InPanel')

项目维护者：[Jackson Dou](https://github.com/jksdou 'Jackson Dou')

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
rm -rf /usr/local/inpanel/inpaneld
rm -rf /usr/local/bin/inpanel
rm -rf /usr/local/bin/inpanel-config
rm -rf /usr/local/bin/inpanel-uninstall
rm -f /etc/init.d/inpanel
```

注意：卸载不会影响 InPanel 外的其它数据。InPanel 只是在 UI 层面对系统服务及功能进行管理配置，并不会在系统中生成多余的依赖及配置文件，无论卸载或安装，只会影响 InPanel 的数据，对系统已配置好的服务是没有影响的。

## 账号和密码

```bash
inpanel config username 'your-username'
inpanel config password 'your-password'
```

## 授权许可

本项目采用 BSD 开源授权许可证，完整的授权说明已放置在 [LICENSE](https://github.com/inpanel/inpanel/blob/main/LICENSE) 文件中。
