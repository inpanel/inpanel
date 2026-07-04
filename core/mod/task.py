# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Task Management."""

import time
from datetime import datetime
from functools import partial
from pathlib import Path
from shlex import quote
from subprocess import PIPE, Popen

import tornado.escape
import tornado.httpclient

import mod
import remote
from base import app_api, os_versint
from mod import disk


class TaskManager:
    jobs = {}
    locks = {}

    def __init__(self, settings, config):
        self.settings = settings
        self.config = config

    def _lock_job(self, lockname):
        if lockname in self.locks:
            return False
        self.locks[lockname] = True
        return True

    def _unlock_job(self, lockname):
        if lockname not in self.locks:
            return False
        del self.locks[lockname]
        return True

    def _start_job(self, jobname):
        if jobname in self.jobs and self.jobs[jobname]['status'] == 'running':
            return False
        self.jobs[jobname] = {'status': 'running', 'msg': ''}
        return True

    def _update_job(self, jobname, code, msg):
        self.jobs[jobname]['code'] = code
        self.jobs[jobname]['msg'] = msg
        return True

    def _get_job(self, jobname):
        if jobname not in self.jobs:
            return {'status': 'none', 'code': -1, 'msg': ''}
        return self.jobs[jobname]

    def _finish_job(self, jobname, code, msg, data=None):
        self.jobs[jobname]['status'] = 'finish'
        self.jobs[jobname]['code'] = code
        self.jobs[jobname]['msg'] = msg
        if data:
            self.jobs[jobname]['data'] = data

    def _call(self, callback):
        tornado.ioloop.IOLoop.instance().add_callback(callback)

    async def update(self):
        if not self._start_job('update'):
            return

        root_path = self.settings['root_path']
        data_path = self.settings['data_path']

        if Path('%s/../.git' % root_path).exists():
            self._finish_job('update', 0, '升级成功！')
            return

        http_client = tornado.httpclient.AsyncHTTPClient()
        response = await http_client.fetch(app_api['latest'])
        if response.error:
            self._update_job('update', -1, '获取版本信息失败！')
            return
        versioninfo = tornado.escape.json_decode(response.body.decode('utf-8'))
        downloadurl = versioninfo['download']
        initscript = '%s/scripts/init.d/%s/inpanel' % (root_path, self.settings['os_name'])
        binscript = '%s/scripts/bin/inpanel' % root_path
        steps = [
            {
                'desc': '正在备份当前配置文件...',
                'cmd': '/bin/cp -f %s/config.ini /tmp/inpanel_config.ini' % data_path,
            }, {
                'desc': '正在下载安装包...',
                'cmd': 'wget -q "%s" -O %s/inpanel.tar.gz' % (downloadurl, data_path),
            }, {
                'desc': '正在创建解压目录...',
                'cmd': 'mkdir -p %s/inpanel' % data_path,
            }, {
                'desc': '正在解压安装包...',
                'cmd': 'tar zxmf %s/inpanel.tar.gz -C %s/inpanel --strip-components 1' % (data_path, data_path),
            }, {
                'desc': '正在删除旧版本...',
                'cmd': 'find %s -mindepth 1 -maxdepth 1 -path %s -prune -o -exec rm -rf {} \\\\;' % (root_path, data_path),
            }, {
                'desc': '正在复制新版本...',
                'cmd': 'find %s/inpanel -mindepth 1 -maxdepth 1 -exec cp -r {} %s \\\\;' % (data_path, root_path),
            }, {
                'desc': '正在删除旧的服务脚本...',
                'cmd': 'rm -f /etc/init.d/inpanel /usr/local/bin/inpanel',
            }, {
                'desc': '正在安装新的服务脚本...',
                'cmd': 'ln -s %s /etc/init.d/inpanel' % initscript
            }, {
                'desc': '正在安装新的命令脚本...',
                'cmd': 'ln -s %s /usr/local/bin/inpanel' % binscript
            }, {
                'desc': '正在更改脚本权限...',
                'cmd': 'chmod +x /usr/local/bin/inpanel /etc/init.d/inpanel %s/config.py %s/server.py' % (root_path, root_path),
            }, {
                'desc': '正在删除安装临时文件...',
                'cmd': 'rm -rf %s/inpanel %s/inpanel.tar.gz' % (data_path, data_path)
            }, {
                'desc': '正在恢复旧的配置文件...',
                'cmd': '/bin/cp -f /tmp/inpanel_config.ini %s/config.ini' % data_path
            }, {
                'desc': '正在删除旧的配置文件...',
                'cmd': 'rm -f /tmp/inpanel_config.ini'
            }
        ]
        for step in steps:
            desc = step['desc']
            cmd = step['cmd']
            self._update_job('update', 2, desc)
            result, output = await mod.shell.async_command(cmd)
            if result != 0:
                self._update_job('update', -1, desc + '失败！')
                break

        if result == 0:
            code = 0
            msg = '升级成功！请刷新页面重新登录。'
        else:
            code = -1
            msg = '升级失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job('update', code, msg)

    async def service(self, action, service, name):
        jobname = f'service_{action}_{service}'
        if not self._start_job(jobname):
            return

        action_str = {'start': '启动', 'stop': '停止', 'restart': '重启'}
        self._update_job(jobname, 2, f'正在{action_str[action]} {name} 服务...')

        if action == 'start' and service in ('sendmail',) and self.settings['os_name'] in ('redhat', 'centos') and os_versint == 5:
            hostname = mod.server.ServerInfo.hostname()
            hostname_found = False
            dot_found = False
            lines = []
            with open('/etc/hosts', encoding='utf-8') as f:
                for line in f:
                    if not line.startswith('#') and not hostname_found:
                        fields = line.strip().split()
                        if hostname in fields:
                            hostname_found = True
                            dot_found = any(field for field in fields[1:] if '.' in field)
                            if not dot_found:
                                line = '%s %s.localdomain\n' % (line.strip(), hostname)
                    lines.append(line)
            if not dot_found:
                with open('/etc/hosts', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
        if os_versint < 7:
            cmd = f'/etc/init.d/{service} {action}'
        else:
            cmd = f'/bin/systemctl {action} {service}.service'
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = f'{name} 服务{action_str[action]}成功！'
        else:
            code = -1
            txt = output.strip().replace('\n', '<br>')
            msg = f'{name} 服务{action_str[action]}失败！<p style="margin:10px">{txt}</p>'

        self._finish_job(jobname, code, msg)

    async def datetime(self, newdatetime):
        jobname = 'datetime'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在设置系统时间...')

        cmd = 'date -s %s' % (quote(newdatetime),)
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '系统时间设置成功！'
        else:
            code = -1
            txt = output.strip().replace('\n', '<br>')
            msg = f'系统时间设置失败！<p style="margin:10px">{txt}</p>'

        self._finish_job(jobname, code, msg)

    async def ntpdate(self, server):
        jobname = 'ntpdate_%s' % server
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在从 %s 同步时间...' % server)
        cmd = 'ntpdate -u %s' % server
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            offset = output.split(' offset ')[-1].split()[0]
            msg = '同步时间成功！（时间偏差 %s 秒）' % str(offset)
        else:
            code = -1
            if 'no server suitable' in output:
                msg = '同步时间失败！没有找到合适同步服务器。'
            elif 'no servers can be used' in output:
                msg = '同步时间失败！没有找到同步服务器的地址'
            else:
                msg = '同步时间失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg)

    async def swapon(self, action, devname):
        jobname = f'swapon_{action}_{devname}'
        if not self._start_job(jobname):
            return

        action_str = {'on': '启用', 'off': '停用'}
        self._update_job(jobname, 2, f'正在{action_str[action]} {devname}...')

        if action == 'on':
            cmd = f'swapon /dev/{devname}'
        else:
            cmd = f'swapoff /dev/{devname}'

        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = f'{action_str[action]} {devname} 成功！'
        else:
            code = -1
            txt = output.strip().replace('\n', '<br>')
            msg = f'{action_str[action]} {devname} 失败！<p style="margin:10px">{txt}</p>'

        self._finish_job(jobname, code, msg)

    async def mount(self, action, devname, mountpoint, fstype):
        jobname = 'mount_%s_%s' % (action, devname)
        if not self._start_job(jobname):
            return

        action_str = {'mount': '挂载', 'umount': '卸载'}
        self._update_job(jobname, 2, '正在%s %s 到 %s...' % (action_str[action], devname, mountpoint))

        if action == 'mount':
            disk.fstab(devname, {
                'devname': devname,
                'mount': mountpoint,
                'fstype': fstype,
            })
            cmd = 'mount -t %s /dev/%s %s' % (fstype, devname, mountpoint)
        else:
            cmd = 'umount /dev/%s' % (devname)

        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '%s %s 成功！' % (action_str[action], devname)
        else:
            code = -1
            msg = '%s %s 失败！<p style="margin:10px">%s</p>' % (action_str[action], devname, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def format(self, devname, fstype):
        jobname = 'format_%s' % devname
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在格式化 %s，可能需要较长时间，请耐心等候...' % devname)

        if fstype in ('ext2', 'ext3', 'ext4'):
            cmd = 'mkfs.%s -F /dev/%s' % (fstype, devname)
        elif fstype in ('xfs', 'reiserfs', 'btrfs'):
            cmd = 'mkfs.%s -f /dev/%s' % (fstype, devname)
        elif fstype == 'swap':
            cmd = 'mkswap -f /dev/%s' % devname
        else:
            cmd = 'mkfs.%s /dev/%s' % (fstype, devname)
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '%s 格式化成功！' % devname
        else:
            code = -1
            msg = '%s 格式化失败！<p style="margin:10px">%s</p>' % (devname, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def yum_repolist(self):
        jobname = 'yum_repolist'
        if not self._start_job(jobname):
            return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, '已有一个YUM进程在运行，读取软件源列表失败。')
            return

        self._update_job(jobname, 2, '正在获取软件源列表...')

        cmd = 'yum repolist --disableplugin=fastestmirror'
        result, output = await mod.shell.async_command(cmd)
        data = []
        if result == 0:
            code = 0
            msg = '获取软件源列表成功！'
            lines = output.split('\n')
            for line in lines:
                if not line:
                    continue
                repo = line.split()[0]
                if repo in mod.yum.yum_repolist:
                    data.append(repo)
        else:
            code = -1
            msg = '获取软件源列表失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg, data)
        self._unlock_job('yum')

    async def yum_installrepo(self, repo):
        jobname = 'yum_installrepo_%s' % repo
        if not self._start_job(jobname):
            return

        if repo not in mod.yum.yum_repolist:
            self._finish_job(jobname, -1, '不可识别的软件源！')
            self._unlock_job('yum')
            return

        self._update_job(jobname, 2, '正在安装软件源 %s...' % repo)

        arch = self.settings['arch']

        cmds = []
        if repo == 'base':
            for cmd in mod.yum.get_repo_release(os_versint, self.settings['os_name'], self.settings['arch']):
                cmds.append(cmd)

        elif repo in ('epel', 'CentALT'):
            for cmd in mod.yum.get_repo_epel(os_versint, self.settings['os_name'], self.settings['arch']):
                cmds.append(cmd)

        elif repo == 'ius':
            result, output = await mod.shell.async_command(mod.yum.yum_repoinstallcmds['ius'])
            if result != 0:
                error = True

        elif repo == '10gen':
            with open('/etc/mod.yum.repos.d/10gen.repo', 'w', encoding='utf-8') as f:
                f.write(mod.yum.yum_repostr['10gen'][self.settings['arch']])

        elif repo == 'mariadb':
            with open('/etc/mod.yum.repos.d/mariadb.repo', 'w', encoding='utf-8') as f:
                f.write(mod.yum.yum_repostr['mariadb'][self.settings['arch']])

        elif repo == 'atomic':
            result, output = await mod.shell.async_command(mod.yum.yum_repoinstallcmds['atomic'])
            if result != 0:
                error = True

        error = False
        for cmd in cmds:
            result, output = await mod.shell.async_command(cmd)
            if result != 0 and not 'already installed' in output:
                error = True
                break

        if repo == 'CentALT':
            repofile = '/etc/mod.yum.repos.d/centalt.repo'
            if Path(repofile).is_file():
                lines = []
                baseurl_found = False
                with open(repofile, encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('baseurl='):
                            baseurl_found = True
                            line = '#%s' % line
                            lines.append(line)
                        lines.append(line)
                if baseurl_found:
                    with open(repofile, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

        if not error:
            code = 0
            msg = '软件源 %s 安装成功！' % repo
        else:
            code = -1
            msg = '软件源 %s 安装失败！<p style="margin:10px">%s</p>' % (repo, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def yum_info(self, pkg, repo, option):
        jobname = 'yum_info_%s' % pkg
        if not self._start_job(jobname):
            return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, '已有一个YUM进程在运行，读取软件包信息失败。')
            return

        self._update_job(jobname, 2, '正在获取软件版本信息...')

        if repo == '*':
            repo = ''
        arch = self.settings['arch']
        if pkg in mod.yum.yum_pkg_noarchitecture:
            arch = 'noarch'
        if option == 'install':
            cmds = ['yum info %s %s.%s --showduplicates --disableplugin=fastestmirror'
                    % (repo, alias, arch) for alias in mod.yum.yum_pkg_alias[pkg]]
        else:
            cmds = ['yum info %s.%s --disableplugin=fastestmirror' % (pkg, arch)]

        data = []
        matched = False
        await mod.shell.async_command('LANG="en_US.UTF-8"')
        for cmd in cmds:
            result, output = await mod.shell.async_command(cmd)
            if result == 0:
                matched = True
                lines = output.split('\n')
                for line in lines:
                    if any(line.startswith(word)
                           for word in ('Name', 'Version', 'Release', 'Size', 'Repo', 'From repo', 'Summary', 'URL', 'License')):
                        fields = line.strip().split(':', 1)
                        if len(fields) != 2:
                            continue
                        field_name = fields[0].strip().lower().replace(' ', '_')
                        field_value = fields[1].strip()
                        if field_name == 'name':
                            data.append({})
                        if field_name == 'repo':
                            data[-1][field_name] = field_value.split('/')[0]
                        else:
                            data[-1][field_name] = field_value

        if matched:
            code = 0
            msg = '获取软件版本信息成功！'
            data = [pkg for pkg in data if pkg['repo'] in mod.yum.yum_repolist + ('installed',)]
            if option == 'update' and len(data) == 1:
                msg = '没有找到可用的新版本！'
        else:
            code = -1
            msg = '获取软件版本信息失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg, data)
        self._unlock_job('yum')

    async def yum_install(self, repo, pkg, version, release, ext):
        jobname = 'yum_install_%s_%s_%s_%s_%s' % (repo, pkg, ext, version, release)
        jobname = jobname.strip('_').replace('__', '_')
        if not self._start_job(jobname):
            return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, '已有一个YUM进程在运行，安装失败。')
            return

        if ext:
            self._update_job(jobname, 2, '正在下载并安装扩展包，请耐心等候...')
        else:
            self._update_job(jobname, 2, '正在下载并安装软件包，请耐心等候...')

        arch = self.settings['arch']
        if pkg in mod.yum.yum_pkg_noarchitecture:
            arch = 'noarch'

        if ext:
            if version:
                if release:
                    pkgs = ['%s-%s-%s.%s' % (ext, version, release, arch)]
                else:
                    pkgs = ['%s-%s.%s' % (ext, version, arch)]
            else:
                pkgs = ['%s.%s' % (ext, arch)]
        else:
            if version:
                if release:
                    pkgs = ['%s-%s-%s.%s' % (p, version, release, arch)
                            for p, pinfo in mod.yum.yum_pkg_relatives[pkg].items() if pinfo['default']]
                else:
                    pkgs = ['%s-%s.%s' % (p, version, arch)
                            for p, pinfo in mod.yum.yum_pkg_relatives[pkg].items() if pinfo['default']]
            else:
                pkgs = ['%s.%s' % (p, arch)
                        for p, pinfo in mod.yum.yum_pkg_relatives[pkg].items() if pinfo['default']]
        repos = [repo, ]
        if repo in ('CentALT', 'ius', 'atomic', '10gen', 'mariadb'):
            repos.extend(['base', 'updates', 'epel'])
        exclude_repos = [r for r in mod.yum.yum_repolist if r not in repos]

        endinstall = False
        hasconflict = False
        conflicts_backups = []
        while not endinstall:
            cmd = 'yum install -y %s --disablerepo=%s' % (' '.join(pkgs), ','.join(exclude_repos))
            result, output = await mod.shell.async_command(cmd)
            pkg_ext = ext and ext or pkg

            pkgstr = version and '%s v%s-%s' % (pkg_ext, version, release) or (pkg_ext)
            if result == 0:
                if hasconflict:
                    cmd = 'yum install -y %s' % (' '.join(conflicts_backups),)
                    result, output = await mod.shell.async_command(cmd)
                endinstall = True
                code = 0
                msg = '%s 安装成功！' % pkgstr
            else:
                clines = output.split('\n')
                for cline in clines:
                    if cline.startswith('Error:') and ' conflicts with ' in cline:
                        hasconflict = True
                        conflict_pkg = cline.split(' conflicts with ', 1)[1]
                        self._update_job(jobname, 2, '检测到软件冲突，正在卸载处理冲突...')
                        tcmd = 'yum erase -y %s' % conflict_pkg
                        result, output = await mod.shell.async_command(tcmd)
                        if result == 0:
                            lines = output.split('\n')
                            conflicts_backups = []
                            linestart = False
                            for line in lines:
                                if not linestart:
                                    if not line.startswith('Removing for dependencies:'):
                                        continue
                                    linestart = True
                                if not line.strip():
                                    break
                                fields = line.split()
                                conflicts_backups.append('%s-%s' % (fields[0], fields[2]))
                        else:
                            endinstall = True
                        break
                    elif 'conflicts between' in cline:
                        pass
                if not hasconflict:
                    endinstall = True
                if endinstall:
                    code = -1
                    msg = '%s 安装失败！<p style="margin:10px">%s</p>' % (pkgstr, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)
        self._unlock_job('yum')

    async def yum_uninstall(self, repo, pkg, version, release, ext):
        jobname = 'yum_uninstall_%s_%s_%s_%s' % (pkg, ext, version, release)
        jobname = jobname.strip('_').replace('__', '_')
        if not self._start_job(jobname):
            return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, '已有一个YUM进程在运行，卸载失败。')
            return

        if ext:
            self._update_job(jobname, 2, '正在卸载扩展包...')
        else:
            self._update_job(jobname, 2, '正在卸载软件包...')

        arch = self.settings['arch']
        if pkg in mod.yum.yum_pkg_noarchitecture:
            arch = 'noarch'

        if ext:
            pkgs = ['%s-%s-%s.%s' % (ext, version, release, arch)]
        else:
            pkgs = ['%s-%s-%s.%s' % (p, version, release, arch)
                    for p, pinfo in mod.yum.yum_pkg_relatives[pkg].items()
                    if 'base' in pinfo and pinfo['base']]
        cmd = 'yum erase -y %s' % (' '.join(pkgs),)
        result, output = await mod.shell.async_command(cmd)
        pkg_ext = ext and ext or pkg
        if result == 0:
            code = 0
            msg = '%s v%s-%s 卸载成功！' % (pkg_ext, version, release)
        else:
            code = -1
            msg = '%s v%s-%s 卸载失败！<p style="margin:10px">%s</p>' % \
                  (pkg_ext, version, release, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)
        self._unlock_job('yum')

    async def yum_update(self, repo, pkg, version, release, ext):
        jobname = 'yum_update_%s_%s_%s_%s_%s' % (repo, pkg, ext, version, release)
        jobname = jobname.strip('_').replace('__', '_')
        if not self._start_job(jobname):
            return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, '已有一个YUM进程在运行，更新失败。')
            return

        if ext:
            self._update_job(jobname, 2, '正在下载并升级扩展包，请耐心等候...')
        else:
            self._update_job(jobname, 2, '正在下载并升级软件包，请耐心等候...')

        pkg_ext = ext and ext or pkg

        arch = self.settings['arch']
        if pkg_ext in mod.yum.yum_pkg_noarchitecture:
            arch = 'noarch'

        cmd = 'yum update -y %s-%s-%s.%s' % (pkg_ext, version, release, arch)
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '成功升级 %s 到版本 v%s-%s！' % (pkg_ext, version, release)
        else:
            code = -1
            msg = '%s 升级到版本 v%s-%s 失败！<p style="margin:10px">%s</p>' % \
                  (pkg_ext, version, release, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)
        self._unlock_job('yum')

    async def yum_ext_info(self, pkg):
        jobname = 'yum_ext_info_%s' % pkg
        if not self._start_job(jobname):
            return
        if not self._lock_job('yum'):
            self._finish_job(jobname, -1, '已有一个YUM进程在运行，获取扩展信息失败。')
            return

        self._update_job(jobname, 2, '正在收集扩展信息...')

        exts = [k for k, v in mod.yum.yum_pkg_relatives[pkg].items() if 'isext' in v and v['isext']]
        cmd = 'yum info %s --disableplugin=fastestmirror' % (' '.join(['%s.%s' % (ext, self.settings['arch']) for ext in exts]))

        data = []
        matched = False
        await mod.shell.async_command('LANG="en_US.UTF-8"')
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            matched = True
            lines = output.split('\n')
            for line in lines:
                if any(line.startswith(word)
                       for word in ('Name', 'Version', 'Release', 'Size',
                                    'Repo', 'From repo')):
                    fields = line.strip().split(':', 1)
                    if len(fields) != 2:
                        continue
                    field_name = fields[0].strip().lower().replace(' ', '_')
                    field_value = fields[1].strip()
                    if field_name == 'name':
                        data.append({})
                    data[-1][field_name] = field_value
        if matched:
            code = 0
            msg = '获取扩展信息成功！'
        else:
            code = -1
            msg = '获取扩展信息失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg, data)
        self._unlock_job('yum')

    async def copy(self, srcpath, despath):
        jobname = 'copy_%s_%s' % (srcpath, despath)

        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在复制 %s 到 %s...' % (srcpath, despath))

        cmd = 'cp -rf %s %s' % (quote(srcpath), quote(despath))
        result, output = await mod.shell.async_command(cmd)

        if result == 0:
            code = 0
            msg = '复制 %s 到 %s 完成！' % (srcpath, despath)
        else:
            code = -1
            msg = '复制 %s 到 %s 失败！<p style="margin:10px">%s</p>' % (srcpath, despath, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def move(self, srcpath, despath):
        jobname = 'move_%s_%s' % (srcpath, despath)
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在移动 %s 到 %s...' % (srcpath, despath))

        despath_exists = Path(despath).exists()

        if despath_exists:
            if not Path(srcpath).exists():
                self._finish_job(jobname, -1, '不可识别的源！')
                return
            cmd = 'cp -rf %s/* %s' % (quote(srcpath), quote(despath))
        else:
            cmd = 'mv %s %s' % (quote(srcpath), quote(despath))
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '移动 %s 到 %s 完成！' % (srcpath, despath)
        else:
            code = -1
            msg = '移动 %s 到 %s 失败！<p style="margin:10px">%s</p>' % (srcpath, despath, output.strip().replace('\n', '<br>'))

        if despath_exists and code == 0:
            cmd = 'rm -rf %s' % (quote(srcpath),)
            result, output = await mod.shell.async_command(cmd)
            if result == 0:
                code = 0
                msg = '移动 %s 到 %s 完成！' % (srcpath, despath)
            else:
                code = -1
                msg = '移动 %s 到 %s 失败！<p style="margin:10px">%s</p>' % (srcpath, despath, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def remove(self, paths):
        jobname = 'remove_%s' % ','.join(paths)
        if not self._start_job(jobname):
            return

        for path in paths:
            self._update_job(jobname, 2, '正在删除 %s...' % path)
            cmd = 'rm -rf %s' % (quote(path))
            result, output = await mod.shell.async_command(cmd)

            if result == 0:
                code = 0
                msg = '删除 %s 成功！' % path
            else:
                code = -1
                msg = '删除 %s 失败！<p style="margin:10px">%s</p>' % (path, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def compress(self, zippath, paths):
        jobname = 'compress_%s_%s' % (zippath, ','.join(paths))
        if not self._start_job(jobname):
            return
        self._update_job(jobname, 2, '正在压缩生成 %s...' % zippath)

        basepath = str(Path(zippath).parent) + '/'
        path = ' '.join([quote(item.replace(basepath, '')) for item in paths])
        if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
            cmd = 'tar zcf %s -C %s %s' % (quote(zippath), quote(basepath), path)
        elif zippath.endswith('.tar.bz2'):
            cmd = 'tar jcf %s -C %s %s' % (quote(zippath), quote(basepath), path)
        elif zippath.endswith('.zip'):
            if not Path('/usr/bin/zip').exists():
                self._update_job(jobname, 2, '正在安装 zip...')
                if self.settings['os_name'] in ('centos', 'redhat'):
                    cmd = 'yum install -y zip unzip'
                    result, output = await mod.shell.async_command(cmd)
                    if result == 0:
                        self._update_job(jobname, 0, 'zip 安装成功！')
                    else:
                        self._update_job(jobname, -1, 'zip 安装失败！')
                        return
            cmd = 'cd %s; zip -rq9 %s %s' % (quote(basepath), quote(zippath), path)
        elif zippath.endswith('.gz'):
            path = ' '.join([quote(item) for item in paths])
            cmd = 'gzip -f %s' % path
        else:
            self._finish_job(jobname, -1, '不支持的类型！')
            return

        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '压缩到 %s 成功！' % zippath
        else:
            code = -1
            msg = '压缩失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg)

    async def decompress(self, zippath, despath):
        jobname = 'decompress_%s_%s' % (zippath, despath)
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在解压 %s...' % zippath)
        if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
            cmd = 'tar zxf %s -C %s' % (quote(zippath), quote(despath))
        elif zippath.endswith('.tar.bz2'):
            cmd = 'tar jxf %s -C %s' % (quote(zippath), quote(despath))
        elif zippath.endswith('.zip'):
            if not Path('/usr/bin/unzip').is_file():
                self._update_job(jobname, 2, '正在安装 unzip...')
                if self.settings['os_name'] in ('centos', 'redhat'):
                    cmd = 'yum install -y zip unzip'
                    result, output = await mod.shell.async_command(cmd)
                    if result == 0:
                        self._update_job(jobname, 0, 'unzip 安装成功！')
                    else:
                        self._update_job(jobname, -1, 'unzip 安装失败！')
                        return
            cmd = 'unzip -q -o %s -d %s' % (quote(zippath), quote(despath))
        elif zippath.endswith('.gz'):
            cmd = 'gunzip -f %s' % quote(zippath)
        else:
            self._finish_job(jobname, -1, '不支持的类型！')
            return

        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '解压 %s 成功！' % zippath
        else:
            code = -1
            msg = '解压 %s 失败！<p style="margin:10px">%s</p>' % (zippath, output.strip().replace('\n', '<br>'))

        self._finish_job(jobname, code, msg)

    async def chown(self, paths, user, group, option):
        jobname = 'chown_%s' % ','.join(paths)
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在设置用户和用户组...')

        for path in paths:
            result = await mod.shell.async_task(mod.file.chown, path, user, group, option == '-R')
            if result == True:
                code = 0
                msg = '设置用户和用户组成功！'
            else:
                code = -1
                msg = '设置 %s 的用户和用户组时失败！' % path
                break

        self._finish_job(jobname, code, msg)

    async def chmod(self, paths, perms, option):
        jobname = 'chmod_%s' % ','.join(paths)
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在设置权限...')

        try:
            perms = int(perms, 8)
        except:
            self._finish_job(jobname, -1, '权限值输入有误！')
            return

        for path in paths:
            result = await mod.shell.async_task(mod.file.chmod, path, perms, option == '-R')
            if result == True:
                code = 0
                msg = '权限修改成功！'
            else:
                code = -1
                msg = f'修改 {path} 的权限时失败！'
                break

        self._finish_job(jobname, code, msg)

    async def wget(self, url, path):
        jobname = 'wget_%s' % tornado.escape.url_escape(url)
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在下载 {url}...')

        if Path(path).is_dir():
            cmd = 'wget -q "%s" --directory-prefix=%s' % (quote(url), quote(path))
        else:
            cmd = 'wget -q "%s" -O %s' % (quote(url), quote(path))
        result, output = await mod.shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = '下载成功！'
        else:
            code = -1
            msg = '下载失败！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg)

    async def mysql_fupdatepwd(self, password):
        jobname = 'mysql_fupdatepwd'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在检测 MySQL 服务状态...')
        cmd = 'service mysqld status'
        result, output = await mod.shell.async_command(cmd)
        isstopped = 'stopped' in output

        if not isstopped:
            self._update_job(jobname, 2, '正在停止 MySQL 服务...')
            cmd = 'service mysqld stop'
            result, output = await mod.shell.async_command(cmd)
            if result != 0:
                self._finish_job(jobname, -1, '停止 MySQL 服务时出错！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>'))
                return

        self._update_job(jobname, 2, '正在启用 MySQL 恢复模式...')
        manually = False
        cmd = 'service mysqld startsos'
        result, output = await mod.shell.async_command(cmd)
        if result != 0:
            manually = True
            cmd = 'mysqld_safe --skip-grant-tables --skip-networking'
            p = Popen(cmd, stdout=PIPE, stderr=STDOUT, close_fds=True, shell=True)
            if not p:
                self._finish_job(jobname, -1, '启用 MySQL 恢复模式时出错！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>'))
                return

        if manually:
            time.sleep(2)

        error = False
        self._update_job(jobname, 2, '正在强制重置 root 密码...')
        if not mod.mysql.fupdatepwd(password):
            error = True

        if manually:
            result = await mod.shell.async_task(mod.mysql.shutdown, password)
            if result:
                self._update_job(jobname, 0, '成功停止 MySQL 服务！')
            else:
                self._update_job(jobname, -1, '停止 MySQL 服务失败！')
            p.terminate()
            p.wait()

        msg = ''
        if not isstopped:
            if error:
                msg = '重置 root 密码时发生错误！正在重启 MySQL 服务...'
                self._update_job(jobname, -1, msg)
            else:
                self._update_job(jobname, 2, '正在重启 MySQL 服务...')
            if manually:
                cmd = 'service mysqld start'
            else:
                cmd = 'service mysqld restart'
        else:
            if error:
                msg = '重置 root 密码时发生错误！正在停止 MySQL 服务...'
                self._update_job(jobname, -1, msg)
            else:
                self._update_job(jobname, 2, '正在停止 MySQL 服务...')
            if manually:
                cmd = ''
            else:
                cmd = 'service mysqld stop'

        if not cmd:
            if error:
                code = -1
                msg = '%sOK' % msg
            else:
                code = 0
                msg = 'root 密码重置成功！'
        else:
            result, output = await mod.shell.async_command(cmd)
            if result == 0:
                if error:
                    code = -1
                    msg = '%sOK' % msg
                else:
                    code = 0
                    msg = 'root 密码重置成功！'
            else:
                if error:
                    code = -1
                    msg = '%sOK' % msg
                else:
                    code = -1
                    msg = 'root 密码重置成功，但在操作服务时出错！<p style="margin:10px">%s</p>' % output.strip().replace('\n', '<br>')

        self._finish_job(jobname, code, msg)

    async def mysql_databases(self, password):
        jobname = 'mysql_databases'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在获取数据库列表...')
        dbs = []
        dbs = await mod.shell.async_task(mod.mysql.show_databases, password)
        if dbs:
            code = 0
            msg = '获取数据库列表成功！'
        else:
            code = -1
            msg = '获取数据库列表失败！'

        self._finish_job(jobname, code, msg, dbs)

    async def mysql_users(self, password, dbname=None):
        if not dbname:
            jobname = 'mysql_users'
        else:
            jobname = 'mysql_users_%s' % dbname
        if not self._start_job(jobname):
            return

        if not dbname:
            self._update_job(jobname, 2, '正在获取用户列表...')
        else:
            self._update_job(jobname, 2, f'正在获取数据库 {dbname} 的用户列表...')

        users = []
        users = await mod.shell.async_task(mod.mysql.show_users, password, dbname)
        if users:
            code = 0
            msg = '获取用户列表成功！'
        else:
            code = -1
            msg = '获取用户列表失败！'

        self._finish_job(jobname, code, msg, users)

    async def mysql_dbinfo(self, password, dbname):
        jobname = 'mysql_dbinfo_%s' % dbname
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在获取数据库 %s 的信息...' % dbname)
        dbinfo = False
        dbinfo = await mod.shell.async_task(mod.mysql.show_database, password, dbname)
        if dbinfo:
            code = 0
            msg = '获取数据库 %s 的信息成功！' % dbname
        else:
            code = -1
            msg = '获取数据库 %s 的信息失败！' % dbname

        self._finish_job(jobname, code, msg, dbinfo)

    async def mysql_rename(self, password, dbname, newname):
        jobname = 'mysql_rename_%s' % dbname
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在重命名 {dbname}...')
        result = await mod.shell.async_task(mod.mysql.rename_database, password, dbname, newname)
        if result == True:
            code = 0
            msg = f'{dbname} 重命名成功！'
        else:
            code = -1
            msg = f'{dbname} 重命名失败！'

        self._finish_job(jobname, code, msg)

    async def mysql_create(self, password, dbname, collation):
        jobname = f'mysql_create_{dbname}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在创建 {dbname}...')
        result = await mod.shell.async_task(mod.mysql.create_database, password, dbname, collation=collation)
        if result == True:
            code = 0
            msg = f'{dbname} 创建成功！'
        else:
            code = -1
            msg = f'{dbname} 创建失败！'

        self._finish_job(jobname, code, msg)

    async def mysql_export(self, password, dbname, path):
        jobname = f'mysql_export_{dbname}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在导出 {dbname}...')
        result = await mod.shell.async_task(mod.mysql.export_database, password, dbname, path)
        if result == True:
            code = 0
            msg = f'{dbname} 导出成功！'
        else:
            code = -1
            msg = f'{dbname} 导出失败！'

        self._finish_job(jobname, code, msg)

    async def mysql_drop(self, password, dbname):
        jobname = f'mysql_drop_{dbname}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在删除 {dbname}...')
        result = await mod.shell.async_task(mod.mysql.drop_database, password, dbname)
        if result == True:
            code = 0
            msg = f'{dbname} 删除成功！'
        else:
            code = -1
            msg = f'{dbname} 删除失败！'

        self._finish_job(jobname, code, msg)

    async def mysql_createuser(self, password, user, host, pwd=None):
        username = f'{user}@{host}'
        jobname = f'mysql_createuser_{username}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在添加用户 {username}...')
        result = await mod.shell.async_task(mod.mysql.create_user, password, user, host, pwd)
        if result is True:
            code = 0
            msg = f'用户 {username} 添加成功！'
        else:
            code = -1
            msg = f'用户 {username} 添加失败！'

        self._finish_job(jobname, code, msg)

    async def mysql_userprivs(self, password, user, host):
        username = f'{user}@{host}'
        jobname = f'mysql_userprivs_{username}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在获取用户 {username} 的权限...')

        privs = {'global': {}, 'bydb': {}}
        globalprivs = await mod.shell.async_task(mod.mysql.show_user_globalprivs, password, user, host)
        if globalprivs != False:
            code = 0
            msg = f'获取用户 {username} 的全局权限成功！'
            privs['global'] = globalprivs
        else:
            code = -1
            msg = f'获取用户 {username} 的全局权限失败！'
            privs = False

        if privs:
            dbprivs = await mod.shell.async_task(mod.mysql.show_user_dbprivs, password, user, host)
            if dbprivs != False:
                code = 0
                msg = f'获取用户 {username} 的数据库权限成功！'
                privs['bydb'] = dbprivs
            else:
                code = -1
                msg = f'获取用户 {username} 的数据库权限失败！'
                privs = False

        self._finish_job(jobname, code, msg, privs)

    async def mysql_updateuserprivs(self, password, user, host, privs, dbname=None):
        username = f'{user}@{host}'
        if dbname:
            jobname = f'mysql_updateuserprivs_{username}_{dbname}'
        else:
            jobname = f'mysql_updateuserprivs_{username}'
        if not self._start_job(jobname):
            return

        if dbname:
            self._update_job(jobname, 2, f'正在更新用户 {username} 在数据库 {dbname} 中的权限...')
        else:
            self._update_job(jobname, 2, f'正在更新用户 {username} 的权限...')

        rt = await mod.shell.async_task(mod.mysql.update_user_privs, password, user, host, privs, dbname)
        if rt != False:
            code = 0
            msg = f'用户 {username} 的权限更新成功！'
        else:
            code = -1
            msg = f'用户 {username} 的权限更新失败！'

        self._finish_job(jobname, code, msg)

    async def mysql_setuserpassword(self, password, user, host, pwd):
        username = f'{user}@{host}'
        jobname = f'mysql_setuserpassword_{username}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在更新用户 {username} 的密码...')

        rt = await mod.shell.async_task(mod.mysql.set_user_password, password, user, host, pwd)
        if rt != False:
            code = 0
            msg = f'用户 {username} 的密码更新成功 ！'
        else:
            code = -1
            msg = f'用户 {username} 的密码更新失败 ！'

        self._finish_job(jobname, code, msg)

    async def mysql_dropuser(self, password, user, host):
        username = f'{user}@{host}'
        jobname = f'mysql_dropuser_{username}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在删除用户 {username}...')

        rt = await mod.shell.async_task(mod.mysql.drop_user, password, user, host)
        if rt != False:
            code = 0
            msg = f'用户 {username} 删除成功 ！'
        else:
            code = -1
            msg = f'用户 {username} 删除失败 ！'

        self._finish_job(jobname, code, msg)

    async def ssh_genkey(self, path, password=''):
        jobname = 'ssh_genkey'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在生成密钥对...')

        rt = await mod.shell.async_task(mod.ssh.genkey, path, password)
        if rt != False:
            code = 0
            msg = '密钥对生成成功 ！'
        else:
            code = -1
            msg = '密钥对生成失败 ！'

        self._finish_job(jobname, code, msg)

    async def ssh_chpasswd(self, path, oldpassword, newpassword=''):
        jobname = 'ssh_chpasswd'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, '正在修改私钥密码...')

        rt = await mod.shell.async_task(mod.ssh.chpasswd, path, oldpassword, newpassword)
        if rt != False:
            code = 0
            msg = '私钥密码修改成功！'
        else:
            code = -1
            msg = '私钥密码修改失败！'

        self._finish_job(jobname, code, msg)

    async def inpanel_install(self, ssh_ip, ssh_port, ssh_user, ssh_password, instance_name, accessnet, accessport=None, accesskey=None):
        jobname = f'remote_inpanel_install_{ssh_ip}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在将 InPanel 安装到 {ssh_ip}...')

        result = await mod.shell.async_task(remote.inpanel_install, ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=accesskey, inpanel_port=accessport)
        if result == True:
            code = 0
            msg = 'InPanel 安装成功！'
            self.config.set('inpanel', instance_name, f'{accesskey}|{accessnet}|{accessport}')
        else:
            code = -1
            msg = 'InPanel 安装过程中发生错误！'

        self._finish_job(jobname, code, msg)

    async def inpanel_uninstall(self, ssh_ip, ssh_port, ssh_user, ssh_password, instance_name):
        jobname = f'remote_inpanel_uninstall_{ssh_ip}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在卸载 {ssh_ip} 上的 InPanel...')
        result = await mod.shell.async_task(remote.inpanel_uninstall, ssh_ip, ssh_port, ssh_user, ssh_password)
        if result == True:
            code = 0
            msg = 'InPanel 卸载成功！'
            try:
                self.config.remove_option('inpanel', instance_name)
            except:
                pass
        else:
            code = -1
            msg = 'InPanel 卸载过程中发生错误！'

        self._finish_job(jobname, code, msg)

    async def inpanel_config(self, ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=None):
        jobname = f'remote_inpanel_config_{ssh_ip}'
        if not self._start_job(jobname):
            return

        self._update_job(jobname, 2, f'正在更新 {ssh_ip} 上的 InPanel 配置...')

        result = await mod.shell.async_task(remote.inpanel_config, ssh_ip, ssh_port, ssh_user, ssh_password, accesskey=accesskey)
        if result == True:
            code = 0
            msg = 'InPanel 配置更新成功！'
        else:
            code = -1
            msg = 'InPanel 配置更新过程中发生错误！'

        self._finish_job(jobname, code, msg)

    async def uploadtoftp(self, address, account, password, source, target):
        jobname = f'upload_to_ftp_{address}_{source}_{target}'
        if not self._start_job(jobname):
            return

        if not Path(source).exists():
            self._finish_job(jobname, -1, '传输失败！文件不存在')
            return

        self._update_job(jobname, 2, f'正在传输文件 {source}...')
        result = await mod.shell.async_task(mod.ftp.uploadtoftp, address, account, password, source, target)
        if result == True:
            code = 0
            msg = f'文件 {source} 已成功传输到 {address} 服务器！'
        else:
            code = -1
            msg = '文件传输失败！'
        self._finish_job(jobname, code, msg)