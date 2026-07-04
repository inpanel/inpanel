# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for System Detection and Information'''

import os
import shutil
from platform import mac_ver, platform, uname, win32_ver
from typing import Dict, Optional, Tuple


def get_os_release() -> Dict[str, str]:
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


def get_os_family() -> str:
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


def get_os_id() -> str:
    """获取操作系统 ID"""
    return OS_ID


def get_os_version() -> str:
    """获取操作系统版本号（完整）"""
    return OS_VERSION_ID


def get_os_version_major() -> int:
    """获取操作系统主版本号（整数）"""
    if OS_VERSION_ID:
        try:
            return int(OS_VERSION_ID.split(".")[0])
        except (ValueError, IndexError):
            pass
    return 0


def get_os_version_full() -> Tuple[int, int]:
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


def get_os_title() -> str:
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


def get_os_name() -> str:
    """获取操作系统发行名称"""
    if OS_ID:
        return OS_ID.capitalize()
    kernel_name, _, _, _, _, _ = uname()
    if kernel_name == "Darwin":
        return "macOS"
    if kernel_name == "Windows":
        return "Windows"
    return "Unknown"


def is_rhel_family() -> bool:
    """是否为 RHEL 家族系统"""
    return get_os_family() == "rhel"


def is_debian_family() -> bool:
    """是否为 Debian 家族系统"""
    return get_os_family() == "debian"


def is_darwin() -> bool:
    """是否为 macOS 系统"""
    return get_os_family() == "darwin"


def is_windows() -> bool:
    """是否为 Windows 系统"""
    return get_os_family() == "windows"


def compare_version(version_str: str) -> int:
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


def has_package_manager() -> bool:
    """检查系统是否有包管理器"""
    return any([
        shutil.which("yum"),
        shutil.which("dnf"),
        shutil.which("apt"),
        shutil.which("zypper"),
        shutil.which("pacman"),
    ])


def get_system_info() -> Dict[str, str]:
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