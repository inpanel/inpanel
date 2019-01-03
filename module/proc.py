# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for process management."""

import os


def get_process_list():

    process = {}
    l = []
    for subdir in os.listdir('/proc'):
        if subdir.isdigit():
            p = {'pid': subdir, 'name': get_process_name(subdir)}
            l.append(p)
    process['process'] = l
    process['total'] = len(l)
    return process


def get_process_name(pid):
    if not pid:
        return False
    name = ''
    comm = '/proc/%s/comm' % pid
    with open(comm, 'r') as f:
        line = f.readline()
        name = line.strip()
    if not name:
        sched = '/proc/%s/sched' % pid
        with open(sched, 'r') as f:
            line = f.readline()
            name = line.split()[0]
    if not name:
        status = '/proc/%s/status' % pid
        with open(status, 'r') as f:
            line = f.readline()
            name = line.split()[1]
    if not name:
        stat = '/proc/%s/stat' % pid
        with open(stat, 'r') as f:
            # name = line.strip()
            # name = line.replace('(','').replace(')','')
            line = f.readline()
            line = line.split()[1]
            if line[0] == '(':
                line = line[1:]
            if line[-1] == ')':
                line = line[:-1]
            name = line
    return name


# if __name__ == '__main__':
#     pids = process_list()
#     print(pids)
#     print('Total: {0}'.format(len(pids)))
