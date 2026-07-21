# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''InPanel 远程服务器操作模块

提供远程安装、卸载、配置 InPanel 的底层 SSH 操作函数，
以及供 web.py dispatch 调用的异步任务函数（remote_* 命名）。
'''


from ..lib import pxssh
from . import shell


# ------------------------------------------------------------------
# 底层 SSH 操作（同步，由异步任务函数包装调用）
# ------------------------------------------------------------------

def _inpanel_install(ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None, inpanel_ip=None, inpanel_port=None):
    '''在远程服务器上安装 InPanel。'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('rm -f install.py')
        s.prompt()
        s.sendline('wget https://raw.githubusercontent.com/inpanel/inpanel/master/install.py')
        s.prompt()
        s.sendline('python install.py')
        s.expect('INSTALL COMPLETED!')
        s.sendcontrol('c')  # 不设置用户名和密码
        s.prompt()
        s.sendline('rm -f install.py')
        s.prompt()
        s.sendline('/usr/bin/inpanel config loginlock on')
        s.prompt()
        if accesskey != None:
            s.sendline('/usr/bin/inpanel config accesskey %s' % accesskey)
            s.prompt()
            s.sendline('/usr/bin/inpanel config accesskeyenable on')
            s.prompt()
        if inpanel_ip != None:
            s.sendline('/usr/bin/inpanel config ip %s' % inpanel_ip)
            s.prompt()
        if inpanel_port != None:
            s.sendline('/usr/bin/inpanel config port %s' % inpanel_port)
            s.prompt()
        s.sendline('service inpanel restart')
        s.prompt()
        s.logout()
        return True
    except pxssh.ExceptionPxssh:
        return False


def _inpanel_uninstall(ssh_ip, ssh_port, ssh_user, ssh_password):
    '''在远程服务器上卸载 InPanel。'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('service inpanel stop')
        s.prompt()
        s.sendline('rm -rf /usr/bin/inpanel /etc/init.d/inpanel')
        s.prompt()
        s.logout()
        return True
    except pxssh.ExceptionPxssh:
        return False


def _inpanel_config(ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None, accesskeyenable=None, username=None, password=None, loginlock=None, inpanel_ip=None, inpanel_port=None):
    '''更新远程服务器上的配置。'''
    try:
        s = pxssh.pxssh()
        s.login(ssh_ip, ssh_user, ssh_password, port=ssh_port)
        s.sendline('service inpanel stop')
        s.prompt()
        if accesskey != None:
            s.sendline('/usr/bin/inpanel config accesskey %s' % accesskey)
            s.prompt()
        if accesskeyenable != None:
            s.sendline('/usr/bin/inpanel config accesskeyenable %s' % (accesskeyenable and 'on' or 'off'))
            s.prompt()
        if username != None:
            s.sendline('/usr/bin/inpanel config username %s' % username)
            s.prompt()
        if password != None:
            s.sendline('/usr/bin/inpanel config password %s' % password)
            s.prompt()
        if loginlock != None:
            s.sendline('/usr/bin/inpanel config loginlock %s' % (loginlock and 'on' or 'off'))
            s.prompt()
        if inpanel_ip != None:
            s.sendline('/usr/bin/inpanel config ip %s' % inpanel_ip)
            s.prompt()
        if inpanel_port != None:
            s.sendline('/usr/bin/inpanel config port %s' % inpanel_port)
            s.prompt()
        s.logout()
        return True
    except:
        return False


# ------------------------------------------------------------------
# 异步任务函数（由 web.py 的 _dispatch_task 调用）
# 命名规则：remote_<method>
# ------------------------------------------------------------------

async def remote_install(tm, ssh_ip, ssh_port, ssh_user, ssh_password,
                         instance_name='', accessnet='', accessport=None, accesskey=None):
    """远程安装 InPanel（异步任务）"""
    jobname = f'remote.install_{ssh_ip}'
    if not tm._start_job(jobname):
        return

    tm._update_job(jobname, 2, f'正在将 InPanel 安装到 {ssh_ip}...')

    result = await shell.async_task(_inpanel_install, ssh_ip, ssh_port, ssh_user, ssh_password,
                                    accesskey=accesskey, inpanel_port=accessport)
    if result == True:
        code = 0
        msg = 'InPanel 安装成功！'
        if instance_name:
            tm.config.set('inpanel', instance_name, f'{accesskey}|{accessnet}|{accessport}')
    else:
        code = -1
        msg = 'InPanel 安装过程中发生错误！'

    tm._finish_job(jobname, code, msg)


async def remote_uninstall(tm, ssh_ip, ssh_port, ssh_user, ssh_password, instance_name=''):
    """远程卸载 InPanel（异步任务）"""
    jobname = f'remote.uninstall_{ssh_ip}'
    if not tm._start_job(jobname):
        return

    tm._update_job(jobname, 2, f'正在卸载 {ssh_ip} 上的 InPanel...')
    result = await shell.async_task(_inpanel_uninstall, ssh_ip, ssh_port, ssh_user, ssh_password)
    if result == True:
        code = 0
        msg = 'InPanel 卸载成功！'
        if instance_name:
            try:
                tm.config.remove_option('inpanel', instance_name)
            except:
                pass
    else:
        code = -1
        msg = 'InPanel 卸载过程中发生错误！'

    tm._finish_job(jobname, code, msg)


async def remote_config(tm, ssh_ip, ssh_port, ssh_user, ssh_password,
                        accesskey=None):
    """远程更新 InPanel 配置（异步任务）"""
    jobname = f'remote.config_{ssh_ip}'
    if not tm._start_job(jobname):
        return

    tm._update_job(jobname, 2, f'正在更新 {ssh_ip} 上的 InPanel 配置...')

    result = await shell.async_task(_inpanel_config, ssh_ip, ssh_port, ssh_user, ssh_password,
                                    accesskey=accesskey)
    if result == True:
        code = 0
        msg = 'InPanel 配置更新成功！'
    else:
        code = -1
        msg = 'InPanel 配置更新过程中发生错误！'

    tm._finish_job(jobname, code, msg)


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(install('42.121.98.82', '22', 'root', 'xx', '960BmT039ONbgV6NxGfeIQgOVQcRF7fHvthFPSmlq+c='))
    #pp.pprint(uninstall('42.121.98.82', '22', 'root', 'xx'))
    # pp.pprint(gen_accesskey())
