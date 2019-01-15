# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for SSL/TLS management."""


def get_keys_list():
    res = None
    res = [{
        'domain': 'baokan.pub',
        'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
        'size': 2048
    }, {
        'domain': 'zhoubao.pub',
        'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
        'size': 2048
    }]
    return res


def get_crts_list():
    res = None
    res = [{
        'domain': 'baokan.pub',
        'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
        'size': 2048
    }, {
        'domain': 'zhoubao.pub',
        'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
        'size': 2048
    }]
    return res


def get_csrs_list():
    res = None
    res = [{
        'domain': 'baokan.pub',
        'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
        'size': 2048
    }, {
        'domain': 'zhoubao.pub',
        'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
        'size': 2048
    }]
    return res


def get_host_list():
    res = None
    res = [{
        'domain': 'baokan.pub',
        'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
        'size': 2048
    }, {
        'domain': 'zhoubao.pub',
        'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
        'size': 2048
    }]
    return res


def web_response(self):
    action = self.get_argument('action', '')
    if action == 'keys_list':
        res = [
            {
                'domain': 'baokan.pub',
                'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
                'size': 2048
            }, {
                'domain': 'zhoubao.pub',
                'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
                'size': 2048
            }
        ]
        self.write({'code': 0, 'msg': 'SSL 配置信息获取成功！', 'data': res})
    elif action == 'savesettings':
        self.write({'code': 0, 'msg': 'ProFTPD 服务配置保存成功！',
                    'data': set_config(self)})
    return


def get_config():
    return dict()


def set_config(self):
    return dict()
