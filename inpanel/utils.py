# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''工具函数模块'''

import base64
import random
import re
import socket
import string
import time
import uuid


def randstr(length=32):
    """生成指定长度的随机字符串
    """
    # table = range(0x30, 0x3a) + range(0x41, 0x5b) + range(0x61, 0x7b)
    # pop = [chr(i) for i in table]
    return ''.join(random.sample('abcdefghijklmnopqrstuvwxyz!@#$%^&*()', length))


def make_cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).decode('utf-8')


def is_valid_ip(ip):
    '''校验 IP 地址是否有效'''
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)


def is_valid_ipv4(ip):
    '''校验 IPv4 地址是否有效'''
    if not ip or ip == '':
        return False
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False


def is_valid_ipv6(ip):
    '''校验 IPv6 地址是否有效'''
    if not ip or ip == '':
        return False
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False


def is_valid_netmask(mask):
    """校验 IPv4 子网掩码是否有效
    """
    return mask in map(lambda x: ipv4_cidr_to_netmask(x), range(0, 33))


def ipv4_cidr_to_netmask(bits):
    """将 CIDR 位数转换为子网掩码"""
    netmask = ''
    for i in range(4):
        if i:
            netmask += '.'
        if bits >= 8:
            netmask += '%d' % (2**8-1)
            bits -= 8
        else:
            netmask += '%d' % (256-2**(8-bits))
            bits = 0
    return netmask


def b2h(n):
    # 字节数转人类可读格式
    # http://code.activestate.com/recipes/578019
    # >>> b2h(10000)
    # '9.8K'
    # >>> b2h(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n


def ftime(secs):
    return time.strftime('%Y-%m-%d %X', time.localtime(secs))


def is_valid_domain(name, allow_localname=True):
    '''校验域名是否有效'''
    if not name or name == '':
        return False
    name = name.lower()
    if allow_localname:
        pt = r'^(?:(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z0-9])\.)*(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z0-9])$'
    else:
        pt = r'^(?:(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z0-9])\.)+[a-z]{2,6}$'
    return re.match(pt, name.decode('utf-8')) and True or False


def is_url(url):
    '''检查 URL 格式是否正确'''
    return re.match('[a-z]+://.+', url) and True or False


def version_get(v1, v2):
    """检查版本 v1 是否大于等于版本 v2"""
    return [int(i) for i in v1.split('.') if i.isdigit()] > [int(i) for i in v2.split('.') if i.isdigit()]


def valid_filename(filename):
    """检查文件名是否合法
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return not any([c for c in filename if c not in valid_chars])


def callbackable(func):
    """使函数支持回调
    """
    def wrapper(*args, **kwds):
        callback = kwds['callback']
        if callback:
            del kwds['callback']
        result = func(*args, **kwds)
        if callback:
            return callback(result)
        else:
            return result
    return wrapper


def loadconfig(cfgfile, delimiter, detail=False):
    """读取配置文件并将配置项解析为字典
    """
    #if not cfgfile: cfgfile = SSHCFG

    settings = {}
    with open(cfgfile, encoding='utf-8') as f:
        for line_i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith('# '):
                continue

            # 检测该行是否被注释
            if line.startswith('#'):
                line = line.strip('#')
                commented = True
                if not detail:
                    continue
            else:
                commented = False

            fs = re.split(delimiter, line, 1)
            if len(fs) != 2:
                continue

            item = fs[0].strip()
            value = fs[1].strip()

            if item in settings:
                if detail:
                    count = settings[item]['count'] + 1
                if not commented:
                    settings[item] = detail and {
                        'file': cfgfile,
                        'line': line_i,
                        'value': value,
                        'commented': commented,
                    } or value
            else:
                count = 1
                settings[item] = detail and {
                    'file': cfgfile,
                    'line': line_i,
                    'value': fs[1].strip(),
                    'commented': commented,
                } or value
            if detail:
                settings[item]['count'] = count

    return settings


def cfg_get(cfgfile, item, delimiter, detail=False, config=None):
    """获取配置项的值
    """
    if not config:
        config = loadconfig(cfgfile, delimiter, detail=detail)
    if item in config:
        return config[item]
    else:
        return None


def cfg_set(cfgfile, item, value, delimiter, commented=False, config=None):
    """设置配置项的值
    """
    #cfgfile = SSHCFG
    v = cfg_get(cfgfile, item, delimiter, detail=True, config=config)
    if delimiter == r'\s+':
        delimiter = ' '
    if v:
        # 检测值是否有变化
        if v['commented'] == commented and v['value'] == value:
            return True

        # 空值应被注释掉
        if value == '':
            commented = True

        # 替换行中的配置项
        lines = []
        with open(v['file'], encoding='utf-8') as f:
            for line_i, line in enumerate(f):
                if line_i == v['line']:
                    if not v['commented']:
                        if commented:
                            if v['count'] > 1:
                                # 删除该行，直接忽略
                                pass
                            else:
                                # 注释该行
                                lines.append('#%s%s%s\n' %
                                             (item, delimiter, value))
                        else:
                            lines.append('%s%s%s\n' % (item, delimiter, value))
                    else:
                        if commented:
                            # 不允许更改已注释的值
                            lines.append(line)
                            pass
                        else:
                            # 在注释行后追加新行
                            lines.append(line)
                            lines.append('%s%s%s\n' % (item, delimiter, value))
                else:
                    lines.append(line)
        with open(v['file'], 'w', encoding='utf-8') as f:
            f.write(''.join(lines))
    else:
        # 追加到文件末尾
        with open(cfgfile, 'a', encoding='utf-8') as f:
            f.write('\n%s%s%s\n' % (item, delimiter, value))

    return True


def cfg_get_array(cfgfile, configs_array, delimiter):
    for key in configs_array:
        q_value = cfg_get(cfgfile, key, delimiter)
        configs_array[key] = q_value
    return configs_array


def cfg_set_array(cfgfile, configs_array, delimiter):
    for key in configs_array:
        q_value = cfg_get(cfgfile, key, delimiter)
        if q_value:
            cfg_set(cfgfile, key, q_value, delimiter)
    return True


def gen_accesskey():
    """生成访问密钥
    """
    keys = [chr(int(random.random()*256)) for i in range(0, 32)]
    return base64.b64encode(''.join(keys))
