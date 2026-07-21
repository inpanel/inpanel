# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''YUM 管理模块

概念说明：
- 镜像源（mirror）：基础发行版仓库的 URL 地址，切换本质是修改已有 .repo 文件中 baseurl 的域名。
- 软件仓库（repo）：完整的 .repo 配置文件，可以添加自定义仓库来安装特定软件（如 remi、epel）。
'''

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from .. import base
from . import config
from . import file
from ..base import config_path as _base_config_path
from ..templates.sources import load_yum
_yum_cfg = load_yum()
yum_reporpms = _yum_cfg['yum_reporpms']
_YUM_BUILTIN_MIRRORS = _yum_cfg['yum_builtin_mirrors']

config_path = '/etc/yum.repos.d'


# ==================================================================
# 镜像源管理（持久化到 sources_yum.json）
# ==================================================================
def _get_sources_file():
    conf_dir = str(_base_config_path).rstrip('/')
    return str(Path(conf_dir) / 'sources_yum.json')


def _load_sources_config():
    filepath = _get_sources_file()
    if Path(filepath).is_file():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, IOError):
            pass
    sources = [{'name': m['name'], 'url': m['url'], 'builtin': m.get('builtin', True)} for m in _YUM_BUILTIN_MIRRORS]
    _save_sources_config(sources)
    return sources


def _save_sources_config(sources):
    filepath = _get_sources_file()
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
    """检测当前系统中启用的 yum baseurl（取第一个启用的 repo 的 baseurl）"""
    d = Path(config_path)
    if not d.exists():
        return ''
    for repo_file in sorted(d.glob('*.repo')):
        try:
            cfg = config.Config(str(repo_file))
            data = cfg.get_config()
            for rid, rdata in data.items():
                if rdata.get('enabled') in (1, '1', True):
                    bu = rdata.get('baseurl', '')
                    if bu:
                        return bu.strip('/')
        except Exception:
            pass
    return ''


def _extract_domain(url):
    """从 URL 中提取域名（scheme://host）"""
    try:
        p = urlparse(url)
        return '%s://%s' % (p.scheme, p.netloc)
    except Exception:
        return url


def get_mirrors():
    """获取镜像源列表（用于镜像URL切换）

    从 sources_yum.json 读取所有已注册的镜像源，结合当前系统
    检测哪个源是激活状态。
    """
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

    # 如果当前激活的镜像不在配置文件中
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
# 软件仓库管理（系统 .repo 文件）
# ==================================================================

def get_list():
    '''get repo list'''
    res = []
    if base.kernel_name in ('Linux'):
        d = str(Path(config_path))
        if not Path(d).exists() or not Path(d).is_dir():
            return None
        items = sorted(p.name for p in Path(d).iterdir())
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
    '''get structured repo list with name/path/created（.repo 文件列表）'''
    if base.kernel_name != 'Linux':
        return None
    d = Path(config_path)
    if not d.exists() or not d.is_dir():
        return []
    items = sorted(p.name for p in Path(d).iterdir())
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


# ==================================================================
# Web Handler
# ==================================================================

def web_handler(context, action):
    '''Handle web requests for YUM repository management

    支持的 action：
    - overview / refresh / list / item / search / install  : 通用操作
    - mirrors       : 获取镜像源列表（用于URL切换）
    - mirror-add    : 添加自定义镜像URL
    - mirror-del    : 删除自定义镜像URL
    - switch        : 切换镜像源（修改已有 .repo 文件中的 baseurl 域名）
    - repo-add      : 添加仓库（写入新的 .repo 文件）
    - repo-edit     : 编辑仓库
    - repo-del      : 删除仓库（删除 .repo 文件）
    '''
    repo = context.get_argument('repo', '') or context.get_argument('name', '')

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
        if not repo:
            context.write({'code': -1, 'msg': '配置文件不能为空！'})
        else:
            data = get_repo_detail(repo)
            if data is None:
                context.write({'code': -1, 'msg': '配置文件不存在！'})
            else:
                context.write({'code': 0, 'msg': '', 'data': data})
    elif action == 'search':
        keyword = context.get_argument('keyword', '')
        context.write({'code': 0, 'msg': '', 'data': search_repos(keyword)})
    elif action == 'install':
        context.write(install_package(repo))

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
        context.write({'code': 0, 'msg': 'YUM 镜像源已添加：%s' % url})

    elif action == 'mirror-del':
        if not repo:
            context.write({'code': -1, 'msg': '镜像源名称不能为空！'})
            return
        sources = _load_sources_config()
        found = None
        for s in sources:
            if s['name'] == repo:
                found = s
                break
        if found is None:
            context.write({'code': -1, 'msg': '镜像源不存在！'})
            return
        if found.get('builtin'):
            context.write({'code': -1, 'msg': '内置镜像源不可删除！'})
            return
        sources = [s for s in sources if s['name'] != repo]
        _save_sources_config(sources)
        context.write({'code': 0, 'msg': '镜像源「%s」已删除' % repo})

    elif action == 'switch':
        """切换镜像源：替换已有 .repo 文件中 baseurl 的域名部分"""
        url = context.get_argument('url', '').strip()
        source_name = context.get_argument('name', '') or context.get_argument('repo', '')
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

        d = Path(config_path)
        if not d.exists():
            context.write({'code': -1, 'msg': '未找到 YUM 配置目录！'})
            return

        modified_count = 0
        for repo_file in sorted(d.glob('*.repo')):
            try:
                cfg = config.Config(str(repo_file))
                data = cfg.get_config()
                updated = {}
                has_change = False
                for rid, rdata in data.items():
                    old_baseurl = rdata.get('baseurl', '')
                    if not old_baseurl:
                        updated[rid] = rdata
                        continue
                    # 提取旧域名，替换为新域名，保留路径
                    old_domain = _extract_domain(old_baseurl)
                    if old_domain:
                        new_baseurl = old_baseurl.replace(old_domain, new_domain, 1)
                    else:
                        new_baseurl = old_baseurl
                    rdata['baseurl'] = new_baseurl
                    updated[rid] = rdata
                    if new_baseurl != old_baseurl:
                        has_change = True

                if has_change:
                    config.Config(str(repo_file), updated)
                    modified_count += 1
            except Exception:
                pass

        if modified_count > 0:
            context.write({'code': 0, 'msg': 'YUM 镜像源已切换至：%s（修改了 %d 个仓库文件）' % (source_name or url, modified_count)})
        else:
            context.write({'code': -1, 'msg': '没有找到需要切换的 .repo 文件'})

    # --- 软件仓库管理（.repo 文件操作）---
    elif action == 'repo-add':
        serverid = context.get_argument('serverid', '')
        if not serverid:
            context.write({'code': -1, 'msg': '仓库标识ID不能为空！'})
            return
        name = context.get_argument('name', '')
        if not name:
            context.write({'code': -1, 'msg': '仓库名称不能为空！'})
            return
        baseurl = context.get_argument('baseurl', '')
        if not baseurl:
            context.write({'code': -1, 'msg': '仓库地址不能为空！'})
            return
        repo_file = context.get_argument('repo', '')
        if not repo_file:
            repo_file = '%s.repo' % serverid

        enabled = context.get_argument('enabled', True)
        gpgcheck = context.get_argument('gpgcheck', False)
        gpgkey = context.get_argument('gpgkey', '')

        data = {
            serverid: {
                'name': name,
                'enabled': 0 if not enabled else 1,
                'baseurl': baseurl,
                'gpgcheck': 0 if not gpgcheck else 1,
                'gpgkey': gpgkey,
            }
        }

        if item_exists(repo_file):
            context.write({'code': -1, 'msg': '仓库文件「%s」已存在！' % repo_file})
        elif add_item(repo_file, data) is True:
            context.write({'code': 0, 'msg': '仓库「%s」添加成功！' % repo_file})
        else:
            context.write({'code': -1, 'msg': '仓库添加失败！'})

    elif action == 'repo-edit':
        if not repo:
            context.write({'code': -1, 'msg': '配置文件不能为空！'})
            return
        serverid = context.get_argument('serverid', '')
        if not serverid:
            context.write({'code': -1, 'msg': '仓库标识ID不能为空！'})
            return
        name = context.get_argument('name', '')
        if not name:
            context.write({'code': -1, 'msg': '仓库名称不能为空！'})
            return
        baseurl = context.get_argument('baseurl', '')
        if not baseurl:
            context.write({'code': -1, 'msg': '仓库地址不能为空！'})
            return

        enabled = context.get_argument('enabled', True)
        gpgcheck = context.get_argument('gpgcheck', False)
        gpgkey = context.get_argument('gpgkey', '')

        data = {
            serverid: {
                'name': name,
                'enabled': 0 if not enabled else 1,
                'baseurl': baseurl,
                'gpgcheck': 0 if not gpgcheck else 1,
                'gpgkey': gpgkey,
            }
        }

        if not item_exists(repo):
            context.write({'code': -1, 'msg': '配置文件不存在！'})
        elif set_item(repo, data) is True:
            context.write({'code': 0, 'msg': '仓库配置修改成功！'})
        else:
            context.write({'code': -1, 'msg': '仓库配置修改失败！'})

    elif action == 'repo-del':
        if not repo:
            context.write({'code': -1, 'msg': '仓库文件名不能为空！'})
        elif not item_exists(repo):
            context.write({'code': -1, 'msg': '仓库文件不存在！'})
        elif del_item(repo):
            context.write({'code': 0, 'msg': '仓库「%s」已删除' % repo})
        else:
            context.write({'code': -1, 'msg': '仓库删除失败！'})

    # --- 第三方专用源 ---
    elif action == 'third_party':
        context.write(_get_third_party('rhel'))

    elif action == 'third_party-install':
        source_id = context.get_argument('id', '')
        context.write(_install_third_party(source_id, 'rhel'))

    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})


# ==================================================================
# 第三方专用源（共享）
# ==================================================================

_THIRD_PARTY_CACHE = None


def _load_third_party():
    """加载第三方专用源配置文件"""
    global _THIRD_PARTY_CACHE
    if _THIRD_PARTY_CACHE is not None:
        return _THIRD_PARTY_CACHE
    try:
        from pathlib import Path as _Path
        from .. import base
        _path = _Path(base.root_path) / 'templates' / 'sources' / 'third_party.json'
        with open(_path, 'r', encoding='utf-8') as f:
            _THIRD_PARTY_CACHE = json.load(f)
    except Exception:
        _THIRD_PARTY_CACHE = []
    return _THIRD_PARTY_CACHE


def _get_installed_repo_files(pm_type):
    """获取已安装的 .repo 文件列表（用于检测模板是否已安装）"""
    try:
        d = Path(config_path)
        if not d.exists():
            return set()
        return {f.name for f in d.glob('*.repo') if f.is_file()}
    except Exception:
        return set()


def _get_third_party(platform):
    """获取适配当前平台的第三方专用源列表"""
    sources = _load_third_party()
    installed_files = _get_installed_repo_files('yum')

    result = []
    for s in sources:
        platforms = s.get('platform', [])
        if platform not in platforms:
            continue

        repo_file = s.get('repo_file', '')
        if platform == 'rhel':
            rhel_cfg = s.get('rhel', {})
            repo_file = rhel_cfg.get('repo_file', s.get('repo_file', ''))

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

    # 按分类排序
    category_order = {'Base': 0, 'PHP': 1, 'Web Server': 2, 'Database': 3, 'Cache': 4,
                      'Runtime': 5, 'Container': 6, 'DevOps': 7, 'Monitor': 8,
                      'Log & Search': 9, 'Message Queue': 10, 'Tools': 11}
    result.sort(key=lambda x: category_order.get(x['category'], 99))
    return {'code': 0, 'msg': '', 'data': result}


def _get_el_version():
    """获取当前系统的 RHEL/CentOS 主版本号（如 '7', '8', '9'）"""
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('VERSION_ID='):
                    ver = line.strip().split('=')[1].strip('"')
                    return ver.split('.')[0]
    except Exception:
        pass
    try:
        # 兼容 CentOS 7 以下的老版本
        with open('/etc/redhat-release', 'r') as f:
            content = f.read()
            import re
            m = re.search(r'release\s+(\d+)', content)
            if m:
                return m.group(1)
    except Exception:
        pass
    return '9'  # 默认


def _install_third_party(source_id, platform):
    """安装第三方专用源"""
    sources = _load_third_party()
    source = None
    for s in sources:
        if s['id'] == source_id:
            source = s
            break
    if not source:
        return {'code': -1, 'msg': '第三方专用源不存在！'}

    platforms = source.get('platform', [])
    if platform not in platforms:
        return {'code': -1, 'msg': '该第三方专用源不支持当前系统平台！'}

    if platform == 'rhel':
        rhel_cfg = source.get('rhel', {})
        repo_url = rhel_cfg.get('repo_url', source.get('repo_url', ''))
        repo_file = rhel_cfg.get('repo_file', source.get('repo_file', ''))
        gpgkey = rhel_cfg.get('gpgkey', source.get('gpgkey', ''))
    else:
        repo_url = source.get('repo_url', '')
        repo_file = source.get('repo_file', '')
        gpgkey = source.get('gpgkey', '')

    if not repo_file:
        return {'code': -1, 'msg': '仓库配置信息不完整！'}

    # 替换 URL 中的占位符
    el_ver = _get_el_version()
    repo_url = repo_url.replace('{el}', el_ver)

    # 如果 repo_url 是 .rpm 文件，则通过 rpm 安装
    if repo_url.endswith('.rpm'):
        status, output = getstatusoutput('rpm -U %s 2>&1' % repo_url)
        if status == 0:
            return {'code': 0, 'msg': '第三方专用源「%s」安装成功！' % source['name']}
        return {'code': -1, 'msg': '第三方专用源安装失败：%s' % output}

    # 如果是脚本地址（如 mariadb_repo_setup）
    if 'mariadb_repo_setup' in repo_url:
        status, output = getstatusoutput('curl -sSL %s | bash 2>&1' % repo_url)
        if status == 0:
            return {'code': 0, 'msg': '第三方专用源「%s」安装成功！' % source['name']}
        return {'code': -1, 'msg': '第三方专用源安装失败：%s' % output}

    # 如果是 nodesource setup 脚本
    if 'nodesource' in repo_url and 'setup' in repo_url:
        status, output = getstatusoutput('curl -fsSL %s | bash - 2>&1' % repo_url)
        if status == 0:
            return {'code': 0, 'msg': '第三方专用源「%s」安装成功！' % source['name']}
        return {'code': -1, 'msg': '第三方专用源安装失败：%s' % output}

    # 其他情况：创建 .repo 文件
    if repo_url:
        content = _generate_repo_content(source, platform, repo_url)
        if content:
            repo_path = str(Path(config_path) / repo_file)
            try:
                with open(repo_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {'code': 0, 'msg': '第三方专用源「%s」添加成功！' % source['name']}
            except Exception as e:
                return {'code': -1, 'msg': '第三方专用源添加失败：%s' % str(e)}
        return {'code': -1, 'msg': '第三方专用源添加失败！'}

    return {'code': -1, 'msg': '不支持的第三方专用源安装方式！'}


def _generate_repo_content(source, platform, resolved_url=None):
    """根据第三方专用源配置生成 .repo 文件内容"""
    if platform == 'rhel':
        rhel_cfg = source.get('rhel', {})
        baseurl = resolved_url or rhel_cfg.get('repo_url', source.get('repo_url', ''))
        gpgkey = rhel_cfg.get('gpgkey', source.get('gpgkey', ''))
    else:
        baseurl = resolved_url or source.get('repo_url', '')
        gpgkey = source.get('gpgkey', '')

    if not baseurl:
        return None

    serverid = source['id']
    lines = ['[%s]' % serverid]
    lines.append('name=%s' % source['name'])
    lines.append('baseurl=%s' % baseurl)
    lines.append('enabled=1')
    lines.append('gpgcheck=1' if gpgkey else 'gpgcheck=0')
    if gpgkey:
        lines.append('gpgkey=%s' % gpgkey)
    lines.append('')
    return '\n'.join(lines)


if __name__ == '__main__':
    l = get_list()
    print(l)
    if l:
        i = l[0]
        print(i)
        c = get_item(i)
        print(c)
