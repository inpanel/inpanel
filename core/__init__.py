# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''The InPanel Core.'''

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

__all__ = ['api', 'build', 'name', 'releasetime', 'version_info', 'version']
