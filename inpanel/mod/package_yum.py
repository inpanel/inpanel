# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for YUM Package Manager'''

import shutil
from .package_base import PackageManager
from .system import is_rhel_family, get_os_version_major


class YumPM(PackageManager):
    """CentOS 7 及以下 / RHEL 7 及以下：yum"""
    
    def detect(self) -> bool:
        if not shutil.which("yum"):
            return False
        if not is_rhel_family():
            return False
        if shutil.which("dnf"):
            version_major = get_os_version_major()
            return version_major == 7
        version_major = get_os_version_major()
        return version_major in (5, 6, 7) or version_major == 0
    
    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["yum"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["install"] + packages)
        return self._run_cmd(cmd)
    
    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["yum"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["remove"] + packages)
        return self._run_cmd(cmd)
    
    def refresh(self) -> tuple[bool, str]:
        return self._run_cmd(["yum", "makecache"])
    
    def search(self, pattern: str) -> tuple[bool, str]:
        return self._run_cmd(["yum", "search", pattern])
    
    def list_installed(self) -> tuple[bool, str]:
        return self._run_cmd(["yum", "list", "installed"])
    
    def update(self) -> tuple[bool, str]:
        return self._run_cmd(["yum", "-y", "update"])
    
    def upgrade(self) -> tuple[bool, str]:
        return self._run_cmd(["yum", "-y", "upgrade"])
    
    def info(self, package: str) -> tuple[bool, str]:
        return self._run_cmd(["yum", "info", package])
    
    def clean(self) -> tuple[bool, str]:
        return self._run_cmd(["yum", "clean", "all"])