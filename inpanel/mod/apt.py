# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for APT Repository Management'''

import os
import re
from pathlib import Path

from .. import base
from . import file
from ..apt import apt_sources

sources_list_path = '/etc/apt/sources.list'
sources_list_d_path = '/etc/apt/sources.list.d'


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
    
    if source == 'sources.list':
        filepath = sources_list_path
    elif source.startswith('sources.list.d/'):
        filename = source[len('sources.list.d/'):]
        filepath = str(Path(sources_list_d_path) / filename)
    else:
        filepath = str(Path(sources_list_d_path) / source)
    
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
    
    if source == 'sources.list':
        filepath = sources_list_path
    elif source.startswith('sources.list.d/'):
        filename = source[len('sources.list.d/'):]
        filepath = str(Path(sources_list_d_path) / filename)
    else:
        filepath = str(Path(sources_list_d_path) / source)
    
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
    
    if source == 'sources.list':
        filepath = sources_list_path
        if Path(filepath).exists():
            return False
    elif source.startswith('sources.list.d/'):
        filename = source[len('sources.list.d/'):]
        filepath = str(Path(sources_list_d_path) / filename)
    else:
        filepath = str(Path(sources_list_d_path) / source)
    
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
    
    if source == 'sources.list':
        filepath = sources_list_path
    elif source.startswith('sources.list.d/'):
        filename = source[len('sources.list.d/'):]
        filepath = str(Path(sources_list_d_path) / filename)
    else:
        filepath = str(Path(sources_list_d_path) / source)
    
    return file.delete(filepath)


def parse_sources(content):
    '''parse sources.list content into structured data'''
    sources = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        match = re.match(r'^(deb|deb-src)\s+(\S+)\s+(\S+)(?:\s+(.+))?$', line)
        if match:
            source_type = match.group(1)
            url = match.group(2)
            distribution = match.group(3)
            components = match.group(4).split() if match.group(4) else []
            
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


def web_handler(context):
    '''Handle web requests for APT repository management'''
    action = context.get('action', '')
    source = context.get('source', '')
    
    if action == 'list':
        items = get_list()
        if items is None:
            return {'code': -1, 'msg': '获取配置失败！'}
        else:
            return {'code': 0, 'msg': '', 'data': items}
    
    elif action == 'item':
        if not source:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        data = get_item(source)
        if data is None:
            return {'code': -1, 'msg': '配置文件不存在！'}
        else:
            return {'code': 0, 'msg': '', 'data': data}
    
    elif action == 'add':
        if not source:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        
        content = context.get('content', '')
        if not content:
            return {'code': -1, 'msg': '配置内容不能为空！'}
        
        data = {'content': content}
        
        if item_exists(source):
            return {'code': -1, 'msg': '配置文件已存在！'}
        if add_item(source, data) is True:
            return {'code': 0, 'msg': '配置添加成功！'}
        else:
            return {'code': -1, 'msg': '配置添加失败！'}
    
    elif action == 'edit':
        if not source:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        
        content = context.get('content', '')
        if not content:
            return {'code': -1, 'msg': '配置内容不能为空！'}
        
        data = {'content': content}
        
        if not item_exists(source):
            return {'code': -1, 'msg': '配置文件不存在！'}
        if set_item(source, data) is True:
            return {'code': 0, 'msg': '配置修改成功！'}
        else:
            return {'code': -1, 'msg': '配置修改失败！'}
    
    elif action == 'del':
        if not source:
            return {'code': -1, 'msg': '配置文件不能为空！'}
        if not item_exists(source):
            return {'code': -1, 'msg': '配置文件不存在！'}
        if del_item(source) is True:
            return {'code': 0, 'msg': '配置文件已移入回收站！'}
        else:
            return {'code': -1, 'msg': '删除失败！'}
    
    elif action == 'parse':
        content = context.get('content', '')
        if not content:
            return {'code': -1, 'msg': '内容不能为空！'}
        sources = parse_sources(content)
        return {'code': 0, 'msg': '', 'data': sources}
    
    elif action == 'generate':
        sources = context.get('sources', [])
        content = generate_sources(sources)
        return {'code': 0, 'msg': '', 'data': {'content': content}}
    
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