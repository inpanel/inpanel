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

from configuration import Config

from yum import yum_reporpms

from files import delete

os_type = system()
config_path = '/etc/yum.repos.d'
# print(os_type)


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


def item_exists(repo):
    '''exists'''
    return exists(join(config_path, repo))


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

        if exists('/etc/issue.inpanel'):
            cmds.append('cp -f /etc/issue.inpanel /etc/issue')
        if exists('/etc/redhat-release.inpanel'):
            cmds.append('cp -f /etc/redhat-release.inpanel /etc/redhat-release')
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
    import json
    l = get_list()
    print(l)
    i = l[2]
    print(i)
    c = get_item(i)
    print(c)
    # print(json.loads(c))
