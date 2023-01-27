# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Service Management.'''


import os
# from mod_shell import async_command
from glob import glob
from shlex import split
from subprocess import PIPE, Popen

from base import kernel_name, os_name


def web_handler(context):
    '''for web server'''
    action = context.get_argument('action', '')

    if action == 'start':
        name = context.get_argument('name', '')
        service_label = context.get_argument('service', '')
        if not name:
            name = service_label
        if do_start(name):
            context.write({'code': 0, 'msg': f'{name} 已启动成功'})
        else:
            context.write({'code': -1, 'msg': f'{name} 启动运行失败'})
    elif action == 'stop':
        name = context.get_argument('name', '')
        service_label = context.get_argument('service', '')
        if not name:
            name = service_label
        if do_stop(name):
            context.write({'code': 0, 'msg': f'{name} 已成功停止运行'})
        else:
            context.write({'code': -1, 'msg': f'{name} 停止运行失败'})
    elif action == 'restart':
        name = context.get_argument('name', '')
        service_label = context.get_argument('service', '')
        if not name:
            name = service_label
        if do_start(name):
            context.write({'code': 0, 'msg': f'{name} 已重新启动'})
        else:
            context.write({'code': -1, 'msg': f'{name} 重新启动失败'})
    elif action == 'chkconfig':
        autostart = context.get_argument('autostart', '')
        if not name:
            name = service_label

        autostart_str = {'on': '启用', 'off': '禁用'}
        if set_autostart(service_label, autostart == 'on' and True or False):
            context.write({'code': 0, 'msg': f'成功{autostart_str[autostart]} {name} 自动启动！'})
        else:
            context.write({'code': -1, 'msg': f'{autostart_str[autostart]} {name} 自动启动失败！'})
    elif action == 'get_autostart_list':
        context.write({'code': 0, 'data': get_autostart_list()})
    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})

def do_start(service_name=None):
    '''start service'''
    if not service_name:
        return False
    return True


def do_stop(service_name=None):
    '''stop service'''
    if not service_name:
        return False
    return True


def do_restart(service_name=None):
    '''stop service then start service'''
    if not service_name:
        return False
    do_stop()
    do_start()


def get_status(name = None):
    '''get '''
    if name is None:
        return False
    return True


def do_search():
    '''set service auto start on system up'''
    return True


def get_list():
    '''Return a list of all service'''
    return []


def get_autostart_list():
    """Return a list of the autostart service name.
    """
    if kernel_name == 'Linux':
        if os_name == 'Ubuntu':
            return []
        startlevel = -1
        with open('/etc/inittab', encoding='utf-8') as f:
            for line in f:
                if line.startswith('id:'):
                    startlevel = line.split(':')[1]
                    break
        if startlevel == -1:
            p = Popen(split('runlevel'), stdout=PIPE, close_fds=True)
            startlevel = int(p.stdout.read().decode().strip().replace('N ', ''))
            p.wait()

        rcpath = f'/etc/rc.d/rc{startlevel}.d/'
        enable_service_path = '/etc/systemd/system/multi-user.target.wants/'
        services = [
            os.path.basename(os.readlink(filepath))
            for filepath in glob(f'{rcpath}/S*')
        ]
        services += [
            os.path.basename(filePath).replace('.service', '')
            for filePath in glob(f'{enable_service_path}*.service')
        ]
        return services
    elif kernel_name == 'Darwin':
        return []
    # others
    return []


def set_autostart(service_name=None, autostart=True):
    """Add or remove service to autostart list.
    E.g: chkconfig service_name on|off
    """
    if not service_name:
        return False
    if kernel_name == 'Linux':
        cmdbin = 'chkconfig'
        status = 'on' if autostart else 'off'
        cmd = f'{cmdbin} {service_name} {status}'
        cmd = split(cmd)
        p = Popen(cmd, stdout=PIPE, close_fds=True)
        p.stdout.read()
        return p.wait() == 0 and True or False
    elif kernel_name == 'Darwin':
        return False
    else:
        return False

def do_add():
    '''create service config file'''
    return True


__all__ = [
    'do_start', 'do_stop', 'do_restart', 'do_search', 'get_list',
    'get_autostart_list', 'set_autostart'
]

class Service(object):

    '''supported service operate script'''
    service_items = {
        'inpanel': False,
        'nginx': False,
        'httpd': False,
        'vsftpd': False,
        'mysqld': False,
        'redis': False,
        'memcached': False,
        'mongod': False,
        'php-fpm': False,
        'sendmail': False,
        'postfix': False,
        'sshd': False,
        'iptables': False,
        'crond': False,
        'ntpd': False,
        'named': False,
        'lighttpd': False,
        'proftpd': False,
        'pure-ftpd': False,
        'smb': False
    }

    pidnames = {
        'sendmail': ['sm-client'],
        'smb': ['smbd']
    }

    subsys_locks = (
        'iptables'
    )

    @classmethod
    def status(self, service = None):
        if not service:
            return None
        initscript = f'/etc/init.d/{service}'
        if not os.path.exists(initscript):
            initscript = f'/usr/lib/systemd/system/{service}.service'
            if not os.path.exists(initscript):
                return None

        pidfile = f'/var/run/{service}.pid'
        if not os.path.exists(pidfile):
            p = glob(f'/var/run/{service}/*.pid')
            if len(p) > 0:
                pidfile = p[0]
            else:
                # some services have special pid filename
                if service in Service.pidnames:
                    for pidname in Service.pidnames[service]:
                        pidfile = f'/var/run/{pidname}.pid'
                        if os.path.exists(pidfile):
                            break
                        else:
                            pidfile = None
                else:
                    pidfile = None
        if not pidfile:
            # not always corrent, some services dead but the lock still exists
            # some services don't have the pidfile
            if service in Service.subsys_locks:
                if os.path.exists(f'/var/lock/subsys/{service}'):
                    return 'running'

            # try execute pidof to find the pidfile
            cmd_ = split(f'pidof -c -o %%PPID -x {service}')
            p = Popen(cmd_, stdout=PIPE, close_fds=True)
            pid = p.stdout.read().decode().strip()
            p.wait()

            if not pid:
                return 'stopped'

        if pidfile:
            with open(pidfile, encoding='utf-8') as f:
                pid = f.readline().strip()
            if not pid:
                return 'stopped'
            if not os.path.exists(f'/proc/{pid}'):
                return 'stopped'

        return 'running'



if __name__ == '__main__':
    autostart_services = get_autostart_list()
    for service in Service.support_services:
        print('* Status of %s: %s (autostart: %s)' % (service, Service.status(service), str(service in autostart_services)))
