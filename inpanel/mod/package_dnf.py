# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''DNF 包管理器模块'''

import shutil

from .package_yum import YumPM
from .system import get_os_id, get_os_version_major


class DnfPM(YumPM):
    """Alma 8-10 / Rocky 8-10 / CentOS 8+ / RHEL 8+ / Fedora：dnf"""
    
    def detect(self):
        if not shutil.which("dnf"):
            return False
        os_id = get_os_id()
        if os_id == "fedora":
            return True
        version_major = get_os_version_major()
        return version_major >= 8
    
    def install(self, packages, assume_yes = True):
        cmd = ["dnf"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["install"] + packages)
        return self._run_cmd(cmd)
    
    def remove(self, packages, assume_yes = True):
        cmd = ["dnf"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["remove"] + packages)
        return self._run_cmd(cmd)
    
    def refresh(self):
        return self._run_cmd(["dnf", "makecache"])
    
    def search(self, pattern):
        return self._run_cmd(["dnf", "search", pattern])
    
    def list_installed(self):
        return self._run_cmd(["dnf", "list", "installed"])
    
    def update(self):
        return self._run_cmd(["dnf", "-y", "update"])
    
    def upgrade(self):
        return self._run_cmd(["dnf", "-y", "upgrade"])
    
    def info(self, package):
        return self._run_cmd(["dnf", "info", package])
    
    def clean(self):
        return self._run_cmd(["dnf", "clean", "all"])

    def list_available(self, pattern = ''):
        cmd = ["dnf", "list", "available"]
        if pattern:
            cmd.append(pattern)
        return self._run_cmd(cmd)