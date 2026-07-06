# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for APT(Advanced Packaging Tool) Management'''

import shutil
from typing import List, Tuple

from .package_base import PackageManager
from .system import is_debian_family


class AptPM(PackageManager):
    """Debian 9-13 / Ubuntu 18.04+ / Linux Mint：apt"""
    
    def detect(self) -> bool:
        if not shutil.which("apt"):
            return False
        return is_debian_family()
    
    def install(self, packages: List[str], assume_yes: bool = True) -> Tuple[bool, str]:
        cmd = ["apt"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["install"] + packages)
        return self._run_cmd(cmd)
    
    def remove(self, packages: List[str], assume_yes: bool = True) -> Tuple[bool, str]:
        cmd = ["apt"]
        if assume_yes:
            cmd.append("-y")
        cmd.extend(["remove"] + packages)
        return self._run_cmd(cmd)
    
    def refresh(self) -> Tuple[bool, str]:
        return self._run_cmd(["apt", "update"])
    
    def search(self, pattern: str) -> Tuple[bool, str]:
        return self._run_cmd(["apt", "search", pattern])
    
    def list_installed(self) -> Tuple[bool, str]:
        return self._run_cmd(["dpkg", "-l"])
    
    def update(self) -> Tuple[bool, str]:
        return self._run_cmd(["apt", "-y", "upgrade"])
    
    def upgrade(self) -> Tuple[bool, str]:
        return self._run_cmd(["apt", "-y", "full-upgrade"])
    
    def info(self, package: str) -> Tuple[bool, str]:
        return self._run_cmd(["apt", "show", package])
    
    def clean(self) -> Tuple[bool, str]:
        return self._run_cmd(["apt", "clean"])
    
    def get_os_type(self) -> str:
        return "debian"