# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for Homebrew Management'''

import os
from pathlib import Path
from subprocess import getstatusoutput

from ..base import kernel_name


def _run(args):
    """执行 brew 命令并返回 (status, output)"""
    if kernel_name != 'Darwin' and kernel_name != 'Linux':
        return (1, '当前系统不支持 Homebrew')
    return getstatusoutput(args)


def is_installed():
    """检查 brew 是否已安装"""
    status, _ = getstatusoutput('which brew')
    return status == 0


def get_version():
    """获取 brew 版本"""
    status, output = _run('brew --version')
    if status != 0:
        return ''
    # Homebrew 4.x.x
    return output.strip().split('\n')[0]


def get_prefix():
    """获取 brew 安装路径"""
    status, output = _run('brew --prefix')
    if status != 0:
        return ''
    return output.strip()


def get_status():
    """获取 brew 状态信息"""
    status = {
        'installed': is_installed(),
        'version': '',
        'prefix': '',
        'running': False,
    }
    if not status['installed']:
        return status
    status['version'] = get_version()
    status['prefix'] = get_prefix()
    # brew 本身不是常驻服务，只要命令可用即视为可用
    status['running'] = True
    return status


def service_control(action):
    """brew 服务控制（管理 brew services）

    Args:
        action: 'start' | 'stop' | 'restart'
    """
    action_msg = {'start': '启动', 'stop': '停止', 'restart': '重启'}
    if action == 'restart':
        # 重启所有已运行的服务
        getstatusoutput('brew services stop --all')
        status, output = getstatusoutput('brew services start --all')
    else:
        if action == 'start':
            status, output = getstatusoutput('brew services start --all')
        else:
            status, output = getstatusoutput('brew services stop --all')
    if status == 0:
        return {'code': 0, 'msg': 'brew 服务已%s' % action_msg.get(action, action)}
    return {'code': -1, 'msg': 'brew 服务%s失败：%s' % (action_msg.get(action, action), output)}


def get_services():
    """获取 brew services 列表"""
    status, output = _run('brew services list 2>/dev/null')
    if status != 0 or not output.strip():
        return []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return []
    header = lines[0].split()
    services = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        item = {}
        for idx, key in enumerate(header):
            item[key] = parts[idx] if idx < len(parts) else ''
        services.append(item)
    return services


def _tap_path(tap_name):
    """根据 tap 名称推算本地路径"""
    # tap_name 形如 homebrew/cask
    prefix = get_prefix()
    if not prefix:
        return ''
    try:
        user, repo = tap_name.split('/', 1)
    except ValueError:
        return ''
    # homebrew/core -> Homebrew/Library/Taps/homebrew/homebrew-core
    path1 = Path(prefix) / 'Homebrew' / 'Library' / 'Taps' / user / ('homebrew-' + repo)
    if path1.exists():
        return str(path1)
    # fallback: old style path
    path2 = Path(prefix) / 'Library' / 'Taps' / user / ('homebrew-' + repo)
    return str(path2)


def get_tap_list():
    """获取 brew tap 列表"""
    status, output = _run('brew tap')
    if status != 0:
        return []
    taps = []
    for line in output.strip().split('\n'):
        name = line.strip()
        if not name:
            continue
        path = _tap_path(name)
        created = ''
        if path and Path(path).exists():
            try:
                import time
                created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(path).stat().st_ctime))
            except Exception:
                pass
        taps.append({'name': name, 'path': path, 'created': created})
    return taps


def _list_formula_in_tap(tap_path):
    """遍历 tap 目录，列出所有 formula 名称"""
    packages = []
    if not tap_path or not Path(tap_path).exists():
        return packages
    formula_dir = Path(tap_path) / 'Formula'
    if formula_dir.exists():
        for f in formula_dir.rglob('*.rb'):
            pkg_name = f.stem
            packages.append({'name': pkg_name})
    # 有些 tap 可能有 Aliases 目录
    alias_dir = Path(tap_path) / 'Aliases'
    if alias_dir.exists():
        for f in alias_dir.rglob('*'):
            if f.is_file() and not f.name.startswith('.'):
                packages.append({'name': f.name})
    return packages


def get_tap_detail(name):
    """获取某个 tap 的详情及软件列表"""
    if not name:
        return None
    path = _tap_path(name)
    created = ''
    if path and Path(path).exists():
        try:
            import time
            created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(path).stat().st_ctime))
        except Exception:
            pass
    packages = _list_formula_in_tap(path)
    return {'name': name, 'path': path, 'created': created, 'packages': packages}


def search_taps(keyword):
    """搜索 brew tap"""
    if not keyword:
        return []
    items = get_tap_list()
    kw = keyword.lower()
    return [t for t in items if kw in t['name'].lower()]


def install_package(name):
    """通过 brew 安装软件"""
    if not name:
        return {'code': -1, 'msg': '软件名称不能为空！'}
    status, output = _run('brew install %s' % name)
    if status == 0:
        return {'code': 0, 'msg': '软件 %s 安装成功！' % name, 'data': output}
    return {'code': -1, 'msg': '软件 %s 安装失败：%s' % (name, output)}


def refresh_cache():
    """brew update 更新索引"""
    status, output = _run('brew update')
    if status == 0:
        return {'code': 0, 'msg': 'brew 索引已更新！'}
    return {'code': -1, 'msg': 'brew 索引更新失败：%s' % output}


def web_handler(context):
    """Handle web requests for brew management"""
    action = context.get('action', '')
    name = context.get('name', '') or context.get('repo', '')

    if action == 'overview':
        return {'code': 0, 'msg': '', 'data': get_status()}
    elif action == 'services':
        return {'code': 0, 'msg': '', 'data': get_services()}
    elif action == 'service':
        op = context.get('op', '')
        if not op:
            return {'code': -1, 'msg': '操作类型不能为空！'}
        return service_control(op)
    elif action == 'list':
        return {'code': 0, 'msg': '', 'data': get_tap_list()}
    elif action == 'item':
        if not name:
            return {'code': -1, 'msg': '软件库名称不能为空！'}
        data = get_tap_detail(name)
        if data is None:
            return {'code': -1, 'msg': '软件库不存在！'}
        return {'code': 0, 'msg': '', 'data': data}
    elif action == 'search':
        keyword = context.get('keyword', '')
        return {'code': 0, 'msg': '', 'data': search_taps(keyword)}
    elif action == 'install':
        if not name:
            return {'code': -1, 'msg': '软件名称不能为空！'}
        return install_package(name)
    elif action == 'refresh':
        return refresh_cache()
    else:
        return {'code': -1, 'msg': '未定义的操作！'}
