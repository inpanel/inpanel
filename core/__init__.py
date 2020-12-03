# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''The InPanel Core.'''


import platform

__version__ = '1.1.1.25'

name = 'InPanel'
version = '1.1.1'
build = '25'
releasetime = '2020-12-03 23:00:00 GMT+0800'
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
system = None
distribution = None
distname = None
distversion = None
distarch = None


system = platform.system()
if hasattr(platform, 'linux_distribution'):
    dist = platform.linux_distribution()
else:
    dist = platform.dist()

distribution = dist[0]
distname = distribution.lower()
distversion = dist[1]
distversion = distversion[0:distversion.find('.', distversion.index('.') + 1)]
distarch = 'x86_64' if platform.machine() == 'x86_64' else 'i386'

__all__ = [
    'api',
    'build',
    'distname',
    'distribution',
    'distversion',
    'distarch',
    'name',
    'releasetime',
    'version_info',
    'version'
]


# distname = dist[0].lower()


# print(distname, platform_version, arch)
# print(platform.platform())
# print('machine', platform.machine())
# print('os', platform.system())
# print('uname', platform.uname())
# print('dist', dist)
