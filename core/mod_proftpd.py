# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for ProFTPD configuration management."""


def web_handler(self):
    action = self.get_argument('action', '')
    if action == 'getsettings':
        self.write({'code': 0, 'msg': 'ProFTPD 配置信息获取成功！', 'data': get_config()})
    elif action == 'savesettings':
        self.write({'code': 0, 'msg': 'ProFTPD 服务配置保存成功！', 'data': set_config(self)})
    return


def get_config():
    return dict()


def set_config(self):
    return dict()
