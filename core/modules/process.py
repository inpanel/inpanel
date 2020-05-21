# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for process Management.'''

from os import listdir
from os.path import exists
from platform import system

from core.web import RequestHandler

try:
    from commands import getstatusoutput
except:
    from subprocess import getstatusoutput

os_type = system()


class WebRequestProcess(RequestHandler):
    '''Handler for load process list.'''
    def get(self, sec, pid=None):
        self.authed()
        if sec == 'list':
            res = get_list()
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程列表失败！'})

        if sec == 'info':
            res = get_info(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程信息失败！'})
        if sec == 'status':
            res = get_status(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程状态信息失败！'})
        if sec == 'file':
            res = get_file(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程文件使用情况失败！'})
        if sec == 'io':
            res = get_io(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程IO状态失败！'})
        if sec == 'memory':
            res = get_memory(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程内存使用情况失败！'})
        if sec == 'network':
            res = get_network(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': u'获取进程网络状态失败！'})

    def post(self, sec, pids):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': u'DEMO状态不允许操作进程！'})
            return

        if sec == 'kill':
            if kill_pids(pids):
                self.write({'code': 0, 'msg': u'进程终止成功！'})
            else:
                self.write({'code': -1, 'msg': u'进程终止失败！'})


def get_list():
    '''get process list'''
    res = []
    if os_type == 'Linux':
        for pid in listdir('/proc'):
            if pid.isdigit():
                res.append(get_base(pid))
    elif os_type == 'Darwin':
        pass
    elif os_type == 'Windows':
        pass
    return res


def get_name(pid):
    '''get name by pid'''
    if not pid:
        return None
    name = None
    if os_type == 'Linux':
        p = '/proc/%s/comm' % pid
        if exists(p):
            with open(p, 'r') as f:
                line = f.readline()
                name = line.strip()
        if not name:
            p = '/proc/%s/status' % pid
            if exists(p):
                with open(p, 'r') as f:
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
        return None
    pids = get_pids(name)
    # print('pid', pids)
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
    if os_type in ('Linux', 'Darwin'):
        cmd = u'/bin/kill -9 %s' % pids
        status, result = getstatusoutput(cmd)
        return status == 0
    else:
        return False


def get_pids(name):
    '''get pids of a process'''
    if not name:
        return None
    res = []
    if os_type in ('Linux', 'Darwin'):
        cmd = u"/bin/ps auxww | grep %s | grep -v grep | awk '{print $2}'" % name
        status, result = getstatusoutput(cmd)
        if status == 0 and result:
            res = ' '.join(result.split()).split(' ')  # list
    return res


def get_cmdline(pid):
    '''parse cmdline'''
    if not pid:
        return None
    if os_type == 'Linux':
        p = '/proc/%s/cmdline' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            return line.strip()


def get_base(pid):
    '''get base info'''
    if not pid:
        return None
    res = {
        'name': '',
        'state': '',
        'tgid': '',
        'pid': '',
        'ppid': '',
        'fdsize': '',
        'vmpeak': '',
        'vmsize': '',
        'vmrss': ''
    }
    if os_type == 'Linux':
        p = '/proc/%s/status' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            while line:
                out = line.strip()
                label = out.split()
                if out.startswith('Name'):
                    res['name'] = label[1]
                elif out.startswith('State'):
                    res['state'] = label[1]
                elif out.startswith('Tgid'):
                    res['tgid'] = label[1]
                elif out.startswith('Pid'):
                    res['pid'] = label[1]
                elif out.startswith('PPid'):
                    res['ppid'] = label[1]
                elif out.startswith('FDSize'):
                    res['fdsize'] = label[1]
                elif out.startswith('VmPeak'):
                    res['vmpeak'] = label[1]
                elif out.startswith('VmSize'):
                    res['vmsize'] = label[1]
                elif out.startswith('VmRSS'):
                    res['vmrss'] = label[1]
                elif out.startswith('Threads'):
                    break # No need to read the following content
                line = f.readline()
    return res


def get_file(pid):
    '''get process file'''
    if not pid:
        return
    return {'name': 'test', 'pid': pid}


def get_environ(pid):
    '''parse environ'''
    if not pid:
        return None
    res = ''
    if os_type == 'Linux':
        p = '/proc/%s/environ' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            res = line.strip()
    return res


def get_status(pid):
    '''parse status'''
    if not pid:
        return None
    res = {}
    if os_type == 'Linux':
        p = '/proc/%s/status' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            while line:
                out = line.strip()
                tmp = out.split()
                if out.startswith('Uid') or out.startswith('Gid') or out.startswith('Vm'):
                    res[tmp[0].split(':')[0].lower()] = tmp[1:]
                elif out.startswith('State'):
                    res[tmp[0].split(':')[0].lower()] = [tmp[1], tmp[2][1:-1].lower()]
                else:
                    res[tmp[0].split(':')[0].lower()] = tmp[1] if len(tmp) > 1 else ''
                line = f.readline()
    return res


def get_io(pid):
    '''parse io'''
    if not pid:
        return None
    res = {}
    if os_type == 'Linux':
        p = '/proc/%s/io' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            while line:
                out = line.strip()
                res[out.split()[0].split(':')[0].lower()] = out.split()[1]
                line = f.readline()
    return res


def get_memory(pid):
    '''get memory, parse statm'''
    if not pid:
        return None
    res = ''
    if os_type == 'Linux':
        p = '/proc/%s/statm' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            line = line.strip()
            res = line.split()
    return res


def get_info(pid):
    '''parse stat'''
    if not pid:
        return None
    res = {}
    if os_type == 'Linux':
        p = '/proc/%s/stat' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            while line:
                out = line.strip()
                res = out.split()
                line = f.readline()
    return res


def get_network(pid):
    '''parse network'''
    if not pid:
        return None
    res = {}
    if os_type == 'Linux':
        p = '/proc/%s/stat' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            while line:
                out = line.strip()
                res = out.split()
                line = f.readline()
    return res


if __name__ == '__main__':
    # pids = get_list()
    # print(pids)
    # print('kill_process', kill_process('sshd'))
    # print('kill_pid00', kill_pids(11587))
    # print(get_pids('php'))
    print(get_status(1))
    # print(get_base(2345))
