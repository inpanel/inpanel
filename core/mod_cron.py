# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Cron Jobs Management."""

from os.path import exists, join
import re


crontab = '/etc/crontab'
cronspool = '/var/spool/cron/'
cfg_map = {
    'SHELL': 'shell',
    'MAILTO': 'mailto',
    'HOME': 'home',
    'PATH': 'path'
}


def load_config():
    try:
        if not exists(crontab):
            return {}
    except OSError:
        return {}

    config = {}
    with open(crontab, 'r', encoding='utf-8') as f:
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
        if not exists(filepath):
            return False
    except OSError:
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
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

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(output)
        return True

    return False


def cron_list(level='normal', user=None):
    '''
    parser Cron config to python object (array)
    return a list of cron jobs
    '''
    if level == 'normal':
        if user is None:
            return None
        spool = join(cronspool, user)
    elif level == 'system':
        spool = crontab

    try:
        if not exists(spool):
            return None
    except OSError:
        return None

    crons = []
    with open(spool, encoding='utf-8') as f:
        i = 0
        for line in f:
            line = line.strip()
            line_user = ''
            if re.findall("^\d|^\*|^\-", line):
                if level == 'normal':
                    text = re.split('\s+', line, 5)
                    command = text[5]
                    line_user = user
                elif level == 'system':
                    # this user's list
                    text = re.split('\s+', line, 6)
                    if user and user != text[5]:
                        continue
                    else:
                        line_user = text[5]
                    command = text[6]
                else:
                    continue
                i += 1
                crons.append({
                    'id': i,
                    'minute': text[0],
                    'hour': text[1],
                    'day': text[2],
                    'month': text[3],
                    'weekday': text[4],
                    'command': command,
                    'user': line_user
                })
    return crons


def cron_add(user, minute, hour, day, month, weekday, command, level):
    '''add normal or system cron
    '''
    if level == 'system':
        if user is None or user == '' or len(user) == 0:
            return False
        spool = crontab
        line = "%s %s %s %s %s %s %s\n" % (minute, hour, day, month, weekday, user, command)
    else:
        user = user or 'root'
        spool = join(cronspool, user)
        line = "%s %s %s %s %s %s\n" % (minute, hour, day, month, weekday, command)

    with open(spool, 'a+', encoding='utf-8') as f:
        f.write(line)
        return True

    return False


def cron_mod(user, id, minute, hour, day, month, weekday, command, level, currlist=''):
    '''modify normal or system cron
    '''
    if user is None or id is None:
        return False
    if level == 'system':
        spool = crontab
        cron_line = "%s %s %s %s %s %s %s\n" % (minute, hour, day, month, weekday, user, command)
    else:
        spool = join(cronspool, user)
        cron_line = "%s %s %s %s %s %s\n" % (minute, hour, day, month, weekday, command)

    with open(spool, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        j += 1
        if re.findall("^\d|^\*|^\-", line):
            if level == 'normal':
                i += 1
            elif level == 'system':
                # if currlist is this user's list
                if currlist and currlist == user:
                    text = re.split('\s+', line, 6)
                    if user == text[5]:
                        i += 1
                else:
                    i += 1
            else:
                continue
            if str(i) == str(id):
                lines[j-1] = cron_line
                break

    with open(spool, 'w+', encoding='utf-8') as f:
        f.writelines(lines)
        return True

    return False


def cron_del(user, id, level, currlist=''):
    if user is None or id is None:
        return False
    spool = crontab if level == 'system' else join(cronspool, user)

    with open(spool, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        j += 1
        if re.findall("^\d|^\*|^\-", line):
            if level == 'normal':
                i += 1
            elif level == 'system':
                if currlist and currlist == user:
                    text = re.split('\s+', line, 6)
                    if user == text[5]:
                        i += 1
                else:
                    i += 1
            else:
                continue
            if str(i) == str(id):
                del lines[j-1]
                break

    with open(spool, 'w+', encoding='utf-8') as f:
        f.writelines(lines)
        return True

    return False


if __name__ == "__main__":
    import json
    crontab = '/Users/douzhenjiang/test/inpanel/test/crontab'
    cronspool = '/Users/douzhenjiang/test/inpanel/test/var_spool_cron'
    # print crontab
    # os.system("top")
    # print loadconfig(crontab, cfg_map)
    # print raw_loadconfig(crontab)
    # print(load_config())
    # print update_config({'shell': 'shelshelshel', 'home': 'homehomehome', 'path':'abc'})
    # print dict((v, k) for k, v in cfg_map.items())

    config = cron_list(level='system', user='root')
    # config = cron_list(level='system', user='apache')
    # config = cron_list(level='system')
    print(json.dumps(config))
    # print(cron_add('root', '*','*','*','*','*', 'command'))
