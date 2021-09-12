# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''The InPanel Base.'''

from platform import uname

__version__ = '1.1.1.26'

name = 'InPanel'
version = '1.1.1'
build = '26'
releasetime = '2021-09-20 23:00:00 GMT+0800'

version_info = {
    'name': name,
    'build': build,
    'version': version,
    'releasetime': releasetime
}

api = {
    'latest': 'http://api.inpanel.org/?s=latest',
    'site_packages': 'http://api.inpanel.org/?s=site_packages',
    'download_package': 'http://api.inpanel.org/?s=site_packages&a=download'
}

kernel_name, node, kernel_release, kernel_version, machine, processor = uname()

distribution = 'Unknown'
dist_version = ''
dist_versint = 0
if '.el8.' in kernel_release:
    distribution = 'CentOS'
    dist_versint = 8
elif '.el7.' in kernel_release:
    distribution = 'CentOS'
    dist_versint = 7
elif '.el6.' in kernel_release:
    distribution = 'CentOS'
    dist_versint = 6
elif '.el5.' in kernel_release:
    distribution = 'CentOS'
    dist_versint = 5

server_info = {
    'distribution': distribution,
    'dist_version': dist_version,
    'dist_versint': dist_versint,
    'kernel_name': kernel_name,
    'node': node,
    'kernel_release': kernel_release,
    'kernel_version': kernel_version,
    'machine': machine,  # arch
    'processor': processor
}

__all__ = [
    '__version__', 'api', 'build', 'name', 'releasetime', 'version_info',
    'version', 'server_info', 'distribution', 'dist_version', 'dist_versint',
    'kernel_name', 'kernel_release', 'kernel_version', 'node', 'machine',
    'processor'
]
