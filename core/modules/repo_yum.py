# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for YUM Management'''

from os import listdir
from os.path import abspath, exists, isdir, join
from platform import system
from core.modules.configuration import Config

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

def get_item(repo):
    '''get repo config'''
    if not repo:
        return None
    repo_file = join(config_path, repo)
    if exists(repo_file):
        config = Config(repo_file)
        return config.get_config()
    return None

if __name__ == '__main__':
    import json
    l = get_list()
    print(l)
    i = l[2]
    print(i)
    c = get_item(i)
    print(c)
    # print(json.loads(c))
