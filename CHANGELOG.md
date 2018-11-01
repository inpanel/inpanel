#### 项目正式更名为Intranet

>  项目转移到crogram组织

#### VPSMate 已暂停更新

>  感谢大家对 VPSMate 的喜爱和关注，VPSMate 目前已暂停更新。

#### VPSMate v1.0 b10 (2013-01-18)

> **Bug 修复：**
>
> - [解决“Error: No matching Packages to list”的问题。](http://bbs.vpsmate.org/read.php?tid=307)
> - [解决软件源版本更新导致安装失败的问题。](http://bbs.vpsmate.org/read.php?tid=380)

#### VPSMate v1.0 b9 (2012-12-06)

> **Bug 修复：**
>
> - [修复文件名中存在乱码时文件列表加载失败的问题。](http://bbs.vpsmate.org/read.php?tid=267)
> - [修复系统类型为i686时获取软件版本失败的问题。](http://bbs.vpsmate.org/read.php?tid=215)
> - [解决安装MySQL时提示软件冲突/安装失败的问题。](http://bbs.vpsmate.org/read.php?tid=274)
> - [解决安装软件时总是提示已有一个YUM进程正在安装的问题。](http://bbs.vpsmate.org/read.php?tid=113)

#### VPSMate v1.0 b8 (2012-11-20)

> **新功能：**
>
> - 增加对 [atomic](http://www.atomicorp.com/mirrorlist/atomic/) 软件源的支持。
>
> **Bug 修复：**
>
> - [解决远程控制设置保存失败的问题。](http://bbs.vpsmate.org/read.php?tid=131)
> - [解决phpMyAdmin无法安装的问题。](http://bbs.vpsmate.org/read.php?tid=135)
> - [解决部分系统因lvs版本不同导致500错误的问题。](http://bbs.vpsmate.org/read.php?tid=160)
> - [解决数据库密码修改后进入数据库管理异常的问题。](http://bbs.vpsmate.org/read.php?tid=165)
> - 解决在数据库管理中修改root@localhost用户密码后进入数据库管理异常的问题。
> - [解决zip文件解压或压缩时安装zip命令无响应的问题。](http://bbs.vpsmate.org/read.php?tid=146)
> - 解决文件管理中批量删除后，再次点击批量删除时提示文件不存在的问题。
> - [解决强制修改mysql root密码时无响应的问题。](http://bbs.vpsmate.org/read.php?tid=201)
> - [解决 centos 5.4 下强制修改 root 密码失败的问题。](http://bbs.vpsmate.org/read.php?tid=200)
>
> **功能改进：**
>
> - [网站管理和文件管理增加加载提示。](http://bbs.vpsmate.org/read.php?tid=108)
> - 增加对软件 release 的识别管理。
> - 消除登录超时后重登录时URL后面的s=参数串。

#### VPSMate v1.0 b7 (2012-11-07)

> **新功能：**
>
> - 增加对 ssh 服务的配置，支持公钥验证方式。
> - 增加远程管理密钥功能，以支持 [ECSMate](http://www.ecsmate.org/) 的远程管理。
>
> **Bug 修复：**
>
> - 解决部分使用了LVM的系统进入面板首页报未知错误的问题。

#### VPSMate v1.0 b6 (2012-11-04)

> **新功能：**
>
> - 增加 MySQL 数据库管理功能。
>
> **Bug 修复：**
>
> - 解决中文文件内容读取出错的问题，添加对多种字符集的支持。
> - 解决并发写入配置文件导致部分配置丢失的问题。
> - [解决添加只返回错误的Nginx站点后站点列表无法加载的问题。](http://bbs.vpsmate.org/read.php?tid=60)
> - [解决Nginx黑白名单网段保存后变乱的问题。](http://bbs.vpsmate.org/read.php?tid=73)
> - 解决文件名中含有中文时许多操作无响应的问题。
> - [解决Nginx反代网站中，添加多个域名保存后，代理后端配置丢失的问题。](http://bbs.vpsmate.org/read.php?tid=86)
> - 解决首页在线更新按钮点击出现无法找到页面的问题。
> - 解决自动创建缓存区目录报错的问题。
>
> **功能改进：**
>
> - [文件保存时自动生成备份文件。](http://bbs.vpsmate.org/read.php?tid=58)
> - [增加对Nginx跳转地址格式的检测。](http://bbs.vpsmate.org/read.php?tid=57)
> - 文件保存时支持选择指定字符集进行保存。
> - 优化 VPSMate 的加载提示。
> - 优化 Nginx 站点列表、创建Nginx、用户列表、用户组列表的界面。
> - [文件管理增加批量复制、批量剪切功能。](http://bbs.vpsmate.org/read.php?tid=74)
> - 删除文件时，同时删除备份文件。
> - JS压缩并合并为一个文件，加快下载和加载速度。

#### VPSMate v1.0 b5 (2012-10-31)

> **Bug 修复：**
>
> - 解决自动创建缓存区目录报错的问题。
> - 解决中文文件名操作失败的问题。
> - [解决自动创建缓存区目录报错的问题。](http://bbs.vpsmate.org/read.php?tid=42)
> - [解决时区不可识别时显示为空的问题。](http://bbs.vpsmate.org/read.php?tid=45)
> - [解决 Nginx 版本低于 v1.1.8 时连接限制配置出错的问题。](http://bbs.vpsmate.org/read.php?tid=43)
>
> **功能改进：**
>
> - [时区设置时添加快速选择常用时区功能。](http://bbs.vpsmate.org/read.php?tid=45)
> - 增加对 OpenVZ simfs 文件系统的支持。
> - 增加对操作系统虚拟平台的识别。
> - 改进对网络接口类型的检测，支持 OpenVZ 的 venet0:0 格式的接口。
> - [禁用 OpenVZ 平台下的 NTPD 服务。](http://bbs.vpsmate.org/read.php?tid=47)
> - [禁用 OpenVZ 平台下的磁盘分区功能。](http://bbs.vpsmate.org/read.php?tid=46)

#### VPSMate v1.0 b4 (2012-10-30)

> **新功能：**
>
> - 增加对 PHP 的常用配置的支持。
> - 增加对 PHP-FPM 常用配置的支持。
> - [Nginx Rewrite 配置时检测文件是否存在。](http://bbs.vpsmate.org/read.php?tid=19)
> - [增加对 Nginx 反代模式时缓存的支持。](http://bbs.vpsmate.org/read.php?tid=8)
> - 文件管理中增加文件上传功能。
>
> **Bug 修复：**
>
> - 解决文件管理功能中，同名目录覆盖时，原目录会写入为子目录的问题。
> - 解决中文文件名操作失败的问题。
> - [解决 Rewrite 格式检测出错的问题。](http://bbs.vpsmate.org/read.php?tid=17)
> - [解决修改 Nginx 配置后，配置紊乱的问题。](http://bbs.vpsmate.org/read.php?tid=9)
> - [解决 OpenVZ 虚拟机下进入面板出错的问题。](http://bbs.vpsmate.org/read.php?tid=22)
>
> **功能改进：**
>
> - 站点列表按域名字母顺序排列。
> - 删除右下角评论模块，改为链接到官网论坛。

#### VPSMate v1.0 b3 (2012-10-24)

> **新功能：**
>
> - 增加对 Nginx 站点路径的 Rewrite 支持。
> - 增加 MySQL 忘记 root 密码强制重置功能。
>
> **Bug 修复：**
>
> - DEMO 模式下快速安装网站失败的问题。
> - 解决未安装 Nginx 时 Nginx 模块加载时提示未知错误的问题。
> - 解决 Nginx 站点列表为空时提示未知错误的问题。
>
> **功能改进：**
>
> - 改进多窗口登录过期的检测。
> - 登录和修改密码时，将密码MD5后再提交，防止密码明文泄漏，同时改用JS进行密码安全性检测。
> - 改进多标签页模块中的URL定位，刷新后仍可保留在原来的标签页。
> - CentALT 官方的源不稳定，改用 VPSMate 的镜像。

#### VPSMate v1.0 b2 (2012-10-12)

> **Bug 修复：**
>
> - 修正 Nginx 设置黑白名单时，黑白名单为空时服务重启失败的问题。
> - 修正登录评论模块时跳转到首页的问题，以及评论模块中的错误链接。
> - 修正 unzip 时，因为输出太多超出缓冲区导致进程卡死的问题。
>
> **功能改进：**
>
> - VPSMate 帐户密码修改时，需要确认新密码，并将原密码放前面。
> - MYSQL 修改密码时，也需要确认新密码，并将原密码放前面。
> - 改进文件和目录选择器。
> - 同时只允许一个 YUM 操作，防止后台启动过多的YUM进程。
> - 增加 DEMO 演示模式。

#### VPSMate v1.0 b1 (2012-10-10)

> 初始版本发布
