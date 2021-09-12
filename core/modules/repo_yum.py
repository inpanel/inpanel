# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for YUM Management'''

from os import listdir
from os.path import abspath, exists, isdir, join
from platform import system

from core.modules.configuration import Config
from tornado.web import RequestHandler

from yum import yum_reporpms

from .files import delete

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

        if sec in ('edit', 'add'):
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo is None:
                self.write({'code': -1, 'msg': u'配置文件不能为空！'})
                return
            serverid = self.get_argument('serverid', '')
            if serverid == '':
                self.write({'code': -1, 'msg': u'仓库标识ID不能为空！'})
                return
            name = self.get_argument('name', '')
            if name == '':
                self.write({'code': -1, 'msg': u'仓库名称不能为空！'})
                return
            baseurl = self.get_argument('baseurl', '')
            if baseurl == '':
                self.write({'code': -1, 'msg': u'仓库路径不能为空！'})
                return
            enabled = self.get_argument('enabled', True)
            gpgcheck = self.get_argument('gpgcheck', False)
            data = {
                serverid: {
                    'name': name,
                    'enabled': 0 if not enabled else 1,
                    'baseurl': baseurl,
                    'gpgcheck': 0 if not gpgcheck else 1,
                    'gpgkey': ''
                }
            }
            if sec == 'edit':
                if not exists(join(config_path, repo)):
                    self.write({'code': -1, 'msg': u'配置文件不存在！'})
                    return
                if set_item(repo, data) is True:
                    self.write({'code': 0, 'msg': u'配置修改成功！'})
                else:
                    self.write({'code': -1, 'msg': u'配置修改失败！'})
            else:
                if exists(join(config_path, repo)):
                    self.write({'code': -1, 'msg': u'配置文件已存在！'})
                    return
                if add_item(repo, data) is True:
                    self.write({'code': 0, 'msg': u'配置添加成功！'})
                else:
                    self.write({'code': -1, 'msg': u'配置修改失败！'})
        elif sec == 'del':
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo is None:
                self.write({'code': -1, 'msg': u'配置文件不能为空！'})
                return
            if not exists(join(config_path, repo)):
                self.write({'code': -1, 'msg': u'配置文件不存在！'})
                return
            if del_item(repo) is True:
                self.write({'code': 0, 'msg': u'配置文件已移入回收站！'})
            else:
                self.write({'code': -1, 'msg': u'删除失败！'})
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
        config = Config(repo_file, data)
        return True
        # return config.update()


def del_item(repo):
    '''delete repo file'''
    if not repo:
        return None
    repo_file = join(config_path, repo)
    return delete(repo_file)


def get_repo_release(dist_versint, dist_name, arch):
    '''install release'''
    cmds = []
    if dist_versint == 5:
        if dist_name == 'redhat':
            # backup system version info
            cmds.append('cp -f /etc/redhat-release /etc/redhat-release.inpanel')
            cmds.append('cp -f /etc/issue /etc/issue.inpanel')
            cmds.append('rpm -e redhat-release-5Server --nodeps')
    elif dist_versint == 7:
        if dist_name == 'centos':
            cmds.append('yum install -y centos-release')
    elif dist_versint == 8:
        if dist_name == 'centos':
            cmds.append('yum install -y centos-release')
    else:
        for rpm in yum_reporpms['base'][dist_versint][arch]:
            cmds.append('rpm -U %s' % rpm)

        if exists('/etc/issue.inpanel'):
            cmds.append('cp -f /etc/issue.inpanel /etc/issue')
        if exists('/etc/redhat-release.inpanel'):
            cmds.append('cp -f /etc/redhat-release.inpanel /etc/redhat-release')
    return cmds


def get_repo_epel(dist_versint, dist_name, arch):
    '''install epel'''
    # CentALT and ius depends on epel
    cmds = []

    if dist_versint == 7:
        if dist_name == 'centos':
            cmds.append('yum install -y epel-release')
    if dist_versint == 8:
        if dist_name == 'centos':
            cmds.append('yum install -y epel-release')
    else:
        for rpm in yum_reporpms['epel'][dist_versint][arch]:
            cmds.append('rpm -U %s' % rpm)

    return cmds


if __name__ == '__main__':
    import json
    l = get_list()
    print(l)
    i = l[2]
    print(i)
    c = get_item(i)
    print(c)
    # print(json.loads(c))
