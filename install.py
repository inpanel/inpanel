#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

""" Install script for VPSMate """

import getpass
import os
import platform
import shlex
import socket
import subprocess
# import urllib2
import sys
# import re

class Install(object):
    def __init__(self):

        self.user = getpass.getuser()

        if (self.user != 'root'):
            print('Must run in root')
            sys.exit()

        if hasattr(platform, 'linux_distribution'):
            self.dist = platform.linux_distribution(full_distribution_name=0)
        else:
            self.dist = platform.dist()
        self.arch = platform.machine()
        if self.arch != 'x86_64': self.arch = 'i386'
        self.installpath = '/usr/local/vpsmate'
        self.distname = self.dist[0].lower()
        self.version = self.dist[1]
        self.version = self.version[0:self.version.find('.', self.version.index('.') + 1)]
        self.os = platform.system()
        print('Platform %s %s [%s]' % (self.dist[0], self.dist[1], self.os))

    def _run(self, cmd, shell=False):
        if shell:
            return subprocess.call(cmd, shell=shell)
        else:
            return subprocess.call(shlex.split(cmd))

    def check_platform(self):
        supported = True
        if self.distname == 'centos':
            if float(self.version) < 5.4:
                supported = False
        elif self.distname == 'redhat':
            if float(self.version) < 5.4:
                supported = False
        elif self.os == 'Darwin':
            supported = True
        # elif self.distname == 'ubuntu':
        #    if float(self.version) < 10.10:
        #        supported = False
        # elif self.distname == 'debian':
        #    if float(self.version) < 6.0:
        #        supported = False
        else:
            supported = False
        return supported

    def check_git(self):
        supported = True
        try:
            if self.distname in ('centos', 'redhat'):
                self._run("yum install -y git")
        except:
            pass

        if self.distname == 'centos':
            if float(self.version) < 5.4:
                supported = False
        elif self.distname == 'redhat':
            if float(self.version) < 5.4:
                supported = False
        elif self.os == 'Darwin':
            supported = True
        elif self.distname == 'ubuntu':
           if float(self.version) < 10.10:
               supported = False
        elif self.distname == 'debian':
           if float(self.version) < 6.0:
               supported = False
        else:
            supported = False
        return supported

    def install_epel_release(self):
        if self.distname in ('centos', 'redhat'):
            # following this: http://fedoraproject.org/wiki/EPEL/FAQ
            if int(float(self.version)) == 5:
                epelrpm = 'epel-release-5-4.noarch.rpm'
                epelurl = 'http://download.fedoraproject.org/pub/epel/5/%s/%s' % (self.arch, epelrpm)
                # install fastestmirror plugin for yum
                fastestmirror = 'http://mirror.centos.org/centos/5/os/%s/CentOS/yum-fastestmirror-1.1.16-21.el5.centos.noarch.rpm' % (self.arch)
                self._run('rpm -Uvh %s' % fastestmirror)
            elif int(float(self.version)) == 6:
                epelrpm = 'epel-release-6-8.noarch.rpm'
                epelurl = 'https://mirrors.aliyun.com/epel/6/%s/%s' % (self.arch, epelrpm)
                fastestmirror = 'https://mirrors.aliyun.com/centos/6/os/%s/Packages/yum-plugin-fastestmirror-1.1.30-41.el6.noarch.rpm' % (self.arch)
                # fastestmirror = 'http://mirror.centos.org/centos/6/os/%s/Packages/yum-plugin-fastestmirror-1.1.30-41.el6.noarch.rpm' % (self.arch)
                self._run('rpm -Uvh %s' % fastestmirror)
            elif int(float(self.version)) == 7:
                epelrpm = 'epel-release-7-11.noarch.rpm'
                epelurl = 'https://mirrors.aliyun.com/epel/7/%s/Packages/e/%s' % (self.arch, epelrpm)
                fastestmirror = 'https://mirrors.aliyun.com/centos/7/os/%s/Packages/yum-plugin-fastestmirror-1.1.31-45.el7.noarch.rpm' % (self.arch)
                # fastestmirror = 'http://mirror.centos.org/centos/7/os/%s/Packages/yum-plugin-fastestmirror-1.1.31-45.el7.noarch.rpm' % (self.arch)
                self._run('rpm -Uvh %s' % fastestmirror)

            self._run('wget -nv -c %s' % epelurl)
            self._run('rpm -Uvh %s' % epelrpm)

    def install_python(self):
        if self.distname == 'centos':
            self._run('yum -y install python26')

        elif self.distname == 'redhat':
            self._run('yum -y install python26')

        elif self.distname == 'ubuntu':
            self._run('apt-get -y install python')

        elif self.distname == 'debian':
            pass

    def install_vpsmate(self):
        # localpkg_found = False
        # if os.path.exists(os.path.join(os.path.dirname(__file__), 'vpsmate.tar.gz')):
        #     # local install package found
        #     localpkg_found = True
        # else:
        #     # or else install online
        #     print('* Downloading install package from www.vpsmate.org')
        #     f = urllib2.urlopen('http://www.vpsmate.org/api/latest')
        #     data = f.read()
        #     f.close()
        #     downloadurl = re.search('"download":"([^"]+)"', data).group(1).replace('\/', '/')
        #     self._run('wget -nv -c "%s" -O vpsmate.tar.gz' % downloadurl)
        
        # # uncompress and install it
        # self._run('mkdir vpsmate')
        # self._run('tar zxmf vpsmate.tar.gz -C vpsmate')
        # if not localpkg_found: os.remove('vpsmate.tar.gz')

        # stop service
        print
        if os.path.exists('/etc/init.d/vpsmate'):
            self._run('/etc/init.d/vpsmate stop')

        # backup data and remove old code
        if os.path.exists('%s/data/' % self.installpath):
            self._run('mkdir /tmp/vpsmate_data', True)
            self._run('cp -r %s/data/* /tmp/vpsmate_data/' % self.installpath, True)
        self._run('rm -rf %s' % self.installpath)
        self._run('git clone https://github.com/doudoudzj/vpsmate.git %s' % self.installpath)

        # install new code
        # self._run('mv vpsmate %s' % self.installpath)
        self._run('chmod +x %s/config.py %s/server.py' % (self.installpath, self.installpath))

        # install service
        initscript = '%s/tools/init.d/%s/vpsmate' % (self.installpath, self.distname)
        self._run('cp %s /etc/init.d/vpsmate' % initscript)
        self._run('chmod +x /etc/init.d/vpsmate')

        # start service
        if self.distname in ('centos', 'redhat'):
            self._run('chkconfig vpsmate on')
            self._run('service vpsmate start')
        elif self.distname == 'ubuntu':
            pass
        elif self.distname == 'debian':
            pass

    def config_firewall(self):
        self._run('iptables -A INPUT -p tcp --dport 8888 -j ACCEPT')
        self._run('iptables -A OUTPUT -p tcp --sport 8888 -j ACCEPT')

    def config(self, username, password):
        self._run('%s/config.py username "%s"' % (self.installpath, username))
        self._run('%s/config.py password "%s"' % (self.installpath, password))

    def detect_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('www.baidu.com', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def install(self):
        # check platform environment
        print('* Checking platform...'),
        supported = self.check_platform()

        if not supported:
            print('FAILED')
            print('Unsupport platform %s %s %s' % self.dist)
            sys.exit()
        else:
            print(self.distname)
            print('...OK')

        print('* Install depend software ...')
        self._run('yum install -y wget net-tools vim psmisc rsync libxslt-devel GeoIP GeoIP-devel gd gd-devel')

        print('Install epel-release...'),
        self.install_epel_release()

        # check python version
        print('* Current Python version [%s.%s] ...' % (sys.version_info[:2][0], sys.version_info[:2][1])),

        if (sys.version_info[:2] == (2, 6) or sys.version_info[:2] == (2, 7)):
            print('OK')
        else:
            print('FAILED')

            # install the right version
            print('* Installing python 2.6 ...'),
            self.install_python()

        # check GIT version
        print('* Checking GIT ...'),
        if self.check_git():
            print('OK')
        else:
            print('FAILED')

        # if sys.version_info[:2] == (2, 6):
        #     print('OK')
        # else:
        #     print('FAILED')
        #
        #     # install the right version


        #     print '* Installing python 2.6 ...'
        #     self.install_python()

        # stop firewall
        if os.path.exists('/etc/init.d/iptables'):
            self._run('/etc/init.d/iptables stop')

        # get the latest vpsmate version
        print('* Installing VPSMate')
        self.install_vpsmate()

        # set username and password
        print
        print('============================')
        print('*    INSTALL COMPLETED!    *')
        print('============================')
        print
        username = raw_input('Admin username [default: admin]: ').strip()
        password = raw_input('Admin password [default: admin]: ').strip()
        if len(username) == 0:
            username = 'admin'
        if len(password) == 0:
            password = 'admin'
        self.config(username, password)

        print
        print('* Username and password set successfully!')
        print

        print('* Config iptables')
        self.config_firewall()

        print('* The URL of your VPSMate is:'),
        print('http://%s:8888/' % self.detect_ip())
        print

        pass


def main():
    install = Install()
    install.install()


if __name__ == "__main__":
    main()