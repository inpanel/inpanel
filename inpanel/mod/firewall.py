# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''防火墙管理器集成模块'''

from .firewall_base import FirewallManager
from .firewall_firewalld import FirewalldPM
from .firewall_iptables import IptablesPM
from .firewall_ufw import UfwPM
from .firewall_macos import MacosFirewallPM


def get_firewall_manager():
    """工厂函数：根据系统返回对应的防火墙管理器实例"""
    managers = [FirewalldPM(), UfwPM(), IptablesPM(), MacosFirewallPM()]
    for mgr in managers:
        if mgr.detect():
            return mgr
    return None


def get_firewall_type():
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


def web_handler(context, action):
    """Handle web requests for Firewall management"""
    mgr = get_firewall_manager()
    
    if mgr is None:
        context.write({'code': -1, 'msg': '未检测到支持的防火墙类型！', 'data': {'type': 'unknown'}})
        return
    
    firewall_type = get_firewall_type()
    
    if action == 'detect':
        context.write({'code': 0, 'msg': '', 'data': {'type': firewall_type}})
    
    elif action == 'status':
        success, output = mgr.status()
        is_running = mgr.is_running()
        context.write({'code': 0, 'msg': '', 'data': {
            'type': firewall_type,
            'status': output,
            'running': is_running
        }})
    
    elif action == 'start':
        success, output = mgr.start()
        if success:
            context.write({'code': 0, 'msg': '防火墙已启动！', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'启动失败：{output}', 'data': {'output': output}})
    
    elif action == 'stop':
        success, output = mgr.stop()
        if success:
            context.write({'code': 0, 'msg': '防火墙已停止！', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'停止失败：{output}', 'data': {'output': output}})
    
    elif action == 'restart':
        success, output = mgr.restart()
        if success:
            context.write({'code': 0, 'msg': '防火墙已重启！', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'重启失败：{output}', 'data': {'output': output}})
    
    elif action == 'enable':
        success, output = mgr.enable()
        if success:
            context.write({'code': 0, 'msg': '防火墙已设置开机自启！', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'设置失败：{output}', 'data': {'output': output}})
    
    elif action == 'disable':
        success, output = mgr.disable()
        if success:
            context.write({'code': 0, 'msg': '防火墙已关闭开机自启！', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'设置失败：{output}', 'data': {'output': output}})
    
    elif action == 'list_rules':
        rules = mgr.parse_rules()
        context.write({'code': 0, 'msg': '', 'data': {
            'type': firewall_type,
            'rules': rules
        }})
    
    elif action == 'add_port_rule':
        port = context.get_argument('port', '')
        protocol = context.get_argument('protocol', 'tcp')
        zone = context.get_argument('zone', '')
        
        if not port:
            context.write({'code': -1, 'msg': '端口号不能为空！'})
            return
        
        try:
            port_num = int(port)
        except ValueError:
            context.write({'code': -1, 'msg': '端口号必须是数字！'})
            return
        
        success, output = mgr.add_rule(port_num, protocol, zone)
        if success:
            context.write({'code': 0, 'msg': f'已添加端口规则：{port}/{protocol}', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'添加失败：{output}', 'data': {'output': output}})
    
    elif action == 'remove_port_rule':
        port = context.get_argument('port', '')
        protocol = context.get_argument('protocol', 'tcp')
        zone = context.get_argument('zone', '')
        
        if not port:
            context.write({'code': -1, 'msg': '端口号不能为空！'})
            return
        
        try:
            port_num = int(port)
        except ValueError:
            context.write({'code': -1, 'msg': '端口号必须是数字！'})
            return
        
        success, output = mgr.remove_rule(port_num, protocol, zone)
        if success:
            context.write({'code': 0, 'msg': f'已移除端口规则：{port}/{protocol}', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'移除失败：{output}', 'data': {'output': output}})
    
    elif action == 'add_ip_rule':
        ip = context.get_argument('ip', '')
        action_type = context.get_argument('action_type', 'allow')
        
        if not ip:
            context.write({'code': -1, 'msg': 'IP地址不能为空！'})
            return
        
        success, output = mgr.add_ip_rule(ip, action_type)
        if success:
            context.write({'code': 0, 'msg': f'已添加IP规则：{action_type} {ip}', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'添加失败：{output}', 'data': {'output': output}})
    
    elif action == 'remove_ip_rule':
        ip = context.get_argument('ip', '')
        
        if not ip:
            context.write({'code': -1, 'msg': 'IP地址不能为空！'})
            return
        
        success, output = mgr.remove_ip_rule(ip)
        if success:
            context.write({'code': 0, 'msg': f'已移除IP规则：{ip}', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': f'移除失败：{output}', 'data': {'output': output}})
    
    elif action == 'remove_app_rule':
        app_path = context.get_argument('app_path', '')
        
        if not app_path:
            context.write({'code': -1, 'msg': '应用路径不能为空！'})
            return
        
        if hasattr(mgr, 'remove_app_rule'):
            success, output = mgr.remove_app_rule(app_path)
            if success:
                context.write({'code': 0, 'msg': f'已移除应用规则：{app_path}', 'data': {'output': output}})
            else:
                context.write({'code': -1, 'msg': f'移除失败：{output}', 'data': {'output': output}})
        else:
            context.write({'code': -1, 'msg': '当前防火墙类型不支持应用规则管理'})
    
    elif action == 'list_zones':
        success, zones = mgr.list_zones()
        if success:
            context.write({'code': 0, 'msg': '', 'data': {'zones': zones}})
        else:
            context.write({'code': -1, 'msg': '不支持区域管理', 'data': {'zones': []}})
    
    elif action == 'get_default_zone':
        success, zone = mgr.get_default_zone()
        if success:
            context.write({'code': 0, 'msg': '', 'data': {'zone': zone}})
        else:
            context.write({'code': -1, 'msg': '不支持区域管理', 'data': {'zone': ''}})
    
    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})