# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Service Management.'''


from glob import glob
from os import readlink
from os.path import basename, exists
from shlex import split
from subprocess import PIPE, Popen

from base import kernel_name, os_name


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
    def status(self, service):
        initscript = '/etc/init.d/%s' % service
        if not exists(initscript):
            initscript = '/usr/lib/systemd/system/%s.service' % service
            if not exists(initscript):
                return None

        pidfile = '/var/run/%s.pid' % service
        if not exists(pidfile):
            p = glob('/var/run/%s/*.pid' % service)
            if len(p) > 0:
                pidfile = p[0]
            else:
                # some services have special pid filename
                if service in Service.pidnames:
                    for pidname in Service.pidnames[service]:
                        pidfile = '/var/run/%s.pid' % pidname
                        if exists(pidfile):
                            break
                        else:
                            pidfile = None
                else:
                    pidfile = None
        if not pidfile:
            # not always corrent, some services dead but the lock still exists
            # some services don't have the pidfile
            if service in Service.subsys_locks:
                if exists('/var/lock/subsys/%s' % service):
                    return 'running'

            # try execute pidof to find the pidfile
            cmd_ = split('pidof -c -o %%PPID -x %s' % service)
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
            if not exists('/proc/%s' % pid):
                return 'stopped'

        return 'running'

    @classmethod
    def autostart_set(self, service, autostart=True):
        """Add or remove service to autostart list.
        E.g: chkconfig service_name on|off
        """
        cmdbin = 'chkconfig'
        status = 'on' if autostart else 'off'
        cmd = '%s %s %s' % (cmdbin, service, status)
        cmd = split(cmd)
        p = Popen(cmd, stdout=PIPE, close_fds=True)
        p.stdout.read()
        return p.wait() == 0 and True or False

    @classmethod
    def autostart_list(self):
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

            rcpath = '/etc/rc.d/rc%s.d/' % startlevel
            enableServicePath = '/etc/systemd/system/multi-user.target.wants/'
            services = [
                basename(readlink(filepath))
                for filepath in glob('%s/S*' % rcpath)
            ]
            services += [
                basename(filePath).replace('.service', '')
                for filePath in glob('%s*.service' % enableServicePath)
            ]
            return services
        elif kernel_name == 'Darwin':
            return []


if __name__ == '__main__':
    autostart_services = Service.autostart_list()
    for service in Service.support_services:
        print('* Status of %s: %s (autostart: %s)' % (service, Service.status(service), str(service in autostart_services)))
