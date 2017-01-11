#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

""" Install script for VPSMate """

import os
import sys
import platform
import shlex
import subprocess
import urllib2
import re
import socket

class Install(object):

    def __init__(self):
        if hasattr(platform, 'linux_distribution'):
            self.dist = platform.linux_distribution(full_distribution_name=0)
        else:
            self.dist = platform.dist()
        self.arch = platform.machine()
        if self.arch != 'x86_64': self.arch = 'i386'
        self.installpath = '/usr/local/vpsmate'
        self.distname = self.dist[0].lower()
        self.version = self.dist[1]
        
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
        #elif self.distname == 'ubuntu':
        #    if float(self.version) < 10.10:
        #        supported = False
        #elif self.distname == 'debian':
        #    if float(self.version) < 6.0:
        #        supported = False
        else:
            supported = False
        return supported
    
    def install_python(self):
        if self.distname in ('centos', 'redhat'):
            # following this: http://fedoraproject.org/wiki/EPEL/FAQ
            if int(float(self.version)) == 5:
                epelrpm = 'epel-release-5-4.noarch.rpm'
                epelurl = 'http://download.fedoraproject.org/pub/epel/5/%s/%s' % (self.arch, epelrpm)
                # install fastestmirror plugin for yum
                fastestmirror = 'http://mirror.centos.org/centos/5/os/%s/CentOS/yum-fastestmirror-1.1.16-21.el5.centos.noarch.rpm' % (self.arch, )
            elif int(float(self.version)) == 6:
                epelrpm = 'epel-release-6-7.noarch.rpm'
                epelurl = 'http://download.fedoraproject.org/pub/epel/6/%s/' % (self.arch, epelrpm)
                fastestmirror = 'http://mirror.centos.org/centos/6/os/%s/Packages/yum-plugin-fastestmirror-1.1.30-14.el6.noarch.rpm' % (self.arch, )
            self._run('wget -nv -c %s' % epelurl)
            self._run('rpm -Uvh %s' % epelrpm)
            self._run('rpm -Uvh %s' % fastestmirror)
            self._run('yum -y install python26')

        if self.distname == 'centos':
            pass
        elif self.distname == 'redhat':
            pass
        elif self.distname == 'ubuntu':
            pass
        elif self.distname == 'debian':
            pass

    def install_vpsmate(self):
        localpkg_found = False
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'vpsmate.tar.gz')):
            # local install package found
            localpkg_found = True
        else:
            # or else install online
            print '* Downloading install package from www.vpsmate.org'
            f = urllib2.urlopen('http://www.vpsmate.org/api/latest')
            data = f.read()
            f.close()
            downloadurl = re.search('"download":"([^"]+)"', data).group(1).replace('\/', '/')
            self._run('wget -nv -c "%s" -O vpsmate.tar.gz' % downloadurl)
            
        # uncompress and install it
        self._run('mkdir vpsmate')
        self._run('tar zxmf vpsmate.tar.gz -C vpsmate')
        if not localpkg_found: os.remove('vpsmate.tar.gz')
        
        # stop service
        print
        if os.path.exists('/etc/init.d/vpsmate'):
            self._run('/etc/init.d/vpsmate stop')

        # backup data and remove old code
        if os.path.exists('%s/data/' % self.installpath):
            self._run('cp -r %s/data/* vpsmate/data/' % self.installpath, True)
        self._run('rm -rf %s' % self.installpath)
        
        # install new code
        self._run('mv vpsmate %s' % self.installpath)
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
        print '* Checking platform...',
        supported = self.check_platform()
        
        if not supported:
            print 'FAILED'
            print 'Unsupport platform %s %s %s' % self.dist
            sys.exit()
        else:
            print 'OK'

        # check python version
        print '* Checking python version ...',
        if sys.version_info[:2] == (2, 6):
            print 'OK'
        else:
            print 'FAILED'

            # install the right version
            print '* Installing python 2.6 ...'
            self.install_python()

        # stop firewall
        if os.path.exists('/etc/init.d/iptables'):
            self._run('/etc/init.d/iptables stop')
        
        # get the latest vpsmate version
        print '* Installing latest VPSMate'
        self.install_vpsmate()
        
        # set username and password
        print
        print '============================'
        print '*    INSTALL COMPLETED!    *'
        print '============================'
        print 
        username = raw_input('Admin username [default: admin]: ').strip()
        password = raw_input('Admin password [default: admin]: ').strip()
        if len(username) == 0:
            username = 'admin'
        if len(password) == 0:
            password = 'admin'
        self.config(username, password)
        
        print
        print '* Username and password set successfully!'
        print 
        print '* The URL of your VPSMate is:',
        print 'http://%s:8888/' % self.detect_ip()
        print 

        pass


def main():
    install = Install()
    install.install()
    

if __name__ == "__main__":
    main()