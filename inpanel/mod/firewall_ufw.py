# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''UFW（简易防火墙）管理模块'''

import shutil

from .firewall_base import FirewallManager
from .system import is_debian_family


class UfwPM(FirewallManager):
    """Debian 9-13 / Ubuntu 18.04+ / Linux Mint：ufw"""
    
    def detect(self):
        if not shutil.which("ufw"):
            return False
        return is_debian_family()
    
    def status(self):
        return self._run_cmd(["ufw", "status", "verbose"])
    
    def enable(self):
        return self._run_cmd(["ufw", "enable"])
    
    def disable(self):
        return self._run_cmd(["ufw", "disable"])
    
    def start(self):
        return self._run_cmd(["ufw", "enable"])
    
    def stop(self):
        return self._run_cmd(["ufw", "disable"])
    
    def restart(self):
        return self._run_cmd(["ufw", "reload"])
    
    def add_rule(self, port, protocol = 'tcp', zone = ''):
        return self._run_cmd(["ufw", "allow", f"{port}/{protocol}"])
    
    def remove_rule(self, port, protocol = 'tcp', zone = ''):
        return self._run_cmd(["ufw", "delete", "allow", f"{port}/{protocol}"])
    
    def add_ip_rule(self, ip, action = 'allow'):
        if action == 'allow':
            return self._run_cmd(["ufw", "allow", "from", ip])
        else:
            return self._run_cmd(["ufw", "deny", "from", ip])
    
    def remove_ip_rule(self, ip):
        success1, output1 = self._run_cmd(["ufw", "delete", "allow", "from", ip])
        if not success1:
            success2, output2 = self._run_cmd(["ufw", "delete", "deny", "from", ip])
            return (success2, output2)
        return (success1, output1)
    
    def list_rules(self):
        return self._run_cmd(["ufw", "status"])
    
    def list_zones(self):
        return (False, [])
    
    def get_default_zone(self):
        return (False, "Not supported")
    
    def parse_rules(self):
        rules = []
        success, output = self._run_cmd(["ufw", "status", "numbered"])
        if not success:
            return rules
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Status:') or line.startswith('To') or line.startswith('--'):
                continue
            
            parts = line.split()
            if len(parts) < 4:
                continue
            
            num = parts[0].rstrip('[')
            target = parts[1]
            action = parts[2]
            source = parts[3]
            
            protocol = 'tcp'
            port = ''
            ip = ''
            
            if '/' in target:
                port, proto = target.split('/', 1)
                protocol = proto
            elif target.isdigit():
                port = int(target)
            else:
                rules.append({
                    'type': 'service',
                    'service': target,
                    'port': '',
                    'protocol': '',
                    'action': action.lower(),
                    'ip': '',
                    'zone': '',
                    'description': f"{action}: {target} from {source}"
                })
                continue
            
            if source != 'Anywhere':
                ip = source
            
            rules.append({
                'type': 'port',
                'service': '',
                'port': int(port) if port.isdigit() else port,
                'protocol': protocol,
                'action': action.lower(),
                'ip': ip,
                'zone': '',
                'description': f"{action}: {port}/{protocol} from {source}"
            })
        
        return rules