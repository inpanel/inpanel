# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for service management.'''

import glob
import os
import shlex
import subprocess


class Service(object):
    '''supported service operate script'''
    support_services = [
        'intranet',
        'nginx',
        'httpd',
        'vsftpd',
        'mysqld',
        'redis',
        'memcached',
        'mongod',
        'php-fpm',
        'postfix',
        'sendmail',
        'sshd',
        'iptables',
        'crond',
        'ntpd',
        'named',
        'lighttpd',
        'proftpd',
        'pure-ftpd'
    ]

    pidnames = {
        'sendmail': ('sm-client', ),
    }

    @classmethod
    def status(self, service):
        initscript = '/etc/init.d/%s' % service
        if not os.path.exists(initscript):
            initscript = '/usr/lib/systemd/system/%s.service' % service
            if not os.path.exists(initscript):
                return None

        pidfile = '/var/run/%s.pid' % service
        if not os.path.exists(pidfile):
            p = glob.glob('/var/run/%s/*.pid' % service)
            if len(p) > 0:
                pidfile = p[0]
            else:
                # some services have special pid filename
                if Service.pidnames.has_key(service):
                    for pidname in Service.pidnames[service]:
                        pidfile = '/var/run/%s.pid' % pidname
                        if os.path.exists(pidfile):
                            break
                        else:
                            pidfile = None
                else:
                    pidfile = None
        if not pidfile:
            # not always corrent, some services dead but the lock still exists
            # some services don't have the pidfile
            # if os.path.exists('/var/lock/subsys/%s' % service):
            #    return 'running'

            # try execute pidof to find the pidfile
            cmd_ = shlex.split('pidof -c -o %%PPID -x %s' % service)
            p = subprocess.Popen(cmd_, stdout=subprocess.PIPE, close_fds=True)
            pid = p.stdout.read().strip()
            p.wait()

            if not pid:
                return 'stopped'

        if pidfile:
            with file(pidfile) as f:
                pid = f.readline().strip()
            if not pid:
                return 'stopped'
            proc = '/proc/%s' % pid
            if not os.path.exists(proc):
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
        cmd = shlex.split(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        p.stdout.read()
        return p.wait() == 0 and True or False

    @classmethod
    def autostart_list(self):
        """Return a list of the autostart service name.
        """
        startlevel = -1
        with open('/etc/inittab') as f:
            for line in f:
                if line.startswith('id:'):
                    startlevel = line.split(':')[1]
                    break
        if startlevel == -1:
            p = subprocess.Popen(shlex.split('runlevel'),
                                 stdout=subprocess.PIPE, close_fds=True)
            startlevel = int(p.stdout.read().strip().replace('N ', ''))
            p.wait()

        rcpath = '/etc/rc.d/rc%s.d/' % startlevel
        enableServicePath = '/etc/systemd/system/multi-user.target.wants/'
        services = [
            os.path.basename(os.readlink(filepath))
            for filepath in glob.glob('%s/S*' % rcpath)
        ]
        services += [
            os.path.basename(filePath).replace('.service', '')
            for filePath in glob.glob('%s*.service' % enableServicePath)
        ]
        return services


if __name__ == '__main__':
    autostart_services = Service.autostart_list()
    for service in Service.support_services:
        print '* Status of %s: %s (autostart: %s)' % (service,
                                                      Service.status(service), str(service in autostart_services))
    print
