# -*- coding: utf-8 -*-
'''The InPanel Base Information'''
# Copyright (c) 2017 - present, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

from os.path import exists
from platform import mac_ver, platform, uname, win32_ver

# 基本信息
debug = False
app_name = 'InPanel'
version = '1.2.0'
build = '27'
releasetime = '2022-03-15'

# 版本信息
version_info = {
    'name'        : app_name,
    'build'       : build,
    'changelog'   : 'https://inpanel.org/changelog.html',
    'releasetime' : releasetime,
    'version'     : version
}

# 链接信息
app_api = {
    'latest'           : 'https://api.inpanel.org/?s=latest',
    'site_packages'    : 'https://api.inpanel.org/?s=site_packages',
    'download_package' : 'https://api.inpanel.org/?s=site_packages&a=download'
}

# 配置文件
config_path  = '/usr/local/etc/inpanel/config.ini'
runlogs_path = '/usr/local/etc/inpanel/runlogs.ini'
share_path   = '/usr/local/share/inpanel'
execfile     = '/usr/local/inpanel/inpanel'
logfile      = '/usr/local/var/log/inpanel/main.log'
pidfile      = '/usr/local/var/run/inpanel.pid'

kernel_name, hostname, kernel_release, kernel_version, machine, processor = uname()

# 发行名称，如：CentOS release 8.0
os_title    = 'Unknown'

# 发行名称，如：macOS
os_name     = 'Unknown'

# 发行版本号，如：11.5.2
os_version  = ''

# 发行版本整数，如：11
os_versint  = 0

os_platform = platform()

# 根据内核名称判断
if kernel_name == 'Darwin':
    os_name = 'macOS'
    os_version, _, _ = mac_ver()
    os_versint = os_version.split('.')[0]
    os_title = 'macOS ' + os_version
elif kernel_name == 'Windows':
    os_name = 'Windows'
    os_version, _, _ = win32_ver()
    os_title = 'Windows ' + os_version
    os_versint = os_version.split('.')[0]
elif kernel_name == 'Linux':
    if 'Ubuntu' in kernel_version:
        os_name = 'Ubuntu'
        if exists('/etc/issue'):
            # Ubuntu 20.04.5 LTS \n \l
            with open('/etc/issue', 'r', encoding='utf-8') as f:
                line = f.readlines(1)
                os_title = line[0].replace('\\n', '').replace('\\l', '').strip()
                os_version = os_title.split()[1]
                os_versint = int(os_version.split('.')[0])
    else:
        if '.el8.' in kernel_release:
            os_name = 'CentOS'
            os_versint = 8
            os_title = 'CentOS 8'
        elif '.el7.' in kernel_release:
            os_name = 'CentOS'
            os_versint = 7
            os_title = 'CentOS 7'
        elif '.el6.' in kernel_release:
            os_name = 'CentOS'
            os_versint = 6
            os_title = 'CentOS 6'
        elif '.el5.' in kernel_release:
            os_name = 'CentOS'
            os_versint = 5
            os_title = 'CentOS 5'

server_info = {
    'os_title'      : os_title,        # 系统名称全称
    'os_name'       : os_name,         # 发行名称
    'os_version'    : os_version,      # 发行版本（全）
    'os_versint'    : os_versint,      # 发行版本（主版本号）
    'os_platform'   : os_platform,
    'hostname'      : hostname,        # 主机名
    'kernel_name'   : kernel_name,     # 内核类型
    'kernel_release': kernel_release,  # 内核编号
    'kernel_version': kernel_version,  # 内核版本信息
    'machine'       : machine,         # arch x86_64
    'processor'     : processor
}

__version__ = version

__all__ = [
    '__version__', 'debug', 'app_api', 'app_name', 'build', 'config_path',
    'execfile', 'releasetime', 'version_info', 'version', 'server_info',
    'os_name', 'os_title', 'os_version', 'os_versint', 'os_platform',
    'kernel_name', 'kernel_release', 'kernel_version', 'hostname', 'machine',
    'runlogs_path', 'logfile', 'pidfile', 'processor'
]

if __name__ == '__main__':
    print(uname())
    print(mac_ver())
    print(platform())
    print(server_info)
