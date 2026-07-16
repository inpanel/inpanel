# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Homebrew 管理模块

概念说明：
- 软件仓库（repository / tap）：brew tap 管理的仓库。内置官方仓库（homebrew/core、
  homebrew/cask）不可编辑/不可删除，自定义仓库可添加/删除。
- 镜像源（mirror）：内置官方仓库的 git remote URL。在仓库详情中可切换镜像源 URL。

交互流程：
  仓库列表 → 点击"详情" → 查看仓库信息 → 如果是内置仓库，可切换镜像源 URL
'''

import json
import os
import time
from pathlib import Path
from subprocess import getstatusoutput

from ..base import kernel_name

from ..base import config_path

from ..templates.sources import load_brew

_cfg = load_brew()

_BREW_BUILTIN_TAPS = _cfg['brew_builtin_taps']
_BREW_TAP_TEMPLATES = _cfg['brew_tap_templates']
_BREW_BUILTIN_MIRRORS = _cfg['brew_builtin_mirrors']

# ==================================================================
# 镜像源配置持久化（sources_brew.json）
# ==================================================================

def _get_sources_file():
    conf_dir = str(config_path).rstrip('/')
    return os.path.join(conf_dir, 'sources_brew.json')


def _load_sources_config():
    filepath = _get_sources_file()
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, IOError):
            pass
    sources = [{'name': m['name'], 'url': m['url'], 'builtin': m.get('builtin', True)} for m in _BREW_BUILTIN_MIRRORS]
    _save_sources_config(sources)
    return sources


def _save_sources_config(sources):
    filepath = _get_sources_file()
    conf_dir = os.path.dirname(filepath)
    if not os.path.isdir(conf_dir):
        try:
            os.makedirs(conf_dir, exist_ok=True)
        except OSError:
            pass
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def _get_active_url():
    """检测当前 Homebrew 使用的 core tap URL"""
    status, output = getstatusoutput(
        'cd "$(brew --repo homebrew/core)" 2>/dev/null && git remote get-url origin 2>/dev/null'
    )
    if status == 0 and output.strip():
        return output.strip().rstrip('/').rstrip('.git')
    return ''


def get_mirrors():
    """获取镜像源列表"""
    sources = _load_sources_config()
    active_url = _get_active_url()

    mirrors = []
    active_in_list = False

    for s in sources:
        normalized = s['url'].rstrip('/').rstrip('.git')
        is_active = normalized == active_url
        if is_active:
            active_in_list = True
        mirrors.append({
            'name': s['name'],
            'path': s['url'],
            'url': s['url'],
            'status': 'active' if is_active else 'inactive',
            'builtin': s.get('builtin', False),
        })

    if not active_in_list and active_url:
        mirrors.insert(0, {
            'name': '当前源（未注册）',
            'path': active_url,
            'url': active_url,
            'status': 'active',
            'builtin': False,
        })

    return mirrors


# ==================================================================
# 基础函数
# ==================================================================

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
    status['running'] = True
    return status


def service_control(action):
    """brew 服务控制"""
    action_msg = {'start': '启动', 'stop': '停止', 'restart': '重启'}
    if action == 'restart':
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


# ==================================================================
# 软件仓库管理（brew tap）
# ==================================================================

def _tap_path(tap_name):
    """根据 tap 名称推算本地路径"""
    prefix = get_prefix()
    if not prefix:
        return ''
    try:
        user, repo = tap_name.split('/', 1)
    except ValueError:
        return ''
    path1 = Path(prefix) / 'Homebrew' / 'Library' / 'Taps' / user / ('homebrew-' + repo)
    if path1.exists():
        return str(path1)
    path2 = Path(prefix) / 'Library' / 'Taps' / user / ('homebrew-' + repo)
    return str(path2)


def get_tap_list():
    """获取 brew tap 列表（仓库列表），确保内置官方仓库始终在列表中"""
    status, output = _run('brew tap')
    taps = []
    seen_names = set()

    if status == 0:
        for line in output.strip().split('\n'):
            name = line.strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            path = _tap_path(name)
            created = ''
            if path and Path(path).exists():
                try:
                    created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(path).stat().st_ctime))
                except Exception:
                    pass
            taps.append({
                'name': name,
                'path': path,
                'created': created,
                'builtin': name in _BREW_BUILTIN_TAPS,
            })

    # 确保内置官方仓库始终在列表中
    for bt in _BREW_BUILTIN_TAPS:
        if bt not in seen_names:
            path = _tap_path(bt)
            created = ''
            if path and Path(path).exists():
                try:
                    created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(path).stat().st_ctime))
                except Exception:
                    pass
            taps.insert(0, {
                'name': bt,
                'path': path,
                'created': created,
                'builtin': True,
            })

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
    alias_dir = Path(tap_path) / 'Aliases'
    if alias_dir.exists():
        for f in alias_dir.rglob('*'):
            if f.is_file() and not f.name.startswith('.'):
                packages.append({'name': f.name})
    return packages


def get_tap_detail(name):
    """获取某个 tap 的详情（含软件列表、是否内置、镜像源列表）"""
    if not name:
        return None
    path = _tap_path(name)
    created = ''
    if path and Path(path).exists():
        try:
            created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(path).stat().st_ctime))
        except Exception:
            pass
    packages = _list_formula_in_tap(path)
    is_builtin = name in _BREW_BUILTIN_TAPS

    result = {
        'name': name,
        'path': path,
        'created': created,
        'packages': packages,
        'builtin': is_builtin,
    }

    # 如果是内置仓库，附加当前镜像 URL 和可选镜像列表
    if is_builtin:
        current_url = ''
        if path and Path(path).exists():
            s, o = getstatusoutput('cd "%s" && git remote get-url origin 2>/dev/null' % path)
            if s == 0:
                current_url = o.strip()
        result['current_mirror_url'] = current_url
        result['mirrors'] = get_mirrors()

    return result


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


def get_repo_list():
    """获取仓库列表（tap 列表），兼容旧接口"""
    return get_tap_list()


# ==================================================================
# Web Handler
# ==================================================================

def web_handler(context, action):
    """Handle web requests for brew management"""
    name = context.get_argument('name', '') or context.get_argument('repo', '')

    if action == 'overview':
        context.write({'code': 0, 'msg': '', 'data': get_status()})
    elif action == 'services':
        context.write({'code': 0, 'msg': '', 'data': get_services()})
    elif action == 'service':
        op = context.get_argument('op', '')
        if not op:
            context.write({'code': -1, 'msg': '操作类型不能为空！'})
        else:
            context.write(service_control(op))
    elif action == 'list':
        context.write({'code': 0, 'msg': '', 'data': get_tap_list()})
    elif action == 'item':
        if not name:
            context.write({'code': -1, 'msg': '仓库名称不能为空！'})
        else:
            data = get_tap_detail(name)
            if data is None:
                context.write({'code': -1, 'msg': '仓库不存在！'})
            else:
                context.write({'code': 0, 'msg': '', 'data': data})
    elif action == 'search':
        keyword = context.get_argument('keyword', '')
        context.write({'code': 0, 'msg': '', 'data': search_taps(keyword)})
    elif action == 'install':
        if not name:
            context.write({'code': -1, 'msg': '软件名称不能为空！'})
        else:
            context.write(install_package(name))
    elif action == 'refresh':
        context.write(refresh_cache())

    # --- 第三方专用源 ---
    elif action == 'third_party':
        installed_taps = {t['name'] for t in get_tap_list()}
        sources = []
        for t in _BREW_TAP_TEMPLATES:
            sources.append({
                'id': t['id'],
                'name': t['name'],
                'description': t['description'],
                'url': t['url'],
                'installed': t['name'] in installed_taps,
            })
        context.write({'code': 0, 'msg': '', 'data': sources})

    elif action == 'third_party-install':
        source_id = context.get_argument('id', '')
        if not source_id:
            context.write({'code': -1, 'msg': '第三方专用源ID不能为空！'})
            return
        source = None
        for t in _BREW_TAP_TEMPLATES:
            if t['id'] == source_id:
                source = t
                break
        if not source:
            context.write({'code': -1, 'msg': '第三方专用源不存在！'})
            return
        status, output = getstatusoutput('brew tap %s 2>/dev/null' % source['name'])
        if status == 0:
            context.write({'code': 0, 'msg': '第三方专用源「%s」安装成功！' % source['name']})
        else:
            context.write({'code': -1, 'msg': '第三方专用源安装失败：%s' % output})

    # --- 镜像源管理 ---
    elif action == 'mirrors':
        context.write({'code': 0, 'msg': '', 'data': get_mirrors()})

    elif action == 'add':
        # 添加镜像源（兼容旧接口）
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '').strip()
        if not url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        if not source_name:
            source_name = url
        sources = _load_sources_config()
        normalized_url = url.rstrip('/').rstrip('.git')
        for s in sources:
            if s['url'].rstrip('/').rstrip('.git') == normalized_url:
                context.write({'code': -1, 'msg': '该镜像地址已存在！'})
                return
        sources.append({'name': source_name, 'url': url, 'builtin': False})
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': 'Homebrew 镜像源已添加：%s' % url})

    elif action == 'mirror-add':
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '').strip()
        if not url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        if not source_name:
            source_name = url
        sources = _load_sources_config()
        normalized_url = url.rstrip('/').rstrip('.git')
        for s in sources:
            if s['url'].rstrip('/').rstrip('.git') == normalized_url:
                context.write({'code': -1, 'msg': '该镜像地址已存在！'})
                return
        sources.append({'name': source_name, 'url': url, 'builtin': False})
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': 'Homebrew 镜像源已添加：%s' % url})

    elif action == 'mirror-edit':
        if not name:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
            return
        new_url = context.get_argument('url', '').strip()
        new_name = context.get_argument('new_name', '').strip() or name
        if not new_url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        sources = _load_sources_config()
        found = None
        for s in sources:
            if s['name'] == name:
                found = s
                break
        if found is None:
            context.write({'code': -1, 'msg': '镜像源不存在！'})
            return
        if found.get('builtin'):
            context.write({'code': -1, 'msg': '内置镜像源不可编辑！'})
            return
        found['url'] = new_url
        if new_name != name:
            found['name'] = new_name
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': '镜像源已更新'})

    elif action == 'mirror-del' or action == 'del':
        if not name:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
            return
        sources = _load_sources_config()
        found = None
        for s in sources:
            if s['name'] == name:
                found = s
                break
        if found is None:
            context.write({'code': -1, 'msg': '镜像源不存在！'})
            return
        if found.get('builtin'):
            context.write({'code': -1, 'msg': '内置镜像源不可删除！'})
            return
        sources = [s for s in sources if s['name'] != name]
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': '镜像源「%s」已删除' % name})

    elif action == 'enable' or action == 'switch':
        """切换镜像源：修改指定 tap 的 git remote URL"""
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '') or context.get_argument('repo', '')
        tap_name = context.get_argument('repo', '') or context.get_argument('tap', '')  # 指定切换哪个 tap 的镜像

        if not url and not source_name:
            context.write({'code': -1, 'msg': '镜像地址或名称不能为空！'})
            return
        if not url and source_name:
            sources = _load_sources_config()
            for s in sources:
                if s['name'] == source_name:
                    url = s['url']
                    break
        if not url:
            context.write({'code': -1, 'msg': '未找到该镜像源的地址！'})
            return

        # 确定要切换的 tap 路径
        if not tap_name:
            tap_name = 'homebrew/core'

        tap_path = _tap_path(tap_name)
        if not tap_path or not Path(tap_path).exists():
            context.write({'code': -1, 'msg': '未找到 tap「%s」的路径，请确认该仓库已安装' % tap_name})
            return

        status, output = getstatusoutput(
            'cd "%s" && git remote set-url origin %s 2>/dev/null' % (tap_path, url)
        )
        if status == 0:
            context.write({'code': 0, 'msg': 'tap「%s」镜像源已切换至：%s' % (tap_name, source_name or url)})
        else:
            context.write({'code': -1, 'msg': '切换失败：%s' % output})

    # --- 软件仓库管理（tap 操作）---
    elif action == 'tap-add':
        if not name:
            context.write({'code': -1, 'msg': 'tap 名称不能为空！'})
            return
        status, output = getstatusoutput('brew tap %s 2>/dev/null' % name)
        if status == 0:
            context.write({'code': 0, 'msg': 'tap「%s」添加成功！' % name})
        else:
            context.write({'code': -1, 'msg': 'tap 添加失败：%s' % output})

    elif action == 'tap-del':
        if not name:
            context.write({'code': -1, 'msg': 'tap 名称不能为空！'})
            return
        if name in _BREW_BUILTIN_TAPS:
            context.write({'code': -1, 'msg': '内置仓库不可删除！'})
            return
        status, output = getstatusoutput('brew untap %s 2>/dev/null' % name)
        if status == 0:
            context.write({'code': 0, 'msg': 'tap「%s」已删除' % name})
        else:
            context.write({'code': -1, 'msg': 'tap 删除失败：%s' % output})

    # --- 仓库编辑（自定义仓库编辑 tap 的 URL，即修改 git remote）---
    elif action == 'repo-edit':
        if not name:
            context.write({'code': -1, 'msg': '仓库名称不能为空！'})
            return
        if name in _BREW_BUILTIN_TAPS:
            context.write({'code': -1, 'msg': '内置仓库不可编辑，请在详情中切换镜像源！'})
            return
        new_url = context.get_argument('url', '').strip()
        if not new_url:
            context.write({'code': -1, 'msg': '仓库地址不能为空！'})
            return
        tap_path = _tap_path(name)
        if not tap_path or not Path(tap_path).exists():
            context.write({'code': -1, 'msg': '未找到 tap「%s」的路径' % name})
            return
        status, output = getstatusoutput(
            'cd "%s" && git remote set-url origin %s 2>/dev/null' % (tap_path, new_url)
        )
        if status == 0:
            context.write({'code': 0, 'msg': 'tap「%s」地址已更新' % name})
        else:
            context.write({'code': -1, 'msg': '编辑失败：%s' % output})

    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})
