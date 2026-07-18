## InPanel v1.2.5 (2026-07-18)

**版本更新：**

- 发布 InPanel v1.2.5

**任务管理重构：**

- 后端路由和处理器重命名：`BackendHandler` → `TaskHandler`，`/api/backend/` → `/api/task/`
- 新增任务列表查询接口（`/api/task/list`），支持查看所有后台任务状态
- 新增任务取消支持，`Task.call` 前端方法支持 `cancel` 状态处理
- 修复 `functools.partial` 对象无法被 `await` 导致任务异步执行异常的问题
- 新增后台异步任务管理页面（`/utils/task`），支持任务统计、状态查看和取消操作

**查询接口优化：**

- 通配符重命名：`**` → `all`、`*` → `dynamic`，语义更清晰
- 修复 `service.all` 通配符解析错误，通配符被错误追加到列表导致匹配失败

**前端重构：**

- 服务工厂重命名：`Backend` → `Task`，所有控制器同步更新依赖注入
- 路由配置新增 `/utils/task` 页面入口
- 工具列表新增"后台异步任务"入口

**其他：**

- 修复 `remote.py` 相对导入路径错误（`.lib` → `..lib`）
- 删除未使用的 `ufw.py` 模块
- 版本号更新至 1.2.5

## InPanel v1.2.4 (2026-07-17)

**版本更新：**

- 发布 InPanel v1.2.4

**代码注释中文化：**

- 全部模块的 docstring 和行内注释从英文翻译为中文（涵盖 55 个模块）

**项目结构优化：**

- 将 acme.py、aliyuncs.py、remote.py 从 inpanel/ 迁移至 inpanel/mod/
- 将 file/preview.html、index.html 从 templates/ 迁移至 public/templates/
- 删除顶层已废弃的 apt.py、dnf.py、yum.py

**软件源管理重构：**

- 新增软件源 JSON 模板系统（templates/sources/，含 apt/brew/dnf/docker/pip/yum 等 8 个配置文件）
- 新增 Docker 镜像源管理模块（docker_source.py），支持镜像源增删改查与切换
- 重构 apt/brew/dnf/yum/pip 模块，统一源管理 API
- 新增统一的 sources.html 前端页面，替换旧 repository.html

**其他：**

- 移除 plugin.py 中不必要的 typing 导入，提升低版本 Python 兼容性
- 修复 config.py 密码 HMAC 计算逻辑

## InPanel v1.2.3 (2026-07-12)

**版本更新:**

- 发布 InPanel v1.2.3

**插件系统重构:**

- 新增插件基类（`inpanel/plugin.py`），定义插件接口和生命周期管理
- 新增插件管理模块（`inpanel/mod/plugins.py`），支持插件列表、安装、配置、启用/禁用
- 新增插件前端页面：config.html、detail.html、info.html
- 重构 plugins.js 控制器，实现全新插件管理界面
- 重构 plugins/index.html 列表页面，增强插件管理功能
- 删除旧版 plugins.html 文件
- 在 web.py 中新增插件管理 API 接口
- 更新 app.py 和 base.py，集成插件系统
- 补充插件切换和卸载操作的日志记录

**包管理增强:**

- 新增 macOS brew 包管理模块（`inpanel/mod/brew.py`）
- 新增 Python pip 包管理模块（`inpanel/mod/pip.py`）
- 在 web.py 中新增 RepoBrewHandler 和 RepoPipHandler 处理 brew/pip API
- 新增 RepoSupportedHandler，根据操作系统自动检测支持的包管理器
- 优化 yum/dnf/apt 包管理模块

**Docker 容器管理:**

- 新增 Docker 容器管理模块（`inpanel/mod/docker.py`）
- 支持容器列表、启动/停止/重启/删除操作
- 支持容器日志查看
- 支持容器镜像管理

**多语言版本管理:**

- 支持 Java 版本管理
- 支持 Node.js 版本管理
- 支持 PHP 版本管理

**安装与系统兼容:**

- 新增安装类型检测（pip/RPM/DEB），重构模块实例化方式
- 补充时间设置模块中当前时间和时区数据，兼容 macOS 系统

**打包配置优化:**

- 更新 debian/control 依赖配置
- 修正 rpmbuild.spec 中 URL 格式
- 更新 .gitignore，忽略 *.code-workspace 文件

**Bug 修复:**

- 修复插件管理界面状态刷新问题
- 修复插件详情页按钮样式和文本显示
- 修复插件列表页空状态表格列数不匹配
- 修复导航菜单链接指向

## InPanel v1.2.2 (2026-07-08)

**版本更新:**

- 发布 InPanel v1.2.2

**功能改进:**

- 新增常用目录功能：点击 star 图标添加到常用目录，点击 remove 图标取消
- 常用目录支持文件和目录类型，文件点击时自动打开所在目录
- 将 runlogs.ini 重命名为 lastfile.ini，记录最后操作的文件和目录
- 将 update_info.ini 重命名为 upgrade.ini，统一升级配置文件命名
- 修复下拉菜单宽度被超长路径撑宽的问题，添加文本截断处理

**项目结构优化:**

- 删除根目录下的 public/ 文件夹，前端资源已统一移至 inpanel/public/
- 删除冗余的 README-zh.md 文件，中文文档统一使用 README.md

**打包配置优化:**

- 新增 MANIFEST.in，排除 test/tests 文件夹在构建时被包含
- 在 pyproject.toml 中添加 exclude 参数，排除 test* 包
- 删除根目录下冗余的 templates/ 文件夹，模板已统一移至 inpanel/templates/
- 将 inpanel.spec 重命名为 rpmbuild.spec，避免与 PyInstaller 的 spec 文件混淆
- 删除 PyInstaller 构建脚本 build.sh 和相关依赖
- 移除 requirements.txt 中的 pyinstaller 依赖

**Bug 修复:**

- 登录页：更新重置密码命令格式

## InPanel v1.2.1 (2026-07-07)

**版本更新:**

- 发布 InPanel v1.2.1

**安全修复:**

- 修复密码明文存储问题，使用 HMAC-MD5 哈希处理密码
- 在配置查看命令中隐藏密码字段显示，防止敏感信息泄露
- 在认证模块中添加详细日志记录，便于排查安全问题

**功能改进:**

- 文件管理浏览历史改为服务器端持久化存储，支持最大30条记录
- 浏览历史自动去重并按访问时间排序
- 将版本更新信息从 config.ini 独立到 update_info.ini 存储
- 前端浏览历史从 Cookie 存储改为 API 接口动态获取
- 新增 history_path 路径配置，支持三种运行模式

**版本管理:**

- 以 pyproject.toml 为单一版本源，程序运行时自动读取
- RPM 包使用 %pyproject_version 宏动态获取版本号
- DEB 包构建时自动生成 changelog

**Python 兼容性:**

- 修复 Python 3.8 兼容性问题（联合类型语法）
- 修复 Python 3.9+ 泛型类型注解问题
- 修复正则表达式转义序列警告
- 更新最低支持版本为 Python 3.6
- 添加 Python 3.12-3.14 版本分类

**文档优化:**

- 优化中文和英文 README 文档

**其他:**

- 修改 .gitignore 忽略开发模式下的 inpanel/data/* 目录
- 更新 GitHub Actions 工作流配置

**Bug 修复:**

- 修复密码明文存储问题，使用 HMAC-MD5 哈希处理密码
- 修复 Python 3.8 兼容性问题（联合类型语法）
- 修复 Python 3.9+ 泛型类型注解问题
- 修复正则表达式转义序列警告

## InPanel v1.2.0 (2026-07-05)

**特别说明：本次变更不兼容之前版本，导致本次更新需要全新安装，不能从之前的版本兼容升级，很抱歉因此给你带来不便。**

**版本更新:**

- 发布 InPanel v1.2.0

**核心重构:**

- 代码重构：全面升级到 Python3，移除对 Python2 的支持
- 依赖升级：升级 tornado 到 6.0+、psutil 到 5.6+、pexpect 到 4.6+、cryptography 到 2.8+
- 项目结构重构：所有源码迁移到 inpanel/ 子目录，符合 Python 包规范
- 新增 pyproject.toml，使用现代 Python 打包规范（PEP 621）

**安装与分发:**

- 发布形式调整：使用 Python 包形式分发，支持 pip/RPM/DEB 多种安装方式
- 命令入口统一：`/usr/bin/inpanel`，支持 start/stop/status/restart/reload/run/config 子命令
- 新增 yum/apt 一键安装支持，用户可通过 `curl | bash` 自动配置源并安装
- 新增 RPM 打包支持，兼容 CentOS/RHEL/Fedora 发行版
- 新增 DEB 打包支持，兼容 Ubuntu/Debian 发行版
- 新增 GitHub Actions CI/CD 自动构建部署流程，标签触发自动构建
- 新增 scripts/build_package.sh，一键构建 RPM/DEB 包
- 新增 scripts/build_repo.sh，构建 yum/apt 仓库
- 新增 scripts/init_repo.sh，初始化 repo.inpanel.org 仓库
- 新增 install_repo.sh，用户一键安装脚本

**配置与数据:**

- 配置文件调整：移入 /etc/inpanel/config.ini，默认自动生成，默认账号/密码 admin
- 日志文件：放置在 /var/log/inpanel 目录
- 支持通过命令行修改配置：`inpanel config <section> <key> <value>`
- 支持修改用户名和密码：`inpanel config username/password <value>`

**服务管理:**

- 更新 systemd 服务配置（/usr/lib/systemd/system/inpanel.service）
- 更新 init.d 服务配置（/etc/init.d/inpanel），支持 CentOS/RHEL/Ubuntu
- 更新 macOS 服务配置（launchd）
- 支持服务自启动：安装后自动启用并启动服务
- 支持服务卸载：`inpanel uninstall` 命令，可选保留或删除配置和日志

**系统兼容:**

- 支持 CentOS/RHEL 7/8/9
- 支持 Ubuntu 20.04/22.04/24.04
- 支持 Debian 10/11/12
- 支持 macOS 系统基础功能
- 基础功能支持：系统概览、文件管理、用户管理、进程查看等

**功能改进:**

- 新增运行模式设置：生产模式、演示模式（调整到演示模式后不支持再次修改）
- 新增页面：【关于应用】、【捐助项目】，增加了捐助通道（微信、支付宝扫码）
- 文件管理：新增图片预览功能
- 插件系统：支持 acme、shadowsocks-libev 等插件
- 文件管理：支持回收站机制
- 站点管理：支持 Nginx/Apache 站点的创建和管理
- 数据库管理：支持 MySQL/MariaDB 数据库管理
- 软件包管理：支持 yum/dnf/apt 多种包管理器
- 防火墙管理：支持 iptables/firewalld/ufw

**Bug 修复:**

- 待补充

## InPanel v1.1.1 b31 (2024-06-25)

**版本更新:**

- 发布 InPanel v1.1.1 b31

> **功能改进:**

- 新增端口占用查看功能

## InPanel v1.1.1 b30 (2024-06-25)

**版本更新:**

- 发布 InPanel v1.1.1 b30

**功能改进:**

- 新增 MinIO 管理模块
- 新增文件管理-【常用目录】文件快捷操作
- 新增文件管理-【浏览历史】目录记录，最大支持30条

## InPanel v1.1.1 b29 (2023-06-29)

**版本更新:**

- 发布 InPanel v1.1.1 b29

**Bug修复:**

- 修复打开根路径 `/` 时账号登录失效的问题

**功能改进:**

## InPanel v1.1.1 b28 (2023-06-27)

**版本更新:**

- 发布 InPanel v1.1.1 b28

**功能改进:**

- 添加控制命令、配置和卸载脚本文件，安装位置在 /usr/local/bin/inpanel，/usr/local/bin/inpanel-config 和 /usr/local/bin/inpanel-uninstall
- 补充 runtime 接口

## InPanel v1.1.1 b27 (2023-06-27)

**版本更新:**

- 发布 InPanel v1.1.1 b27

**功能改进:**

- 更新 README.md

## InPanel v1.1.1 b26 (2023-06-26)

**版本更新:**

- 发布 InPanel v1.1.1 b26

**Bug 修复:**

- 修复打开根路径 `/` 时账号登录失效的问题

**功能改进:**

- 新增页面：【关于应用】、【捐助项目】，增加了捐助通道（微信、支付宝扫码）
- 接口调整：所有接口地址调整到子目录 /api/
- 路径调整：首页路径调整为 `/`
- 界面调整：部分表格样式完善
- 完善逻辑：core/modules/server.py

#### InPanel v1.1.1 b25 (2020-12-03)

**版本更新:**

- 发布 InPanel v1.1.1 b25

**Bug 修复:**

- 更新 CentOS 7 yum 源配置文件

#### InPanel v1.1.1 b24 (2020-10-06)

**版本更新:**

- 发布 InPanel v1.1.1 b24

**功能改进:**

- 优化主界面内存统计信息及自动刷新开关
- **Bug 修复:**

- 修复文件名或路径包含#等特殊符号的文件下载时出错的问题

#### InPanel v1.1.1 b23 (2020-05-13)

**版本更新:**

- 发布 InPanel v1.1.1 b23

**Bug 修复:**

- 修复: 更新 centos-release-7 链接地址

#### InPanel v1.1.1 b22 (2020-04-05)

**版本更新:**

- 发布 InPanel v1.1.1 b22

**新增功能:**

- 新增: 支持客户端模块
- 新增: 面板配置，可自定义 SSL 证书与私钥

**Bug 修复:**

- 修复: Nginx 站点配置中 SSL 显示状态不对的问题
- 修复: 文件名包含空格的不能进行压缩和解压的问题
- 修复: 链接文件不能删除，实际删除的是原始文件的问题

**功能改进:**

- 优化安装脚本，增加可选参数，自定义安装
- 优化内存使用统计
- 优化远程控制功能，支持客户端授权模式

#### InPanel v1.1.1 b21 (2019-12-24)

**版本更新:**

- 发布 InPanel v1.1.1 b21

**新增功能:**

- 新增: FTP 客户端模块
- 新增: 复制文件至 FTP 的功能
- 新增: 设置项，可强制使用 HTTPS 访问面板
- 新增: 对 CentOS7 及以上版本的简单支持

**功能改进:**

- 暂无

**正在开发:**

- SSL 管理
- Apache 站点修改功能
- Shadowsocks 管理
- 网络磁盘 管理
- 软件仓库 管理

#### InPanel v1.1.1 b20 (2019-08-08)

**版本更新:**

- 发布 InPanel v1.1.1 b20

**新增功能:**

- 新增: 用户及系统级的 Cron 任务的增删改查
- 新增: 在线执行 SHELL 命令功能（超级简单版）

**功能改进:**

- 优化安装脚本对依赖包 epel-release 的安装
- 优化 Apache 站点的添加，支持多个域名配置，站点目录不存在时可直接创建
- 快速安装建站系统接口的完善
- 前端页面 loading 块改为可复用组件

**正在开发:**

- SSL 管理
- Apache 站点修改功能
- Shadowsocks 管理
- 网络磁盘 管理
- 软件仓库 管理

#### InPanel v1.1.1 b19 (2019-04-02)

**版本更新:**

- 发布 InPanel v1.1.1 b19

**Bug 修复:**

- 修复: 对 iptables 运行状态显示不匹配的问题
- 修复: 在查看 Nginx 站点配置中,地址为 IPv6 时,显示异常的问题
- 修复: 在修改 Nginx 站点配置中,地址为 IPv6 时,保存报错的问题
- 修复: 在修改 Nginx 站点配置中,选中快捷选择的端口时保存报错的问题

**新增功能:**

- 新增: 对 Nginx 站点管理中 IPv6 地址配置的支持
- 新增: 对 Samba 服务的基础支持
- 新增: 网络磁盘管理页面
- 新增: 软件仓库的管理页面

**功能改进:**

- 面板服务开启 Gzip 压缩,页面加载更快
- Apache 的管理添加了对 IPv6 的支持
- 对代码进行了优化和调整,站点、进程、用户、管理等界面也做了优化调整

**正在开发:**

- SSL 管理
- Apache 管理
- Shadowsocks 管理
- 网络磁盘 管理
- 软件仓库 管理

#### InPanel v1.1.1 b18 (2019-02-23)

**注意：由于项目名称的变更，导致本次更新需要全新安装，不能从之前的版本兼容升级，很抱歉因此给你带来不便。**

**版本更新：**

- 发布 InPanel v1.1.1 b18
- 项目统一使用 InPanel 标识

**Bug 修复：**

- 修复查看进程列表界面，JS 错误导致自动请求停止的问题
- 修复保存 DNS 为空时出错的问题
- 修复保存绑定的 IP 或端口时报错的问题

**新增功能：**

- 新增：修改主机名(工具 > 网络设置 > 修改主机名)
- 新增：进程管理 > 强制停止进程操作

**功能改进：**

- 优化登陆界面对账号或密码为空时的判断
- 退出登录时头部导航菜单的及时更新
- 程序自有功能模块文件统一到 modules 目录，导入的第三方模块统一放置在 lib 目录，目录 plugins 作为插件模块（计划）
- 对程序代码进行了优化，部分界面也做了优化调整
- Nginx 站点管理界面做优化

**正在开发：**

- SSL 管理
- Apache 管理
- Shadowsocks 管理

#### Intranet Panel v1.1.1 b17 (2018-12-20)

**Bug 修复：**

- 修复时间设置界面进入后出现接口报错的问题
- 修复时间同步服务界面一直提示“正在检测 NTPD 服务” 无法使用的问题
- 修复安装之后 8888 端口在打开防火墙时不能访问的问题

**新增功能：**

- 增加对软件 Lighttpd、named 的支持
- 增加 FTP 软件 ProFTPD、Pure-FTPd 支持

**功能改进：**

- 针对 vsftp、SSH、NTP、ProFTPD、Pure-FTPd、iptables 及 Lighttpd 等扩展包的支持
- 安装时软件仓库的安装先于依赖软件

#### Intranet Panel v1.1.1 b16 (2018-12-17)

**注意：本次升级必须重新安装，不能从之前的版本兼容升级**

**版本升级：**

- 后端服务脚本及前端页面程序重命名为 intranet
- 全新安装 Intarnet 时，加入对 VPSMate 的检测，可以选择保留 VPSMate，暂时和 Intranet 不能同时运行

#### Intranet Panel v1.1.1 b15 (2018-12-13)

**Bug 修复：**

- 修复版本更新完成时页面显示的版本信息与当前实际版本信息不一致的问题

#### Intranet Panel v1.1.1 b14 (2018-12-13)

**版本升级：**

- 更新版本到 v1.1.1b14，用于测试版本更新

#### Intranet Panel v1.1.1 b13 (2018-12-13)

**Bug 修复：**

- 修复版本更新时配置文件丢失的问题

#### 项目更名为 Intranet Panel (2018-12-13)

**项目调整：**

- 项目名称改为 Intranet Panel，并转移到 intranet-panel 组织
- 相关项目：Intranet Site、Intranet API 和 Intranet Docs 也一并转移到 intranet-panel

#### Intranet v1.1.1 b12 (2018-12-12)

**功能改进：**

- 完善更新功能

**Bug 修复：**

- 修复更新接口的报错信息

#### Intranet v1.1.1 b11 (2018-11-10)

**发布第一个正式版本：v1.1.1 b11**

版本号均在 VPSMate 的基础上加一

#### 项目正式更名为 Intranet (2018-11-01)

**项目调整：**

- 项目名称改为 Intranet，并转移到 crogram 组织，便于协同开发
- 新增 TODOLIST 任务列表

#### 项目许可文件更新 (2018-10-25)

**项目调整：**

许可文件更新，使用 The New BSD License 许可

#### 项目启动更新 (2017-08-14)

**项目启动：**

以 VPSMate 为基础，二次开发的项目 Intranet 正式启动，Intranet 将一如既往的保持原来 VPSMate 的简洁与快速，希望大家喜爱和关注。

#### VPSMate 项目已暂停更新

感谢大家对 VPSMate 的喜爱和关注，VPSMate 目前已暂停更新。

#### VPSMate v1.0 b10 (2013-01-18)

**Bug 修复：**

- 解决“Error: No matching Packages to list”的问题。
- 解决软件源版本更新导致安装失败的问题。

#### VPSMate v1.0 b9 (2012-12-06)

**Bug 修复：**

- 修复文件名中存在乱码时文件列表加载失败的问题。
- 修复系统类型为 i686 时获取软件版本失败的问题。
- 解决安装 MySQL 时提示软件冲突/安装失败的问题。
- 解决安装软件时总是提示已有一个 YUM 进程正在安装的问题。

#### VPSMate v1.0 b8 (2012-11-20)

**新功能：**

- 增加对 [atomic](http://www.atomicorp.com/mirrorlist/atomic/) 软件源的支持。

**Bug 修复：**

- 解决远程控制设置保存失败的问题。
- 解决 phpMyAdmin 无法安装的问题。
- 解决部分系统因 lvs 版本不同导致 500 错误的问题。
- 解决数据库密码修改后进入数据库管理异常的问题。
- 解决在数据库管理中修改 root@localhost 用户密码后进入数据库管理异常的问题。
- 解决 zip 文件解压或压缩时安装 zip 命令无响应的问题。
- 解决文件管理中批量删除后，再次点击批量删除时提示文件不存在的问题。
- 解决强制修改 mysql root 密码时无响应的问题。
- 解决 centos 5.4 下强制修改 root 密码失败的问题。

**功能改进：**

- 网站管理和文件管理增加加载提示。
- 增加对软件 release 的识别管理。
- 消除登录超时后重登录时 URL 后面的 s= 参数串。

#### VPSMate v1.0 b7 (2012-11-07)

**新功能：**

- 增加对 ssh 服务的配置，支持公钥验证方式。
- 增加远程管理密钥功能，以支持 ECSMate 的远程管理。

**Bug 修复：**

- 解决部分使用了 LVM 的系统进入面板首页报未知错误的问题。

#### VPSMate v1.0 b6 (2012-11-04)

**新功能：**

- 增加 MySQL 数据库管理功能。

**Bug 修复：**

- 解决中文文件内容读取出错的问题，添加对多种字符集的支持。
- 解决并发写入配置文件导致部分配置丢失的问题。
- 解决添加只返回错误的 Nginx 站点后站点列表无法加载的问题。
- 解决 Nginx 黑白名单网段保存后变乱的问题。
- 解决文件名中含有中文时许多操作无响应的问题。
- 解决 Nginx 反代网站中，添加多个域名保存后，代理后端配置丢失的问题。
- 解决首页在线更新按钮点击出现无法找到页面的问题。
- 解决自动创建缓存区目录报错的问题。

**功能改进：**

- 文件保存时自动生成备份文件。
- 增加对 Nginx 跳转地址格式的检测。
- 文件保存时支持选择指定字符集进行保存。
- 优化 VPSMate 的加载提示。
- 优化 Nginx 站点列表、创建 Nginx、用户列表、用户组列表的界面。
- 文件管理增加批量复制、批量剪切功能。
- 删除文件时，同时删除备份文件。
- JS 压缩并合并为一个文件，加快下载和加载速度。

#### VPSMate v1.0 b5 (2012-10-31)

**Bug 修复：**

- 解决自动创建缓存区目录报错的问题。
- 解决中文文件名操作失败的问题。
- 解决自动创建缓存区目录报错的问题。
- 解决时区不可识别时显示为空的问题。
- 解决 Nginx 版本低于 v1.1.8 时连接限制配置出错的问题。

**功能改进：**

- 时区设置时添加快速选择常用时区功能。
- 增加对 OpenVZ simfs 文件系统的支持。
- 增加对操作系统虚拟平台的识别。
- 改进对网络接口类型的检测，支持 OpenVZ 的 venet0:0 格式的接口。
- 禁用 OpenVZ 平台下的 NTPD 服务。
- 禁用 OpenVZ 平台下的磁盘分区功能。

#### VPSMate v1.0 b4 (2012-10-30)

**新功能：**

- 增加对 PHP 的常用配置的支持。
- 增加对 PHP-FPM 常用配置的支持。
- Nginx Rewrite 配置时检测文件是否存在。
- 增加对 Nginx 反代模式时缓存的支持。
- 文件管理中增加文件上传功能。

**Bug 修复：**

- 解决文件管理功能中，同名目录覆盖时，原目录会写入为子目录的问题。
- 解决中文文件名操作失败的问题。
- 解决 Rewrite 格式检测出错的问题。
- 解决修改 Nginx 配置后，配置紊乱的问题。
- 解决 OpenVZ 虚拟机下进入面板出错的问题。

**功能改进：**

- 站点列表按域名字母顺序排列。
- 删除右下角评论模块，改为链接到官网论坛。

#### VPSMate v1.0 b3 (2012-10-24)

**新功能：**

- 增加对 Nginx 站点路径的 Rewrite 支持。
- 增加 MySQL 忘记 root 密码强制重置功能。

**Bug 修复：**

- DEMO 模式下快速安装网站失败的问题。
- 解决未安装 Nginx 时 Nginx 模块加载时提示未知错误的问题。
- 解决 Nginx 站点列表为空时提示未知错误的问题。

**功能改进：**

- 改进多窗口登录过期的检测。
- 登录和修改密码时，将密码 MD5 后再提交，防止密码明文泄漏，同时改用 JS 进行密码安全性检测。
- 改进多标签页模块中的 URL 定位，刷新后仍可保留在原来的标签页。
- CentALT 官方的源不稳定，改用 VPSMate 的镜像。

#### VPSMate v1.0 b2 (2012-10-12)

**Bug 修复：**

- 修正 Nginx 设置黑白名单时，黑白名单为空时服务重启失败的问题。
- 修正登录评论模块时跳转到首页的问题，以及评论模块中的错误链接。
- 修正 unzip 时，因为输出太多超出缓冲区导致进程卡死的问题。

**功能改进：**

- VPSMate 帐户密码修改时，需要确认新密码，并将原密码放前面。
- MYSQL 修改密码时，也需要确认新密码，并将原密码放前面。
- 改进文件和目录选择器。
- 同时只允许一个 YUM 操作，防止后台启动过多的 YUM 进程。
- 增加 DEMO 演示模式。

#### VPSMate v1.0 b1 (2012-10-10)

初始版本发布
