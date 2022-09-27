# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for process Management.'''

from os import makedirs
from os.path import dirname, exists, isdir
from subprocess import getstatusoutput

import psutil

from base import kernel_name
from mod_web import RequestHandler

# from utils import b2h


class WebRequestProcess(RequestHandler):
    '''Handler for load process list.'''

    def get(self, sec, pid=None):
        self.authed()

        if sec == 'list':
            self.write({'code': 0, 'data': get_list()})
        elif sec == 'info':
            self.write({'code': 0, 'data': get_info(pid)})
        elif sec == 'status':
            res = get_status(pid)
            if res:
                self.write({'code': 0, 'data': res})
            else:
                self.write({'code': -1, 'msg': '获取进程状态信息失败！'})
        elif sec == 'file':
            self.write({'code': 0, 'data': get_file(pid)})
        elif sec == 'memory':
            self.write({'code': 0, 'data': get_memory(pid)})
        elif sec == 'network':
            self.write({'code': 0, 'data': get_network(pid)})
        else:
            self.write({'code': -1, 'msg': '操作非法！'})

    def post(self, sec, pids):
        self.authed()

        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': 'DEMO状态不允许操作进程！'})
            return

        if sec == 'kill':
            if kill_pid(pids):
                self.write({'code': 0, 'msg': '进程终止成功！'})
            else:
                self.write({'code': -1, 'msg': '进程终止失败！'})


def get_list():
    '''get process list'''
    res = []
    pids = psutil.pids()
    # print('pids', pids)
    for pid in pids:
        item = get_base(pid)
        if item is not None:
            res.append(item)
    return res


def get_name(pid):
    '''get name by pid'''
    if not pid:
        return None
    p = psutil.Process(int(pid))
    return p.name()


def kill_process(name=None):
    '''kill process by name'''
    if name is None:
        return None
    pids = get_pids(name)
    # print('pid', pids)
    if pids:
        return kill_pid(pids)
    else:
        return False


def kill_pid(pid):
    '''kill process by pids'''
    if not pid:
        return None
    # print('kill_pid', pid)
    p = psutil.Process(int(pid))
    try:
        p.kill()
        return True
    except:
        return False

def get_pids(name):
    '''get pids of a process'''
    if not name:
        return None
    res = []
    # /bin/ps auxww | grep php | grep -v grep | awk '{print $2}'
    if kernel_name in ('Linux', 'Darwin'):
        cmd = "/bin/ps auxww | grep %s | grep -v grep | awk '{print $2}'" % name
        status, result = getstatusoutput(cmd)
        if status == 0 and result:
            res = ' '.join(result.split()).split(' ')  # list
    return res


def get_cmdline(pid):
    '''parse cmdline'''
    if not pid:
        return None
    if kernel_name == 'Linux':
        p = '/proc/%s/cmdline' % pid
        if not exists(p):
            return None
        with open(p, 'r') as f:
            line = f.readline()
            return line.strip()


def get_base(pid=None):
    '''get base info'''
    if pid is None:
        return {}
    p = psutil.Process(int(pid))
    memory = p.memory_info()
    return {
        'name': p.name(),  # 进程名
        'status': p.status(),  # 进程状态
        'pid': pid,
        'ppid': p.ppid(),
        'rss': str(memory[0]),  # rss 是常驻集大小，它是进程使用的实际物理内存
        'vms': str(memory[1])  # vms 是虚拟内存大小，它是进程正在使用的虚拟内存
    }


def get_file(pid=None):
    '''get files opened by process'''
    if pid is None:
        return []
    p = psutil.Process(int(pid))
    return p.open_files()


def save_pidfile(pidfile, pid):
    '''create/save pid file'''
    if not isdir(dirname(pidfile)):
        makedirs(dirname(pidfile))
    with open(pidfile, 'w+') as f:
        f.write(str(pid))


def get_status(pid=None):
    '''parse status'''
    if pid is None:
        return None
    p = psutil.Process(int(pid))
    return p.status()


def get_io(pid):
    '''parse io'''
    if not pid:
        return None
    res = {}
    if kernel_name == 'Linux':
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


def get_memory(pid=None):
    '''get memory'''
    if pid is None:
        return {}
    p = psutil.Process(int(pid))
    return p.memory_info()


def get_info(pid=None):
    '''get info'''
    if pid is None:
        return {}
    p = psutil.Process(int(pid))

    return {
        'pid': pid,
        'name': p.name(),  # 进程名
        'ppid': p.ppid(),  # 父进程ID
        'cmdline': p.cmdline(),  # 启动的命令行
        'exe': p.exe(),  # 进程exe路径
        'cwd': p.cwd(),  # 进程的工作目录绝对路径
        'status': p.status(),  # 进程状态
        'create_time': p.create_time(),  # 进程创建时间秒
        'uids': p.uids(),  # 进程uid信息
        'gids': p.gids(),  # 进程gids信息
        'username': p.username(),  # 进程用户名
        'cpu_percent': p.cpu_percent(),  # CPU利用率
        'cpu_times': p.cpu_times(),  # 进程的cpu时间信息,包括user,system两个cpu信息
        'memory_info': p.memory_info(),  # 进程内存rss,vms信息 [utils.b2h(i) for i in p.memory_info()]
        'memory_percent': p.memory_percent(),
        'terminal': p.terminal(),  # 进程终端
        'num_threads': p.num_threads(),  # 进程开启的线程数
    }


def get_network(pid=None):
    '''parse network'''
    if pid is None:
        return None
    res = []
    p = psutil.Process(int(pid))
    net = p.connections()
    # print('net', net)
    for n in net:
        res.append({
            'local': {
                'ip': n[3][0],
                'port': n[3][1]
            } if n[3] else None,
            'remote': {
                'ip': n[4][0],
                'port': n[4][1]
            } if n[4] else None,
            'status': n[5]
        })
    # print('res', res)
    return res


if __name__ == '__main__':
    pass
    # pids = get_list()
    # print(pids)
    # print('kill_process', kill_process('sshd'))
    # print('kill_pid00', kill_pids(11587))
    # print(get_pids('php'))
    # print(get_list())
    # print(get_info(144))
    # print(get_network(144))
    # print('psutil.process_iter()', psutil.process_iter())
    # pid = 78269
    # p = psutil.Process(pid)
    # # p = psutil.process_iter()
    # # p = psutil.pids()
    # memory = p.memory_info()
    # # print('memory', memory)
    # res = {
    #     'name': p.name(), # 进程名
    #     'status': p.status(), # 进程状态
    #     'uid': p.uids(), # 进程状态
    #     'tgid': p.gids(), # 进程的gid信息
    #     'create_time': p.create_time(), # 进程创建时间
    #     'pid': pid,
    #     'ppid': p.ppid(),
    #     # 'fdsize': '',
    #     # 'vmpeak': memory[0],
    #     'vmsize': memory[0],
    #     'vmrss': memory[1]
    # }
    # # print('res', res)
    # # for p in pi:
    # #     try:
    # #         print('p', p)
    # #     except psutil.Error:
    # #         pass
