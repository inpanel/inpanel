# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for DNF Package Manager'''

import shutil
from .package_yum import YumPM
from .system import get_os_id, get_os_version_major


class DnfPM(YumPM):
    """Alma 8-10 / Rocky 8-10 / CentOS 8+ / RHEL 8+ / Fedora：dnf"""
    
    def detect(self) -> bool:
        if not shutil.which("dnf"):
            return False
        os_id = get_os_id()
        if os_id == "fedora":
            return True
        version_major = get_os_version_major()
        return version_major >= 8
    
    def install(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["dnf"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["install"] + packages)
        return self._run_cmd(cmd)
    
    def remove(self, packages: list[str], assume_yes: bool = True) -> tuple[bool, str]:
        cmd = ["dnf"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["remove"] + packages)
        return self._run_cmd(cmd)
    
    def refresh(self) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "makecache"])
    
    def search(self, pattern: str) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "search", pattern])
    
    def list_installed(self) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "list", "installed"])
    
    def update(self) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "-y", "update"])
    
    def upgrade(self) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "-y", "upgrade"])
    
    def info(self, package: str) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "info", package])
    
    def clean(self) -> tuple[bool, str]:
        return self._run_cmd(["dnf", "clean", "all"])