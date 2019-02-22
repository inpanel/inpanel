# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for process management."""

import os
import platform
from commands import getstatusoutput as getso


def get_process_list():

    p = []
    os_type = platform.system()
    if os_type == 'Linux':
        for subdir in os.listdir('/proc'):
            if subdir.isdigit():
                pn = get_process_name(subdir)
                if pn:
                    p.append({'pid': int(subdir), 'name': pn})
    elif os_type == 'Darwin':
        pass
    elif os_type == 'Windows':
        pass
    return {'process': p, 'total': len(p)}


def get_process_name(pid):
    if not pid:
        return False
    name = None
    os_type = platform.system()
    if os_type == 'Linux':
        comm = '/proc/%s/comm' % pid
        if os.path.exists(comm):
            with open(comm, 'r') as f:
                line = f.readline()
                name = line.strip()
        if not name:
            sched = '/proc/%s/sched' % pid
            if os.path.exists(sched):
                with open(sched, 'r') as f:
                    line = f.readline()
                    name = line.split()[0]
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
                    # name = line.strip()
                    # name = line.replace('(','').replace(')','')
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
        return None
    pids = get_pids(name)
    print('pid', pids)
    if pids:
        return kill_pids(pids)
    else:
        return False


def kill_pids(pids):
    '''kill process by pids'''
    if not pids:
        return None
    if isinstance(pids, list):
        pids = ' '.join(pids)  # to string
    os_type = platform.system()
    if os_type in ('Linux', 'Darwin'):
        s_cmd = '/bin/kill -9 %s' % pids
        status, result = getso(s_cmd)
        print('kill_pids', status, result)
        if status == 0:
            return True
        else:
            return False
    elif os_type == 'Windows':
        try:
            import ctypes
            for i in pids:
                handle = ctypes.windll.kernel32.OpenProcess(1, False, i)
                ctypes.windll.kernel32.TerminateProcess(handle, 0)
            return True
        except Exception, e:
            return False


def get_pids(name):
    '''get pids of a process'''
    os_type = platform.system()
    if os_type in ('Linux', 'Darwin'):
        s_cmd = "/bin/ps auxww | grep %s | grep -v grep | awk '{print $2}'" % name
        status, result = getso(s_cmd)
        print(status, result)
        if status == 0 and result:
            return ' '.join(result.split()).split(' ')  # list
        else:
            return []
    elif os_type == 'Windows':
        if type(name) == int:
            str_cmd = "netstat -ano|find \"%s\"" % name
            try:
                result = os.popen(str_cmd, 'r').read()
                result = result.split('\n')[0].strip()
                if result.find('WAIT') != -1:
                    return 0
                pid = int(result[result.rfind(' '):].strip())
                return [pid]
            except Exception, e:
                return 0
        else:
            import win32con
            import win32api
            import win32process
            pids = []
            for pid in win32process.EnumProcesses():
                try:
                    hProcess = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
                    hProcessFirstModule = win32process.EnumProcessModules(hProcess)[0]
                    processName = os.path.splitext(os.path.split(win32process.GetModuleFileNameEx(hProcess, hProcessFirstModule))[1])[0]
                    if processName == name:
                        pids.append(pid)
                except Exception, e:
                    pass
            return pids


if __name__ == '__main__':
    # pids = get_process_list()
    # print(pids)
    print('kill_process', kill_process('sshd'))
    # print('kill_pid00', kill_pids(11587))
