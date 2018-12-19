# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Lighttpd configuration management."""


def web_response(self):
    action = self.get_argument('action', '')
    if action == 'getsettings':
        self.write({'code': 0, 'msg': 'Lighttpd 配置信息获取成功！', 'data': get_config()})
    elif action == 'savesettings':
        self.write({'code': 0, 'msg': 'Lighttpd 服务配置保存成功！', 'data': set_config(self)})
    return


def get_config():
    return dict()


def set_config(self):
    return dict()
