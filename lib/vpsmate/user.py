#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

"""Package for user management.
"""

import os
if __name__ == '__main__':
    import sys
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import pexpect
import shlex
import time
import pwd
import grp
import subprocess
from utils import b2h, ftime


def listuser(fullinfo=True):
    if fullinfo:
        # get lock status from /etc/shadow
        locks = {}
        with open('/etc/shadow') as f:
            for line in f:
                fields = line.split(':', 2)
                locks[fields[0]] = fields[1].startswith('!')
        users = pwd.getpwall()
        for i, user in enumerate(users):
            users[i] = dict((name, getattr(user, name))
                            for name in dir(user)
                            if not name.startswith('__'))
            try:
                gname = grp.getgrgid(user.pw_gid).gr_name
            except:
                gname = ''
            users[i]['pw_gname'] = gname
            users[i]['lock'] = locks[user.pw_name]
    else:
        users = [pw.pw_name for pw in pwd.getpwall()]
    return users


def passwd(username, password):
    try:
        cmd = shlex.split('passwd \'%s\'' % username)
    except:
        return False
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['New password', 'Unknown user name'])
    if i == 1:
        if child.isalive(): child.wait()
        return False
    child.sendline(password)
    child.expect('Retype new password')
    child.sendline(password)
    i = child.expect(['updated successfully', pexpect.EOF])
    if child.isalive(): child.wait()
    return i == 0


def useradd(username, options):
    # command like: useradd -c 'New User' -g newgroup -s /bin/bash -m newuser
    cmd = ['useradd']
    if options.has_key('pw_gname') and options['pw_gname']:
        cmd.extend(['-g', options['pw_gname']])
    if options.has_key('pw_gecos'):
        cmd.extend(['-c', options['pw_gecos']])
    if options.has_key('pw_shell'):
        cmd.extend(['-s', options['pw_shell']])
    if options.has_key('createhome') and options['createhome']:
        cmd.append('-m')
    else:
        cmd.append('-M')
    cmd.append(username)
    p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    if p.wait() != 0: return False
    
    # check if need to lock/unlock the new account
    if options.has_key('lock') and options['lock']:
        if not usermod(username, {'lock': options['lock']}): return False

    # check if need to set passwd
    if options.has_key('pw_passwd'):
        if not passwd(username, options['pw_passwd']): return False
    
    return True


def usermod(username, options):
    user = pwd.getpwnam(username)
    # command like: usermod -c 'I am root' -g root -d /root/ -s /bin/bash -U root
    cmd = ['usermod']
    if options.has_key('pw_gname'):
        cmd.extend(['-g', options['pw_gname']])
    if options.has_key('pw_gecos') and options['pw_gecos'] != user.pw_gecos:
        cmd.extend(['-c', options['pw_gecos']])
    if options.has_key('pw_dir') and options['pw_dir'] != user.pw_dir:
        cmd.extend(['-d', options['pw_dir']])
    if options.has_key('pw_shell') and options['pw_shell'] != user.pw_shell:
        cmd.extend(['-s', options['pw_shell']])
    if options.has_key('lock') and options['lock']:
        cmd.append('-L')
    else:
        cmd.append('-U')
    cmd.append(username)
    if len(cmd) > 2:
        p = subprocess.Popen(cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p.stdout.read()
        msg = p.stderr.read()
        if p.wait() != 0:
            if not 'no changes' in msg:
                return False

    # check if need to change passwd
    if options.has_key('pw_passwd'):
        if not passwd(username, options['pw_passwd']): return False

    return True
        

def userdel(username):
    p = subprocess.Popen(['userdel', username],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def listgroup(fullinfo=True):
    if fullinfo:
        groups = grp.getgrall()
        for i, group in enumerate(groups):
            groups[i] = dict((name, getattr(group, name))
                            for name in dir(group)
                            if not name.startswith('__'))
    else:
        groups = [gr.gr_name for gr in grp.getgrall()]
    return groups


def groupadd(groupname):
    p = subprocess.Popen(['groupadd', groupname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupmod(groupname, newgroupname):
    p = subprocess.Popen(['groupmod', '-n', newgroupname, groupname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupdel(groupname):
    p = subprocess.Popen(['groupdel', groupname],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupmems(groupname, option, mem):
    cmd = ['groupmems', '-g', groupname]
    if option == 'add':
        cmd.extend(['-a', mem])
    elif option == 'del':
        cmd.extend(['-d', mem])
    p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0
