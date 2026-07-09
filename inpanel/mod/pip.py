# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for pip (Python Package Installer) Management'''

import os
import re
from pathlib import Path
from subprocess import getstatusoutput


def _pip_cmd():
    """返回可用的 pip 命令"""
    for cmd in ('pip3', 'pip'):
        status, _ = getstatusoutput('which %s' % cmd)
        if status == 0:
            return cmd
    return 'pip'


def _run(args):
    """执行 pip 命令"""
    return getstatusoutput('%s %s' % (_pip_cmd(), args))


def is_installed():
    """检查 pip 是否已安装"""
    status, _ = getstatusoutput('which %s' % _pip_cmd())
    return status == 0


def get_version():
    """获取 pip 版本"""
    status, output = _run('--version')
    if status != 0:
        return ''
    # pip 23.x from /usr/lib/... (python 3.x)
    return output.strip().split('\n')[0]


def get_status():
    """获取 pip 状态信息"""
    status = {
        'installed': is_installed(),
        'version': '',
        'running': False,
        'python': '',
    }
    if not status['installed']:
        return status
    status['version'] = get_version()
    status['running'] = True
    status['python'] = _python_version()
    return status


def _python_version():
    status, output = getstatusoutput('python3 --version 2>/dev/null || python --version 2>/dev/null')
    if status == 0:
        return output.strip()
    return ''


def _parse_config():
    """解析 pip config list 输出，返回配置字典"""
    status, output = _run('config list 2>/dev/null')
    config = {}
    if status != 0 or not output.strip():
        return config
    for line in output.strip().split('\n'):
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            config[k.strip()] = v.strip().strip("'").strip('"')
    return config


def _config_file():
    """获取 pip 配置文件路径"""
    status, output = _run('config list -v 2>/dev/null')
    if status != 0:
        return ''
    for line in output.split('\n'):
        if 'site.' in line or 'global.' in line or 'user.' in line:
            continue
        m = re.search(r'(/[^ \n]+\.ini|/[^ \n]+\.conf)', line)
        if m:
            return m.group(1)
    return ''


def get_repo_list():
    """获取 pip 配置的软件源列表"""
    config = _parse_config()
    repos = []
    # index-url / extra-index-url
    index_url = config.get('global.index-url', config.get('index-url', ''))
    if index_url:
        repos.append({'name': 'index-url', 'path': index_url, 'created': ''})
    extra = config.get('global.extra-index-url', config.get('extra-index-url', ''))
    if extra:
        for url in extra.split():
            repos.append({'name': 'extra-index-url', 'path': url, 'created': ''})
    if not repos:
        # 默认 PyPI
        repos.append({'name': 'index-url', 'path': 'https://pypi.org/simple', 'created': ''})
    # 配置文件信息
    cfg = _config_file()
    if cfg and Path(cfg).exists():
        try:
            import time
            created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(cfg).stat().st_ctime))
        except Exception:
            created = ''
        for r in repos:
            r['config_file'] = cfg
            r['created'] = created
    return repos


def get_repo_detail(name):
    """获取软件源详情（含已安装包列表）"""
    repos = get_repo_list()
    target = None
    for r in repos:
        if r['name'] == name:
            target = r
            break
    if not target:
        return None
    # 列出已安装的包
    packages = []
    status, output = _run('list --format=freeze 2>/dev/null')
    if status == 0 and output.strip():
        for line in output.strip().split('\n'):
            line = line.strip()
            if '==' in line:
                pname, ver = line.split('==', 1)
                packages.append({'name': pname.strip(), 'version': ver.strip()})
    target['packages'] = packages
    return target


def search_repos(keyword):
    """搜索已安装的包（pip search 已不可用，按已安装包过滤）"""
    if not keyword:
        return []
    status, output = _run('list --format=freeze 2>/dev/null')
    if status != 0:
        return []
    kw = keyword.lower()
    result = []
    for line in output.strip().split('\n'):
        if '==' in line:
            pname, ver = line.split('==', 1)
            pname = pname.strip()
            if kw in pname.lower():
                result.append({'name': pname, 'version': ver.strip()})
    return result


def install_package(name):
    """通过 pip 安装软件"""
    if not name:
        return {'code': -1, 'msg': '软件名称不能为空！'}
    status, output = _run('install %s' % name)
    if status == 0:
        return {'code': 0, 'msg': '软件 %s 安装成功！' % name, 'data': output}
    return {'code': -1, 'msg': '软件 %s 安装失败：%s' % (name, output)}


def refresh_cache():
    """pip 没有缓存刷新概念，这里返回提示"""
    return {'code': 0, 'msg': 'pip 无需更新索引'}


def web_handler(context):
    """Handle web requests for pip management"""
    action = context.get('action', '')
    name = context.get('name', '') or context.get('repo', '')

    if action == 'overview':
        return {'code': 0, 'msg': '', 'data': get_status()}
    elif action == 'list':
        return {'code': 0, 'msg': '', 'data': get_repo_list()}
    elif action == 'item':
        if not name:
            return {'code': -1, 'msg': '软件库名称不能为空！'}
        data = get_repo_detail(name)
        if data is None:
            return {'code': -1, 'msg': '软件库不存在！'}
        return {'code': 0, 'msg': '', 'data': data}
    elif action == 'search':
        keyword = context.get('keyword', '')
        return {'code': 0, 'msg': '', 'data': search_repos(keyword)}
    elif action == 'install':
        if not name:
            return {'code': -1, 'msg': '软件名称不能为空！'}
        return install_package(name)
    elif action == 'refresh':
        return refresh_cache()
    else:
        return {'code': -1, 'msg': '未定义的操作！'}
