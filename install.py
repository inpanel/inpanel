#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

''' Install Script for InPanel '''

import getpass
import os
import platform
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import getopt
import readline

import urllib.request as request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'inpanel'))
try:
    from inpanel.mod.package import get_package_manager, resolve_package_names
except ImportError:
    from mod.package import get_package_manager, resolve_package_names


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

        self.input = input
        self.dist = self._get_linux_dist()
        self.arch = platform.machine()
        if self.arch != 'x86_64':
            self.arch = 'i386'
        self.systemd_service = '/etc/systemd/system/inpanel.service'
        self.initd_script = '/etc/init.d/inpanel'
        self.installpath = '/usr/bin/inpanel'
        self.listen_port = 14433
        self.username = 'admin'
        self.password = 'admin'
        self.repository = 'https://github.com/inpanel/inpanel.git'
        self.branch = 'master'
        self.distname = self.dist[0].lower()
        self.sys_version = self.dist[1]
        self.sys_version = self.sys_version[0:self.sys_version.find('.', self.sys_version.index('.') + 1)]
        self.os = platform.system()
        self.pm = get_package_manager()
        self.install_mode = 'pip'
        print('Platform %s %s [%s]' % (self.dist[0], self.dist[1], self.os))

    def handle_options(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'b:r:u:p:P:vm:h', \
            ['dev', 'branch=', 'repository=', 'username=', 'password=', 'port=', 'version', 'mode=', 'help'])
        except getopt.GetoptError:
            print('Error: invalid arguments')
            print('Try \'install.py --help\' for more information.')
            sys.exit(2)
        for opt_name, arg_value in opts:
            if opt_name in ('--dev'):
                self.branch = 'dev'
            elif opt_name in ('-b', '--branch'):
                self.branch = arg_value
            elif opt_name in ('-r', '--repository'):
                self.repository = arg_value
            elif opt_name in ('-u', '--username'):
                self.username = arg_value
            elif opt_name in ('-p', '--password'):
                self.password = arg_value
            elif opt_name in ('-P', '--port'):
                self.listen_port = arg_value
            elif opt_name in ('-m', '--mode'):
                self.install_mode = arg_value
            elif opt_name in ('-v', '--version'):
                print('v1.2.27')
                sys.exit(0)
            elif opt_name in ('--help'):
                print('Usage: install.py [OPTIONS...]')
                print('-r, --repository=<address>      set repository')
                print('-b, --branch=<value>            set branch')
                print('-u, --username=<value>          set username')
                print('-p, --password=<value>          set password')
                print('-P, --port=<value>              set listen port')
                print('-m, --mode=<pip|source>         install mode (default: pip)')
                print('-v, --version                   output version information and exit')
                print('-h, --help                      display this help and exit')
                print('')
                sys.exit(0)

    def _run(self, cmd, shell=False):
        if shell:
            return subprocess.call(cmd, shell=shell)
        else:
            return subprocess.call(shlex.split(cmd))

    def _run_output(self, cmd, shell=False):
        if shell:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        else:
            result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def _get_linux_dist(self):
        dist_id = ''
        version = ''
        codename = ''

        if Path('/etc/os-release').exists():
            with open('/etc/os-release', 'r') as f:
                info = {}
                for line in f:
                    if '=' in line:
                        key, val = line.strip().split('=', 1)
                        info[key] = val.strip('"')
                dist_id = info.get('ID', '').lower()
                version = info.get('VERSION_ID', '').strip('"')
                codename = info.get('VERSION_CODENAME', '')
                if not codename and 'VERSION' in info:
                    ver = info.get('VERSION', '')
                    if '(' in ver and ')' in ver:
                        codename = ver.split('(')[1].split(')')[0]
            return (dist_id, version, codename)

        if Path('/etc/redhat-release').exists():
            with open('/etc/redhat-release', 'r') as f:
                content = f.read().lower()
                if 'centos' in content:
                    dist_id = 'centos'
                elif 'red hat' in content or 'rhel' in content:
                    dist_id = 'rhel'
                import re
                match = re.search(r'(\d+\.?\d*)', content)
                if match:
                    version = match.group(1)
            return (dist_id, version, codename)

        if Path('/etc/lsb-release').exists():
            with open('/etc/lsb-release', 'r') as f:
                info = {}
                for line in f:
                    if '=' in line:
                        key, val = line.strip().split('=', 1)
                        info[key] = val.strip('"')
                dist_id = info.get('DISTRIB_ID', '').lower()
                version = info.get('DISTRIB_RELEASE', '')
                codename = info.get('DISTRIB_CODENAME', '')
            return (dist_id, version, codename)

        uname = platform.uname()
        dist_id = uname.system.lower()
        version = uname.release
        return (dist_id, version, codename)

    def check_platform(self):
        supported = True
        if self.distname == 'centos':
            if float(self.sys_version) < 5.4:
                supported = False
        elif self.distname == 'redhat':
            if float(self.sys_version) < 5.4:
                supported = False
        elif self.os == 'Darwin':
            supported = True
        elif self.distname == 'ubuntu':
            if float(self.sys_version) < 10.10:
                supported = False
        elif self.distname == 'debian':
            if float(self.sys_version) < 6.0:
                supported = False
        else:
            supported = False
        return supported

    def handle_git(self):
        success = True
        print('* Install GIT ...', end='')
        try:
            if self.pm:
                packages = resolve_package_names(self.pm, ['git'])
                success, output = self.pm.install(packages)
            else:
                if self.distname in ('centos', 'redhat'):
                    self._run('yum install -y git')
                elif self.distname in ('ubuntu', 'debian'):
                    self._run('apt-get -y install git')
            print('[ %s ]' % (OK if success else FAILED))
        except Exception as e:
            success = False
            print('[ %s ]' % FAILED)
        return success

    def handle_dependent(self):
        success = True
        print('* Install Dependent Software...', end='')
        try:
            if self.pm:
                packages = resolve_package_names(self.pm, ['epel-release', 'wget', 'net-tools', 'vim', 'psmisc', 'rsync', 'libxslt-devel', 'GeoIP', 'GeoIP-devel', 'gd', 'gd-devel'])
                success, output = self.pm.install(packages)
            else:
                if self.distname in ('centos', 'redhat'):
                    self._run('yum install -y -q epel-release')
                    self._run('yum install -y -q wget net-tools vim psmisc rsync libxslt-devel GeoIP GeoIP-devel gd gd-devel')
                elif self.distname in ('ubuntu', 'debian'):
                    self._run('apt-get -y install wget net-tools vim psmisc rsync libxslt-dev geoip-bin libgeoip-dev libgd-dev')
            print('[ %s ]' % (OK if success else FAILED))
        except Exception as e:
            success = False
            print('[ %s ]' % FAILED)
        return success

    def handle_python(self):
        print('* Current Python Version is [%s.%s] ...' % (sys.version_info[:2][0], sys.version_info[:2][1]), end='')
        if sys.version_info[:2] >= (3, 7):
            print('[ %s ]' % OK)
            return True
        else:
            print('[ %s ]' % FAILED)
            print('* Installing Python 3 ...', end='')
            try:
                if self.pm:
                    packages = resolve_package_names(self.pm, ['python3'])
                    success, output = self.pm.install(packages)
                else:
                    if self.distname in ('centos', 'redhat'):
                        self._run('yum -y install python3')
                    elif self.distname in ('ubuntu', 'debian'):
                        self._run('apt-get -y install python3')
                print('[ %s ]' % OK)
            except Exception as e:
                print('[ %s ]' % FAILED)
            return True

    def install_pip_package(self):
        print('* Installing InPanel via pip...')
        self._run('pip3 install -e .', shell=True)
        print('[ %s ]' % OK)

    def install_source_package(self):
        print('* Installing InPanel from source...')
        if Path(self.initd_script).exists():
            self._run('%s stop' % self.initd_script)
        if Path(self.systemd_service).exists():
            self._run('systemctl stop inpanel')

        if self.installpath:
            self._run('rm -rf %s' % self.installpath)
        print('')
        print('Repository   : %s' % self.repository)
        print('Branch       : %s' % self.branch)
        print('Install path : %s' % self.installpath)
        print('')
        self._run('git clone -b %s %s %s' % (self.branch, self.repository, self.installpath))
        self._run('pip3 install -e %s' % self.installpath, shell=True)
        print('[ %s ]' % OK)

    def handle_inpanel(self):
        print('* Installing InPanel')
        if self.install_mode == 'source':
            self.install_source_package()
        else:
            self.install_pip_package()

    def install_systemd_service(self):
        print('* Installing systemd service...', end='')
        service_content = '''[Unit]
Description=InPanel Control Panel
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/inpanel run
ExecStop=/usr/bin/inpanel stop
ExecReload=/usr/bin/inpanel reload
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
'''
        with open(self.systemd_service, 'w') as f:
            f.write(service_content)
        self._run('systemctl daemon-reload')
        self._run('systemctl enable inpanel')
        print('[ %s ]' % OK)

    def install_initd_service(self):
        print('* Installing init.d service...', end='')
        initd_content = '''#!/bin/bash
# chkconfig: 2345 99 01
# description: InPanel Control Panel

PROG="inpanel"
PROG_PATH="/usr/bin/inpanel"

case "$1" in
    start|stop|status|restart|reload)
        $PROG_PATH $1
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|reload}"
        exit 1
        ;;
esac

exit 0
'''
        with open(self.initd_script, 'w') as f:
            f.write(initd_content)
        self._run('chmod +x %s' % self.initd_script)
        if self.distname in ('centos', 'redhat'):
            self._run('chkconfig --add inpanel')
            self._run('chkconfig inpanel on')
        print('[ %s ]' % OK)

    def install_service(self):
        if Path('/etc/systemd/system').exists():
            self.install_systemd_service()
        else:
            self.install_initd_service()

    def handle_intranet(self):
        if Path('/etc/init.d/intranet').exists():
            print('* Found Intranet')
            self._run('/etc/init.d/intranet stop')
            self._run('rm -rf /etc/init.d/intranet')
            self._run('rm -rf /usr/local/intranet')
            print('* Intranet has been deleted')

    def config_firewall(self):
        print('* Config firewall...'),
        if self.distname in ('centos', 'redhat'):
            if float(self.sys_version) < 7 and Path('/etc/init.d/iptables').exists():
                self._run('iptables -A INPUT -m state --state NEW -p tcp --dport %s -j ACCEPT' % self.listen_port)
                self._run('iptables -A OUTPUT -m state --state NEW -p tcp --sport %s -j ACCEPT' % self.listen_port)
                self._run('service iptables save')
                self._run('/etc/init.d/iptables restart')
                print('[ %s ]' % OK)
            elif Path('/etc/firewalld/firewalld.conf').exists():
                self._run('firewall-cmd --permanent --zone=public --add-port=%s/tcp' % self.listen_port)
                self._run('systemctl restart firewalld.service')
                print('[ %s ]' % OK)
            else:
                print('Not Installed, No configuration required.')
        elif self.distname in ('ubuntu', 'debian'):
            if Path('/usr/sbin/ufw').exists():
                self._run('ufw allow %s/tcp' % self.listen_port)
                print('[ %s ]' % OK)
            else:
                print('Not Installed, No configuration required.')

    def config_account(self):
        if self.username == 'admin' or not self.username:
            self.username = self.input('Admin Username [default: admin]: ').strip()
        if self.password == 'admin' or not self.password:
            self.password = self.input('Admin Password [default: admin]: ').strip()
        if len(self.username) == 0:
            self.username = 'admin'
        if len(self.password) == 0:
            self.password = 'admin'
        self._run('inpanel config set auth username "%s"' % self.username, shell=True)
        self._run('inpanel config set auth password "%s"' % self.password, shell=True)
        print('* Username and password set successfully!')

    def detect_ip(self):
        ip = request.urlopen('http://ip.42.pl/raw').readline()
        return ip.decode('utf-8').strip()

    def config_port(self):
        if self.listen_port == 14433 or not str(self.listen_port).isdigit() or int(self.listen_port) < 5000:
            port = self.input('InPanel Port [default: 14433, minimum: 5000]: ').strip()
            if port and port.isdigit() and int(port) >= 5000:
                self.listen_port = int(port)
        self._run('inpanel config set server port "%s"' % self.listen_port, shell=True)
        print('* InPanel will work on port "%s"' % self.listen_port)

    def handle_vpsmate(self):
        v_script = '/etc/init.d/vpsmate'
        if not Path(v_script).exists():
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
            self._run('inpanel config set server port "%s"' % self.listen_port, shell=True)
            print('* InPanel will work on port %s' % self.listen_port)

    def start_service(self):
        print('* Starting InPanel...', end='')
        if Path('/etc/systemd/system').exists():
            self._run('systemctl start inpanel')
        else:
            self._run('%s start' % self.initd_script)
        print('[ %s ]' % OK)

    def install(self):
        self.handle_options()
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
        if self.install_mode == 'source':
            self.handle_git()
        self.handle_intranet()
        self.handle_inpanel()
        self.install_service()
        self.handle_vpsmate()
        self.config_account()
        self.config_port()
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
        print('Username is: %s' % self.username)
        print('Password is: %s' % self.password)
        print('\033[5;32mWish you a happy life !\033[0m')
        print('')
        print('')


if __name__ == '__main__':
    install = Install()
    install.install()