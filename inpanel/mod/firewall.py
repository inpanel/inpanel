# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for Firewall Manager Integration'''

from typing import Dict

from .firewall_base import FirewallManager
from .firewall_firewalld import FirewalldPM
from .firewall_iptables import IptablesPM
from .firewall_ufw import UfwPM
from .firewall_macos import MacosFirewallPM


def get_firewall_manager() -> FirewallManager | None:
    """工厂函数：根据系统返回对应的防火墙管理器实例"""
    managers = [FirewalldPM(), UfwPM(), IptablesPM(), MacosFirewallPM()]
    for mgr in managers:
        if mgr.detect():
            return mgr
    return None


def get_firewall_type() -> str:
    """获取当前系统的防火墙类型"""
    mgr = get_firewall_manager()
    if isinstance(mgr, FirewalldPM):
        return 'firewalld'
    elif isinstance(mgr, UfwPM):
        return 'ufw'
    elif isinstance(mgr, IptablesPM):
        return 'iptables'
    elif isinstance(mgr, MacosFirewallPM):
        return 'macos'
    return 'unknown'


def web_handler(context: Dict) -> Dict:
    """Handle web requests for Firewall management"""
    action = context.get('action', '')
    mgr = get_firewall_manager()
    
    if mgr is None:
        return {'code': -1, 'msg': '未检测到支持的防火墙类型！', 'data': {'type': 'unknown'}}
    
    firewall_type = get_firewall_type()
    
    if action == 'detect':
        return {'code': 0, 'msg': '', 'data': {'type': firewall_type}}
    
    elif action == 'status':
        success, output = mgr.status()
        is_running = mgr.is_running()
        return {'code': 0, 'msg': '', 'data': {
            'type': firewall_type,
            'status': output,
            'running': is_running
        }}
    
    elif action == 'start':
        success, output = mgr.start()
        if success:
            return {'code': 0, 'msg': '防火墙已启动！', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'启动失败：{output}', 'data': {'output': output}}
    
    elif action == 'stop':
        success, output = mgr.stop()
        if success:
            return {'code': 0, 'msg': '防火墙已停止！', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'停止失败：{output}', 'data': {'output': output}}
    
    elif action == 'restart':
        success, output = mgr.restart()
        if success:
            return {'code': 0, 'msg': '防火墙已重启！', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'重启失败：{output}', 'data': {'output': output}}
    
    elif action == 'enable':
        success, output = mgr.enable()
        if success:
            return {'code': 0, 'msg': '防火墙已设置开机自启！', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'设置失败：{output}', 'data': {'output': output}}
    
    elif action == 'disable':
        success, output = mgr.disable()
        if success:
            return {'code': 0, 'msg': '防火墙已关闭开机自启！', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'设置失败：{output}', 'data': {'output': output}}
    
    elif action == 'list_rules':
        rules = mgr.parse_rules()
        return {'code': 0, 'msg': '', 'data': {
            'type': firewall_type,
            'rules': rules
        }}
    
    elif action == 'add_port_rule':
        port = context.get('port', '')
        protocol = context.get('protocol', 'tcp')
        zone = context.get('zone', '')
        
        if not port:
            return {'code': -1, 'msg': '端口号不能为空！'}
        
        try:
            port_num = int(port)
        except ValueError:
            return {'code': -1, 'msg': '端口号必须是数字！'}
        
        success, output = mgr.add_rule(port_num, protocol, zone)
        if success:
            return {'code': 0, 'msg': f'已添加端口规则：{port}/{protocol}', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'添加失败：{output}', 'data': {'output': output}}
    
    elif action == 'remove_port_rule':
        port = context.get('port', '')
        protocol = context.get('protocol', 'tcp')
        zone = context.get('zone', '')
        
        if not port:
            return {'code': -1, 'msg': '端口号不能为空！'}
        
        try:
            port_num = int(port)
        except ValueError:
            return {'code': -1, 'msg': '端口号必须是数字！'}
        
        success, output = mgr.remove_rule(port_num, protocol, zone)
        if success:
            return {'code': 0, 'msg': f'已移除端口规则：{port}/{protocol}', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'移除失败：{output}', 'data': {'output': output}}
    
    elif action == 'add_ip_rule':
        ip = context.get('ip', '')
        action_type = context.get('action_type', 'allow')
        
        if not ip:
            return {'code': -1, 'msg': 'IP地址不能为空！'}
        
        success, output = mgr.add_ip_rule(ip, action_type)
        if success:
            return {'code': 0, 'msg': f'已添加IP规则：{action_type} {ip}', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'添加失败：{output}', 'data': {'output': output}}
    
    elif action == 'remove_ip_rule':
        ip = context.get('ip', '')
        
        if not ip:
            return {'code': -1, 'msg': 'IP地址不能为空！'}
        
        success, output = mgr.remove_ip_rule(ip)
        if success:
            return {'code': 0, 'msg': f'已移除IP规则：{ip}', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': f'移除失败：{output}', 'data': {'output': output}}
    
    elif action == 'remove_app_rule':
        app_path = context.get('app_path', '')
        
        if not app_path:
            return {'code': -1, 'msg': '应用路径不能为空！'}
        
        if hasattr(mgr, 'remove_app_rule'):
            success, output = mgr.remove_app_rule(app_path)
            if success:
                return {'code': 0, 'msg': f'已移除应用规则：{app_path}', 'data': {'output': output}}
            else:
                return {'code': -1, 'msg': f'移除失败：{output}', 'data': {'output': output}}
        else:
            return {'code': -1, 'msg': '当前防火墙类型不支持应用规则管理'}
    
    elif action == 'list_zones':
        success, zones = mgr.list_zones()
        if success:
            return {'code': 0, 'msg': '', 'data': {'zones': zones}}
        else:
            return {'code': -1, 'msg': '不支持区域管理', 'data': {'zones': []}}
    
    elif action == 'get_default_zone':
        success, zone = mgr.get_default_zone()
        if success:
            return {'code': 0, 'msg': '', 'data': {'zone': zone}}
        else:
            return {'code': -1, 'msg': '不支持区域管理', 'data': {'zone': ''}}
    
    else:
        return {'code': -1, 'msg': '未定义的操作！'}