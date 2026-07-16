# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''软件包名称映射模块

Configuration data is loaded from templates/sources/package_map.json.
'''

from ..templates.sources import load_package_map

PACKAGE_MAP = load_package_map()['package_map']


def resolve_package_names(pm, base_names):
    """根据包管理器类型解析实际包名"""
    os_type = pm.get_os_type()
    resolved = []
    for name in base_names:
        if name in PACKAGE_MAP and os_type in PACKAGE_MAP[name]:
            pkg_name = PACKAGE_MAP[name][os_type]
            if pkg_name:
                resolved.append(pkg_name)
        else:
            resolved.append(name)
    return resolved


def is_installed(pm, package):
    """检查包是否已安装"""
    success, output = pm.list_installed()
    if not success:
        return False
    package = package.lower()
    for line in output.split('\n'):
        if package in line.lower():
            return True
    return False


def install_if_not_exists(pm, packages):
    """只安装未安装的包"""
    resolved = resolve_package_names(pm, packages)
    to_install = []
    for pkg in resolved:
        if not is_installed(pm, pkg):
            to_install.append(pkg)
    if not to_install:
        return (True, "All packages already installed")
    return pm.install(to_install)


def parse_search_output(output):
    """解析搜索命令输出，返回包列表"""
    packages = []
    lines = output.split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            pkg_name = parts[0]
            description = ' '.join(parts[1:]) if len(parts) > 1 else ''
            packages.append({'name': pkg_name, 'description': description})
    return packages


def parse_list_installed_output(output):
    """解析已安装包列表输出"""
    packages = []
    lines = output.split('\n')
    for line in lines:
        if not line.strip():
            continue
        if line.startswith('Desired=') or line.startswith('+++') or line.startswith('ii ') or line.startswith('Installed'):
            parts = line.split()
            if len(parts) >= 2:
                if line.startswith('ii '):
                    pkg_name = parts[1]
                    version = parts[2] if len(parts) > 2 else ''
                elif line.startswith('Installed'):
                    continue
                else:
                    continue
                packages.append({'name': pkg_name, 'version': version})
    return packages


def parse_info_output(output):
    """解析包信息输出"""
    info = {}
    lines = output.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info