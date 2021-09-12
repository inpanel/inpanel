# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Pure-FTPd configuration management."""


def web_response(self):
    action = self.get_argument('action', '')
    if action == 'getsettings':
        self.write({'code': 0, 'msg': 'Pure-FTPd 配置信息获取成功！', 'data': get_config()})
    elif action == 'savesettings':
        self.write({'code': 0, 'msg': 'Pure-FTPd 服务配置保存成功！', 'data': set_config(self)})
    return


def get_config():
    return dict()


def set_config(self):
    return dict()
