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

### 方法一：通过 pip 安装

```bash
pip install inpanel
```

### 方法二：通过包管理器安装

#### CentOS / RHEL

```bash
# CentOS 8+ / RHEL 8+
dnf install inpanel

# CentOS 7 / RHEL 7
yum install inpanel
```

#### Debian / Ubuntu

```bash
apt-get update
apt-get install inpanel
```

### 方法三：源码安装

```bash
# 克隆源码
git clone https://github.com/inpanel/inpanel.git
cd inpanel

# 开发模式安装（修改代码立即生效）
pip install -e .

# 生产模式安装
pip install .
```

## 服务管理

```bash
# 启动服务（后台运行）
inpanel start

# 停止服务
inpanel stop

# 查看服务状态
inpanel status

# 重启服务
inpanel restart

# 重新加载配置（重启服务）
inpanel reload

# 前台运行（用于调试或 systemd）
inpanel run
```

## 配置

### 修改用户名和密码

```bash
inpanel config username 'your-username'
inpanel config password 'your-password'
```

### 查看所有配置项

```bash
inpanel config
```

### 修改单个配置项

```bash
inpanel config <section> <key> <value>

# 示例：修改端口
inpanel config server port 14433

# 示例：启用 HTTPS
inpanel config server forcehttps on
```

## 卸载

### 使用命令卸载

```bash
# 默认卸载（保留配置文件和日志）
inpanel uninstall

# 完全卸载（删除配置文件和日志）
inpanel uninstall --purge

# 仅删除配置文件
inpanel uninstall --purge-config

# 仅删除日志文件
inpanel uninstall --purge-logs
```

### 手动卸载（备用）

```bash
service inpanel stop
pip uninstall inpanel
rm -rf /etc/inpanel
rm -rf /var/log/inpanel
rm -f /usr/lib/systemd/system/inpanel.service
rm -f /etc/init.d/inpanel
```

注意：卸载不会影响 InPanel 外的其它数据。InPanel 只是在 UI 层面对系统服务及功能进行管理配置，并不会在系统中生成多余的依赖及配置文件，无论卸载或安装，只会影响 InPanel 的数据，对系统已配置好的服务是没有影响的。

## 本地开发

### 环境要求

- Python 3.8+
- pip 20.0+

### 开发步骤

```bash
# 1. 克隆源码
git clone https://github.com/inpanel/inpanel.git
cd inpanel

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖和开发模式
pip install -e .

# 4. 启动开发服务器（前台运行，支持热重载）
inpanel run
```

### 开发模式特点

- 配置文件位于项目目录的 `data/` 文件夹下
- 日志文件位于项目目录的 `data/` 文件夹下
- 修改代码后无需重新安装，直接生效
- 默认启用 DEBUG 模式

### 构建安装包

```bash
# 构建 pip 包
pip install build
python -m build

# 构建 RPM 包（需要 rpmbuild）
rpmbuild -bb inpanel.spec

# 构建 DEB 包（需要 debuild）
debuild -us -uc
```

## 账号和密码

默认用户名：`admin`

默认密码：`admin`

首次登录后请及时修改密码：

```bash
inpanel config password 'new-password'
```

## 授权许可

本项目采用 BSD 开源授权许可证，完整的授权说明已放置在 [LICENSE](https://github.com/inpanel/inpanel/blob/main/LICENSE) 文件中。