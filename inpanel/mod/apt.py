# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''APT 软件源管理模块

概念说明：
- 镜像源（mirror）：基础发行版仓库的 URL 地址，切换本质是修改已有 .list 文件中 deb URL 的域名。
- 软件仓库（repo）：完整的 .list 配置文件，可以添加自定义仓库来安装特定软件（如 PHP SURY、NodeSource）。
'''

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from .. import base
from . import file
from ..templates.sources import load_apt
_apt_cfg = load_apt()
apt_sources = _apt_cfg['apt_sources']
_APT_BUILTIN_MIRRORS = _apt_cfg['apt_builtin_mirrors']

sources_list_path = '/etc/apt/sources.list'
sources_list_d_path = '/etc/apt/sources.list.d'

from ..base import config_path


# ==================================================================
# 镜像源管理（持久化到 sources_apt.json）
# ==================================================================

def _get_sources_file():
    conf_dir = str(config_path).rstrip('/')
    return os.path.join(conf_dir, 'sources_apt.json')


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
    sources = [{'name': m['name'], 'url': m['url'], 'builtin': m.get('builtin', True)} for m in _APT_BUILTIN_MIRRORS]
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
    """检测当前系统中启用的 apt 源 URL（取第一个启用的 deb 行）"""
    for filepath in _all_source_files():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and line.startswith('deb '):
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1].rstrip('/')
        except Exception:
            pass
    return ''


def _all_source_files():
    """获取所有 sources.list 文件路径"""
    files = []
    if Path(sources_list_path).exists():
        files.append(sources_list_path)
    d = Path(sources_list_d_path)
    if d.exists():
        for f in sorted(d.glob('*.list')):
            files.append(str(f))
    return files


def _extract_domain(url):
    """从 URL 中提取域名（scheme://host）"""
    try:
        p = urlparse(url)
        return '%s://%s' % (p.scheme, p.netloc)
    except Exception:
        return url


def get_mirrors():
    """获取镜像源列表"""
    sources = _load_sources_config()
    active_url = _get_active_url()
    active_domain = _extract_domain(active_url) if active_url else ''

    mirrors = []
    active_in_list = False

    for s in sources:
        mirror_domain = _extract_domain(s['url'])
        is_active = active_domain and mirror_domain == active_domain
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
# 软件仓库管理（系统 .list 文件）
# ==================================================================

def get_list():
    '''get sources list'''
    res = []
    if base.kernel_name in ('Linux'):
        if Path(sources_list_path).exists():
            res.append('sources.list')
        if Path(sources_list_d_path).exists() and Path(sources_list_d_path).is_dir():
            items = sorted(os.listdir(sources_list_d_path))
            for item in items:
                if item.endswith('.list'):
                    res.append('sources.list.d/' + item)
        return res if len(res) > 0 else []
    elif base.kernel_name in ('Darwin'):
        return None
    else:
        return None


def _source_full_path(source):
    '''get full path of a source'''
    if source == 'sources.list':
        return sources_list_path
    elif source.startswith('sources.list.d/'):
        filename = source[len('sources.list.d/'):]
        return str(Path(sources_list_d_path) / filename)
    else:
        return str(Path(sources_list_d_path) / source)


def item_exists(source):
    '''check if source file exists'''
    if source == 'sources.list':
        return Path(sources_list_path).exists()
    elif source.startswith('sources.list.d/'):
        filename = source[len('sources.list.d/'):]
        return Path(sources_list_d_path, filename).exists()
    return False


def get_item(source):
    '''get source config content'''
    if not source:
        return None

    filepath = _source_full_path(source)

    if Path(filepath).exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {'content': content, 'path': filepath}
        except Exception as e:
            return None
    return None


def set_item(source, data):
    '''set source config content'''
    if not source or not data:
        return False

    filepath = _source_full_path(source)

    if Path(filepath).exists():
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data.get('content', ''))
            return True
        except Exception as e:
            return False
    else:
        return False


def add_item(source, data):
    '''add source config file'''
    if not source or not data:
        return False

    filepath = _source_full_path(source)

    if Path(filepath).exists():
        return False

    try:
        parent_dir = Path(filepath).parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data.get('content', ''))
        return True
    except Exception as e:
        return False


def del_item(source):
    '''delete source file'''
    if not source:
        return None

    filepath = _source_full_path(source)
    return file.delete(filepath)


def parse_sources(content):
    '''parse sources.list content into structured data'''
    sources = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        match = re.match(r'^(deb|deb-src)\s+(\[.*?\]\s+)?(\S+)\s+(\S+)(?:\s+(.+))?$', line)
        if match:
            source_type = match.group(1)
            url = match.group(3)
            distribution = match.group(4)
            components = match.group(5).split() if match.group(5) else []

            sources.append({
                'type': source_type,
                'url': url,
                'distribution': distribution,
                'components': components
            })
    return sources


def generate_sources(sources):
    '''generate sources.list content from structured data'''
    lines = []
    for source in sources:
        components_str = ' '.join(source.get('components', []))
        if components_str:
            line = f"{source['type']} {source['url']} {source['distribution']} {components_str}"
        else:
            line = f"{source['type']} {source['url']} {source['distribution']}"
        lines.append(line)
    return '\n'.join(lines) + '\n'


def get_repo_sury(version):
    '''install sury php repository'''
    cmds = []
    cmds.append('apt-get install -y apt-transport-https lsb-release ca-certificates curl')
    cmds.append('curl -sSLo /usr/share/keyrings/deb.sury.org-php.gpg https://packages.sury.org/php/apt.gpg')
    cmds.append(f'echo "deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/php.list')
    cmds.append('apt-get update')
    return cmds


def get_repo_nginx():
    '''install nginx official repository'''
    cmds = []
    cmds.append('apt-get install -y apt-transport-https lsb-release ca-certificates curl')
    cmds.append('curl -sSLo /usr/share/keyrings/nginx-archive-keyring.gpg https://nginx.org/keys/nginx_signing.key')
    cmds.append('echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] http://nginx.org/packages/mainline/debian/ $(lsb_release -sc) nginx" > /etc/apt/sources.list.d/nginx.list')
    cmds.append('echo -e "Package: *\\nPin: origin nginx.org\\nPin: release o=nginx\\nPin-Priority: 900\\n" > /etc/apt/preferences.d/99nginx')
    cmds.append('apt-get update')
    return cmds


def get_repo_mariadb(mariadb_version):
    '''install mariadb official repository'''
    cmds = []
    cmds.append('apt-get install -y apt-transport-https lsb-release ca-certificates curl')
    cmds.append('curl -sSLo /usr/share/keyrings/mariadb-keyring.pgp https://mariadb.org/mariadb_release_signing_key.pgp')
    cmds.append(f'echo "deb [signed-by=/usr/share/keyrings/mariadb-keyring.pgp] https://ftp.osuosl.org/pub/mariadb/repo/{mariadb_version}/debian $(lsb_release -sc) main" > /etc/apt/sources.list.d/mariadb.list')
    cmds.append('apt-get update')
    return cmds


def get_repo_nodesource(node_version):
    '''install nodesource repository'''
    cmds = []
    cmds.append(f'curl -fsSL https://deb.nodesource.com/setup_{node_version}.x | bash -')
    cmds.append('apt-get update')
    return cmds


def get_repo_elastic(stack_version):
    '''install elastic repository'''
    cmds = []
    cmds.append('apt-get install -y apt-transport-https lsb-release ca-certificates curl')
    cmds.append('curl -sSLo /usr/share/keyrings/elasticsearch-keyring.gpg https://artifacts.elastic.co/GPG-KEY-elasticsearch')
    cmds.append(f'echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/{stack_version}.x/apt stable main" > /etc/apt/sources.list.d/elastic.list')
    cmds.append('apt-get update')
    return cmds


import shutil
import time
from subprocess import getstatusoutput


def is_installed():
    '''check if apt is installed'''
    return shutil.which('apt') is not None


def get_version():
    '''get apt version'''
    if not is_installed():
        return ''
    status, output = getstatusoutput('apt --version')
    if status != 0:
        return ''
    return output.strip().split('\n')[0]


def get_status():
    '''get apt status'''
    status = {
        'installed': is_installed(),
        'version': '',
        'running': False,
        'config_path': sources_list_d_path,
    }
    if status['installed']:
        status['version'] = get_version()
        status['running'] = True
    return status


def refresh_cache():
    '''apt update'''
    if not is_installed():
        return {'code': -1, 'msg': 'apt 未安装！'}
    status, output = getstatusoutput('apt update 2>&1')
    if status == 0:
        return {'code': 0, 'msg': 'apt 索引已更新！'}
    return {'code': -1, 'msg': 'apt 索引更新失败：%s' % output}


def get_repo_list():
    '''get structured source list with name/path/created（.list 文件列表）'''
    if base.kernel_name != 'Linux':
        return None
    items = get_list() or []
    repos = []
    for item in items:
        full = _source_full_path(item)
        created = ''
        try:
            created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(full).stat().st_ctime))
        except Exception:
            pass
        repos.append({'name': item, 'path': full, 'created': created})
    return repos


def get_repo_detail(source):
    '''get source detail with package list'''
    if not source:
        return None
    data = get_item(source)
    if data is None:
        return None
    full = _source_full_path(source)
    created = ''
    try:
        created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(full).stat().st_ctime))
    except Exception:
        pass
    # apt 无法精确按源列出包，这里列出系统已安装包作为参考
    packages = []
    st, out = getstatusoutput('dpkg -l 2>/dev/null')
    if st == 0 and out:
        for line in out.split('\n'):
            if line.startswith('ii '):
                parts = line.split()
                if len(parts) >= 3:
                    packages.append({'name': parts[1], 'version': parts[2]})
    return {'name': source, 'path': full, 'created': created, 'content': data.get('content', ''), 'packages': packages}


def search_repos(keyword):
    '''search source files by name'''
    if not keyword:
        return []
    items = get_repo_list() or []
    kw = keyword.lower()
    return [r for r in items if kw in r['name'].lower()]


def install_package(name):
    '''install package via apt'''
    if not name:
        return {'code': -1, 'msg': '软件名称不能为空！'}
    if not is_installed():
        return {'code': -1, 'msg': 'apt 未安装！'}
    status, output = getstatusoutput('apt install -y %s 2>&1' % name)
    if status == 0:
        return {'code': 0, 'msg': '软件 %s 安装成功！' % name, 'data': output}
    return {'code': -1, 'msg': '软件 %s 安装失败：%s' % (name, output)}


# ==================================================================
# Web Handler
# ==================================================================

def web_handler(context, action):
    '''Handle web requests for APT repository management'''
    source = context.get_argument('source', '') or context.get_argument('name', '')

    if action == 'overview':
        context.write({'code': 0, 'msg': '', 'data': get_status()})
    elif action == 'refresh':
        context.write(refresh_cache())
    elif action == 'list':
        items = get_repo_list()
        if items is None:
            context.write({'code': -1, 'msg': '获取配置失败！'})
        else:
            context.write({'code': 0, 'msg': '', 'data': items})
    elif action == 'item':
        if not source:
            context.write({'code': -1, 'msg': '配置文件不能为空！'})
        else:
            data = get_repo_detail(source)
            if data is None:
                context.write({'code': -1, 'msg': '配置文件不存在！'})
            else:
                context.write({'code': 0, 'msg': '', 'data': data})
    elif action == 'search':
        keyword = context.get_argument('keyword', '')
        context.write({'code': 0, 'msg': '', 'data': search_repos(keyword)})
    elif action == 'install':
        context.write(install_package(source))

    # --- 镜像源管理 ---
    elif action == 'mirrors':
        context.write({'code': 0, 'msg': '', 'data': get_mirrors()})

    elif action == 'mirror-add':
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '').strip()
        if not url:
            context.write({'code': -1, 'msg': '镜像地址不能为空！'})
            return
        if not source_name:
            source_name = url
        sources = _load_sources_config()
        normalized_url = url.rstrip('/')
        for s in sources:
            if s['url'].rstrip('/') == normalized_url:
                context.write({'code': -1, 'msg': '该镜像地址已存在！'})
                return
        sources.append({'name': source_name, 'url': url, 'builtin': False})
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': 'APT 镜像源已添加：%s' % url})

    elif action == 'mirror-del':
        if not source:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
            return
        sources = _load_sources_config()
        found = None
        for s in sources:
            if s['name'] == source:
                found = s
                break
        if found is None:
            context.write({'code': -1, 'msg': '镜像源不存在！'})
            return
        if found.get('builtin'):
            context.write({'code': -1, 'msg': '内置镜像源不可删除！'})
            return
        sources = [s for s in sources if s['name'] != source]
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': '镜像源「%s」已删除' % source})

    elif action == 'switch':
        """切换镜像源：替换已有 .list 文件中 deb URL 的域名"""
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '') or context.get_argument('source', '')
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

        new_url = url.rstrip('/')
        new_domain = _extract_domain(new_url)

        modified_count = 0
        for filepath in _all_source_files():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 替换所有非注释行中的 deb URL 域名
                new_lines = []
                has_change = False
                for line in content.split('\n'):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and (stripped.startswith('deb ') or stripped.startswith('deb-src ')):
                        parts = line.split(None, 2)
                        if len(parts) >= 2:
                            # parts[0] = deb/deb-src, parts[1] = [options] or URL
                            # 跳过带 options 的行（如 [signed-by=...]）
                            if parts[1].startswith('['):
                                if len(parts) >= 3:
                                    old_url = parts[2]
                                    old_domain = _extract_domain(old_url)
                                    if old_domain:
                                        parts[2] = old_url.replace(old_domain, new_domain, 1)
                                        line = ' '.join(parts)
                                        has_change = True
                            else:
                                old_url = parts[1]
                                old_domain = _extract_domain(old_url)
                                if old_domain:
                                    parts[1] = old_url.replace(old_domain, new_domain, 1)
                                    line = ' '.join(parts)
                                    has_change = True
                    new_lines.append(line)

                if has_change:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    modified_count += 1
            except Exception:
                pass

        if modified_count > 0:
            context.write({'code': 0, 'msg': 'APT 镜像源已切换至：%s（修改了 %d 个源文件）' % (source_name or url, modified_count)})
        else:
            context.write({'code': -1, 'msg': '没有找到需要切换的源文件'})

    # --- 软件仓库管理（.list 文件操作）---
    elif action == 'repo-add':
        content = context.get_argument('content', '').strip()
        if not content:
            context.write({'code': -1, 'msg': '源配置内容不能为空！'})
            return
        repo_file = source or context.get_argument('source', '') or context.get_argument('repo', '')
        if not repo_file:
            context.write({'code': -1, 'msg': '文件名不能为空！'})
            return
        if not repo_file.endswith('.list'):
            repo_file += '.list'
        if not repo_file.startswith('sources.list.d/'):
            repo_file = 'sources.list.d/' + repo_file

        if item_exists(repo_file):
            context.write({'code': -1, 'msg': '仓库文件「%s」已存在！' % repo_file})
        elif add_item(repo_file, {'content': content}) is True:
            context.write({'code': 0, 'msg': '仓库「%s」添加成功！' % repo_file})
        else:
            context.write({'code': -1, 'msg': '仓库添加失败！'})

    elif action == 'repo-edit':
        if not source:
            context.write({'code': -1, 'msg': '配置文件不能为空！'})
            return
        content = context.get_argument('content', '')
        if not content:
            context.write({'code': -1, 'msg': '配置内容不能为空！'})
            return
        if not item_exists(source):
            context.write({'code': -1, 'msg': '配置文件不存在！'})
        elif set_item(source, {'content': content}) is True:
            context.write({'code': 0, 'msg': '仓库配置修改成功！'})
        else:
            context.write({'code': -1, 'msg': '仓库配置修改失败！'})

    elif action == 'repo-del':
        if not source:
            context.write({'code': -1, 'msg': '仓库文件名不能为空！'})
        elif not item_exists(source):
            context.write({'code': -1, 'msg': '仓库文件不存在！'})
        elif del_item(source):
            context.write({'code': 0, 'msg': '仓库「%s」已删除' % source})
        else:
            context.write({'code': -1, 'msg': '仓库删除失败！'})

    elif action == 'parse':
        content = context.get_argument('content', '')
        if not content:
            context.write({'code': -1, 'msg': '内容不能为空！'})
        else:
            sources = parse_sources(content)
            context.write({'code': 0, 'msg': '', 'data': sources})

    elif action == 'generate':
        sources = context.get_argument('sources', [])
        content = generate_sources(sources)
        context.write({'code': 0, 'msg': '', 'data': {'content': content}})

    # --- 第三方专用源 ---
    elif action == 'third_party':
        context.write(_get_apt_third_party())

    elif action == 'third_party-install':
        source_id = context.get_argument('id', '')
        context.write(_install_apt_third_party(source_id))

    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})


# ==================================================================
# APT 第三方专用源
# ==================================================================

_APT_THIRD_PARTY_CACHE = None


def _load_apt_third_party():
    """加载第三方专用源配置文件"""
    global _APT_THIRD_PARTY_CACHE
    if _APT_THIRD_PARTY_CACHE is not None:
        return _APT_THIRD_PARTY_CACHE
    try:
        from pathlib import Path as _Path
        from .. import base
        _path = _Path(base.root_path) / 'templates' / 'sources' / 'third_party.json'
        with open(_path, 'r', encoding='utf-8') as f:
            _APT_THIRD_PARTY_CACHE = json.load(f)
    except Exception:
        _APT_THIRD_PARTY_CACHE = []
    return _APT_THIRD_PARTY_CACHE


def _get_installed_list_files():
    """获取已安装的 .list 文件列表"""
    try:
        d = Path(sources_list_d_path)
        if not d.exists():
            return set()
        return {f.name for f in d.glob('*.list') if f.is_file()}
    except Exception:
        return set()


def _get_apt_third_party():
    """获取适配 Debian/Ubuntu 的第三方专用源列表"""
    sources = _load_apt_third_party()
    installed_files = _get_installed_list_files()

    result = []
    for s in sources:
        platforms = s.get('platform', [])
        if 'debian' not in platforms:
            continue

        debian_cfg = s.get('debian', {})
        repo_file = debian_cfg.get('repo_file', s.get('repo_file', ''))

        installed = repo_file in installed_files if repo_file else False

        result.append({
            'id': s['id'],
            'name': s['name'],
            'description': s.get('description', ''),
            'category': s.get('category', ''),
            'packages': s.get('packages', []),
            'installed': installed,
            'multi_version': s.get('multi_version', False),
            'note': s.get('note', ''),
            'repo_file': repo_file,
        })

    category_order = {'Base': 0, 'PHP': 1, 'Web Server': 2, 'Database': 3, 'Cache': 4,
                      'Runtime': 5, 'Container': 6, 'DevOps': 7, 'Monitor': 8,
                      'Log & Search': 9, 'Message Queue': 10, 'Tools': 11}
    result.sort(key=lambda x: category_order.get(x['category'], 99))
    return {'code': 0, 'msg': '', 'data': result}


def _install_apt_third_party(source_id):
    """安装 APT 第三方专用源"""
    sources = _load_apt_third_party()
    source = None
    for s in sources:
        if s['id'] == source_id:
            source = s
            break
    if not source:
        return {'code': -1, 'msg': '第三方专用源不存在！'}

    platforms = source.get('platform', [])
    if 'debian' not in platforms:
        return {'code': -1, 'msg': '该第三方专用源不支持当前系统平台！'}

    debian_cfg = source.get('debian', {})
    repo_file = debian_cfg.get('repo_file', source.get('repo_file', ''))
    repo_line = debian_cfg.get('repo_line', '')
    gpgkey_url = debian_cfg.get('gpgkey', source.get('gpgkey', ''))

    if not repo_file:
        return {'code': -1, 'msg': '第三方专用源配置信息不完整！'}

    # 对于有现成安装命令的源，使用专用函数
    source_id_lower = source_id.lower()

    if source_id == 'sury-php':
        cmds = get_repo_sury('')
        return _exec_apt_install_cmds(cmds, source['name'])

    elif source_id == 'nginx-official':
        cmds = get_repo_nginx()
        return _exec_apt_install_cmds(cmds, source['name'])

    elif source_id == 'mariadb-official':
        cmds = get_repo_mariadb('10.11')
        return _exec_apt_install_cmds(cmds, source['name'])

    elif source_id == 'nodesource':
        cmds = get_repo_nodesource('22')
        return _exec_apt_install_cmds(cmds, source['name'])

    elif source_id.startswith('elastic'):
        cmds = get_repo_elastic('8')
        return _exec_apt_install_cmds(cmds, source['name'])

    # 通用安装：使用 repo_line 写入 .list 文件
    if not repo_line:
        return {'code': -1, 'msg': '该第三方专用源暂无自动安装脚本，请手动添加源配置！'}

    # 下载 GPG key
    if gpgkey_url:
        keyring_name = source_id.replace('-', '_') + '.gpg'
        keyring_path = '/usr/share/keyrings/' + keyring_name
        status, output = getstatusoutput(
            'curl -fsSL %s | gpg --dearmor -o %s 2>&1' % (gpgkey_url, keyring_path))
        if status != 0:
            return {'code': -1, 'msg': 'GPG 密钥下载失败：%s' % output}

    # 写入 .list 文件
    list_path = str(Path(sources_list_d_path) / repo_file)
    try:
        parent = Path(list_path).parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        with open(list_path, 'w', encoding='utf-8') as f:
            f.write(repo_line + '\n')
    except Exception as e:
        return {'code': -1, 'msg': '写入源文件失败：%s' % str(e)}

    # apt update
    status, output = getstatusoutput('apt-get update 2>&1')
    if status == 0:
        return {'code': 0, 'msg': '第三方专用源「%s」安装成功！' % source['name']}
    return {'code': -1, 'msg': 'apt update 失败：%s' % output}


def _exec_apt_install_cmds(cmds, repo_name):
    """执行 APT 安装命令序列"""
    for cmd in cmds:
        status, output = getstatusoutput(cmd + ' 2>&1')
        if status != 0:
            return {'code': -1, 'msg': '仓库「%s」安装失败：%s' % (repo_name, output)}
    return {'code': 0, 'msg': '仓库「%s」安装成功！' % repo_name}


if __name__ == '__main__':
    l = get_list()
    print(l)
    if l:
        i = l[0]
        print(i)
        c = get_item(i)
        print(c)
