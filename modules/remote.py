# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012, ECSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for InPanel operations for remote server.'''


import base64
import os
import shlex

import lib.pxssh as pxssh


def intranet_install(ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None, intranet_ip=None, intranet_port=None):
    '''Install InPanel on a remote server.'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('rm -f install.py')
        s.prompt()
        s.sendline('wget https://raw.githubusercontent.com/intranet-panel/intranet/master/install.py')
        s.prompt()
        s.sendline('python install.py')
        s.expect('INSTALL COMPLETED!')
        s.sendcontrol('c')  # don't set username and password
        s.prompt()
        s.sendline('rm -f install.py')
        s.prompt()
        s.sendline('/usr/local/intranet/config.py loginlock on')
        s.prompt()
        if accesskey != None:
            s.sendline('/usr/local/intranet/config.py accesskey %s' % accesskey)
            s.prompt()
            s.sendline('/usr/local/intranet/config.py accesskeyenable on')
            s.prompt()
        if intranet_ip != None:
            s.sendline('/usr/local/intranet/config.py ip %s' % intranet_ip)
            s.prompt()
        if intranet_port != None:
            s.sendline('/usr/local/intranet/config.py port %s' % intranet_port)
            s.prompt()
        s.sendline('service intranet restart')
        s.prompt()
        s.logout()
        return True
    except pxssh.ExceptionPxssh, e:
        return False


def intranet_uninstall(ssh_ip, ssh_port, ssh_user, ssh_password):
    '''Uninstall InPanel on a remote server.'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('service intranet stop')
        s.prompt()
        s.sendline('rm -rf /usr/local/intranet /etc/init.d/intranet')
        s.prompt()
        s.logout()
        return True
    except pxssh.ExceptionPxssh, e:
        return False


def intranet_config(ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None, accesskeyenable=None, username=None, password=None, loginlock=None, intranet_ip=None, intranet_port=None):
    '''Update config on remote server.'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('service intranet stop')
        s.prompt()
        if accesskey != None:
            s.sendline('/usr/local/intranet/config.py accesskey %s' % accesskey)
            s.prompt()
        if accesskeyenable != None:
            s.sendline('/usr/local/intranet/config.py accesskeyenable %s' % (accesskeyenable and 'on' or 'off'))
            s.prompt()
        if username != None:
            s.sendline('/usr/local/intranet/config.py username %s' % username)
            s.prompt()
        if password != None:
            s.sendline('/usr/local/intranet/config.py password %s' % password)
            s.prompt()
        if loginlock != None:
            s.sendline('/usr/local/intranet/config.py loginlock %s' % (loginlock and 'on' or 'off'))
            s.prompt()
        if intranet_ip != None:
            s.sendline('/usr/local/intranet/config.py ip %s' % intranet_ip)
            s.prompt()
        if intranet_port != None:
            s.sendline('/usr/local/intranet/config.py port %s' % intranet_port)
            s.prompt()
        s.logout()
        return True
    except:
        return False


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(install('42.121.98.82', '22', 'root', 'xx', '960BmT039ONbgV6NxGfeIQgOVQcRF7fHvthFPSmlq+c='))
    #pp.pprint(uninstall('42.121.98.82', '22', 'root', 'xx'))
    # pp.pprint(gen_accesskey())
