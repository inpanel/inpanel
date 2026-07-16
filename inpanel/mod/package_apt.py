# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''APT（高级包管理工具）管理模块'''

import shutil

from .package_base import PackageManager
from .system import is_debian_family


class AptPM(PackageManager):
    """Debian 9-13 / Ubuntu 18.04+ / Linux Mint：apt"""
    
    def detect(self):
        if not shutil.which("apt"):
            return False
        return is_debian_family()
    
    def install(self, packages, assume_yes = True):
        cmd = ["apt"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["install"] + packages)
        return self._run_cmd(cmd)
    
    def remove(self, packages, assume_yes = True):
        cmd = ["apt"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["remove"] + packages)
        return self._run_cmd(cmd)
    
    def refresh(self):
        return self._run_cmd(["apt", "update"])
    
    def search(self, pattern):
        return self._run_cmd(["apt", "search", pattern])
    
    def list_installed(self):
        return self._run_cmd(["dpkg", "-l"])
    
    def update(self):
        return self._run_cmd(["apt", "-y", "upgrade"])
    
    def upgrade(self):
        return self._run_cmd(["apt", "-y", "full-upgrade"])
    
    def info(self, package):
        return self._run_cmd(["apt", "show", package])
    
    def clean(self):
        return self._run_cmd(["apt", "clean"])

    def list_available(self, pattern = ''):
        cmd = ["apt", "list"]
        if pattern:
            cmd.append(pattern)
        return self._run_cmd(cmd)
    
    def get_os_type(self):
        return "debian"