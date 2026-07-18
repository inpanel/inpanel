# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''查询处理模块'''

from . import server
from . import service


def handle_query(items):
    """Handle query request.
    
    Args:
        items: comma-separated items to query
    
    Returns:
        dict with query results
    """
    items = items.split(',')
    qdict = {'server': [], 'service': [], 'config': [], 'tool': []}
    
    for item in items:
        if item == 'all':
            qdict = {'server': 'all', 'service': 'all'}
            break
        elif item == 'dynamic':
            qdict = {'server': 'dynamic', 'service': 'dynamic'}
            break
        elif item == 'server.all':
            qdict['server'] = 'all'
        elif item == 'service.all':
            qdict['service'] = 'all'
        else:
            iteminfo = item.split('.', 1)
            if len(iteminfo) != 2:
                continue
            sec, q = iteminfo
            if sec not in ('server', 'service', 'config', 'tool'):
                continue
            if qdict[sec] == 'all':
                continue
            if q in ('all', 'dynamic'):
                qdict[sec] = q
            else:
                qdict[sec].append(q)

    config_items = {
        'fstab': False,
    }
    tool_items = {
        'supportfs': False,
    }

    result = {}
    for sec, qs in qdict.items():
        if sec == 'server':
            server_items = server.ServerInfo.server_items
            if qs == 'all':
                qs = server_items.keys()
            elif qs == 'dynamic':
                qs = [item for item, relup in server_items.items() if relup == True]
            for q in qs:
                if q not in server_items:
                    continue
                result['%s.%s' % (sec, q)] = getattr(server.ServerInfo, q)()
        elif sec == 'service':
            service_items = service.Service.service_items
            autostart_services = service.get_autostart_list()
            if qs == 'all':
                qs = service_items.keys()
            elif qs == 'dynamic':
                qs = [item for item, relup in service_items.items() if relup == True]
            for q in qs:
                if q not in service_items:
                    continue
                status = service.Service.status(q)
                result['%s.%s' % (sec, q)] = status and {
                    'status': status,
                    'autostart': q in autostart_services,
                } or None
        elif sec == 'config':
            for q in qs:
                params = []
                if q.endswith(')'):
                    q = q.strip(')').split('(', 1)
                    if len(q) != 2:
                        continue
                    q, params = q
                    params = params.split(',')
                if q not in config_items:
                    continue
                result['%s.%s' % (sec, q)] = getattr(server.ServerInfo, q)(*params)
        elif sec == 'tool':
            for q in qs:
                params = []
                if q.endswith(')'):
                    q = q.strip(')').split('(', 1)
                    if len(q) != 2:
                        continue
                    q, params = q
                    params = params.split(',')
                if q not in tool_items:
                    continue
                result['%s.%s' % (sec, q)] = getattr(server.ServerTool, q)(*params)

    return result
