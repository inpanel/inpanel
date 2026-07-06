# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for iptables Management'''

import shutil
from typing import Tuple, List, Dict

from .firewall_base import FirewallManager
from .system import is_rhel_family, get_os_version_major


class IptablesPM(FirewallManager):
    """CentOS 7 及以下 / RHEL 7 及以下：iptables"""
    
    def detect(self) -> bool:
        if not shutil.which("iptables"):
            return False
        if not is_rhel_family():
            return False
        version_major = get_os_version_major()
        return version_major <= 7 or version_major == 0
    
    def status(self) -> Tuple[bool, str]:
        success, output = self._run_cmd(["systemctl", "status", "iptables"])
        if not success:
            success, output = self._run_cmd(["service", "iptables", "status"])
        return (success, output)
    
    def enable(self) -> Tuple[bool, str]:
        success, output = self._run_cmd(["systemctl", "enable", "iptables"])
        if not success:
            success, output = self._run_cmd(["chkconfig", "iptables", "on"])
        return (success, output)
    
    def disable(self) -> Tuple[bool, str]:
        success, output = self._run_cmd(["systemctl", "disable", "iptables"])
        if not success:
            success, output = self._run_cmd(["chkconfig", "iptables", "off"])
        return (success, output)
    
    def start(self) -> Tuple[bool, str]:
        success, output = self._run_cmd(["systemctl", "start", "iptables"])
        if not success:
            success, output = self._run_cmd(["service", "iptables", "start"])
        return (success, output)
    
    def stop(self) -> Tuple[bool, str]:
        success, output = self._run_cmd(["systemctl", "stop", "iptables"])
        if not success:
            success, output = self._run_cmd(["service", "iptables", "stop"])
        return (success, output)
    
    def restart(self) -> Tuple[bool, str]:
        success, output = self._run_cmd(["systemctl", "restart", "iptables"])
        if not success:
            success, output = self._run_cmd(["service", "iptables", "restart"])
        return (success, output)
    
    def add_rule(self, port: int, protocol: str = 'tcp', zone: str = '') -> Tuple[bool, str]:
        cmd = ["iptables", "-A", "INPUT", "-p", protocol, "--dport", str(port), "-j", "ACCEPT"]
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["service", "iptables", "save"])
        return (success, output)
    
    def remove_rule(self, port: int, protocol: str = 'tcp', zone: str = '') -> Tuple[bool, str]:
        cmd = ["iptables", "-D", "INPUT", "-p", protocol, "--dport", str(port), "-j", "ACCEPT"]
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["service", "iptables", "save"])
        return (success, output)
    
    def add_ip_rule(self, ip: str, action: str = 'allow') -> Tuple[bool, str]:
        chain = "ACCEPT" if action == 'allow' else "DROP"
        cmd = ["iptables", "-A", "INPUT", "-s", ip, "-j", chain]
        success, output = self._run_cmd(cmd)
        if success:
            self._run_cmd(["service", "iptables", "save"])
        return (success, output)
    
    def remove_ip_rule(self, ip: str) -> Tuple[bool, str]:
        cmd = ["iptables", "-D", "INPUT", "-s", ip, "-j", "ACCEPT"]
        success1, output1 = self._run_cmd(cmd)
        cmd = ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
        success2, output2 = self._run_cmd(cmd)
        if success1 or success2:
            self._run_cmd(["service", "iptables", "save"])
            return (True, output1 + output2)
        return (False, output1 + output2)
    
    def list_rules(self) -> Tuple[bool, str]:
        return self._run_cmd(["iptables", "-L", "-n"])
    
    def list_zones(self) -> Tuple[bool, List[str]]:
        return (False, [])
    
    def get_default_zone(self) -> Tuple[bool, str]:
        return (False, "Not supported")
    
    def parse_rules(self) -> List[Dict]:
        rules = []
        success, output = self._run_cmd(["iptables", "-L", "-n", "-v"])
        if not success:
            return rules
        
        current_chain = ""
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('Chain '):
                current_chain = line.split()[1]
                continue
            
            parts = line.split()
            if len(parts) < 10:
                continue
            
            pkts = parts[0]
            bytes = parts[1]
            target = parts[2]
            prot = parts[3]
            opt = parts[4]
            in_iface = parts[5]
            out_iface = parts[6]
            source = parts[7]
            destination = parts[8]
            
            action = 'allow' if target == 'ACCEPT' else ('deny' if target == 'DROP' or target == 'REJECT' else target.lower())
            
            port = ''
            ip = ''
            
            for i in range(9, len(parts)):
                if parts[i].startswith('dpt:'):
                    port = parts[i].replace('dpt:', '')
                elif parts[i].startswith('spt:'):
                    port = parts[i].replace('spt:', '')
            
            if source != '0.0.0.0/0' and '/' not in source:
                ip = source
            elif source != '0.0.0.0/0':
                ip = source
            
            if port or ip or source != '0.0.0.0/0':
                if port:
                    rules.append({
                        'type': 'port',
                        'service': '',
                        'port': int(port) if port.isdigit() else port,
                        'protocol': prot,
                        'action': action,
                        'ip': '',
                        'zone': '',
                        'description': f"{action.upper()}: {prot} dpt:{port} from {source}"
                    })
                elif ip:
                    rules.append({
                        'type': 'ip',
                        'service': '',
                        'port': '',
                        'protocol': '',
                        'action': action,
                        'ip': ip,
                        'zone': '',
                        'description': f"{action.upper()}: {source}"
                    })
        
        return rules