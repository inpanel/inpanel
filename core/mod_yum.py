# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for YUM Management'''

import os

import base
import configuration
import mod_file
from yum import yum_reporpms

config_path = '/etc/yum.repos.d'


def get_list():
    '''get repo list'''
    res = []
    if base.kernel_name in ('Linux', 'Darwin'):
        d = os.path.abspath(config_path)
        if not os.path.exists(d) or not os.path.isdir(d):
            return None
        items = sorted(os.listdir(d))
        return items if len(items) > 0 else []
    else:
        return None


def item_exists(repo):
    '''exists'''
    return os.path.exists(os.path.join(config_path, repo))


def get_item(repo):
    '''get repo config'''
    if not repo:
        return None
    repo_file = os.path.join(config_path, repo)
    if os.path.exists(repo_file):
        config = configuration.Config(repo_file)
        return config.get_config()
    return None


def set_item(repo, data):
    '''set repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = os.path.join(config_path, repo)
    if os.path.exists(repo_file):
        config = configuration.Config(repo_file, data)
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
    repo_file = os.path.join(config_path, repo)
    if os.path.exists(repo_file):
        return False
    else:
        config = configuration.Config(repo_file, data)
        return True
        # return config.update()


def del_item(repo):
    '''delete repo file'''
    if not repo:
        return None
    repo_file = os.path.join(config_path, repo)
    return mod_file.delete(repo_file)


def get_repo_release(os_versint, os_name, arch):
    '''install release'''
    cmds = []
    if os_versint == 5:
        if os_name == 'redhat':
            # backup system version info
            cmds.append('cp -f /etc/redhat-release /etc/redhat-release.inpanel')
            cmds.append('cp -f /etc/issue /etc/issue.inpanel')
            cmds.append('rpm -e redhat-release-5Server --nodeps')
    elif os_versint == 7:
        if os_name == 'centos':
            cmds.append('yum install -y centos-release')
    elif os_versint == 8:
        if os_name == 'centos':
            cmds.append('yum install -y centos-release')
    else:
        for rpm in yum_reporpms['base'][os_versint][arch]:
            cmds.append('rpm -U %s' % rpm)

        if os.path.exists('/etc/issue.inpanel'):
            cmds.append('cp -f /etc/issue.inpanel /etc/issue')
        if os.path.exists('/etc/redhat-release.inpanel'):
            cmds.append(
                'cp -f /etc/redhat-release.inpanel /etc/redhat-release')
    return cmds


def get_repo_epel(os_versint, os_name, arch):
    '''install epel'''
    # CentALT and ius depends on epel
    cmds = []

    if os_versint == 7:
        if os_name == 'centos':
            cmds.append('yum install -y epel-release')
    if os_versint == 8:
        if os_name == 'centos':
            cmds.append('yum install -y epel-release')
    else:
        for rpm in yum_reporpms['epel'][os_versint][arch]:
            cmds.append('rpm -U %s' % rpm)

    return cmds


if __name__ == '__main__':
    # import json
    l = get_list()
    print(l)
    i = l[2]
    print(i)
    c = get_item(i)
    print(c)
    # print(json.loads(c))
