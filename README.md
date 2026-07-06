# InPanel

简体中文 | [English](README_EN.md)

> InPanel 是一款轻量级、非入侵式的 Linux 系统级运维管理面板，致力于通过 Web 界面实现高效、安全的服务器运维管理。
>
> 后端采用 Python 语言编写，基于 Tornado 异步框架，采用 [BSD 3-Clause](https://github.com/inpanel/inpanel/blob/main/LICENSE) 开源许可证。项目于 2017 年 1 月 11 日启动，持续维护至今。

官方中文站：[inpanel.cn](http://inpanel.cn 'InPanel')

PyPI：[inpanel](https://pypi.org/project/inpanel/ 'PyPI')

项目维护者：[Jackson Dou](https://github.com/jksdou 'Jackson Dou')

## 功能特性

### 核心优势

- **系统级运维**：直接操作系统原生配置文件（`/etc/passwd`、Nginx vhost、防火墙规则等），不依赖中间层
- **极低入侵度**：纯 UI 层面管理，不修改系统核心架构，卸载后系统无残留、无依赖
- **轻量高效**：内存占用仅 30-40MB，资源消耗极低，适合 VPS/轻量服务器环境
- **全功能免费**：开源 BSD 许可证，所有功能无限制使用，无付费墙

### 系统管理

- 用户与权限管理（系统用户、SSH 密钥、sudo 权限）
- 进程管理与监控（进程查看、终止、资源统计）
- 服务管理（systemd/init.d 服务启停、自启配置）
- 防火墙管理（iptables/firewalld 规则配置）

### 网站运维

- Nginx 虚拟主机管理（配置、SSL、重定向）
- Apache HTTP Server 管理（虚拟主机、模块配置）
- PHP 环境管理（版本切换、配置调整）
- MySQL/MariaDB 管理（数据库、用户、权限）
- FTP 服务管理（vsftpd 配置、用户管理）

### 文件管理

- 强大的在线文件管理器（上传、下载、编辑、压缩）
- 回收站机制（误删文件可恢复）
- 文件权限管理（chmod、chown）
- 远程文件管理（SSH 连接其他服务器）

### 系统工具

- 系统资源监控（CPU、内存、磁盘、网络）
- 软件包管理（YUM/DNF/APT 包管理）
- 计划任务（Crontab 管理）
- 系统更新（自动更新检测与安装）
- SSL 证书管理（Let's Encrypt 自动签发）

### 兼容性

- CentOS/RHEL 7+、Debian 10+、Ubuntu 18.04+
- Python 3.6+（兼容至 Python 3.14）

## 版本兼容

| Python 版本 | 状态 |
|-------------|------|
| Python 3.6 | ✅ 兼容 |
| Python 3.7+ | ✅ 兼容 |
| Python 3.12-3.14 | ✅ 兼容（需 tornado>=6.5）|
| Python 3.5 及以下 | ❌ 不支持 |

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

### 查看所有配置项

```bash
inpanel config list
```

### 修改用户名和密码

```bash
inpanel config set auth username 'your-username'
inpanel config set auth password 'your-password'
```

### 修改单个配置项

```bash
inpanel config set <section> <option> <value>

# 示例：修改端口
inpanel config set server port 14433

# 示例：启用 HTTPS
inpanel config set server forcehttps on
```

### 查看配置项

```bash
inpanel config get <section> <option>

# 示例：查看端口
inpanel config get server port
```

### 重置配置

```bash
# 重置为默认配置
inpanel config reset

# 初始化配置文件（首次安装）
inpanel config init
```

## 卸载

### 方法一：使用官方命令卸载（推荐）

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

### 方法二：使用包管理器卸载

#### 通过 pip 安装的情况

```bash
# 停止服务
inpanel stop

# 卸载包
pip uninstall inpanel
```

#### 通过 RPM 包安装的情况（CentOS/RHEL）

```bash
# 保留配置文件卸载
yum remove inpanel

# 完全卸载（删除配置文件）
yum erase inpanel
```

#### 通过 DEB 包安装的情况（Debian/Ubuntu）

```bash
# 保留配置文件卸载
apt-get remove inpanel

# 完全卸载（删除配置文件）
apt-get purge inpanel
```

### 方法三：手动卸载（备用）

```bash
# 停止服务
inpanel stop

# 卸载 Python 包
pip uninstall inpanel

# 删除配置文件
rm -rf /etc/inpanel

# 删除日志文件
rm -rf /var/log/inpanel

# 删除 systemd 服务
rm -f /usr/lib/systemd/system/inpanel.service
rm -f /etc/systemd/system/inpanel.service
systemctl daemon-reload

# 删除 init.d 脚本
rm -f /etc/init.d/inpanel
```

### 卸载注意事项

InPanel 采用**非入侵式架构设计**，所有操作均基于系统原生配置文件，卸载后具有以下特性：

| 特性 | 说明 |
|------|------|
| **无残留依赖** | 卸载仅移除 InPanel 自身组件，不影响系统原有依赖包 |
| **配置文件保留** | 默认卸载保留配置文件（`/etc/inpanel/`），便于后续重新安装恢复配置 |
| **系统服务不受影响** | 通过 InPanel 配置的 Nginx、MySQL、PHP 等服务继续正常运行 |
| **用户数据安全** | 网站文件、数据库等用户数据不受卸载影响 |
| **进程干净退出** | 卸载前自动停止 InPanel 服务并清理 PID 文件 |

**卸载后系统状态**：
- `/etc/passwd`、`/etc/group` 等系统用户配置保持不变
- Nginx vhost 配置、防火墙规则等保持不变
- 已安装的软件包（Nginx、MySQL、PHP 等）保持不变
- 仅移除 InPanel 服务进程、配置目录和日志文件

> **提示**：如需完全清理所有数据，请使用 `inpanel uninstall --purge` 命令。

## 本地开发

### 环境要求

- Python 3.6+
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
inpanel config set auth password 'new-password'
```

## 授权许可

本项目采用 BSD 开源授权许可证，完整的授权说明已放置在 [LICENSE](https://github.com/inpanel/inpanel/blob/main/LICENSE) 文件中。