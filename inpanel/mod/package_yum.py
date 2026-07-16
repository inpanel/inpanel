# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''YUM 包管理器模块'''

import shutil

from .package_base import PackageManager
from .system import is_rhel_family, get_os_version_major


class YumPM(PackageManager):
    """CentOS 7 及以下 / RHEL 7 及以下：yum"""
    
    def detect(self):
        if not shutil.which("yum"):
            return False
        if not is_rhel_family():
            return False
        if shutil.which("dnf"):
            version_major = get_os_version_major()
            return version_major == 7
        version_major = get_os_version_major()
        return version_major in (5, 6, 7) or version_major == 0
    
    def install(self, packages, assume_yes = True):
        cmd = ["yum"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["install"] + packages)
        return self._run_cmd(cmd)
    
    def remove(self, packages, assume_yes = True):
        cmd = ["yum"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["remove"] + packages)
        return self._run_cmd(cmd)
    
    def refresh(self):
        return self._run_cmd(["yum", "makecache"])
    
    def search(self, pattern):
        return self._run_cmd(["yum", "search", pattern])
    
    def list_installed(self):
        return self._run_cmd(["yum", "list", "installed"])
    
    def update(self):
        return self._run_cmd(["yum", "-y", "update"])
    
    def upgrade(self):
        return self._run_cmd(["yum", "-y", "upgrade"])
    
    def info(self, package):
        return self._run_cmd(["yum", "info", package])
    
    def clean(self):
        return self._run_cmd(["yum", "clean", "all"])

    def list_available(self, pattern = ''):
        cmd = ["yum", "list", "available"]
        if pattern:
            cmd.append(pattern)
        return self._run_cmd(cmd)
    
    def get_os_type(self):
        return "rhel"