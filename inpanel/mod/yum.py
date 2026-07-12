# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for YUM Management'''

import os
from pathlib import Path

from .. import base
from . import config
from . import file
from ..yum import yum_reporpms

config_path = '/etc/yum.repos.d'


def get_list():
    '''get repo list'''
    res = []
    if base.kernel_name in ('Linux'):
        d = str(Path(config_path))
        if not Path(d).exists() or not Path(d).is_dir():
            return None
        items = sorted(os.listdir(d))
        return items if len(items) > 0 else []
    elif base.kernel_name in ('Darwin'):
        return None
    else:
        return None


def item_exists(repo):
    '''exists'''
    return Path(str(Path(config_path) / repo)).exists()


def get_item(repo):
    '''get repo config'''
    if not repo:
        return None
    repo_file = str(Path(config_path) / repo)
    if Path(repo_file).exists():
        _config = config.Config(repo_file)
        return _config.get_config()
    return None


def set_item(repo, data):
    '''set repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = str(Path(config_path) / repo)
    if Path(repo_file).exists():
        _config = config.Config(repo_file, data)
        return True
        # return _config.update()
    else:
        return False


def add_item(repo, data):
    '''add repo config'''
    if not repo:
        return None
    if not data:
        return None
    repo_file = str(Path(config_path) / repo)
    if Path(repo_file).exists():
        return False
    else:
        _config = config.Config(repo_file, data)
        return True
        # return _config.update()


def del_item(repo):
    '''delete repo file'''
    if not repo:
        return None
    repo_file = str(Path(config_path) / repo)
    return file.delete(repo_file)


def get_repo_release(os_versint, os_name, arch):
    '''install release'''
    cmds = []
    if os_versint == 5:
        if os_name == 'redhat':
            # backup system version info
            cmds.append('cp -f /etc/redhat-release /etc/redhat-release.inpanel')
            cmds.append('cp -f /etc/issue /etc/issue.inpanel')
            cmds.append('rpm -e redhat-release-5Server --nodeps')
    elif os_versint == 7:
        if os_name == 'centos':
            cmds.append('yum install -y centos-release')
    elif os_versint == 8:
        if os_name == 'centos':
            cmds.append('yum install -y centos-release')
    else:
        for rpm in yum_reporpms['base'][os_versint][arch]:
            cmds.append('rpm -U %s' % rpm)

        if Path('/etc/issue.inpanel').exists():
            cmds.append('cp -f /etc/issue.inpanel /etc/issue')
        if Path('/etc/redhat-release.inpanel').exists():
            cmds.append(
                'cp -f /etc/redhat-release.inpanel /etc/redhat-release')
    return cmds


def get_repo_epel(os_versint, os_name, arch):
    '''install epel'''
    # CentALT and ius depends on epel
    cmds = []

    if os_versint == 7:
        if os_name == 'centos':
            cmds.append('yum install -y epel-release')
    if os_versint == 8:
        if os_name == 'centos':
            cmds.append('yum install -y epel-release')
    else:
        for rpm in yum_reporpms['epel'][os_versint][arch]:
            cmds.append('rpm -U %s' % rpm)

    return cmds


import shutil
import time
from subprocess import getstatusoutput


def is_installed():
    '''check if yum is installed'''
    return shutil.which('yum') is not None


def get_version():
    '''get yum version'''
    if not is_installed():
        return ''
    status, output = getstatusoutput('yum --version')
    if status != 0:
        return ''
    return output.strip().split('\n')[0]


def get_status():
    '''get yum status'''
    status = {
        'installed': is_installed(),
        'version': '',
        'running': False,
        'config_path': config_path,
    }
    if status['installed']:
        status['version'] = get_version()
        status['running'] = True
    return status


def refresh_cache():
    '''yum makecache'''
    if not is_installed():
        return {'code': -1, 'msg': 'yum 未安装！'}
    status, output = getstatusoutput('yum makecache 2>&1')
    if status == 0:
        return {'code': 0, 'msg': 'yum 缓存已更新！'}
    return {'code': -1, 'msg': 'yum 缓存更新失败：%s' % output}


def get_repo_list():
    '''get structured repo list with name/path/created'''
    if base.kernel_name != 'Linux':
        return None
    d = Path(config_path)
    if not d.exists() or not d.is_dir():
        return []
    items = sorted(os.listdir(str(d)))
    repos = []
    for item in items:
        if not item.endswith('.repo'):
            continue
        full = str(d / item)
        created = ''
        try:
            created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(full).stat().st_ctime))
        except Exception:
            pass
        repos.append({'name': item, 'path': full, 'created': created})
    return repos


def get_repo_detail(repo):
    '''get repo detail with package list'''
    if not repo:
        return None
    data = get_item(repo)
    full = str(Path(config_path) / repo)
    created = ''
    try:
        created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(full).stat().st_ctime))
    except Exception:
        pass
    # collect package list per repo id
    packages = []
    if data:
        for repoid in data.keys():
            try:
                st, out = getstatusoutput(
                    'repoquery --repoid=%s --all --qf="%%{name} %%{version}" 2>/dev/null' % repoid)
                if st == 0 and out.strip():
                    for line in out.strip().split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        pkg = {'name': parts[0]}
                        if len(parts) > 1:
                            pkg['version'] = parts[1]
                        pkg['repoid'] = repoid
                        packages.append(pkg)
            except Exception:
                pass
    return {'name': repo, 'path': full, 'created': created, 'repos': data or {}, 'packages': packages}


def search_repos(keyword):
    '''search repo files by name'''
    if not keyword:
        return []
    items = get_repo_list() or []
    kw = keyword.lower()
    return [r for r in items if kw in r['name'].lower()]


def install_package(name):
    '''install package via yum'''
    if not name:
        return {'code': -1, 'msg': '软件名称不能为空！'}
    if not is_installed():
        return {'code': -1, 'msg': 'yum 未安装！'}
    status, output = getstatusoutput('yum install -y %s 2>&1' % name)
    if status == 0:
        return {'code': 0, 'msg': '软件 %s 安装成功！' % name, 'data': output}
    return {'code': -1, 'msg': '软件 %s 安装失败：%s' % (name, output)}


def web_handler(context):
    '''Handle web requests for YUM repository management'''
    action = context.get('action', '')
    repo = context.get('repo', '') or context.get('name', '')

    if action == 'overview':
        return {'code': 0, 'msg': '', 'data': get_status()}
    elif action == 'refresh':
        return refresh_cache()
    elif action == 'list':
        items = get_repo_list()
        if items is None:
            return {'code': -1, 'msg': '获取配置失败！'}
        else:
            return {'code': 0, 'msg': '', 'data': items}
    elif action == 'item':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        data = get_repo_detail(repo)
        if data is None:
            return {'code': -1, 'msg': '配置文件不存在！'}
        else:
            return {'code': 0, 'msg': '', 'data': data}
    elif action == 'search':
        keyword = context.get('keyword', '')
        return {'code': 0, 'msg': '', 'data': search_repos(keyword)}
    elif action == 'install':
        return install_package(repo)
    
    elif action == 'add':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        serverid = context.get('serverid', '')
        if not serverid:
            return {'code': -1, 'msg': '仓库标识ID不能为空！'}
        name = context.get('name', '')
        if not name:
            return {'code': -1, 'msg': '仓库名称不能为空！'}
        baseurl = context.get('baseurl', '')
        if not baseurl:
            return {'code': -1, 'msg': '仓库路径不能为空！'}
        
        enabled = context.get('enabled', True)
        gpgcheck = context.get('gpgcheck', False)
        
        data = {
            serverid: {
                'name': name,
                'enabled': 0 if not enabled else 1,
                'baseurl': baseurl,
                'gpgcheck': 0 if not gpgcheck else 1,
                'gpgkey': ''
            }
        }
        
        if item_exists(repo):
            return {'code': -1, 'msg': '配置文件已存在！'}
        if add_item(repo, data) is True:
            return {'code': 0, 'msg': '配置添加成功！'}
        else:
            return {'code': -1, 'msg': '配置添加失败！'}
    
    elif action == 'edit':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        serverid = context.get('serverid', '')
        if not serverid:
            return {'code': -1, 'msg': '仓库标识ID不能为空！'}
        name = context.get('name', '')
        if not name:
            return {'code': -1, 'msg': '仓库名称不能为空！'}
        baseurl = context.get('baseurl', '')
        if not baseurl:
            return {'code': -1, 'msg': '仓库路径不能为空！'}
        
        enabled = context.get('enabled', True)
        gpgcheck = context.get('gpgcheck', False)
        
        data = {
            serverid: {
                'name': name,
                'enabled': 0 if not enabled else 1,
                'baseurl': baseurl,
                'gpgcheck': 0 if not gpgcheck else 1,
                'gpgkey': ''
            }
        }
        
        if not item_exists(repo):
            return {'code': -1, 'msg': '配置文件不存在！'}
        if set_item(repo, data) is True:
            return {'code': 0, 'msg': '配置修改成功！'}
        else:
            return {'code': -1, 'msg': '配置修改失败！'}
    
    elif action == 'del':
        if not repo:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        if not item_exists(repo):
            return {'code': -1, 'msg': '配置文件不存在！'}
        if del_item(repo) is True:
            return {'code': 0, 'msg': '配置文件已移入回收站！'}
        else:
            return {'code': -1, 'msg': '删除失败！'}
    
    else:
        return {'code': -1, 'msg': '未定义的操作！'}


if __name__ == '__main__':
    l = get_list()
    print(l)
    if l:
        i = l[0]
        print(i)
        c = get_item(i)
        print(c)
