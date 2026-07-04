# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Module for system user management.'''

import grp
import pwd
import shlex
import subprocess
import sys

import pexpect

from base import kernel_name

def listuser(fullinfo=True):
    if not fullinfo:
        return [pw.pw_name for pw in pwd.getpwall()]

    locks = {}
    if kernel_name == 'Linux':
        # get lock status from /etc/shadow
        with open('/etc/shadow', encoding='utf-8') as f:
            for line in f:
                fields = line.split(':', 2)
                locks[fields[0]] = fields[1].startswith('!')

    users = pwd.getpwall()
    for i, user in enumerate(users):
        users[i] = dict((name, getattr(user, name))
                        for name in dir(user)
                        if not name.startswith('__')
                        and name not in ('count', 'index'))

        try:
            gname = grp.getgrgid(user.pw_gid).gr_name
        except:
            gname = ''

        users[i]['pw_gname'] = gname
        if user.pw_name in locks:
            users[i]['lock'] = locks[user.pw_name]
        else:
            users[i]['lock'] = False
    return users

def passwd(username, password):
    try:
        cmd = shlex.split('passwd \'%s\'' % username)
    except:
        return False
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['New password', 'Unknown user name'])
    if i == 1:
        if child.isalive():
            child.wait()
        return False
    child.sendline(password)
    child.expect('Retype new password')
    child.sendline(password)
    i = child.expect(['updated successfully', pexpect.EOF])
    if child.isalive():
        child.wait()
    return i == 0


def useradd(username, options):
    # command like: useradd -c 'New User' -g newgroup -s /bin/bash -m newuser
    cmd = ['useradd']
    if 'pw_gname' in options and options['pw_gname']:
        cmd.extend(['-g', options['pw_gname']])
    if 'pw_gecos' in options:
        cmd.extend(['-c', options['pw_gecos']])
    if 'pw_shell' in options:
        cmd.extend(['-s', options['pw_shell']])
    if 'createhome' in options and options['createhome']:
        cmd.append('-m')
    else:
        cmd.append('-M')
    cmd.append(username)
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
    p.stdout.read()
    p.stderr.read()
    if p.wait() != 0:
        return False

    # check if need to lock/unlock the new account
    if 'lock' in options and options['lock']:
        if not usermod(username, {'lock': options['lock']}):
            return False

    # check if need to set passwd
    if 'pw_passwd' in options:
        if not passwd(username, options['pw_passwd']):
            return False

    return True


def usermod(username, options):
    user = pwd.getpwnam(username)
    # command like: usermod -c 'I am root' -g root -d /root/ -s /bin/bash -U root
    cmd = ['usermod']
    if 'pw_gname' in options:
        cmd.extend(['-g', options['pw_gname']])
    if 'pw_gecos' in options and options['pw_gecos'] != user.pw_gecos:
        cmd.extend(['-c', options['pw_gecos']])
    if 'pw_dir' in options and options['pw_dir'] != user.pw_dir:
        cmd.extend(['-d', options['pw_dir']])
    if 'pw_shell' in options and options['pw_shell'] != user.pw_shell:
        cmd.extend(['-s', options['pw_shell']])
    if 'lock' in options and options['lock']:
        cmd.append('-L')
    else:
        cmd.append('-U')
    cmd.append(username)
    if len(cmd) > 2:
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        p.stdout.read()
        msg = p.stderr.read()
        if p.wait() != 0:
            if not 'no changes' in msg:
                return False

    # check if need to change passwd
    if 'pw_passwd' in options:
        if not passwd(username, options['pw_passwd']):
            return False

    return True


def userdel(username):
    p = subprocess.Popen(['userdel', username],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def listgroup(fullinfo=True):
    if fullinfo:
        groups = grp.getgrall()
        for i, group in enumerate(groups):
            groups[i] = dict((name, getattr(group, name))
                             for name in dir(group)
                             if not name.startswith('__')
                             and name not in ('count', 'index'))
    else:
        groups = [gr.gr_name for gr in grp.getgrall()]
    return groups


def groupadd(groupname):
    p = subprocess.Popen(['groupadd', groupname],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupmod(groupname, newgroupname):
    p = subprocess.Popen(['groupmod', '-n', newgroupname, groupname],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0


def groupdel(groupname):
    p = subprocess.Popen(['groupdel', groupname],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
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
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=True)
    p.stdout.read()
    p.stderr.read()
    return p.wait() == 0

def web_handler(context):
    action = context.get_argument('action', '')

    if action == 'listuser':
        fullinfo = context.get_argument('fullinfo', 'on')
        context.write({'code': 0, 'msg': '成功获取用户列表！', 'data': listuser(fullinfo=='on')})

    elif action == 'listgroup':
        fullinfo = context.get_argument('fullinfo', 'on')
        context.write({'code': 0, 'msg': '成功获取用户组列表！', 'data': listgroup(fullinfo=='on')})

    elif action in ('useradd', 'usermod'):
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许添加和修改用户！'})
            return

        pw_name = context.get_argument('pw_name', '')
        pw_gecos = context.get_argument('pw_gecos', '')
        pw_gname = context.get_argument('pw_gname', '')
        pw_dir = context.get_argument('pw_dir', '')
        pw_shell = context.get_argument('pw_shell', '')
        pw_passwd = context.get_argument('pw_passwd', '')
        pw_passwdc = context.get_argument('pw_passwdc', '')
        lock = context.get_argument('lock', '')
        lock = (lock == 'on') and True or False

        if pw_passwd != pw_passwdc:
            context.write({'code': -1, 'msg': '两次输入的密码不一致！'})
            return

        options = {
            'pw_gecos': pw_gecos,
            'pw_gname': pw_gname,
            'pw_dir': pw_dir,
            'pw_shell': pw_shell,
            'lock': lock
        }
        if len(pw_passwd) > 0:
            options['pw_passwd'] = pw_passwd

        if action == 'useradd':
            createhome = context.get_argument('createhome', '')
            createhome = (createhome == 'on') and True or False
            options['createhome'] = createhome
            if useradd(pw_name, options):
                context.write({'code': 0, 'msg': '用户添加成功！'})
            else:
                context.write({'code': -1, 'msg': '用户添加失败！'})
        elif action == 'usermod':
            if usermod(pw_name, options):
                context.write({'code': 0, 'msg': '用户修改成功！'})
            else:
                context.write({'code': -1, 'msg': '用户修改失败！'})

    elif action == 'userdel':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许删除用户！'})
            return

        pw_name = context.get_argument('pw_name', '')
        if userdel(pw_name):
            context.write({'code': 0, 'msg': '用户删除成功！'})
        else:
            context.write({'code': -1, 'msg': '用户删除失败！'})

    elif action in ('groupadd', 'groupmod', 'groupdel'):
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许操作用户组！'})
            return

        gr_name = context.get_argument('gr_name', '')
        gr_newname = context.get_argument('gr_newname', '')
        actionstr = {'groupadd': '添加', 'groupmod': '修改', 'groupdel': '删除'}

        if action == 'groupmod':
            rt = groupmod(gr_name, gr_newname)
        else:
            rt = getattr(sys.modules[__name__], action)(gr_name)
        if rt:
            context.write({'code': 0, 'msg': '用户组%s成功！' % actionstr[action]})
        else:
            context.write({'code': -1, 'msg': '用户组%s失败！' % actionstr[action]})

    elif action in ('groupmems_add', 'groupmems_del'):
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许操作用户组成员！'})
            return

        gr_name = context.get_argument('gr_name', '')
        mem = context.get_argument('mem', '')
        option = action.split('_')[1]
        optionstr = {'add': '添加', 'del': '删除'}
        if groupmems(gr_name, option, mem):
            context.write({'code': 0, 'msg': '用户组成员%s成功！' % optionstr[option]})
        else:
            context.write({'code': -1, 'msg': '用户组成员%s失败！' % optionstr[option]})
