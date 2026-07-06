# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for Package Manager Integration'''

from typing import Optional

from .package_base import PackageManager
from .package_yum import YumPM
from .package_dnf import DnfPM
from .package_apt import AptPM
from .package_map import (
    PACKAGE_MAP,
    resolve_package_names,
    is_installed,
    install_if_not_exists,
    parse_search_output,
    parse_list_installed_output,
    parse_info_output
)


def get_package_manager() -> Optional[PackageManager]:
    """工厂函数：根据系统返回对应的包管理器实例"""
    managers = [DnfPM(), YumPM(), AptPM()]
    for mgr in managers:
        if mgr.detect():
            return mgr
    return None