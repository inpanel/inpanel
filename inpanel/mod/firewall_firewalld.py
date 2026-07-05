# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for Firewalld Management'''

import shutil
from typing import Tuple, List, Dict

from .firewall_base import FirewallManager
from .system import is_rhel_family, get_os_version_major


class FirewalldPM(FirewallManager):
    """Alma 8-10 / Rocky 8-10 / CentOS 8+ / RHEL 8+：firewalld"""
    
    def detect(self) -> bool:
        if not shutil.which("firewall-cmd"):
            return False
        if not is_rhel_family():
            return False
        version_major = get_os_version_major()
        return version_major >= 8
    
    def status(self) -> Tuple[bool, str]:
        return self._run_cmd(["firewall-cmd", "--state"])
    
    def enable(self) -> Tuple[bool, str]:
        return self._run_cmd(["systemctl", "enable", "firewalld"])
    
    def disable(self) -> Tuple[bool, str]:
        return self._run_cmd(["systemctl", "disable", "firewalld"])
    
    def start(self) -> Tuple[bool, str]:
        return self._run_cmd(["systemctl", "start", "firewalld"])
    
    def stop(self) -> Tuple[bool, str]:
        return self._run_cmd(["systemctl", "stop", "firewalld"])
    
    def restart(self) -> Tuple[bool, str]:
        return self._run_cmd(["systemctl", "restart", "firewalld"])
    
    def add_rule(self, port: int, protocol: str = 'tcp', zone: str = '') -> Tuple[bool, str]:
        cmd = ["firewall-cmd", "--permanent"]
        if zone:
            cmd.extend(["--zone", zone])
        cmd.extend(["--add-port", f"{port}/{protocol}"])
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["firewall-cmd", "--reload"])
        return (success, output)
    
    def remove_rule(self, port: int, protocol: str = 'tcp', zone: str = '') -> Tuple[bool, str]:
        cmd = ["firewall-cmd", "--permanent"]
        if zone:
            cmd.extend(["--zone", zone])
        cmd.extend(["--remove-port", f"{port}/{protocol}"])
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["firewall-cmd", "--reload"])
        return (success, output)
    
    def add_ip_rule(self, ip: str, action: str = 'allow') -> Tuple[bool, str]:
        cmd = ["firewall-cmd", "--permanent"]
        if action == 'allow':
            cmd.extend(["--add-source", ip])
        else:
            cmd.extend(["--add-rich-rule", f'rule family="ipv4" source address="{ip}" reject'])
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["firewall-cmd", "--reload"])
        return (success, output)
    
    def remove_ip_rule(self, ip: str) -> Tuple[bool, str]:
        cmd = ["firewall-cmd", "--permanent", "--remove-source", ip]
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["firewall-cmd", "--reload"])
        return (success, output)
    
    def list_rules(self) -> Tuple[bool, str]:
        return self._run_cmd(["firewall-cmd", "--list-all"])
    
    def list_zones(self) -> Tuple[bool, List[str]]:
        success, output = self._run_cmd(["firewall-cmd", "--get-zones"])
        if success:
            zones = output.split()
            return (True, zones)
        return (False, [])
    
    def get_default_zone(self) -> Tuple[bool, str]:
        return self._run_cmd(["firewall-cmd", "--get-default-zone"])
    
    def parse_rules(self) -> List[Dict]:
        rules = []
        success, output = self._run_cmd(["firewall-cmd", "--list-all"])
        if not success:
            return rules
        
        zone = ""
        lines = output.split('\n')
        for line in lines:
            if line and not line.startswith(' '):
                zone = line.split(' ')[0]
                continue
            
            line = line.strip()
            if line.startswith('services:'):
                services = line.replace('services:', '').strip()
                if services and services != '-':
                    for svc in services.split():
                        rules.append({
                            'type': 'service',
                            'service': svc,
                            'port': '',
                            'protocol': '',
                            'action': 'allow',
                            'ip': '',
                            'zone': zone,
                            'description': f"服务: {svc}"
                        })
            elif line.startswith('ports:'):
                ports = line.replace('ports:', '').strip()
                if ports and ports != '-':
                    for port in ports.split():
                        parts = port.split('/')
                        p = parts[0]
                        proto = parts[1] if len(parts) > 1 else 'tcp'
                        rules.append({
                            'type': 'port',
                            'service': '',
                            'port': int(p) if p.isdigit() else p,
                            'protocol': proto,
                            'action': 'allow',
                            'ip': '',
                            'zone': zone,
                            'description': f"端口: {p}/{proto}"
                        })
            elif line.startswith('sources:'):
                sources = line.replace('sources:', '').strip()
                if sources and sources != '-':
                    for source in sources.split():
                        rules.append({
                            'type': 'ip',
                            'service': '',
                            'port': '',
                            'protocol': '',
                            'action': 'allow',
                            'ip': source,
                            'zone': zone,
                            'description': f"允许IP: {source}"
                        })
            elif line.startswith('rich rules:'):
                rich_rules = line.replace('rich rules:', '').strip()
                if rich_rules and rich_rules != '-':
                    rules.append({
                        'type': 'rich',
                        'service': '',
                        'port': '',
                        'protocol': '',
                        'action': 'allow',
                        'ip': '',
                        'zone': zone,
                        'description': f"富规则: {rich_rules}"
                    })
        
        return rules