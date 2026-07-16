# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''包管理器抽象基类'''

import subprocess
from abc import ABC, abstractmethod

from .system import (
    get_os_family,
    get_os_id,
    get_os_version_major,
    is_rhel_family,
    is_debian_family,
)


class PackageManager(ABC):
    """包管理器抽象基类"""
    
    @abstractmethod
    def detect(self):
        """检测当前系统是否匹配该包管理器"""
        pass
    
    @abstractmethod
    def install(self, packages, assume_yes = True):
        """
        安装包
        :param packages: 包名列表（内部统一用小写）
        :param assume_yes: 是否自动确认（yum/dnf/apt 的 -y 参数）
        :return: (成功?, 输出日志)
        """
        pass
    
    @abstractmethod
    def remove(self, packages, assume_yes = True):
        """卸载包"""
        pass
    
    @abstractmethod
    def refresh(self):
        """更新包缓存（apt update / yum makecache / dnf makecache）"""
        pass
    
    def search(self, pattern):
        """搜索包"""
        return (False, "Not implemented")
    
    def list_installed(self):
        """列出已安装包"""
        return (False, "Not implemented")
    
    def get_os_type(self):
        """返回操作系统类型：rhel 或 debian"""
        return get_os_family()

    def info(self, package):
        """获取包详细信息"""
        return (False, "Not implemented")

    def update(self):
        """升级所有包"""
        return (False, "Not implemented")

    def upgrade(self):
        """系统升级"""
        return (False, "Not implemented")

    def clean(self):
        """清理缓存"""
        return (False, "Not implemented")

    def list_available(self, pattern = ''):
        """列出可用包（可指定名称模式过滤）"""
        return (False, "Not implemented")
    
    @staticmethod
    def _run_cmd(cmd):
        """执行 shell 命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            output = result.stdout + result.stderr
            return (result.returncode == 0, output.strip())
        except Exception as e:
            return (False, str(e))