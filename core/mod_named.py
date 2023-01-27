# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for named configuration management."""


def web_handler(context):
    action = context.get_argument('action', '')
    if action == 'getsettings':
        context.write({'code': 0, 'msg': 'named 配置信息获取成功！', 'data': get_config()})
    elif action == 'savesettings':
        context.write({'code': 0, 'msg': 'named 服务配置保存成功！', 'data': set_config(context)})
    return


def get_config():
    return dict()


def set_config():
    return dict()
