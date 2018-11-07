#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Package for reading and writing Apache Vhost configuration.
"""

import os.path
import re
import string
import sys


DIRECTIVES = {
    'Directory': '',
    'Files': '',
    'Limit': '',
    'Location': '',
    'VirtualHost': ''
}

OPTIONS = {
    'ServerAdmin': 'admin@localhost',
    'ServerName': 'www',
    'DocumentRoot': '/var/www',
    'Indexs': '',
    'Options': '',
    'ServerAlias': '',
    'Location': '',
    'SuexecUserGroup': '',
}


DIRECTORY = {
    'Options': 'Indexes FollowSymLinks MultiViews',
    'AllowOverride': 'None',
    'Order': 'allow,deny',
    'Allow': 'from all',
}


def load_vhost_conf(conf=''):
    '''parser VirtualHost config to python dict
    '''
    try:
        if not conf:
            sys.exit('need conf file')
        if not os.path.isfile(conf):
            sys.exit('Unknown file %s' % conf)
    except OSError:
        pass

    with open(conf, 'r') as f:
        lines = f.readlines()
        data = filter(lambda i: re.search('^((?!#).)*$', i), lines)

    ID = 0
    enable = False
    virtualHosts = []
    vhost = []
    result = {}
    # ID_D = 0
    enable_d = False
    v_dirs = []
    result_d = {}
    directorys = {} # 附加信息
    match_start = re.compile(r'<VirtualHost(\s+)(\S+)>')
    match_end = re.compile(r'</VirtualHost>')
    match_start_d = re.compile(r'<Directory(\s+)(\S+)>')
    match_end_d = re.compile(r'</Directory>')
    while len(data) > 0:
        out = data.pop(0)

        # start of VirtualHost
        match = match_start.search(out)
        if match:  # if '<VirtualHost' in out:
            # ID_D = 0
            v_dirs = []
            name_port = match.groups()[1].strip(string.punctuation)
            ip, port = name_port.split(':')
            vhost.append(ip)
            vhost.append(port)
            enable = True
            enable_d = False
            continue

        # start of Directory
        match_d = match_start_d.search(out)
        if match_d:
            v_dirs = []
            result_d[ID] = {}
            path = match_d.groups()[1].strip()
            v_dirs.append(path)
            enable_d = True
            continue

        # end of Directory
        if match_end_d.search(out): # if '</Directory>' in out:
            result_d[ID] = v_dirs
            # ID_D += 1
            enable_d = False
            # v_dirs = []
            continue

        # merge of Directory
        if enable_d:
            print('merge D', ID, out)
            v_dirs.append(out)
            # print('Directory', v_dirs)
            continue

        # end of VirtualHost
        if match_end.search(out):  # if '</VirtualHost>' in out:
            # v_dirs = []
            # add directory to vhost
            # directorys[ID] = _append_directory(result_d[ID])
            print('end of VirtualHost', result_d[ID])
            # ID_D = 0 # reset Directory
            enable_d = False

            result[ID] = vhost
            ID += 1
            enable = False
            vhost = []
            continue

        if enable:
            vhost.append(out)
            continue

    for i in result:
        server = {
            'ip': result[i][0],  # IP
            'port': result[i][1],  # port
            # 'Directory': directorys[i]
        }
        for line in result[i]:
            for i in OPTIONS:
                if i in line:
                    if i in ['ServerAlias', 'DirectoryIndex']:
                        server[i] = ' '.join(str(n) for n in line.split()[1:])
                    else:
                        server[i] = line.split()[1].strip(string.punctuation)
                    continue
        virtualHosts.append(server)
    # print(directorys)
    return virtualHosts


def _append_directory(res):
    print('aaa', res)
    directorys = []
    for i in res:
        directory = {
            'path': res[i][0]
        }
        for line in res[i]:
            for i in DIRECTORY:
                if i in line:
                    if i in ['Order']:
                        directory[i] = ','.join(str(n) for n in line.split()[1:])
                    else:
                        directory[i] = line.split()[1].strip(string.punctuation)
                    continue
        directorys.append(directory)

    return directorys

def _load_directory(data):
    ID = 0
    enable = False
    directorys = []
    vhost = []
    result = {}
    match_start = re.compile(r'<Directory(\s+)(\S+)>')
    match_end = re.compile(r'</Directory>')
    while len(data) > 0:
        out = data.pop(0)

        # start of Directory in VirtualHost
        match = match_start.search(out)
        if match:
            path = match.groups()[1].strip()
            print(path)
            vhost.append(path)
            enable = True
            continue

        if match_end.search(out):
            result[ID] = vhost
            ID += 1
            enable = False
            vhost = []
            continue

        if enable:
            vhost.append(out)
            continue

    for i in result:
        directory = {
            'path': result[i][0],  # directory path
        }
        for line in result[i]:
            for i in DIRECTORY:
                if i in line:
                    if i in ['Order']:
                        directory[i] = ','.join(str(n)
                                                for n in line.split()[1:])
                    else:
                        directory[i] = line.split()[1].strip(
                            string.punctuation)
                    continue
        # print(result)

        directorys.append(directory)

    return directorys


if __name__ == '__main__':
    aaa = '/Users/douzhenjiang/Projects/intranet-panel/aaa.com.conf'
    print load_vhost_conf(aaa)
    # load_vhost_conf(aaa)

    # for key in OPTIONS:
    #     # print(key)
    #     if key in ['ServerName', 'DocumentRoot']:
    #         print key

    # _load_directory(aaa)
    # print _load_directory(aaa)
