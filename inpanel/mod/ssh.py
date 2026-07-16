#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''SSH 管理模块'''

import os
import re
import shlex
from pathlib import Path

import pexpect

SSHCFG = '/etc/ssh/sshd_config'


def loadconfig(cfgfile=None, detail=False):
    """Read config file and parse config item to dict.
    """
    if not cfgfile:
        cfgfile = SSHCFG

    settings = {}
    with open(cfgfile, encoding='utf-8') as f:
        for line_i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith('# '):
                continue

            # detect if it's commented
            if line.startswith('#'):
                line = line.strip('#')
                commented = True
                if not detail:
                    continue
            else:
                commented = False

            fs = re.split(r'\s+', line, 1)
            if len(fs) != 2:
                continue

            item = fs[0].strip()
            value = fs[1].strip()

            if item in settings:
                if detail:
                    count = settings[item]['count']+1
                if not commented:
                    settings[item] = detail and {
                        'file': cfgfile,
                        'line': line_i,
                        'value': value,
                        'commented': commented,
                    } or value
            else:
                count = 1
                settings[item] = detail and {
                    'file': cfgfile,
                    'line': line_i,
                    'value': fs[1].strip(),
                    'commented': commented,
                } or value
            if detail:
                settings[item]['count'] = count

    return settings


def cfg_get(item, detail=False, config=None):
    """Get value of a config item.
    """
    if not config:
        config = loadconfig(detail=detail)
    if item in config:
        return config[item]
    else:
        return None


def cfg_set(item, value, commented=False, config=None):
    """Set value of a config item.
    """
    cfgfile = SSHCFG
    v = cfg_get(item, detail=True, config=config)

    if v:
        # detect if value change
        if v['commented'] == commented and v['value'] == value:
            return True

        # empty value should be commented
        if value == '':
            commented = True

        # replace item in line
        lines = []
        with open(v['file'], encoding='utf-8') as f:
            for line_i, line in enumerate(f):
                if line_i == v['line']:
                    if not v['commented']:
                        if commented:
                            if v['count'] > 1:
                                # delete this line, just ignore it
                                pass
                            else:
                                # comment this line
                                lines.append('#%s %s\n' % (item, value))
                        else:
                            lines.append('%s %s\n' % (item, value))
                    else:
                        if commented:
                            # do not allow change comment value
                            lines.append(line)
                            pass
                        else:
                            # append a new line after comment line
                            lines.append(line)
                            lines.append('%s %s\n' % (item, value))
                else:
                    lines.append(line)
        with open(v['file'], 'w', encoding='utf-8') as f:
            f.write(''.join(lines))
    else:
        # append to the end of file
        with open(inifile, 'a', encoding='utf-8') as f:
            f.write('\n%s%s = %s\n' % (commented and '#' or '', item, value))

    return True


def genkey(path, password=''):
    """Generate a ssh key pair.
    """
    cmd = shlex.split('ssh-keygen -t rsa')
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter file in which to save the key', pexpect.EOF])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    child.sendline(path)
    i = child.expect(['Overwrite', 'Enter passphrase', pexpect.EOF])
    if i == 0:
        child.sendline('y')
        i = child.expect(['Enter passphrase', pexpect.EOF])
        if i == 1:
            if child.isalive():
                child.wait()
            return False
    elif i == 2:
        if child.isalive():
            child.wait()
        return False

    child.sendline(password)
    i = child.expect(['Enter same passphrase', pexpect.EOF])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    child.sendline(password)
    child.expect(pexpect.EOF)

    if child.isalive():
        return child.wait() == 0
    return True


def chpasswd(path, oldpassword, newpassword):
    """Change password of a private key.
    """
    if len(newpassword) != 0 and not len(newpassword) > 4:
        return False

    cmd = shlex.split('ssh-keygen -p')
    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter file in which the key is', pexpect.EOF])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    child.sendline(path)
    i = child.expect(
        ['Enter old passphrase', 'Enter new passphrase', pexpect.EOF])
    if i == 0:
        child.sendline(oldpassword)
        i = child.expect(
            ['Enter new passphrase', 'Bad passphrase', pexpect.EOF])
        if i != 0:
            if child.isalive():
                child.wait()
            return False
    elif i == 2:
        if child.isalive():
            child.wait()
        return False

    child.sendline(newpassword)
    i = child.expect(['Enter same passphrase again', pexpect.EOF])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    child.sendline(newpassword)
    child.expect(pexpect.EOF)

    if child.isalive():
        return child.wait() == 0
    return True


def web_handler(context):
    action = context.get_argument('action', '')

    if action == 'getsettings':
        port = cfg_get('Port')
        enable_pwdauth = cfg_get('PasswordAuthentication') == 'yes'
        enable_pubkauth = cfg_get('PubkeyAuthentication') == 'yes'
        subsystem = cfg_get('Subsystem')
        enable_sftp = subsystem and 'sftp' in subsystem
        pubkey_path = '/root/.ssh/sshkey_inpanel.pub'
        prvkey_path = '/root/.ssh/sshkey_inpanel'
        context.write({'code': 0, 'msg': '获取 SSH 服务配置信息成功！', 'data': {
           'port': port,
           'enable_pwdauth': enable_pwdauth,
           'enable_pubkauth': enable_pubkauth,
           'enable_sftp': enable_sftp,
           'pubkey': Path(pubkey_path).is_file() and pubkey_path or '',
           'prvkey': Path(prvkey_path).is_file() and prvkey_path or '',
        }})

    elif action == 'savesettings':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许修改 SSH 服务设置！'})
            return

        port = context.get_argument('port', '')
        if port:
            cfg_set('Port', port)
        enable_pwdauth = context.get_argument('enable_pwdauth', '')
        if enable_pwdauth:
            cfg_set('PasswordAuthentication', enable_pwdauth=='on' and 'yes' or 'no')
        enable_pubkauth = context.get_argument('enable_pubkauth', '')
        if enable_pubkauth:
            if enable_pubkauth == 'on':
                pubkey_path = context.get_argument('pubkey', '')
                if not Path(pubkey_path).is_file():
                    context.write({'code': -1, 'msg': '公钥文件不存在！'})
                    return
            cfg_set('PubkeyAuthentication', enable_pubkauth=='on' and 'yes' or 'no')
            cfg_set('AuthorizedKeysFile', pubkey_path)

        enable_sftp = context.get_argument('enable_sftp', '')
        if enable_sftp:
            cfg_set('Subsystem', 'sftp /usr/libexec/openssh/sftp-server', enable_sftp!='on')
        context.write({'code': 0, 'msg': 'SSH 服务配置保存成功！'})


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    # pp.pprint(loadconfig())
    #print cfg_get('Port')
    #print cfg_get('Subsystem', detail=True)
    #print cfg_set('Protocol', '2', commented=False)
    #print cfg_set('Subsystem', 'sftp\t/usr/libexec/openssh/sftp-server', commented=True)

    #print genkey('/root/.ssh/sshkey_inpanel')
    #print chpasswd('/root/.ssh/sshkey_inpanel', '', 'aaaaaa')
