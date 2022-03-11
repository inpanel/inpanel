# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - present, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.
'''The InPanel Base Information'''

from platform import mac_ver, platform, uname, win32_ver

__license__ = 'BSD'
__version__ = '1.1.1.26'
__author__ = 'Jackson Dou'

# 程序基本信息
app_name = 'InPanel'
version = '1.1.1'
build = '26'
releasetime = '2021-09-20 23:00:00 GMT+0800'

# 程序版本信息
version_info = {
    'name': app_name,
    'build': build,
    'version': version,
    'releasetime': releasetime
}

# 程序接口地址
app_api = {
    'latest': 'http://api.inpanel.org/?s=latest',
    'site_packages': 'http://api.inpanel.org/?s=site_packages',
    'download_package': 'http://api.inpanel.org/?s=site_packages&a=download'
}

# 主配置文件
# config_path = '/etc/inpanel/config.ini'
config_path = '/usr/local/etc/inpanel/config.ini'

kernel_name, hostname, kernel_release, kernel_version, machine, processor = uname()

# 发行名称，如：MacOS
dist_name = 'Unknown'

# 发行版本号，如：11.5.2
dist_version = ''

# 发行版本整数，如：11
dist_versint = 0

dist_platform = platform()

# 根据内核名称判断
if kernel_name == 'Darwin':
    dist_name = 'MacOS'
    dist_version, _, _ = mac_ver()
    dist_versint = dist_version.split('.')[0]
elif kernel_name == 'Windows':
    dist_name = 'Windows'
    dist_version, _, _ = win32_ver()
    dist_versint = dist_version.split('.')[0]
elif kernel_name == 'Linux':
    if 'Ubuntu' in kernel_version:
        dist_name = 'Ubuntu'
        dist_versint = int(kernel_release.split('.')[0])
    else:
        if '.el8.' in kernel_release:
            dist_name = 'CentOS'
            dist_versint = 8
        elif '.el7.' in kernel_release:
            dist_name = 'CentOS'
            dist_versint = 7
        elif '.el6.' in kernel_release:
            dist_name = 'CentOS'
            dist_versint = 6
        elif '.el5.' in kernel_release:
            dist_name = 'CentOS'
            dist_versint = 5

server_info = {
    'dist_name': dist_name,  # 发行名称
    'dist_version': dist_version,  # 发行版本（全）
    'dist_versint': dist_versint,  # 发行版本（主版本号）
    'dist_platform': dist_platform,
    'hostname': hostname,  # 主机名
    'kernel_name': kernel_name,  # 内核类型
    'kernel_release': kernel_release,  # 内核编号
    'kernel_version': kernel_version,  # 内核版本信息
    'machine': machine,  # arch x86_64
    'processor': processor
}

__all__ = [
    '__version__', 'app_api', 'app_name', 'build', 'config_path',
    'releasetime', 'version_info', 'version', 'server_info', 'dist_name',
    'dist_version', 'dist_versint', 'dist_platform', 'kernel_name',
    'kernel_release', 'kernel_version', 'hostname', 'machine', 'processor'
]

if __name__ == '__main__':
    print(uname())
    print(mac_ver())
    print(platform())
    print(server_info)
