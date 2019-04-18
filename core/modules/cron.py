# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Cron Jobs Management."""

import os
import re
import shlex
import subprocess
import getpass
import json

# from configloader import (loadconfig, raw_loadconfig, raw_saveconfig, readconfig, saveconfig, writeconfig)

cfgdir = '/etc/cron.d/'
crontab = '/etc/crontab'
user_dir = '/var/spool/cron/'
# user_dir = '/Users/douzhenjiang/Projects/inpanel/test/var_spool_cron'


cfg_map = {
    'SHELL': 'shell',
    'MAILTO': 'mailto',
    'HOME': 'home',
    'PATH': 'path'
}


def load_config():
    try:
        if not os.path.exists(crontab):
            return {}
    except OSError:
        return {}

    config = {}
    with open(crontab, 'r') as f:
        lines = f.readlines()

    while len(lines) > 0:
        line = lines.pop(0)
        out = line.strip()
        if not out or out.startswith('#'):
            continue

        k = out.strip().split('=')[0]
        if k and k in cfg_map:
            config[cfg_map[k]] = out.split('=')[1]

    return config


def update_config(configs):
    cmap_reverse = dict((v, k) for k, v in cfg_map.items())
    new_config = {}
    for k, v in configs.items():
        if k in cmap_reverse:
            new_config[cmap_reverse[k]] = v
    return save_config(crontab, new_config)


def save_config(filepath, config):
    try:
        if not os.path.exists(filepath):
            return False
    except OSError:
        return False

    with open(filepath, 'r') as f:
        lines = f.readlines()

    output = []
    while len(lines) > 0:
        line = lines.pop(0)
        out = line.strip()
        if not out or out.startswith('#'):
            output.append('%s' % (line))
            continue

        k = out.split('=')[0]
        if k:
            if k in config:
                output.append('%s=%s\n' % (k, config[k]))
            else:
                output.append('%s' % (line))

    with open(filepath, 'w') as f:
        f.writelines(output)
        return True

    return False


def cron_list(user=None):
    # return a test list
    user = user or 'root'
    return _parse_cron(os.path.join(user_dir, user), 'other', user=user)


def _parse_cron(filename, option, user=None):
    '''parser Cron config to python object (array)
    '''
    try:
        if not os.path.exists(filename):
            return None
    except OSError:
        return None

    cronlist = []
    with open(filename) as f:
        i = 0
        for line in f:
            line = line.strip()
            if re.findall("^\d|^\*|^\-", line):
                if option == 'other':
                    text = re.split('\s+', line, 5)
                    command = text[5]
                    # user = None
                else:
                    text = re.split('\s+', line, 6)
                    user = text[5]
                    command = text[6]
                i = i + 1
                cronlist.append({
                    'id': i,
                    'minute': text[0],
                    'hour': text[1],
                    'day': text[2],
                    'month': text[3],
                    'weekday': text[4],
                    'command': command,
                    'user': user
                })
    return cronlist


def cron_add(user, minute, hour, day, month, weekday, command):
    line = "%s %s %s %s %s %s\n" % (minute, hour, day, month, weekday, command)
    user = user or 'root'
    with open(os.path.join(user_dir, user), 'a+') as f:
        f.write(line)
        return True


def cron_mod(user, id, minute, hour, day, month, weekday, command):
    cron_line = "%s %s %s %s %s %s\n" % (minute, hour, day, month, weekday, command)
    with open(os.path.join(user_dir, user), 'r') as f:
        lines = f.readlines()

    i = 0
    j = 0
    for line in lines:
        j = j+1
        if re.findall("^\d|^\*|^\-", line):
            i = i+1
            if str(i) == str(id):
                lines[j-1] = cron_line
                break

    with open(os.path.join(user_dir, user), 'w+') as f:
        f.writelines(lines)

    return True


def cron_del(user, id):
    with open(os.path.join(user_dir, user), 'r') as f:
        lines = f.readlines()

    i = 0
    j = 0
    for line in lines:
        j = j+1
        if re.findall("^\d|^\*|^\-", line):
            i = i+1
            if str(i) == str(id):
                del lines[j-1]
                break

    with open(os.path.join(user_dir, user), 'w+') as f:
        f.writelines(lines)

    return True


def listCron():
    p = subprocess.Popen(['crontab', '-l'],
                         #  stdout=subprocess.PIPE,
                         #  stderr=subprocess.PIPE,
                         close_fds=True)
    # p.stdout.read()
    # p.stderr.read()
    return p.wait() == 0


if __name__ == "__main__":
    # print crontab
    # print listCron()
    # os.system("top")
    # print loadconfig(crontab, cfg_map)
    # print raw_loadconfig(crontab)
    print(load_config())
    # print update_config({'shell': 'shelshelshel', 'home': 'homehomehome', 'path':'abc'})
    # print dict((v, k) for k, v in cfg_map.items())
    config = cron_list('root')
    print(json.dumps(config))
    # print(cron_add('root', '*','*','*','*','*', 'command'))
