# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''macOS 防火墙管理模块'''

import re
import shutil

from .firewall_base import FirewallManager
from .system import get_os_family


class MacosFirewallPM(FirewallManager):
    """macOS 防火墙管理器"""
    
    SOCKETFILTERFW = '/usr/libexec/ApplicationFirewall/socketfilterfw'
    PFCTL = '/sbin/pfctl'
    
    def detect(self):
        """检测当前系统是否为 macOS"""
        return get_os_family() == 'darwin'
    
    def status(self):
        """获取防火墙状态"""
        if shutil.which(self.SOCKETFILTERFW):
            success, output = self._run_cmd([self.SOCKETFILTERFW, '--getglobalstate'])
            if success:
                if 'enabled' in output.lower():
                    return (True, '运行中')
                elif 'disabled' in output.lower():
                    return (True, '已停止')
        return (False, '未知')
    
    def enable(self):
        """启用防火墙（开机自启）"""
        if shutil.which(self.SOCKETFILTERFW):
            success, output = self._run_cmd(['sudo', self.SOCKETFILTERFW, '--setglobalstate', 'on'])
            if success:
                return (True, '防火墙已启用')
        return (False, '无法启用防火墙')
    
    def disable(self):
        """禁用防火墙（关闭开机自启）"""
        if shutil.which(self.SOCKETFILTERFW):
            success, output = self._run_cmd(['sudo', self.SOCKETFILTERFW, '--setglobalstate', 'off'])
            if success:
                return (True, '防火墙已禁用')
        return (False, '无法禁用防火墙')
    
    def start(self):
        """启动防火墙服务"""
        return self.enable()
    
    def stop(self):
        """停止防火墙服务"""
        return self.disable()
    
    def restart(self):
        """重启防火墙服务"""
        self.disable()
        return self.enable()
    
    def add_rule(self, port, protocol = 'tcp', zone = ''):
        """添加端口规则 - macOS 使用 pf"""
        if shutil.which(self.PFCTL):
            rule = f'pass in proto {protocol} from any to any port {port}'
            success, output = self._run_cmd(['sudo', self.PFCTL, '-t', 'InPanel', '-T', 'add', rule])
            if not success:
                success, output = self._run_cmd(['sudo', self.PFCTL, '-f', '/dev/stdin'], input=rule)
                if success:
                    return (True, f'已添加端口规则: {port}/{protocol}')
        return (False, '无法添加端口规则')
    
    def remove_rule(self, port, protocol = 'tcp', zone = ''):
        """移除端口规则"""
        if shutil.which(self.PFCTL):
            success, output = self._run_cmd(['sudo', self.PFCTL, '-t', 'InPanel', '-T', 'delete', f'pass in proto {protocol} from any to any port {port}'])
            if success:
                return (True, f'已移除端口规则: {port}/{protocol}')
        return (False, '无法移除端口规则')
    
    def add_ip_rule(self, ip, action = 'allow'):
        """添加IP规则"""
        if shutil.which(self.PFCTL):
            if action == 'allow':
                rule = f'pass in from {ip} to any'
            else:
                rule = f'block in from {ip} to any'
            success, output = self._run_cmd(['sudo', self.PFCTL, '-t', 'InPanel', '-T', 'add', rule])
            if success:
                return (True, f'已添加IP规则: {action} {ip}')
        return (False, '无法添加IP规则')
    
    def remove_ip_rule(self, ip):
        """移除IP规则"""
        if shutil.which(self.PFCTL):
            success, output = self._run_cmd(['sudo', self.PFCTL, '-t', 'InPanel', '-T', 'delete', f'pass in from {ip} to any'])
            if not success:
                success, output = self._run_cmd(['sudo', self.PFCTL, '-t', 'InPanel', '-T', 'delete', f'block in from {ip} to any'])
            if success:
                return (True, f'已移除IP规则: {ip}')
        return (False, '无法移除IP规则')
    
    def remove_app_rule(self, app_path):
        """移除应用规则"""
        if shutil.which(self.SOCKETFILTERFW):
            success, output = self._run_cmd(['sudo', self.SOCKETFILTERFW, '--remove', app_path])
            if success:
                return (True, f'已移除应用规则: {app_path}')
        return (False, '无法移除应用规则')
    
    def list_rules(self):
        """列出所有规则"""
        rules = []
        
        if shutil.which(self.SOCKETFILTERFW):
            success, output = self._run_cmd([self.SOCKETFILTERFW, '--listapps'])
            if success:
                rules.append("=== 应用规则 ===")
                rules.append(output)
        
        if shutil.which(self.PFCTL):
            success, output = self._run_cmd(['sudo', self.PFCTL, '-s', 'rules'])
            if success:
                rules.append("\n=== PF 端口规则 ===")
                rules.append(output)
        
        return (True, '\n'.join(rules) if rules else '无规则')
    
    def list_zones(self):
        """macOS 不使用区域概念"""
        return (True, [])
    
    def get_default_zone(self):
        """macOS 不使用区域概念"""
        return (True, '')
    
    def parse_rules(self):
        """解析规则列表为结构化数据"""
        rules = []
        success, output = self.list_rules()
        
        if not success:
            return rules
        
        lines = output.split('\n')
        app_section = False
        pf_section = False
        current_app_path = ''
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if '=== 应用规则 ===' in line:
                app_section = True
                pf_section = False
                continue
            if '=== PF 端口规则 ===' in line:
                app_section = False
                pf_section = True
                continue
            
            if app_section and line:
                if 'total number of apps' in line:
                    continue
                
                app_match = re.match(r'\d+\s*:\s*(/.+)', line)
                if app_match:
                    current_app_path = app_match.group(1).strip()
                    app_name = current_app_path.split('/')[-1].replace('.app', '')
                    rules.append({
                        'type': 'app',
                        'port': '',
                        'protocol': '',
                        'action': 'allow',
                        'ip': '',
                        'zone': '',
                        'description': app_name,
                        'app_path': current_app_path
                    })
                elif 'Allow incoming connections' in line and current_app_path:
                    pass
            
            if pf_section and line:
                port_match = re.search(r'port\s+(\d+)', line)
                proto_match = re.search(r'proto\s+(\w+)', line)
                ip_match = re.search(r'from\s+(\d+\.\d+\.\d+\.\d+)', line)
                
                rule_type = 'port' if port_match else 'ip'
                port = port_match.group(1) if port_match else ''
                protocol = proto_match.group(1) if proto_match else 'tcp'
                ip = ip_match.group(1) if ip_match else ''
                action = 'allow' if 'pass' in line else 'deny'
                
                rules.append({
                    'type': rule_type,
                    'port': port,
                    'protocol': protocol,
                    'action': action,
                    'ip': ip,
                    'zone': '',
                    'description': line
                })
        
        return rules