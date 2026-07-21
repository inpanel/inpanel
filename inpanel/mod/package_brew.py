# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Homebrew 包管理器模块'''

import shutil

from .package_base import PackageManager


class BrewPM(PackageManager):
    """macOS Homebrew 包管理器"""

    def detect(self):
        return shutil.which("brew") is not None

    def install(self, packages, assume_yes=True):
        cmd = ["brew", "install"] + packages
        return self._run_cmd(cmd)

    def remove(self, packages, assume_yes=True):
        cmd = ["brew", "uninstall", "--ignore-dependencies"] + packages
        return self._run_cmd(cmd)

    def refresh(self):
        return self._run_cmd(["brew", "update"])

    def search(self, pattern):
        return self._run_cmd(["brew", "search", pattern])

    def list_installed(self):
        return self._run_cmd(["brew", "list", "--formula"])

    def update(self):
        return self._run_cmd(["brew", "upgrade"])

    def upgrade(self):
        return self._run_cmd(["brew", "upgrade"])

    def info(self, package):
        return self._run_cmd(["brew", "info", package])

    def clean(self):
        return self._run_cmd(["brew", "cleanup"])

    def list_available(self, pattern=''):
        cmd = ["brew", "search"]
        if pattern:
            cmd.append(pattern)
        return self._run_cmd(cmd)

    def get_os_type(self):
        return "darwin"
