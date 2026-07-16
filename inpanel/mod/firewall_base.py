# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''防火墙管理器抽象基类'''

import subprocess
from abc import ABC, abstractmethod


class FirewallManager(ABC):
    """防火墙管理器抽象基类"""
    
    @abstractmethod
    def detect(self):
        """检测当前系统是否匹配该防火墙管理器"""
        pass
    
    @abstractmethod
    def status(self):
        """获取防火墙状态（运行中/已停止）"""
        pass
    
    @abstractmethod
    def enable(self):
        """启用防火墙（开机自启）"""
        pass
    
    @abstractmethod
    def disable(self):
        """禁用防火墙（关闭开机自启）"""
        pass
    
    @abstractmethod
    def start(self):
        """启动防火墙服务"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止防火墙服务"""
        pass
    
    @abstractmethod
    def restart(self):
        """重启防火墙服务"""
        pass
    
    @abstractmethod
    def add_rule(self, port, protocol = 'tcp', zone = ''):
        """
        添加端口规则
        :param port: 端口号
        :param protocol: 协议（tcp/udp）
        :param zone: 区域（firewalld专用）
        :return: (成功?, 输出日志)
        """
        pass
    
    @abstractmethod
    def remove_rule(self, port, protocol = 'tcp', zone = ''):
        """移除端口规则"""
        pass
    
    @abstractmethod
    def add_ip_rule(self, ip, action = 'allow'):
        """
        添加IP规则
        :param ip: IP地址
        :param action: allow/deny
        :return: (成功?, 输出日志)
        """
        pass
    
    @abstractmethod
    def remove_ip_rule(self, ip):
        """移除IP规则"""
        pass
    
    @abstractmethod
    def list_rules(self):
        """列出所有规则"""
        pass
    
    @abstractmethod
    def list_zones(self):
        """列出所有区域（firewalld专用）"""
        pass
    
    @abstractmethod
    def get_default_zone(self):
        """获取默认区域（firewalld专用）"""
        pass
    
    @abstractmethod
    def parse_rules(self):
        """解析规则列表为结构化数据
        
        返回格式示例：
        [
            {
                'type': 'port',  # 'port' 或 'ip'
                'port': 80,      # 端口号
                'protocol': 'tcp',  # 'tcp' 或 'udp'
                'action': 'allow',  # 'allow' 或 'deny'
                'ip': '',        # IP地址（type='ip'时使用）
                'zone': '',      # 区域（firewalld专用）
                'description': ''  # 规则描述
            }
        ]
        """
        pass
    
    def is_running(self):
        """检查防火墙是否正在运行"""
        success, output = self.status()
        return success and 'running' in output.lower()
    
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