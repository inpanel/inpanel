# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for YUM Management'''

from json import loads
from os import listdir
from os.path import abspath, exists, isdir, join
from platform import system

from core.modules.configuration import Config
from core.web import RequestHandler

os_type = system()
config_path = '/etc/yum.repos.d'
# print(os_type)

class WebRequestRepoYUM(RequestHandler):
    """Handler for YUM Request.
    """
    def get(self, sec, repo=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO 状态不允许设置 YUM ！'})
            return
        if sec == 'list':
            items = get_list()
            if items is None:
                self.write({'code': -1, 'msg': u'获取配置失败！'})
            else:
                self.write({'code': 0, 'msg': '', 'data': items})
        elif sec == 'item':
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo == None:
                self.write({'code': -1, 'msg': u'配置文件不能为空！'})
                return
            data = get_item(repo)
            if data is None:
                self.write({'code': -1, 'msg': u'配置文件不存在！'})
            else:
                self.write({'code': 0, 'msg': '', 'data': data})
        else:
            self.write({'code': -1, 'msg': u'未定义的操作！'})

    def post(self, sec, repo=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO 状态不允许设置 YUM ！'})
            return

        if sec == 'edit':
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo is None:
                self.write({'code': -1, 'msg': u'配置文件不能为空！'})
                return
            if not exists(join(config_path, repo)):
                self.write({'code': -1, 'msg': u'配置文件不存在！'})
                return
            data = self.get_argument('data', '')
            if data == '':
                self.write({'code': -1, 'msg': u'配置不能为空！'})
                return
            if set_item(repo, data) is True:
                self.write({'code': 0, 'msg': u'配置修改成功！'})
            else:
                self.write({'code': -1, 'msg': u'配置修改失败！'})
        elif sec == 'add':
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo is None:
                self.write({'code': -1, 'msg': u'配置文件不能为空！'})
                return
            if exists(join(config_path, repo)):
                self.write({'code': -1, 'msg': u'配置文件已存在！'})
                return
            data = self.get_argument('data', '')
            if data == '':
                self.write({'code': -1, 'msg': u'配置不能为空！'})
                return
            if add_item(repo, data) is True:
                self.write({'code': 0, 'msg': u'配置添加成功！'})
            else:
                self.write({'code': -1, 'msg': u'配置修改失败！'})
        else:
            self.write({'code': -1, 'msg': u'未定义的操作！'})


def get_list():
    '''get repo list'''
    res = []
    if os_type in ('Linux', 'Darwin'):
        d = abspath(config_path)
        if not exists(d) or not isdir(d):
            return None
        items = sorted(listdir(d))
        return items if len(items) > 0 else []
    else:
        return None

def get_item(repo):
    '''get repo config'''
    if not repo:
        return None
    repo_file = join(config_path, repo)
    if exists(repo_file):
        config = Config(repo_file)
        return config.get_config()
    return None

def set_item(repo, data):
    '''set repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = join(config_path, repo)
    if exists(repo_file):
        data = loads(data) or {}
        config = Config(repo_file, data)
        return True
        # return config.update()
    else:
        return False

def add_item(repo, data):
    '''add repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = join(config_path, repo)
    if exists(repo_file):
        return False
    else:
        data = loads(data) or {}
        config = Config(repo_file, data)
        return True
        # return config.update()

if __name__ == '__main__':
    import json
    l = get_list()
    print(l)
    i = l[2]
    print(i)
    c = get_item(i)
    print(c)
    # print(json.loads(c))
