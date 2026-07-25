# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''日志维护管理模块

提供面板日志、SSH登录日志、网站日志、服务日志的查询、导出等功能。
'''

import re
import subprocess
from datetime import datetime
from pathlib import Path
from time import time

from ..base import (
    data_path,
    files_log,
    filespath_log,
    logerror,
    logfile,
    logging_path,
)


def _read_lines(filepath, tail=None):
    """读取文件内容，返回行列表。

    Args:
        filepath: 文件路径
        tail: 若指定，则只返回最后 N 行

    Returns:
        list: 行内容列表
    """
    path = Path(filepath)
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        lines = [line.rstrip('\n').rstrip('\r') for line in lines]
        if tail and tail > 0:
            lines = lines[-tail:]
        return lines
    except Exception:
        return []


def _read_file_content(filepath, tail=None):
    """读取文件内容，返回文本字符串。

    Args:
        filepath: 文件路径
        tail: 若指定，则只返回最后 N 行

    Returns:
        str: 文件内容
    """
    path = Path(filepath)
    if not path.exists():
        return ''
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            if tail:
                lines = f.readlines()
                lines = lines[-tail:]
                return ''.join(lines)
            return f.read()
    except Exception:
        return ''


# ========== 面板日志 ==========

def get_operation_log():
    """获取面板操作日志。

    读取 InPanel 主日志，过滤面板操作相关条目。

    Returns:
        list: 操作日志条目列表
    """
    lines = _read_lines(logfile, tail=500)
    entries = []
    for line in lines:
        if not line.strip():
            continue
        entry = _parse_log_line(line)
        if entry:
            entries.append(entry)
    return entries


def get_login_log(status_filter='all'):
    """获取面板登录日志。

    Args:
        status_filter: 状态筛选，'all'/'success'/'fail'

    Returns:
        list: 登录日志条目列表
    """
    lines = _read_lines(logfile, tail=500)
    entries = []
    for line in lines:
        if 'login' in line.lower() or '登录' in line or 'authentication' in line.lower():
            entry = _parse_log_line(line)
            if entry:
                if status_filter == 'all':
                    entries.append(entry)
                elif status_filter == 'success' and ('成功' in entry.get('message', '') or 'success' in entry.get('message', '').lower()):
                    entries.append(entry)
                elif status_filter == 'fail' and ('失败' in entry.get('message', '') or '错误' in entry.get('message', '') or 'fail' in entry.get('message', '').lower() or 'error' in entry.get('message', '').lower()):
                    entries.append(entry)
    return entries


def get_runtime_log():
    """获取面板运行日志。

    只读取错误日志（主日志已移除）。

    Returns:
        str: 错误日志内容
    """
    return _read_file_content(logerror, tail=500)


def get_error_log():
    """获取面板错误日志。

    读取错误日志文件内容。

    Returns:
        str: 错误日志内容
    """
    return _read_file_content(logerror, tail=500)


def get_task_log():
    """获取后台异步任务日志。

    读取 task.log 文件内容。

    Returns:
        list: 任务日志条目列表
    """
    task_log_path = str(Path(logging_path) / 'task.log')
    lines = _read_lines(task_log_path)
    entries = []
    for line in lines:
        if not line.strip():
            continue
        entry = _parse_task_log_line(line)
        if entry:
            entries.append(entry)
    return entries


def _parse_task_log_line(line):
    """解析任务日志行。

    格式: 时间 | 任务名称 | 任务状态 | 执行结果 | 任务描述 | 开始时间 | 结束时间 | 耗时(秒)

    Args:
        line: 日志行字符串

    Returns:
        dict or None: 解析后的日志条目
    """
    parts = line.split('|')
    if len(parts) >= 8:
        return {
            'time': parts[0].strip(),
            'name': parts[1].strip(),
            'status': parts[2].strip(),
            'result': parts[3].strip(),
            'desc': parts[4].strip(),
            'start_time': parts[5].strip(),
            'end_time': parts[6].strip(),
            'duration': parts[7].strip(),
        }
    # 简单解析：尝试至少获取时间和消息
    entry = _parse_log_line(line)
    return entry


def get_files_log():
    """获取面板文件操作日志。

    读取文件操作日志文件。

    Returns:
        list: 文件操作日志条目
    """
    lines = _read_lines(files_log)
    entries = []
    for line in lines:
        if not line.strip():
            continue
        entry = _parse_file_operation_log(line)
        if entry:
            entries.append(entry)
    return entries


def get_files_access_log():
    """获取面板文件访问日志（文件浏览路径记录）。

    读取文件路径访问日志文件。

    Returns:
        list: 文件访问日志条目
    """
    lines = _read_lines(filespath_log)
    entries = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split('|', 1)
        if len(parts) == 2:
            entries.append({
                'time': parts[0].strip(),
                'path': parts[1].strip(),
            })
        else:
            entries.append({
                'time': '',
                'path': line.strip(),
            })
    return entries


def get_cron_log():
    """获取计划任务日志。

    从系统 cron 日志中读取，正确解析时间和级别。

    Returns:
        list: 计划任务日志条目
    """
    cron_log_paths = [
        '/var/log/cron',
        '/var/log/cron.log',
        '/var/log/syslog',
    ]
    entries = []
    for log_path in cron_log_paths:
        if Path(log_path).exists():
            lines = _read_lines(log_path, tail=200)
            for line in lines:
                if 'CRON' in line or 'cron' in line.lower():
                    entry = _parse_cron_log_line(line)
                    if entry:
                        entries.append(entry)
            break
    return entries


def _parse_cron_log_line(line):
    """解析 cron 日志行，正确提取时间、级别和消息。

    支持两种格式：
    1. syslog 格式: Jan 24 12:00:01 hostname CRON[pid]: (user) CMD (command)
    2. rsyslog 标准格式: 2024-01-24 12:00:01 hostname CRON[pid]: message

    Args:
        line: 日志行字符串

    Returns:
        dict: 解析后的日志条目
    """
    entry = {'time': '', 'level': 'INFO', 'message': line}

    # 尝试匹配 ISO 日期格式: 2024-01-24 12:00:01
    match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.*)', line)
    if match:
        entry['time'] = match.group(1)
        remaining = match.group(2)
        # 尝试从剩余内容提取级别
        level_match = re.match(r'(\w+)\s+(.*)', remaining)
        if level_match and level_match.group(1) in ('INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'):
            entry['level'] = level_match.group(1)
            entry['message'] = level_match.group(2)
        else:
            entry['message'] = remaining
        return entry

    # 尝试匹配 syslog 格式: Jan 24 12:00:01 hostname ...
    match = re.match(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)', line)
    if match:
        entry['time'] = match.group(1)
        remaining = match.group(3)
        # 提取 CRON 后面的内容作为消息
        cron_match = re.search(r'CRON\[\d+\]:\s*(.*)', remaining)
        if cron_match:
            entry['message'] = cron_match.group(1)
        else:
            entry['message'] = remaining
        return entry

    return entry


def _parse_log_line(line):
    """解析日志行，提取时间、级别、消息等信息。

    Args:
        line: 日志行字符串

    Returns:
        dict or None: 解析后的日志条目
    """
    entry = {'time': '', 'level': '', 'message': line}
    # 尝试匹配常见日志格式: 2024-01-01 12:00:00 - INFO - message
    match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*[-–]\s*(\w+)\s*[-–]\s*(.*)', line)
    if match:
        entry['time'] = match.group(1)
        entry['level'] = match.group(2)
        entry['message'] = match.group(3)
        return entry
    # 尝试匹配 syslog 格式: Jan  1 12:00:00 hostname process[pid]: message
    match = re.match(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+\S+\s+(\S+?)(?:\[\d+\])?:\s*(.*)', line)
    if match:
        entry['time'] = match.group(1)
        entry['level'] = match.group(2)
        entry['message'] = match.group(3)
        return entry
    return entry


def _parse_file_operation_log(line):
    """解析文件操作日志行。

    格式: 时间 | 文件路径 | 操作 | 结果 | 变更内容（可选）

    Args:
        line: 日志行字符串

    Returns:
        dict or None: 解析后的日志条目
    """
    parts = line.split('|')
    if len(parts) >= 5:
        return {
            'time': parts[0].strip(),
            'path': parts[1].strip(),
            'operation': parts[2].strip(),
            'result': parts[3].strip(),
            'detail': parts[4].strip(),
        }
    elif len(parts) >= 4:
        return {
            'time': parts[0].strip(),
            'path': parts[1].strip(),
            'operation': parts[2].strip(),
            'result': parts[3].strip(),
            'detail': '',
        }
    elif len(parts) >= 3:
        return {
            'time': parts[0].strip(),
            'path': parts[1].strip(),
            'operation': parts[2].strip(),
            'result': '',
            'detail': '',
        }
    return None


# 用于去重：记录最后写入的日志内容和时间
_last_log_content = None
_last_log_time = 0


def write_file_operation_log(operation, filepath, result, detail=''):
    """写入文件操作日志。

    Args:
        operation: 操作类型（创建/修改/删除/复制/移动/重命名/查看/压缩/解压等）
        filepath: 操作的文件路径
        result: 操作结果（成功/失败）
        detail: 变更内容（可选，如旧名称→新名称、旧路径→新路径等）

    Returns:
        bool: 是否写入成功
    """
    global _last_log_content, _last_log_time
    try:
        log_path = Path(files_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        now = time()
        timestamp = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
        if detail:
            content = f'{filepath} | {operation} | {result} | {detail}'
            line = f'{timestamp} | {content}\n'
        else:
            content = f'{filepath} | {operation} | {result}'
            line = f'{timestamp} | {content}\n'
        # 去重：2秒内与上一条日志内容完全相同则跳过
        if content == _last_log_content and (now - _last_log_time) < 2:
            return True
        _last_log_content = content
        _last_log_time = now
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(line)
        return True
    except Exception:
        return False


def write_file_access_log(filepath):
    """写入文件访问路径日志。

    记录浏览过的文件路径。

    Args:
        filepath: 浏览的文件路径

    Returns:
        bool: 是否写入成功
    """
    try:
        log_path = Path(filespath_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'{timestamp} | {filepath}\n'
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(line)
        return True
    except Exception:
        return False


# ========== SSH 登录日志 ==========

def get_ssh_log(status_filter='all'):
    """获取 SSH 登录日志。

    从系统安全日志中读取 SSH 登录记录。

    Args:
        status_filter: 状态筛选，'all'/'success'/'fail'

    Returns:
        list: SSH 登录日志条目
    """
    auth_log_paths = [
        '/var/log/auth.log',
        '/var/log/secure',
    ]
    entries = []
    for log_path in auth_log_paths:
        if Path(log_path).exists():
            lines = _read_lines(log_path, tail=500)
            for line in lines:
                if 'sshd' not in line.lower():
                    continue
                entry = _parse_ssh_log_line(line)
                if entry:
                    if status_filter == 'all':
                        entries.append(entry)
                    elif status_filter == 'success' and entry.get('status') == '成功':
                        entries.append(entry)
                    elif status_filter == 'fail' and entry.get('status') == '失败':
                        entries.append(entry)
            break
    return entries


def _parse_ssh_log_line(line):
    """解析 SSH 登录日志行。

    正确提取时间（含年份）、IP、端口、用户、状态。

    Args:
        line: 日志行字符串

    Returns:
        dict or None: 解析后的 SSH 登录条目
    """
    entry = {'time': '', 'ip': '', 'port': '', 'location': '', 'user': '', 'status': ''}

    # 匹配时间 - 支持多种格式
    # ISO 格式: 2024-01-24 12:00:01
    iso_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
    if iso_match:
        entry['time'] = iso_match.group(1)
    else:
        # syslog 格式: Jan 24 12:00:01
        syslog_match = re.match(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', line)
        if syslog_match:
            time_str = syslog_match.group(1)
            # 添加当前年份
            current_year = datetime.now().year
            entry['time'] = f'{current_year} {time_str}'

    # 匹配 IP 和端口 (from X.X.X.X port YYYY)
    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+port\s+(\d+)', line)
    if ip_match:
        entry['ip'] = ip_match.group(1)
        entry['port'] = ip_match.group(2)
    else:
        # 匹配 from X.X.X.X 或 from hostname
        from_match = re.search(r'from\s+(\S+)', line)
        if from_match:
            addr = from_match.group(1)
            if ':' in addr and not addr.startswith('::'):
                # IPv6 with port? Actually could be host:port or ipv6
                parts = addr.rsplit(':', 1)
                host = parts[0]
                port = parts[1]
                if port.isdigit():
                    entry['ip'] = host
                    entry['port'] = port
                else:
                    entry['ip'] = addr
            else:
                entry['ip'] = addr

    # 匹配用户
    user_match = re.search(r'for\s+(\S+)', line)
    if user_match:
        entry['user'] = user_match.group(1)
    else:
        user_match2 = re.search(r'user[=\s]+(\S+)', line)
        if user_match2:
            entry['user'] = user_match2.group(1).rstrip(',')

    # 匹配 invalid user
    invalid_match = re.search(r'[Ii]nvalid user\s+(\S+)', line)
    if invalid_match:
        entry['user'] = invalid_match.group(1)

    # 匹配状态
    if 'Accepted' in line or 'accepted' in line.lower():
        entry['status'] = '成功'
    elif 'Failed' in line or 'failed' in line.lower() or 'Invalid' in line or 'error' in line.lower():
        entry['status'] = '失败'
    else:
        entry['status'] = '其他'

    return entry


# ========== 网站日志 ==========

def get_website_runtime_log(server_type='nginx', site_name=''):
    """获取网站运行日志。

    Args:
        server_type: 服务器类型，如 nginx、apache
        site_name: 站点名称（可选）

    Returns:
        str: 日志内容
    """
    log_dirs = []
    if server_type == 'nginx':
        log_dirs = [
            '/var/log/nginx',
            '/usr/local/nginx/logs',
        ]
    elif server_type == 'apache':
        log_dirs = [
            '/var/log/httpd',
            '/var/log/apache2',
        ]

    content = ''
    for log_dir in log_dirs:
        log_path = Path(log_dir)
        if not log_path.exists():
            continue
        access_log = log_path / 'access.log'
        error_log = log_path / 'error.log'
        if access_log.exists():
            content += f'=== {access_log} ===\n'
            content += _read_file_content(str(access_log), tail=200)
            content += '\n\n'
        if error_log.exists():
            content += f'=== {error_log} ===\n'
            content += _read_file_content(str(error_log), tail=200)
            content += '\n\n'
        break

    return content


def get_website_error_log(server_type='nginx'):
    """获取网站异常日志。

    Args:
        server_type: 服务器类型，如 nginx、apache

    Returns:
        str: 错误日志内容
    """
    log_dirs = []
    if server_type == 'nginx':
        log_dirs = [
            '/var/log/nginx',
            '/usr/local/nginx/logs',
        ]
    elif server_type == 'apache':
        log_dirs = [
            '/var/log/httpd',
            '/var/log/apache2',
        ]

    content = ''
    for log_dir in log_dirs:
        log_path = Path(log_dir)
        if not log_path.exists():
            continue
        error_log = log_path / 'error.log'
        if error_log.exists():
            content = _read_file_content(str(error_log), tail=200)
        break

    return content


# ========== 服务日志 ==========

SERVICE_LOG_CONFIG = {
    'nginx': {
        'name': 'Nginx',
        'paths': ['/var/log/nginx/error.log', '/var/log/nginx/access.log',
                   '/usr/local/nginx/logs/error.log', '/usr/local/nginx/logs/access.log'],
    },
    'mysql': {
        'name': 'MySQL',
        'paths': ['/var/log/mysql/error.log', '/var/log/mysqld.log',
                   '/var/log/mariadb/mariadb.log'],
    },
    'mariadb': {
        'name': 'MariaDB',
        'paths': ['/var/log/mariadb/mariadb.log', '/var/log/mysql/error.log'],
    },
    'redis': {
        'name': 'Redis',
        'paths': ['/var/log/redis/redis-server.log', '/var/log/redis/redis.log'],
    },
    'php': {
        'name': 'PHP',
        'paths': ['/var/log/php-fpm.log', '/var/log/php_errors.log',
                   '/var/log/php/error.log', '/var/log/php8*-fpm.log'],
    },
    'vsftpd': {
        'name': 'vsftpd',
        'paths': ['/var/log/vsftpd.log', '/var/log/xferlog'],
    },
    'apache': {
        'name': 'Apache',
        'paths': ['/var/log/httpd/error_log', '/var/log/httpd/error.log',
                   '/var/log/apache2/error.log'],
    },
    'docker': {
        'name': 'Docker',
        'paths': ['/var/log/docker.log'],
    },
}


def get_service_list():
    """获取可用的服务日志列表。

    Returns:
        list: 服务列表，包含名称和可用日志文件
    """
    services = []
    for svc_id, svc_info in SERVICE_LOG_CONFIG.items():
        available_logs = []
        for log_path_str in svc_info['paths']:
            log_path = Path(log_path_str)
            if log_path.exists():
                available_logs.append({
                    'path': str(log_path),
                    'name': log_path.name,
                    'size': log_path.stat().st_size if log_path.is_file() else 0,
                })
        services.append({
            'id': svc_id,
            'name': svc_info['name'],
            'available': len(available_logs) > 0,
            'logs': available_logs,
        })
    return services


def get_service_log_content(service_id, log_path=''):
    """获取指定服务的日志内容。

    Args:
        service_id: 服务 ID，如 nginx、mysql
        log_path: 具体日志文件路径（可选）

    Returns:
        dict: 包含服务名称和日志内容
    """
    svc_info = SERVICE_LOG_CONFIG.get(service_id, {})
    svc_name = svc_info.get('name', service_id)

    if log_path and Path(log_path).exists():
        return {
            'name': svc_name,
            'log_path': log_path,
            'content': _read_file_content(log_path, tail=500),
        }

    # 查找第一个可用日志文件
    for log_path_str in svc_info.get('paths', []):
        if Path(log_path_str).exists():
            return {
                'name': svc_name,
                'log_path': log_path_str,
                'content': _read_file_content(log_path_str, tail=500),
            }

    return {
        'name': svc_name,
        'log_path': '',
        'content': '',
    }


# ========== 通用导出 ==========

def export_log_content(content, filename_prefix='log'):
    """生成导出的日志文件内容。

    Args:
        content: 日志内容字符串
        filename_prefix: 文件名前缀

    Returns:
        tuple: (内容, 文件名)
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{filename_prefix}_{timestamp}.log'
    return content, filename


# ========== Web Handler ==========

def web_handler(context):
    """日志模块的 Web 请求处理入口。

    支持以下 action：
    GET:
      - operation: 面板操作日志
      - login: 面板登录日志（参数: status=all/success/fail）
      - error: 面板错误日志
      - task: 后台异步任务日志
      - files: 文件操作日志
      - files_access: 文件访问日志（路径浏览记录）
      - cron: 计划任务日志
      - ssh: SSH 登录日志（参数: status=all/success/fail）
      - website_runtime: 网站运行日志（参数: type=nginx/apache）
      - website_error: 网站异常日志（参数: type=nginx/apache）
      - service_list: 服务日志列表
      - service_log: 服务日志内容（参数: id, path）
      - export: 导出日志（参数: type, content）
    """
    action = context.get_argument('action', '')

    if action == 'operation':
        entries = get_operation_log()
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'login':
        status = context.get_argument('status', 'all')
        entries = get_login_log(status)
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'error':
        content = get_error_log()
        context.write({'code': 0, 'msg': '', 'data': {'content': content}})

    elif action == 'task':
        entries = get_task_log()
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'runtime':
        content = get_runtime_log()
        context.write({'code': 0, 'msg': '', 'data': {'content': content}})

    elif action == 'files':
        entries = get_files_log()
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'files_access':
        entries = get_files_access_log()
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'cron':
        entries = get_cron_log()
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'ssh':
        status = context.get_argument('status', 'all')
        entries = get_ssh_log(status)
        context.write({'code': 0, 'msg': '', 'data': entries})

    elif action == 'website_runtime':
        server_type = context.get_argument('type', 'nginx')
        content = get_website_runtime_log(server_type)
        context.write({'code': 0, 'msg': '', 'data': {'content': content}})

    elif action == 'website_error':
        server_type = context.get_argument('type', 'nginx')
        content = get_website_error_log(server_type)
        context.write({'code': 0, 'msg': '', 'data': {'content': content}})

    elif action == 'service_list':
        services = get_service_list()
        context.write({'code': 0, 'msg': '', 'data': services})

    elif action == 'service_log':
        service_id = context.get_argument('id', '')
        log_path = context.get_argument('path', '')
        data = get_service_log_content(service_id, log_path)
        context.write({'code': 0, 'msg': '', 'data': data})

    elif action == 'export':
        content = context.get_argument('content', '')
        log_type = context.get_argument('type', 'log')
        export_content, filename = export_log_content(content, log_type)
        context.set_header('Content-Type', 'application/octet-stream')
        context.set_header('Content-Disposition', f'attachment; filename={filename}')
        context.write(export_content)

    else:
        context.write({'code': -1, 'msg': f'未定义的操作: {action}'})
