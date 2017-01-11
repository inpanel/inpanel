#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

import random
import socket
import base64
import uuid
import time
import re
import string

def randstr(length=32):
    """Generate a fixed-length random string.
    """
    table = range(0x30, 0x3a) + range(0x41, 0x5b) + range(0x61, 0x7b)
    pop = [chr(i) for i in table]
    return ''.join(random.sample(pop, length))

def make_cookie_secret():
    return base64.b64encode(
            uuid.uuid4().bytes + uuid.uuid4().bytes)

def is_valid_ip(ip):
    """Validates IP addresses.
    """
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)

def is_valid_ipv4(ip):
    """Validates IPv4 addresses.
    """
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False

def is_valid_ipv6(ip):
    """Validates IPv6 addresses.
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False

def is_valid_netmask(mask):
    """Validates IPv4 sub-network mask.
    """
    return mask in map(lambda x: ipv4_cidr_to_netmask(x), range(0,33))
    
def ipv4_cidr_to_netmask(bits):
    """Convert CIDR bits to netmask """
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
    # bypes to human
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
    name = name.lower()
    if allow_localname:
        pt = r'^(?:(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z0-9])\.)*(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z0-9])$'
    else:
        pt = r'^(?:(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z0-9])\.)+[a-z]{2,6}$'
    return re.match(pt, name) and True or False

def version_get(v1, v2):
    """Check if version v1 is great or equal then version v2.
    """
    return [int(i) for i in v1.split('.') if i.isdigit()] > [int(i) for i in v2.split('.') if i.isdigit()]

def valid_filename(filename):
    """Check if a filename is validate.
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return not any([c for c in filename if c not in valid_chars])