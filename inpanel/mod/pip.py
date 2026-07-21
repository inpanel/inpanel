# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''PIP（Python 包安装器）管理模块

pip 只有单一 index-url，没有多仓库概念。此处管理的是"镜像源 URL"的切换。'''

import json
import re
import time
from pathlib import Path
from subprocess import getstatusoutput

from ..base import config_path


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


from ..templates.sources import load_pip

_cfg = load_pip()

_PIP_BUILTIN_MIRRORS = _cfg['pip_builtin_mirrors']


def _get_pip_sources_file():
    """获取 pip 源配置文件的路径"""
    return str(Path(config_path) / 'sources_pip.json')


def _load_sources_config():
    """加载 sources_pip.json 配置文件。

    如果配置文件不存在，用内置镜像源初始化并写入。
    返回源列表（list of dict），每个 dict 包含 name、url、builtin。
    """
    filepath = _get_pip_sources_file()
    if Path(filepath).is_file():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, IOError):
            pass

    # 配置文件不存在或损坏，用内置源初始化
    sources = [{'name': m['name'], 'url': m['url'], 'builtin': m.get('builtin', True)} for m in _PIP_BUILTIN_MIRRORS]
    _save_sources_config(sources)
    return sources


def _save_sources_config(sources):
    """保存 pip 源配置到 sources_pip.json"""
    filepath = _get_pip_sources_file()
    conf_dir = str(Path(filepath).parent)
    if not Path(conf_dir).is_dir():
        try:
            Path(conf_dir).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def _get_active_url():
    """获取当前激活的 pip index-url（通过 pip config list 检测）"""
    config = _parse_config()
    return config.get('global.index-url', config.get('index-url', '')).rstrip('/')


def get_repo_list():
    """获取 pip 软件源列表。

    从 sources_pip.json 读取所有已注册的源，结合当前系统 pip 配置
    检测哪个源是激活状态：
    - 配置文件中已注册的源：标记 status='active' 或 'inactive'
    - 当前系统启用的源如果不在配置文件中，只在列表显示但不写入配置文件
    """
    sources = _load_sources_config()
    active_url = _get_active_url()
    cfg = _config_file()
    created = ''
    if cfg and Path(cfg).exists():
        try:
            created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(cfg).stat().st_ctime))
        except Exception:
            created = ''

    repos = []
    active_in_file = False

    # 先放当前激活的源（如果它在配置文件中）
    for s in sources:
        if s['url'].rstrip('/') == active_url:
            repos.append({
                'name': s['name'],
                'path': s['url'],
                'url': s['url'],
                'status': 'active',
                'builtin': s.get('builtin', False),
                'config_file': cfg or '-',
                'created': created,
            })
            active_in_file = True
            break

    # 如果当前激活的源不在配置文件中（如用户手动改过 pip config），
    # 也展示在列表第一位，但不写入配置文件
    if not active_in_file and active_url:
        repos.append({
            'name': '当前源（未注册）',
            'path': active_url,
            'url': active_url,
            'status': 'active',
            'builtin': False,
            'config_file': cfg or '-',
            'created': created,
        })

    # 放其余未激活的源（从配置文件）
    for s in sources:
        if s['url'].rstrip('/') != active_url:
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


def web_handler(context, action):
    """Handle web requests for pip management"""
    name = context.get_argument('name', '') or context.get_argument('repo', '')

    if action == 'overview':
        context.write({'code': 0, 'msg': '', 'data': get_status()})
    elif action == 'list':
        context.write({'code': 0, 'msg': '', 'data': get_repo_list()})
    elif action == 'item':
        if not name:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
        else:
            data = get_repo_detail(name)
            if data is None:
                context.write({'code': -1, 'msg': '镜像源不存在！'})
            else:
                context.write({'code': 0, 'msg': '', 'data': data})
    elif action == 'search':
        keyword = context.get_argument('keyword', '')
        context.write({'code': 0, 'msg': '', 'data': search_repos(keyword)})
    elif action == 'install':
        if not name:
            context.write({'code': -1, 'msg': '软件名称不能为空！'})
        else:
            context.write(install_package(name))
    elif action == 'refresh':
        context.write(refresh_cache())
    elif action == 'add':
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '').strip()
        if not url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        if not source_name:
            source_name = url

        # 只持久化写入配置文件，不立即启用
        sources = _load_sources_config()
        normalized_url = url.rstrip('/')
        for s in sources:
            if s['url'].rstrip('/') == normalized_url:
                context.write({'code': -1, 'msg': '该镜像地址已存在！'})
                return
        sources.append({'name': source_name, 'url': url, 'builtin': False})
        _save_sources_config(sources)

        context.write({'code': 0, 'msg': 'pip 镜像源已添加：%s' % url})

    elif action == 'enable':
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '') or context.get_argument('repo', '')
        if not url and not source_name:
            context.write({'code': -1, 'msg': '镜像地址或名称不能为空！'})
            return

        # 如果传了名称，从配置文件中查找 url
        if not url and source_name:
            sources = _load_sources_config()
            for s in sources:
                if s['name'] == source_name:
                    url = s['url']
                    break
        if not url:
            context.write({'code': -1, 'msg': '未找到该镜像源的地址！'})
            return

        # 用 pip config 设置当前激活源
        status, output = _run('config set global.index-url %s' % url)
        if status != 0:
            context.write({'code': -1, 'msg': '切换 pip 镜像源失败：%s' % output})
            return

        context.write({'code': 0, 'msg': 'pip 镜像源已切换至：%s' % (source_name or url)})

    elif action == 'del':
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
    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})
