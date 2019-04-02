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
    res = []
    if os_type in ('Linux', 'Darwin'):
        s_cmd = u"/bin/ps auxww | grep %s | grep -v grep | awk '{print $2}'" % name
        status, result = getstatusoutput(s_cmd)
        if status == 0 and result:
            res = ' '.join(result.split()).split(' ')  # list
    return res


def get_cmdline(pid):
    '''parse cmdline'''
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
        'name': '',
        'state': '',
        'pid': '',
        'ppid': '',
        'fdsize': '',
        'vmpeak': '',
        'vmsize': ''
    }
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/status' % pid):
            f = open('/proc/%s/status' % pid, 'r')
            line = f.readline()
            while line:
                out = line.strip()
                if out.startswith('Name'):
                    res['name'] = out.split()[1]
                if out.startswith('State'):
                    res['state'] = out.split()[1]
                if out.startswith('Pid'):
                    res['pid'] = out.split()[1]
                if out.startswith('PPid'):
                    res['ppid'] = out.split()[1]
                if out.startswith('FDSize'):
                    res['fdsize'] = out.split()[1]
                if out.startswith('VmPeak'):
                    res['vmpeak'] = out.split()[1]
                if out.startswith('VmSize'):
                    res['vmsize'] = out.split()[1]
                # print(line),
                line = f.readline()
                if res['name'] and res['state'] and res['pid'] and res['ppid'] and res['fdsize'] and res['vmpeak'] and res['vmsize']:
                    break
            f.close()
    return res


def get_file(pid):
    '''get process file'''
    if not pid:
        return
    return {'name': 'test', 'pid': pid}


def get_environ(pid):
    '''parse environ'''
    if not pid:
        return
    res = ''
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/environ' % pid):
            with open('/proc/%s/environ' % pid, 'r') as f:
                line = f.readline()
                res = line.strip()
    return res


def get_status(pid):
    '''parse status'''
    if not pid:
        return
    res = {}
    if os_type == 'Linux':
        sts = '/proc/%s/status' % pid
        # sts = '/Users/douzhenjiang/test/inpanel/test/proc_status.txt'
        # if os_type in ('Linux', 'Darwin'):
        if os.path.exists(sts):
            f = open(sts, 'r')
            line = f.readline()
            while line:
                out = line.strip()
                # print('aaaaaaasplit', out.split())
                tmp = out.split()
                if out.startswith('Uid') or out.startswith('Gid') or out.startswith('Vm'):
                    res[tmp[0].split(':')[0].lower()] = tmp[1:]
                elif out.startswith('State'):
                    res[tmp[0].split(':')[0].lower()] = [tmp[1], tmp[2][1:-1].lower()]
                else:
                    res[tmp[0].split(':')[0].lower()] = tmp[1] if len(tmp) > 1 else ''
                line = f.readline()
            f.close()
    return res


def get_io(pid):
    '''parse io'''
    if not pid:
        return
    res = {}
    if os_type == 'Linux':
        sts = '/proc/%s/io' % pid
        # sts = '/Users/douzhenjiang/test/inpanel/test/proc_io.txt'
        # if os_type in ('Linux', 'Darwin'):
        if os.path.exists(sts):
            f = open(sts, 'r')
            line = f.readline()
            while line:
                out = line.strip()
                res[out.split()[0].split(':')[0].lower()] = out.split()[1]
                line = f.readline()
            f.close()
    return res


def get_memory(pid):
    '''get memory, parse statm'''
    if not pid:
        return
    res = ''
    if os_type == 'Linux':
        if os.path.exists('/proc/%s/statm' % pid):
            with open('/proc/%s/statm' % pid, 'r') as f:
                line = f.readline()
                line = line.strip()
                res = line.split()
    return res


def get_info(pid):
    '''parse stat'''
    if not pid:
        return
    res = {}
    if os_type == 'Linux':
        sts = '/proc/%s/stat' % pid
        # sts = '/Users/douzhenjiang/test/inpanel/test/proc_stat.txt'
        # if os_type in ('Linux', 'Darwin'):
        if os.path.exists(sts):
            f = open(sts, 'r')
            line = f.readline()
            while line:
                out = line.strip()
                res = out.split()
                line = f.readline()
            f.close()
    return res


def get_network(pid):
    '''parse network'''
    if not pid:
        return
    res = {}
    if os_type == 'Linux':
        sts = '/proc/%s/stat' % pid
        # sts = '/Users/douzhenjiang/test/inpanel/test/proc_stat.txt'
        # if os_type in ('Linux', 'Darwin'):
        if os.path.exists(sts):
            f = open(sts, 'r')
            line = f.readline()
            while line:
                out = line.strip()
                res = out.split()
                line = f.readline()
            f.close()
    return res


if __name__ == '__main__':
    # pids = get_list()
    # print(pids)
    # print('kill_process', kill_process('sshd'))
    # print('kill_pid00', kill_pids(11587))
    # print(get_pids('php'))
    print(get_status(1))
    # print(get_base(2345))
