# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for InPanel operations for remote server.'''


import base64
import os
import shlex

import lib.pxssh as pxssh


def inpanel_install(ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None, inpanel_ip=None, inpanel_port=None):
    '''Install InPanel on a remote server.'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('rm -f install.py')
        s.prompt()
        s.sendline('wget https://raw.githubusercontent.com/inpanel/inpanel/master/install.py')
        s.prompt()
        s.sendline('python install.py')
        s.expect('INSTALL COMPLETED!')
        s.sendcontrol('c')  # don't set username and password
        s.prompt()
        s.sendline('rm -f install.py')
        s.prompt()
        s.sendline('/usr/local/inpanel/config.py loginlock on')
        s.prompt()
        if accesskey != None:
            s.sendline('/usr/local/inpanel/config.py accesskey %s' % accesskey)
            s.prompt()
            s.sendline('/usr/local/inpanel/config.py accesskeyenable on')
            s.prompt()
        if inpanel_ip != None:
            s.sendline('/usr/local/inpanel/config.py ip %s' % inpanel_ip)
            s.prompt()
        if inpanel_port != None:
            s.sendline('/usr/local/inpanel/config.py port %s' % inpanel_port)
            s.prompt()
        s.sendline('service inpanel restart')
        s.prompt()
        s.logout()
        return True
    except pxssh.ExceptionPxssh:
        return False


def inpanel_uninstall(ssh_ip, ssh_port, ssh_user, ssh_password):
    '''Uninstall InPanel on a remote server.'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('service inpanel stop')
        s.prompt()
        s.sendline('rm -rf /usr/local/inpanel /etc/init.d/inpanel')
        s.prompt()
        s.logout()
        return True
    except pxssh.ExceptionPxssh:
        return False


def inpanel_config(ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None, accesskeyenable=None, username=None, password=None, loginlock=None, inpanel_ip=None, inpanel_port=None):
    '''Update config on remote server.'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('service inpanel stop')
        s.prompt()
        if accesskey != None:
            s.sendline('/usr/local/inpanel/config.py accesskey %s' % accesskey)
            s.prompt()
        if accesskeyenable != None:
            s.sendline('/usr/local/inpanel/config.py accesskeyenable %s' % (accesskeyenable and 'on' or 'off'))
            s.prompt()
        if username != None:
            s.sendline('/usr/local/inpanel/config.py username %s' % username)
            s.prompt()
        if password != None:
            s.sendline('/usr/local/inpanel/config.py password %s' % password)
            s.prompt()
        if loginlock != None:
            s.sendline('/usr/local/inpanel/config.py loginlock %s' % (loginlock and 'on' or 'off'))
            s.prompt()
        if inpanel_ip != None:
            s.sendline('/usr/local/inpanel/config.py ip %s' % inpanel_ip)
            s.prompt()
        if inpanel_port != None:
            s.sendline('/usr/local/inpanel/config.py port %s' % inpanel_port)
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
