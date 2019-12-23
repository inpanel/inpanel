#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, doudoudzj
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

''' Install Script for InPanel '''

import getpass
import os
import platform
import shlex
import socket
import subprocess
# import urllib2
import sys
# import re

OK = '\033[1;32mOK\033[0m'
FAILED = '\033[1;31mFAILED\033[0m'
INSTALL_COMPLETED = '\033[1;32mINSTALL COMPLETED\033[0m'


class Install(object):
    def __init__(self):

        self.user = getpass.getuser()
        if (self.user != 'root'):
            print('')
            print('\033[7;31mThis script must be run as root !\033[0m')
            print('')
            sys.exit()

        if sys.version_info[0] < 3:
            self.input = raw_input
        else:
            self.input = input
        if hasattr(platform, 'linux_distribution'):
            self.dist = platform.linux_distribution(full_distribution_name=0)
        else:
            self.dist = platform.dist()
        self.arch = platform.machine()
        if self.arch != 'x86_64':
            self.arch = 'i386'
        self.initd_script = '/etc/init.d/inpanel'
        self.installpath = '/usr/local/inpanel'
        self.listen_port = 8888
        self.repository = 'https://github.com/inpanel/inpanel.git'
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
        elif self.distname == 'ubuntu':
            if float(self.version) < 10.10:
                supported = False
        elif self.distname == 'debian':
            if float(self.version) < 6.0:
                supported = False
        else:
            supported = False
        return supported

    def handle_git(self):
        '''install git'''
        success = True
        print('* Install GIT ...'),
        try:
            if self.distname in ('centos', 'redhat'):
                self._run('yum install -y git')
            if self.distname in ('ubuntu', 'debian'):
                self._run('apt-get -y install git')
            success = True
            print('[ %s ]' % OK)
        except:
            success = False
            print('[ %s ]' % FAILED)
        return success

    def handle_dependent(self):
        '''Install dependent software'''
        success = True
        print('* Install Dependent Software...'),
        try:
            self._run('yum install -y -q epel-release')
            self._run('yum install -y -q wget net-tools vim psmisc rsync libxslt-devel GeoIP GeoIP-devel gd gd-devel')
            success = True
            print('[ %s ]' % OK)
        except:
            success = False
            print('[ %s ]' % FAILED)
        return success

    def handle_python(self):
        '''handle Python and install Python 2.6'''
        # check python version
        print('* Current Python Version is [%s.%s] ...' % (sys.version_info[:2][0], sys.version_info[:2][1])),
        if (sys.version_info[:2] == (2, 6) or sys.version_info[:2] == (2, 7)):
            print('[ %s ]' % OK)
            return True
        else:
            print('[ %s ]' % FAILED)
        # Install Python
        print('* Installing Python 2.6 ...'),
        if self.distname == 'centos':
            self._run('yum -y install python26')

        elif self.distname == 'redhat':
            self._run('yum -y install python26')

        elif self.distname == 'ubuntu':
            self._run('apt-get -y install python')

        elif self.distname == 'debian':
            self._run('apt-get -y install python')
        print('[ %s ]' % OK)

    def handle_inpanel(self):
        # handle InPanel
        # get the latest InPanel version
        print('* Installing InPanel')
        # localpkg_found = False
        # if os.path.exists(os.path.join(os.path.dirname(__file__), 'inpanel.tar.gz')):
        #     # local install package found
        #     localpkg_found = True
        # else:
        #     # or else install online
        #     print('* Downloading install package from inpanel.pub')
        #     f = urllib2.urlopen('http://api.inpanel.org/?s=latest')
        #     data = f.read()
        #     f.close()
        #     downloadurl = re.search('"download":"([^"]+)"', data).group(1).replace('\/', '/')
        #     self._run('wget -nv -c "%s" -O inpanel.tar.gz' % downloadurl)

        # # uncompress and install it
        # self._run('mkdir inpanel')
        # self._run('tar zxmf inpanel.tar.gz -C inpanel  --strip-components 1')
        # if not localpkg_found: os.remove('inpanel.tar.gz')

        # stop service
        if os.path.exists(self.initd_script):
            self._run('%s stop' % self.initd_script)

        # backup data and remove old code
        # if os.path.exists('%s/data/' % self.installpath):
        #     self._run('mkdir /tmp/inpanel_data', True)
        #     self._run('/bin/cp -rf %s/data/* /tmp/inpanel_data/' % self.installpath, True)

        if self.installpath:
            self._run('rm -rf %s' % self.installpath)
        branch = 'master'
        if len(sys.argv) == 2 and sys.argv[1] == '--dev':
            branch = 'dev'
        self._run('git clone -b %s %s %s' % (branch, self.repository, self.installpath))

        # install new code
        # self._run('mv inpanel %s' % self.installpath)
        self._run('chmod +x %s/config.py %s/server.py' % (self.installpath, self.installpath))

        # install service
        initscript = '%s/core/init.d/%s/inpanel' % (self.installpath, self.distname)
        self._run('cp %s %s' % (initscript, self.initd_script))
        self._run('chmod +x %s' % self.initd_script)

    def handle_intranet(self):
        '''handle the old version Intranet Panel'''
        if os.path.exists('/etc/init.d/intranet'):
            print('* Found Intranet')
            self._run('/etc/init.d/intranet stop')
            self._run('rm -rf /etc/init.d/intranet')
            self._run('rm -rf /usr/local/intranet')
            print('* Intranet has been deleted')

    def config_firewall(self):
        '''config firewall'''
        print('* Config firewall...'),
        if self.distname in ('centos', 'redhat'):
            if self.version < 7 and os.path.exists('/etc/init.d/iptables'):
                self._run('iptables -A INPUT -m state --state NEW -p tcp --dport %s -j ACCEPT' % self.listen_port)
                self._run('iptables -A OUTPUT -m state --state NEW -p tcp --sport %s -j ACCEPT' % self.listen_port)
                self._run('service iptables save')
                self._run('/etc/init.d/iptables restart')
                print('[ %s ]' % OK)
            elif os.path.exists('/etc/firewalld/firewalld.conf'):
                self._run('firewall-cmd --permanent --zone=public --add-port=%s/tcp' % self.listen_port)
                self._run('systemctl restart firewalld.service')
                print('[ %s ]' % OK)
            else:
                print('Not Installed, No configuration required.')

    def config_account(self):
        '''set username and password'''
        username = self.input('Admin username [default: admin]: ').strip()
        password = self.input('Admin password [default: admin]: ').strip()
        if len(username) == 0:
            username = 'admin'
        if len(password) == 0:
            password = 'admin'
        self._run('%s/config.py username "%s"' % (self.installpath, username))
        self._run('%s/config.py password "%s"' % (self.installpath, password))
        print('* Username and password set successfully!')

    def detect_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('www.baidu.com', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def handle_port(self):
        # config listen port
        start_port = int(self.listen_port)
        # 2^16-1 = 65535
        while (start_port < 65536):
            res = self.find_free_port(start_port)
            if res:
                break
            else:
                start_port = start_port + 1
        self.listen_port = start_port
        # self.listen_port = 8899
        self._run('%s/config.py port "%s"' % (self.installpath, self.listen_port))
        print('* InPanel will work on port %s' % self.listen_port)

    def find_free_port(self, port_number):
        # find an unuse port
        enabled = False
        local_ip = socket.gethostbyname(socket.gethostname())
        skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_list = tuple(set(('127.0.0.1', '0.0.0.0', local_ip)))
        print(ip_list)
        for ip in ip_list:
            print(ip)
            try:
                res = skt.connect_ex((str(ip), int(port_number)))
                # res = skt.connect_ex(('127.0.0.1', port_number))
                if res == 0:
                    # print('Port %d is open' % port_number)
                    enabled = True
                else:
                    # print('Port %d is not open' % port_number)
                    enabled = False
                skt.close()
            except:
                enabled = False

        return enabled

    def handle_vpsmate(self):
        # handle VPSMate
        v_script = '/etc/init.d/vpsmate'
        if not os.path.exists(v_script):
            return False

        print('* Checking VPSMate')
        v_path = '/usr/local/vpsmate'
        isdel = self.input('Need to delete VPSMate ? [yes or no, default: yes]: ').strip()
        if len(isdel) == 0:
            isdel = 'yes'
        if isdel == 'yes':
            self._run('%s stop' % v_script)
            self._run('rm -f %s' % v_script)
            print('* VPSMate has been deleted')
            if v_path:
                self._run('rm -rf %s' % v_path)
        else:
            if not isdel == 'no':
                print('* The command you entered is incorrect !')
            print('* VPSMate will continue to work !')
            self.listen_port = 8899
            self._run('%s/config.py port "%s"' % (self.installpath, self.listen_port))
            print('* InPanel will work on port %s' % self.listen_port)

    def start_service(self):
        # start service
        if not os.path.exists(self.initd_script):
            print('Starting InPanel [ %s ]' % FAILED)
            return False
        if self.distname in ('centos', 'redhat'):
            self._run('chkconfig inpanel on')
            self._run('service inpanel start')
        elif self.distname == 'ubuntu':
            pass
        elif self.distname == 'debian':
            pass

    def install(self):
        '''check platform environment to install software'''
        print('* Checking Platform...'),
        if not self.check_platform():
            print('[ %s ]' % FAILED)
            print('Unsupport Platform %s %s %s' % self.dist)
            sys.exit()
        else:
            print(self.distname),
            print('...%s' % OK)

        self.handle_dependent()
        self.handle_python()
        self.handle_git()
        self.handle_intranet()
        self.handle_inpanel()
        self.handle_vpsmate()
        # self.handle_port()
        self.config_account()
        self.config_firewall()
        self.start_service()
        print('')
        print('============================')
        print('*                          *')
        print('*     %s    *' % INSTALL_COMPLETED)
        print('*                          *')
        print('============================')
        print('')
        print('The URL of your InPanel is:'),
        print('\033[4;34mhttp://%s:%s/\033[0m' % (self.detect_ip(), self.listen_port))
        print('')
        print('\033[5;32mWish you a happy life !\033[0m')
        print('')
        print('')


if __name__ == '__main__':
    install = Install()
    install.install()
