# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012 - 2016, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for Utils.'''

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
    return mask in map(lambda x: ipv4_cidr_to_netmask(x), range(0, 33))


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

def is_url(url):
    '''Check that the URL is in the correct format'''
    return re.match('[a-z]+://.+', url) and True or False

def version_get(v1, v2):
    """Check if version v1 is great or equal then version v2.
    """
    return [int(i) for i in v1.split('.') if i.isdigit()] > [int(i) for i in v2.split('.') if i.isdigit()]


def valid_filename(filename):
    """Check if a filename is validate.
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return not any([c for c in filename if c not in valid_chars])


def callbackable(func):
    """Make a function callbackable.
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
    """Read config file and parse config item to dict.
    """
    #if not cfgfile: cfgfile = SSHCFG

    settings = {}
    with open(cfgfile) as f:
        for line_i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith('# '):
                continue

            # detect if it's commented
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
                    count = settings[item]['count']+1
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
    """Get value of a config item.
    """
    if not config:
        config = loadconfig(cfgfile, delimiter, detail=detail)
    if item in config:
        return config[item]
    else:
        return None


def cfg_set(cfgfile, item, value, delimiter, commented=False, config=None):
    """Set value of a config item.
    """
    #cfgfile = SSHCFG
    v = cfg_get(cfgfile, item, delimiter, detail=True, config=config)
    if delimiter == '\s+':
        delimiter = ' '
    if v:
        # detect if value change
        if v['commented'] == commented and v['value'] == value:
            return True

        # empty value should be commented
        if value == '':
            commented = True

        # replace item in line
        lines = []
        with open(v['file']) as f:
            for line_i, line in enumerate(f):
                if line_i == v['line']:
                    if not v['commented']:
                        if commented:
                            if v['count'] > 1:
                                # delete this line, just ignore it
                                pass
                            else:
                                # comment this line
                                lines.append('#%s%s%s\n' %
                                             (item, delimiter, value))
                        else:
                            lines.append('%s%s%s\n' % (item, delimiter, value))
                    else:
                        if commented:
                            # do not allow change comment value
                            lines.append(line)
                            pass
                        else:
                            # append a new line after comment line
                            lines.append(line)
                            lines.append('%s%s%s\n' % (item, delimiter, value))
                else:
                    lines.append(line)
        with open(v['file'], 'w') as f:
            f.write(''.join(lines))
    else:
        # append to the end of file
        with open(cfgfile, 'a') as f:
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
    """Generate a access key.
    """
    keys = [chr(int(random.random()*256)) for i in range(0, 32)]
    return base64.b64encode(''.join(keys))
