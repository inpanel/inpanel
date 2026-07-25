#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Redis 数据库管理模块"""

import re
import shlex
from pathlib import Path

import pexpect


def _escape(string):
    """转义字符串中的特殊字符"""
    return string.replace("'", "\\'")


def _redis_cli(password=None, host='127.0.0.1', port=6379):
    """打开 redis-cli 客户端并认证登录"""
    args = ['redis-cli', '-h', host, '-p', str(port)]
    if password:
        args.extend(['-a', password, '--no-auth-warning'])

    child = pexpect.spawn(args[0], args[1:])
    i = child.expect([r'127.0.0.1:\d+>', r'(127.0.0.1:\d+)\s*$', pexpect.EOF, 'NOAUTH', 'Could not connect'])
    if i in (0, 1):
        return child
    if i == 3:
        # 需要密码认证
        child.close()
        # 重新连接不带密码，用 AUTH
        args2 = ['redis-cli', '-h', host, '-p', str(port)]
        child2 = pexpect.spawn(args2[0], args2[1:])
        j = child2.expect([r'127.0.0.1:\d+>', r'(127.0.0.1:\d+)\s*$', pexpect.EOF, 'Could not connect'])
        if j in (0, 1):
            if password:
                child2.sendline(f'AUTH {password}')
                k = child2.expect([r'OK', 'ERR', pexpect.EOF])
                if k == 0:
                    child2.expect([r'127.0.0.1:\d+>', pexpect.EOF])
                    return child2
            child2.close()
            return None
        child2.close()
        return None
    if child.isalive():
        child.wait()
    return None


def _send_cmd(child, cmd):
    """发送命令并返回结果"""
    child.sendline(cmd)
    i = child.expect([r'127.0.0.1:\d+>', r'(127.0.0.1:\d+)\s*$', pexpect.EOF])
    if i == 2:
        if child.isalive():
            child.wait()
        return None
    output = child.before
    if isinstance(output, bytes):
        output = output.decode('utf-8', errors='replace')
    return output


def _exit(child):
    """退出 redis-cli"""
    child.sendline('exit')
    child.expect([pexpect.EOF])
    if child.isalive():
        child.wait()


def check_connection(password=None, host='127.0.0.1', port=6379):
    """检查 Redis 连接是否正常"""
    child = _redis_cli(password, host, port)
    if not child:
        return False
    _exit(child)
    return True


def get_server_info(password=None, host='127.0.0.1', port=6379):
    """获取 Redis 服务器信息"""
    child = _redis_cli(password, host, port)
    if not child:
        return None

    output = _send_cmd(child, 'INFO')
    _exit(child)

    if not output:
        return None

    info = {}
    # 处理可能的提示信息
    lines = output.strip().split('\n')
    current_section = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            if line.startswith('# '):
                current_section = line[2:].strip().lower()
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            if current_section:
                if current_section not in info:
                    info[current_section] = {}
                info[current_section][key.strip()] = value.strip()
            else:
                info[key.strip()] = value.strip()

    return info


def get_database_count(password=None, host='127.0.0.1', port=6379):
    """获取数据库数量"""
    child = _redis_cli(password, host, port)
    if not child:
        return None

    output = _send_cmd(child, 'CONFIG GET databases')
    _exit(child)

    if not output:
        return None

    # 解析结果: 1) "databases"  2) "16"
    lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
    for i, line in enumerate(lines):
        if 'databases' in line and i + 1 < len(lines):
            try:
                return int(lines[i + 1].strip('"'))
            except ValueError:
                return 16
    return 16


def get_databases_info(password=None, host='127.0.0.1', port=6379):
    """获取所有数据库的 key 数量"""
    child = _redis_cli(password, host, port)
    if not child:
        return None

    db_count = get_database_count(password, host, port)
    if not db_count:
        db_count = 16

    databases = []
    for db in range(db_count):
        _send_cmd(child, f'SELECT {db}')
        output = _send_cmd(child, 'DBSIZE')
        if output:
            match = re.search(r'(\d+)', output)
            keys = int(match.group(1)) if match else 0
        else:
            keys = 0
        databases.append({
            'index': db,
            'keys': keys,
            'name': f'db{db}',
        })

    _exit(child)
    return databases


def get_database_detail(password=None, host='127.0.0.1', port=6379, db=0):
    """获取指定数据库的详细信息"""
    child = _redis_cli(password, host, port)
    if not child:
        return None

    _send_cmd(child, f'SELECT {db}')
    key_count = 0
    output = _send_cmd(child, 'DBSIZE')
    if output:
        match = re.search(r'(\d+)', output)
        key_count = int(match.group(1)) if match else 0

    # 获取 keys
    keys = []
    if key_count > 0:
        keys_output = _send_cmd(child, 'KEYS *')
        if keys_output:
            for line in keys_output.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('127.0.0.1'):
                    # 提取 key 名称，去除可能的序号前缀
                    m = re.match(r'^\s*\d+\)\s*"(.+)"', line)
                    if m:
                        keys.append(m.group(1))
                    else:
                        clean = line.strip('"').strip()
                        if clean:
                            keys.append(clean)

    # 限制 keys 数量，避免过多
    if len(keys) > 200:
        keys = keys[:200]

    key_details = []
    for key in keys[:50]:  # 只取前 50 个获取类型和 TTL
        type_output = _send_cmd(child, f'TYPE {key}')
        key_type = 'unknown'
        if type_output:
            m = re.search(r'(\w+)', type_output)
            if m:
                key_type = m.group(1)

        ttl_output = _send_cmd(child, f'TTL {key}')
        ttl = -2
        if ttl_output:
            m = re.search(r'(-?\d+)', ttl_output)
            if m:
                ttl = int(m.group(1))

        key_details.append({
            'name': key,
            'type': key_type,
            'ttl': ttl,
        })

    _exit(child)
    return {
        'index': db,
        'name': f'db{db}',
        'key_count': key_count,
        'keys': keys,
        'key_details': key_details,
    }


def flush_database(password=None, host='127.0.0.1', port=6379, db=0):
    """清空指定数据库"""
    child = _redis_cli(password, host, port)
    if not child:
        return False

    _send_cmd(child, f'SELECT {db}')
    output = _send_cmd(child, 'FLUSHDB')
    _exit(child)

    if output and 'OK' in output:
        return True
    return False


def flush_all(password=None, host='127.0.0.1', port=6379):
    """清空所有数据库"""
    child = _redis_cli(password, host, port)
    if not child:
        return False

    output = _send_cmd(child, 'FLUSHALL')
    _exit(child)

    if output and 'OK' in output:
        return True
    return False


def get_key_value(password=None, host='127.0.0.1', port=6379, db=0, key=''):
    """获取指定 key 的值"""
    child = _redis_cli(password, host, port)
    if not child:
        return None

    _send_cmd(child, f'SELECT {db}')

    # 获取类型
    type_output = _send_cmd(child, f'TYPE {key}')
    key_type = 'unknown'
    if type_output:
        m = re.search(r'(\w+)', type_output)
        if m:
            key_type = m.group(1)

    # 获取 TTL
    ttl_output = _send_cmd(child, f'TTL {key}')
    ttl = -2
    if ttl_output:
        m = re.search(r'(-?\d+)', ttl_output)
        if m:
            ttl = int(m.group(1))

    # 获取值
    value = None
    size = 0
    if key_type == 'string':
        val_output = _send_cmd(child, f'GET {key}')
        if val_output:
            lines = val_output.strip().split('\n')
            if len(lines) >= 1:
                v = lines[0].strip()
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                value = v
                size = len(v.encode('utf-8')) if v else 0
    elif key_type == 'list':
        len_output = _send_cmd(child, f'LLEN {key}')
        if len_output:
            m = re.search(r'(\d+)', len_output)
            if m:
                size = int(m.group(1))
        value = f'[List: {size} items]'
    elif key_type == 'set':
        card_output = _send_cmd(child, f'SCARD {key}')
        if card_output:
            m = re.search(r'(\d+)', card_output)
            if m:
                size = int(m.group(1))
        value = f'[Set: {size} members]'
    elif key_type == 'zset':
        card_output = _send_cmd(child, f'ZCARD {key}')
        if card_output:
            m = re.search(r'(\d+)', card_output)
            if m:
                size = int(m.group(1))
        value = f'[ZSet: {size} members]'
    elif key_type == 'hash':
        len_output = _send_cmd(child, f'HLEN {key}')
        if len_output:
            m = re.search(r'(\d+)', len_output)
            if m:
                size = int(m.group(1))
        value = f'[Hash: {size} fields]'
    else:
        value = f'[Unknown type: {key_type}]'

    _exit(child)
    return {
        'key': key,
        'type': key_type,
        'ttl': ttl,
        'value': value,
        'size': size,
    }


def delete_key(password=None, host='127.0.0.1', port=6379, db=0, key=''):
    """删除指定 key"""
    child = _redis_cli(password, host, port)
    if not child:
        return False

    _send_cmd(child, f'SELECT {db}')
    output = _send_cmd(child, f'DEL {key}')
    _exit(child)

    if output and re.search(r'(\d+)', output):
        return True
    return False


def web_handler(context):
    """处理 Redis 操作请求"""
    action = context.get_argument('action', '')
    password = context.get_argument('password', '')
    host = context.get_argument('host', '127.0.0.1')
    port = int(context.get_argument('port', '6379'))

    if action == 'checkpwd':
        if check_connection(password, host, port):
            context.write({'code': 0, 'msg': 'Redis 连接成功！'})
        else:
            context.write({'code': -1, 'msg': 'Redis 连接失败！（密码不正确，或 Redis 服务未启动）'})


# ==========================================================================
# 异步任务函数（供 web.py _dispatch_task 调用，第一个参数 tm 为 TaskManager）
# ==========================================================================


async def redis_info(tm, password=None, host='127.0.0.1', port=6379):
    """获取 Redis 服务器信息（异步任务）"""
    jobname = 'redis.info'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, '正在获取 Redis 服务器信息...')
    info = await shell.async_task(get_server_info, password, host, port)
    if info:
        code = 0
        msg = '获取 Redis 信息成功！'
    else:
        code = -1
        msg = '获取 Redis 信息失败！'

    tm._finish_job(jobname, code, msg, info)


async def redis_databases(tm, password=None, host='127.0.0.1', port=6379):
    """获取 Redis 数据库列表（异步任务）"""
    jobname = 'redis.databases'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, '正在获取 Redis 数据库列表...')
    databases = await shell.async_task(get_databases_info, password, host, port)
    if databases:
        code = 0
        msg = '获取数据库列表成功！'
    else:
        code = -1
        msg = '获取数据库列表失败！'

    tm._finish_job(jobname, code, msg, databases)


async def redis_dbinfo(tm, password=None, host='127.0.0.1', port=6379, db=0):
    """获取 Redis 数据库详情（异步任务）"""
    jobname = f'redis.dbinfo_{db}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在获取数据库 db{db} 的信息...')
    dbinfo = await shell.async_task(get_database_detail, password, host, port, db)
    if dbinfo:
        code = 0
        msg = f'获取数据库 db{db} 信息成功！'
    else:
        code = -1
        msg = f'获取数据库 db{db} 信息失败！'

    tm._finish_job(jobname, code, msg, dbinfo)


async def redis_flushdb(tm, password=None, host='127.0.0.1', port=6379, db=0):
    """清空 Redis 数据库（异步任务）"""
    jobname = f'redis.flushdb_{db}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在清空数据库 db{db}...')
    result = await shell.async_task(flush_database, password, host, port, db)
    if result:
        code = 0
        msg = f'数据库 db{db} 清空成功！'
    else:
        code = -1
        msg = f'数据库 db{db} 清空失败！'

    tm._finish_job(jobname, code, msg)


async def redis_flushall(tm, password=None, host='127.0.0.1', port=6379):
    """清空所有 Redis 数据库（异步任务）"""
    jobname = 'redis.flushall'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, '正在清空所有 Redis 数据库...')
    result = await shell.async_task(flush_all, password, host, port)
    if result:
        code = 0
        msg = '所有数据库清空成功！'
    else:
        code = -1
        msg = '所有数据库清空失败！'

    tm._finish_job(jobname, code, msg)


async def redis_get_key(tm, password=None, host='127.0.0.1', port=6379, db=0, key=''):
    """获取 Redis key 的值（异步任务）"""
    jobname = f'redis.get_key_{db}_{key}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在获取 key: {key}...')
    result = await shell.async_task(get_key_value, password, host, port, db, key)
    if result:
        code = 0
        msg = f'获取 key: {key} 成功！'
    else:
        code = -1
        msg = f'获取 key: {key} 失败！'

    tm._finish_job(jobname, code, msg, result)


async def redis_del_key(tm, password=None, host='127.0.0.1', port=6379, db=0, key=''):
    """删除 Redis key（异步任务）"""
    jobname = f'redis.del_key_{db}_{key}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在删除 key: {key}...')
    result = await shell.async_task(delete_key, password, host, port, db, key)
    if result:
        code = 0
        msg = f'删除 key: {key} 成功！'
    else:
        code = -1
        msg = f'删除 key: {key} 失败！'

    tm._finish_job(jobname, code, msg)
