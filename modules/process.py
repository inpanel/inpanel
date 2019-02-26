# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for process Management.'''

import os
import platform

try:
    from commands import getstatusoutput
except:
    from subprocess import getstatusoutput

os_type = platform.system()


def get_list():
    '''get process list'''
    res = []
    if os_type == 'Linux':
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                res.append(get_base(pid))
    elif os_type == 'Darwin':
        pass
    elif os_type == 'Windows':
        pass
    return res


def get_name(pid):
    if not pid:
        return False
    name = None
    if os_type == 'Linux':
        comm = '/proc/%s/comm' % pid
        if os.path.exists(comm):
            with open(comm, 'r') as f:
                line = f.readline()
                name = line.strip()
        if not name:
            status = '/proc/%s/status' % pid
            if os.path.exists(status):
                with open(status, 'r') as f:
                    line = f.readline()
                    name = line.split()[1]
        if not name:
            stat = '/proc/%s/stat' % pid
            if os.path.exists(stat):
                with open(stat, 'r') as f:
                    line = f.readline()
                    line = line.split()[1]
                    if line[0] == '(':
                        line = line[1:]
                    if line[-1] == ')':
                        line = line[:-1]
                    name = line
    elif os_type == 'Darwin':
        pass
    elif os_type == 'Windows':
        pass
    return name


def kill_process(name):
    '''kill process by name'''
    if not name:
        return
    pids = get_pids(name)
    # print('pid', pids)
    if pids:
        return kill_pids(pids)
    else:
        return False


def kill_pids(pids):
    '''kill process by pids'''
    if not pids:
        return
    if isinstance(pids, list):
        pids = ' '.join(pids)  # to string
    if os_type in ('Linux', 'Darwin'):
        s_cmd = u'/bin/kill -9 %s' % pids
        status, result = getstatusoutput(s_cmd)
        return status == 0
    else:
        return False


def get_pids(name):
    '''get pids of a process'''
    if not name:
        return
    if os_type in ('Linux', 'Darwin'):
        s_cmd = u"/bin/ps auxww | grep %s | grep -v grep | awk '{print $2}'" % name
        status, result = getstatusoutput(s_cmd)
        if status == 0 and result:
            return ' '.join(result.split()).split(' ')  # list
        else:
            return []
    else:
        return []


def get_cmdline(pid):
    if not pid:
        return
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/cmdline' % pid):
            with open('/proc/%s/cmdline' % pid, 'r') as f:
                line = f.readline()
                return line.strip()
        else:
            return ''


def get_base(pid):
    '''get base info'''
    if not pid:
        return
    res = {
        'Name': '',
        'State': '',
        'Pid': '',
        'PPid': '',
        'FDSize': '',
        'VmPeak': '',
        'VmSize': ''
    }
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/status' % pid):
            f = open('/proc/%s/status' % pid, 'r')
            line = f.readline()
            while line:
                out = line.strip()
                if out.startswith('Name'):
                    res['Name'] = out.split()[1]
                if out.startswith('State'):
                    res['State'] = out.split()[1]
                if out.startswith('Pid'):
                    res['Pid'] = out.split()[1]
                if out.startswith('PPid'):
                    res['PPid'] = out.split()[1]
                if out.startswith('FDSize'):
                    res['FDSize'] = out.split()[1]
                if out.startswith('VmPeak'):
                    res['VmPeak'] = out.split()[1]
                if out.startswith('VmSize'):
                    res['VmSize'] = out.split()[1]
                # print(line),
                line = f.readline()
                if res['Name'] and res['State'] and res['Pid'] and res['PPid'] and res['FDSize'] and res['VmPeak'] and res['VmSize']:
                    break
            f.close()
        return res
    else:
        return res


def get_detail(pid):
    '''get process detail'''
    if not pid:
        return
    return {'Name': 'test', 'Pid': pid}


def get_environ(pid):
    if not pid:
        return
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/environ' % pid):
            with open('/proc/%s/environ' % pid, 'r') as f:
                line = f.readline()
                return line.strip()
        else:
            return ''


def get_status(pid):
    '''return the all status info'''
    if not pid:
        return
    res = {}
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/status' % pid):
            f = open('/proc/%s/status' % pid, 'r')
            line = f.readlines()
            while line:
                out = line.strip()
                if out.startswith('Name'):
                    res['Name'] = out.split()[1]
                if out.startswith('State'):
                    res['State'] = out.split()[1]
                if out.startswith('Pid'):
                    res['Pid'] = out.split()[1]
                if out.startswith('PPid'):
                    res['PPid'] = out.split()[1]
                if out.startswith('FDSize'):
                    res['FDSize'] = out.split()[1]
                if out.startswith('VmPeak'):
                    res['VmPeak'] = out.split()[1]
                if out.startswith('VmSize'):
                    res['VmSize'] = out.split()[1]
            f.close()
        return res
    else:
        return res


if __name__ == '__main__':
    pids = get_list()
    print(pids)
    # print('kill_process', kill_process('sshd'))
    # print('kill_pid00', kill_pids(11587))
    # print(get_pids('php'))
    # get_state(4105)
