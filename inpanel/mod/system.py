# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''系统检测与信息模块'''

import os
import shutil
from json import loads
from platform import mac_ver, platform, uname, win32_ver


def get_os_release():
    """读取 /etc/os-release 文件，返回系统信息字典"""
    info = {}
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
    except FileNotFoundError:
        pass
    return info


_os_release = get_os_release()

OS_ID = _os_release.get("ID", "")
OS_ID_LIKE = _os_release.get("ID_LIKE", "")
OS_VERSION_ID = _os_release.get("VERSION_ID", "")
OS_PRETTY_NAME = _os_release.get("PRETTY_NAME", "")
OS_NAME = _os_release.get("NAME", "")


def get_os_family():
    """获取操作系统家族：rhel 或 debian 或 darwin 或 windows"""
    if OS_ID in ("almalinux", "rocky", "centos", "rhel", "fedora", "ol", "scientific", "centos-stream"):
        return "rhel"
    if OS_ID in ("debian", "ubuntu", "linuxmint", "pop", "elementary", "kali"):
        return "debian"
    if OS_ID_LIKE:
        if "rhel" in OS_ID_LIKE:
            return "rhel"
        if "debian" in OS_ID_LIKE:
            return "debian"
    kernel_name, _, _, _, _, _ = uname()
    if kernel_name == "Darwin":
        return "darwin"
    if kernel_name == "Windows":
        return "windows"
    return "unknown"


def get_os_id():
    """获取操作系统 ID"""
    return OS_ID


def get_os_version():
    """获取操作系统版本号（完整）"""
    return OS_VERSION_ID


def get_os_version_major():
    """获取操作系统主版本号（整数）"""
    if OS_VERSION_ID:
        try:
            return int(OS_VERSION_ID.split(".")[0])
        except (ValueError, IndexError):
            pass
    return 0


def get_os_version_full():
    """获取操作系统版本号（主版本，次版本）"""
    major = 0
    minor = 0
    if OS_VERSION_ID:
        parts = OS_VERSION_ID.split(".")
        try:
            major = int(parts[0])
            if len(parts) > 1:
                minor = int(parts[1])
        except ValueError:
            pass
    return (major, minor)


def get_os_title():
    """获取操作系统全称"""
    if OS_PRETTY_NAME:
        return OS_PRETTY_NAME
    if OS_NAME:
        if OS_VERSION_ID:
            return f"{OS_NAME} {OS_VERSION_ID}"
        return OS_NAME
    kernel_name, _, _, _, _, _ = uname()
    if kernel_name == "Darwin":
        os_version, _, _ = mac_ver()
        return f"macOS {os_version}"
    if kernel_name == "Windows":
        os_version, _, _ = win32_ver()
        return f"Windows {os_version}"
    return "Unknown"


def get_os_name():
    """获取操作系统发行名称"""
    if OS_ID:
        return OS_ID.capitalize()
    kernel_name, _, _, _, _, _ = uname()
    if kernel_name == "Darwin":
        return "macOS"
    if kernel_name == "Windows":
        return "Windows"
    return "Unknown"


def is_rhel_family():
    """是否为 RHEL 家族系统"""
    return get_os_family() == "rhel"


def is_debian_family():
    """是否为 Debian 家族系统"""
    return get_os_family() == "debian"


def is_darwin():
    """是否为 macOS 系统"""
    return get_os_family() == "darwin"


def is_windows():
    """是否为 Windows 系统"""
    return get_os_family() == "windows"


def compare_version(version_str):
    """
    比较当前系统版本与指定版本
    返回值: -1 (小于), 0 (等于), 1 (大于)
    """
    current_major, current_minor = get_os_version_full()
    parts = version_str.split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        return 0
    
    if current_major > major:
        return 1
    elif current_major < major:
        return -1
    else:
        if current_minor > minor:
            return 1
        elif current_minor < minor:
            return -1
        return 0


def has_package_manager():
    """检查系统是否有包管理器"""
    return any([
        shutil.which("yum"),
        shutil.which("dnf"),
        shutil.which("apt"),
        shutil.which("zypper"),
        shutil.which("pacman"),
    ])


def get_system_info():
    """返回完整的系统信息字典"""
    kernel_name, hostname, kernel_release, kernel_version, machine, processor = uname()
    return {
        'os_title': get_os_title(),
        'os_name': get_os_name(),
        'os_version': get_os_version(),
        'os_versint': str(get_os_version_major()),
        'os_platform': platform(),
        'os_family': get_os_family(),
        'os_id': get_os_id(),
        'hostname': hostname,
        'kernel_name': kernel_name,
        'kernel_release': kernel_release,
        'kernel_version': kernel_version,
        'machine': machine,
        'processor': processor,
    }


__all__ = [
    'get_os_release',
    'OS_ID',
    'OS_ID_LIKE',
    'OS_VERSION_ID',
    'OS_PRETTY_NAME',
    'OS_NAME',
    'get_os_family',
    'get_os_id',
    'get_os_version',
    'get_os_version_major',
    'get_os_version_full',
    'get_os_title',
    'get_os_name',
    'is_rhel_family',
    'is_debian_family',
    'is_darwin',
    'is_windows',
    'compare_version',
    'has_package_manager',
    'get_system_info',
]


# ------------------------------------------------------------------
# 异步任务函数（由 web.py 的 _dispatch_task 调用）
# 命名规则：system_<method>，对应 jobname 中的 system_<method>
# ------------------------------------------------------------------

import tornado.escape
import tornado.httpclient
from pathlib import Path as _Path
from . import shell
from ..base import app_api


async def system_update(tm, settings=None, config=None):
    """升级 InPanel（异步任务）"""
    if settings is None:
        settings = tm.settings
    if config is None:
        config = tm.config
    jobname = 'system.update'
    if not tm._start_job(jobname):
        return

    root_path = settings['root_path']
    data_path = settings['data_path']

    if _Path(f'{root_path}/../.git').exists():
        tm._finish_job(jobname, 0, '升级成功！')
        return

    http_client = tornado.httpclient.AsyncHTTPClient()
    response = await http_client.fetch(app_api['latest'])
    if response.error:
        tm._finish_job(jobname, -1, '获取版本信息失败！')
        return

    versioninfo = loads(response.body.decode('utf-8'))
    downloadurl = versioninfo['download']
    initscript = f'{root_path}/scripts/init.d/{settings["os_name"]}/inpanel'
    binscript = f'{root_path}/scripts/bin/inpanel'

    steps = [
        {'desc': '正在备份当前配置文件...',
         'cmd': f'/bin/cp -f {data_path}/config.ini /tmp/inpanel_config.ini'},
        {'desc': '正在下载安装包...',
         'cmd': f'wget -q "{downloadurl}" -O {data_path}/inpanel.tar.gz'},
        {'desc': '正在创建解压目录...',
         'cmd': f'mkdir -p {data_path}/inpanel'},
        {'desc': '正在解压安装包...',
         'cmd': f'tar zxmf {data_path}/inpanel.tar.gz -C {data_path}/inpanel --strip-components 1'},
        {'desc': '正在删除旧版本...',
         'cmd': f'find {root_path} -mindepth 1 -maxdepth 1 -path {data_path} -prune -o -exec rm -rf {{}} \\\\;'},
        {'desc': '正在复制新版本...',
         'cmd': f'find {data_path}/inpanel -mindepth 1 -maxdepth 1 -exec cp -r {{}} {root_path} \\\\;'},
        {'desc': '正在删除旧的服务脚本...',
         'cmd': 'rm -f /etc/init.d/inpanel /usr/bin/inpanel'},
        {'desc': '正在安装新的服务脚本...',
         'cmd': f'ln -s {initscript} /etc/init.d/inpanel'},
        {'desc': '正在安装新的命令脚本...',
         'cmd': f'ln -s {binscript} /usr/bin/inpanel'},
        {'desc': '正在更改脚本权限...',
         'cmd': f'chmod +x /usr/bin/inpanel /etc/init.d/inpanel {root_path}/config.py {root_path}/server.py'},
        {'desc': '正在删除安装临时文件...',
         'cmd': f'rm -rf {data_path}/inpanel {data_path}/inpanel.tar.gz'},
        {'desc': '正在恢复旧的配置文件...',
         'cmd': f'/bin/cp -f /tmp/inpanel_config.ini {data_path}/config.ini'},
        {'desc': '正在删除旧的配置文件...',
         'cmd': 'rm -f /tmp/inpanel_config.ini'},
    ]

    result = 0
    output = ''
    for step in steps:
        desc = step['desc']
        cmd = step['cmd']
        tm._update_job(jobname, 2, desc)
        result, output = await shell.async_command(cmd)
        if result != 0:
            tm._update_job(jobname, -1, desc + '失败！')
            break

    if result == 0:
        tm._finish_job(jobname, 0, '升级成功！请刷新页面重新登录。')
    else:
        tm._finish_job(jobname, -1, '升级失败！',
                       data=output.strip().replace('\n', '<br>'))