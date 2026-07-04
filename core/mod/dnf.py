# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for DNF Repository Management'''

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import base
from . import config
from . import file
from dnf import dnf_reporpms

config_path = '/etc/yum.repos.d'


def get_list():
    '''get repo list'''
    res = []
    if base.kernel_name in ('Linux'):
        d = str(Path(config_path))
        if not Path(d).exists() or not Path(d).is_dir():
            return None
        items = sorted(os.listdir(d))
        return items if len(items) > 0 else []
    elif base.kernel_name in ('Darwin'):
        return None
    else:
        return None


def item_exists(repo):
    '''exists'''
    return Path(str(Path(config_path) / repo)).exists()


def get_item(repo):
    '''get repo config'''
    if not repo:
        return None
    repo_file = str(Path(config_path) / repo)
    if Path(repo_file).exists():
        _config = config.Config(repo_file)
        return _config.get_config()
    return None


def set_item(repo, data):
    '''set repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = str(Path(config_path) / repo)
    if Path(repo_file).exists():
        _config = config.Config(repo_file, data)
        return True
    else:
        return False


def add_item(repo, data):
    '''add repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = str(Path(config_path) / repo)
    if Path(repo_file).exists():
        return False
    else:
        _config = config.Config(repo_file, data)
        return True


def del_item(repo):
    '''delete repo file'''
    if not repo:
        return None
    repo_file = str(Path(config_path) / repo)
    return file.delete(repo_file)


def get_repo_release(os_versint, os_name, arch):
    '''install release'''
    cmds = []
    if os_versint >= 8:
        if os_name in ('centos', 'almalinux', 'rocky', 'rhel', 'fedora'):
            cmds.append('dnf install -y %s-release' % os_name)
    else:
        for rpm in dnf_reporpms['base'][os_versint][arch]:
            cmds.append('rpm -U %s' % rpm)
    return cmds


def get_repo_epel(os_versint, os_name, arch):
    '''install epel'''
    cmds = []
    if os_versint >= 8:
        cmds.append('dnf install -y epel-release')
    else:
        for rpm in dnf_reporpms['epel'][os_versint][arch]:
            cmds.append('rpm -U %s' % rpm)
    return cmds


def get_repo_powertools(os_versint, os_name, arch):
    '''install powertools/crb'''
    cmds = []
    if os_versint == 8:
        cmds.append('dnf install -y dnf-plugins-core')
        cmds.append('dnf config-manager --set-enabled powertools')
    elif os_versint >= 9:
        cmds.append('dnf install -y dnf-plugins-core')
        cmds.append('dnf config-manager --set-enabled crb')
    return cmds


def get_repo_remi(os_versint, os_name, arch):
    '''install remi repository'''
    cmds = []
    if os_versint >= 8:
        cmds.append('dnf install -y https://rpms.remirepo.net/enterprise/remi-release-%d.rpm' % os_versint)
    return cmds


def web_handler(context):
    '''Handle web requests for DNF repository management'''
    action = context.get('action', '')
    repo = context.get('repo', '')
    
    if action == 'list':
        items = get_list()
        if items is None:
            return {'code': -1, 'msg': '获取配置失败！'}
        else:
            return {'code': 0, 'msg': '', 'data': items}
    
    elif action == 'item':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        data = get_item(repo)
        if data is None:
            return {'code': -1, 'msg': '配置文件不存在！'}
        else:
            return {'code': 0, 'msg': '', 'data': data}
    
    elif action == 'add':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        serverid = context.get('serverid', '')
        if not serverid:
            return {'code': -1, 'msg': '仓库标识ID不能为空！'}
        name = context.get('name', '')
        if not name:
            return {'code': -1, 'msg': '仓库名称不能为空！'}
        baseurl = context.get('baseurl', '')
        if not baseurl:
            return {'code': -1, 'msg': '仓库路径不能为空！'}
        
        enabled = context.get('enabled', True)
        gpgcheck = context.get('gpgcheck', False)
        
        data = {
            serverid: {
                'name': name,
                'enabled': 0 if not enabled else 1,
                'baseurl': baseurl,
                'gpgcheck': 0 if not gpgcheck else 1,
                'gpgkey': ''
            }
        }
        
        if item_exists(repo):
            return {'code': -1, 'msg': '配置文件已存在！'}
        if add_item(repo, data) is True:
            return {'code': 0, 'msg': '配置添加成功！'}
        else:
            return {'code': -1, 'msg': '配置添加失败！'}
    
    elif action == 'edit':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        serverid = context.get('serverid', '')
        if not serverid:
            return {'code': -1, 'msg': '仓库标识ID不能为空！'}
        name = context.get('name', '')
        if not name:
            return {'code': -1, 'msg': '仓库名称不能为空！'}
        baseurl = context.get('baseurl', '')
        if not baseurl:
            return {'code': -1, 'msg': '仓库路径不能为空！'}
        
        enabled = context.get('enabled', True)
        gpgcheck = context.get('gpgcheck', False)
        
        data = {
            serverid: {
                'name': name,
                'enabled': 0 if not enabled else 1,
                'baseurl': baseurl,
                'gpgcheck': 0 if not gpgcheck else 1,
                'gpgkey': ''
            }
        }
        
        if not item_exists(repo):
            return {'code': -1, 'msg': '配置文件不存在！'}
        if set_item(repo, data) is True:
            return {'code': 0, 'msg': '配置修改成功！'}
        else:
            return {'code': -1, 'msg': '配置修改失败！'}
    
    elif action == 'del':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        if not item_exists(repo):
            return {'code': -1, 'msg': '配置文件不存在！'}
        if del_item(repo) is True:
            return {'code': 0, 'msg': '配置文件已移入回收站！'}
        else:
            return {'code': -1, 'msg': '删除失败！'}
    
    else:
        return {'code': -1, 'msg': '未定义的操作！'}


if __name__ == '__main__':
    l = get_list()
    print(l)
    if l:
        i = l[0]
        print(i)
        c = get_item(i)
        print(c)