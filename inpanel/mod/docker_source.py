# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

"""Docker 镜像加速源管理模块

Docker 镜像加速源管理：通过 /etc/docker/daemon.json 中的 registry-mirrors
配置镜像加速地址，加速 docker pull 操作。

交互流程：
  镜像源列表 → 选择镜像 → 切换启用 → 重启 Docker 服务生效
"""

import json
import os
import time
from pathlib import Path

from ..base import config_path

from ..templates.sources import load_docker

_cfg = load_docker()

_DOCKER_BUILTIN_MIRRORS = _cfg['docker_builtin_mirrors']

# Docker daemon 配置文件路径
_DOCKER_DAEMON_PATH = '/etc/docker/daemon.json'


def _get_docker_sources_file():
    """获取 Docker 源配置文件的路径"""
    return os.path.join(config_path, 'sources_docker.json')


def _load_sources_config():
    """加载 sources_docker.json 配置文件。

    如果配置文件不存在，用内置镜像源初始化并写入。
    返回源列表（list of dict），每个 dict 包含 name、url、builtin。
    """
    filepath = _get_docker_sources_file()
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, IOError):
            pass

    # 配置文件不存在或损坏，用内置源初始化
    sources = [{'name': m['name'], 'url': m['url'], 'builtin': m.get('builtin', True)} for m in _DOCKER_BUILTIN_MIRRORS]
    _save_sources_config(sources)
    return sources


def _save_sources_config(sources):
    """保存 Docker 源配置到 sources_docker.json"""
    filepath = _get_docker_sources_file()
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


def _read_daemon_json():
    """读取 /etc/docker/daemon.json 文件

    Returns:
        dict: daemon.json 的内容，如果文件不存在或解析失败返回空 dict
    """
    if not os.path.isfile(_DOCKER_DAEMON_PATH):
        return {}
    try:
        with open(_DOCKER_DAEMON_PATH, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return {}


def _write_daemon_json(config):
    """写入 /etc/docker/daemon.json 文件

    Args:
        config: dict，要写入的配置
    """
    try:
        daemon_dir = os.path.dirname(_DOCKER_DAEMON_PATH)
        if not os.path.isdir(daemon_dir):
            os.makedirs(daemon_dir, exist_ok=True)
        with open(_DOCKER_DAEMON_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write('\n')
    except IOError as e:
        raise IOError(f'写入 {_DOCKER_DAEMON_PATH} 失败：{e}')


def _get_active_mirrors():
    """获取当前 Docker daemon 配置中的 registry-mirrors

    Returns:
        list: 当前配置的镜像源 URL 列表
    """
    daemon_config = _read_daemon_json()
    return daemon_config.get('registry-mirrors', [])


def get_mirror_list():
    """获取 Docker 镜像源列表。

    从 sources_docker.json 读取所有已注册的源，结合当前 daemon.json
    中的 registry-mirrors 检测哪些源是激活状态：
    - 配置文件中已注册的源：标记 status='active' 或 'inactive'
    - 当前系统启用的源如果不在配置文件中，只在列表显示但不写入配置文件
    """
    sources = _load_sources_config()
    active_mirrors = _get_active_mirrors()
    # 标准化 URL 用于比较
    active_set = set(url.rstrip('/') for url in active_mirrors)

    daemon_created = ''
    if Path(_DOCKER_DAEMON_PATH).exists():
        try:
            daemon_created = time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(Path(_DOCKER_DAEMON_PATH).stat().st_ctime)
            )
        except Exception:
            daemon_created = ''

    repos = []
    active_in_file = False

    # 先放当前激活的源（在配置文件中）
    for s in sources:
        normalized = s['url'].rstrip('/')
        if normalized in active_set:
            repos.append({
                'name': s['name'],
                'path': s['url'],
                'url': s['url'],
                'status': 'active',
                'builtin': s.get('builtin', False),
                'config_file': _DOCKER_DAEMON_PATH,
                'created': daemon_created,
            })
            active_in_file = True
            break

    # 如果当前激活的源不在配置文件中
    if not active_in_file and active_mirrors:
        for url in active_mirrors:
            repos.append({
                'name': '当前源（未注册）',
                'path': url,
                'url': url,
                'status': 'active',
                'builtin': False,
                'config_file': _DOCKER_DAEMON_PATH,
                'created': daemon_created,
            })

    # 放其余未激活的源
    for s in sources:
        normalized = s['url'].rstrip('/')
        if normalized not in active_set:
            repos.append({
                'name': s['name'],
                'path': s['url'],
                'url': s['url'],
                'status': 'inactive',
                'builtin': s.get('builtin', False),
                'config_file': '-',
                'created': '-',
            })

    return repos


def get_mirror_detail(name):
    """获取镜像源详情"""
    repos = get_mirror_list()
    for r in repos:
        if r['name'] == name:
            return r
    return None


def switch_mirror(name, url):
    """切换 Docker 镜像源。

    将 daemon.json 的 registry-mirrors 设置为指定的镜像 URL。

    Args:
        name: 镜像源名称
        url: 镜像源 URL

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    if not url:
        return {'code': -1, 'msg': '镜像地址不能为空！'}

    daemon_config = _read_daemon_json()
    url = url.rstrip('/')

    # 设置 registry-mirrors
    daemon_config['registry-mirrors'] = [url]

    try:
        _write_daemon_json(daemon_config)
    except IOError as e:
        return {'code': -1, 'msg': str(e)}

    return {
        'code': 0,
        'msg': f'Docker 镜像源已切换至：{name or url}（需要重启 Docker 服务生效）',
        'need_restart': True,
    }


def add_mirror(name, url):
    """添加 Docker 镜像源到配置文件

    Args:
        name: 镜像源名称
        url: 镜像源 URL

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    if not url:
        return {'code': -1, 'msg': '镜像地址不能为空！'}
    if not name:
        name = url

    sources = _load_sources_config()
    normalized_url = url.rstrip('/')
    for s in sources:
        if s['url'].rstrip('/') == normalized_url:
            return {'code': -1, 'msg': '该镜像地址已存在！'}

    sources.append({'name': name, 'url': url, 'builtin': False})
    _save_sources_config(sources)

    return {'code': 0, 'msg': f'Docker 镜像源已添加：{url}'}


def delete_mirror(name):
    """删除 Docker 镜像源

    Args:
        name: 镜像源名称

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    if not name:
        return {'code': -1, 'msg': '镜像源名称不能为空！'}

    sources = _load_sources_config()
    found = None
    for s in sources:
        if s['name'] == name:
            found = s
            break

    if found is None:
        return {'code': -1, 'msg': '镜像源不存在！'}
    if found.get('builtin'):
        return {'code': -1, 'msg': '内置镜像源不可删除！'}

    sources = [s for s in sources if s['name'] != name]
    _save_sources_config(sources)

    return {'code': 0, 'msg': f'镜像源「{name}」已删除'}


def edit_mirror(name, new_name, new_url):
    """编辑 Docker 镜像源

    Args:
        name: 原镜像源名称
        new_name: 新名称
        new_url: 新 URL

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    if not name:
        return {'code': -1, 'msg': '镜像源名称不能为空！'}
    if not new_url:
        return {'code': -1, 'msg': '镜像地址不能为空！'}
    if not new_name:
        new_name = name

    sources = _load_sources_config()
    found = None
    for s in sources:
        if s['name'] == name:
            found = s
            break

    if found is None:
        return {'code': -1, 'msg': '镜像源不存在！'}
    if found.get('builtin'):
        return {'code': -1, 'msg': '内置镜像源不可编辑！'}

    found['url'] = new_url
    if new_name != name:
        found['name'] = new_name
    _save_sources_config(sources)

    return {'code': 0, 'msg': '镜像源已更新'}


def web_handler(context, action):
    """Handle web requests for Docker mirror management"""
    name = context.get_argument('name', '')

    if action == 'overview':
        daemon_exists = os.path.isfile(_DOCKER_DAEMON_PATH)
        active_mirrors = _get_active_mirrors()
        context.write({
            'code': 0,
            'msg': '',
            'data': {
                'installed': daemon_exists or True,
                'running': True,
                'version': '',
                'config_path': _DOCKER_DAEMON_PATH,
                'active_mirrors': active_mirrors,
            }
        })

    elif action == 'list':
        context.write({'code': 0, 'msg': '', 'data': get_mirror_list()})

    elif action == 'item':
        if not name:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
        else:
            data = get_mirror_detail(name)
            if data is None:
                context.write({'code': -1, 'msg': '镜像源不存在！'})
            else:
                context.write({'code': 0, 'msg': '', 'data': data})

    elif action == 'enable' or action == 'switch':
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '').strip()
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
        context.write(switch_mirror(source_name, url))

    elif action == 'add':
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '').strip()
        if not url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        context.write(add_mirror(source_name, url))

    elif action == 'edit':
        if not name:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
            return
        new_url = context.get_argument('url', '').strip()
        new_name = context.get_argument('new_name', '').strip()
        if not new_url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        context.write(edit_mirror(name, new_name or name, new_url))

    elif action == 'del':
        if not name:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
            return
        context.write(delete_mirror(name))

    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})
