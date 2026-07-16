# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''PHP 操作模块'''

import os
import subprocess
from glob import glob
from pathlib import Path
from shlex import split

from ..base import config_path
from .config import Config

# load php module config
php_config = Config(str(Path(config_path) / 'module/php.ini'))
# print('php_config', php_config.get_config())
base_config = php_config.get('base', 'config')
base_php_fpm = php_config.get('base', 'php-fpm')

if Path(base_config).exists():
    PHPCFG = base_config
else:
    PHPCFG = '/etc/php.ini'

if Path(base_php_fpm).exists():
    PHPFPMCFG = base_php_fpm
else:
    PHPFPMCFG = '/etc/php-fpm.conf'


def phpinfo():
    """Add or remove service to autostart list.
    """
    cmd = 'php-cgi -i'
    p = subprocess.Popen(split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    info = p.stdout.read().decode('utf8')
    p.stderr.read()
    p.wait()

    # Remove headers like
    # X-Powered-By: PHP/5.3.16
    # Content-type: text/html
    info = info[info.find('<!DOCTYPE'):]
    return info


def loadconfig(initype='php', inifile=None, detail=False):
    """Read the php.ini or php-fpm.ini.

    initype can be 'php' or 'php-fpm'.
    """
    if not inifile:
        inifile = initype == 'php' and PHPCFG or PHPFPMCFG

    settings = {}
    with open(inifile, encoding='utf-8') as f:
        for line_i, line in enumerate(f):
            line = line.strip()
            if not line or line == ';' or line.startswith('; ') or line.startswith(';;'):
                continue

            # detect if it is a section
            if line.startswith('['):
                continue

            # detect if it's commented
            if line.startswith(';'):
                line = line.strip(';')
                commented = True
                if not detail:
                    continue
            else:
                commented = False

            fs = line.split('=', 1)
            if len(fs) != 2:
                continue

            item = fs[0].strip()
            value = fs[1].strip()
            if item == 'include':
                for incfile in sorted(glob(value)):
                    settings.update(loadconfig(initype, incfile, detail))
            else:
                if item in settings:
                    if detail:
                        count = settings[item]['count']+1
                    if not commented:
                        settings[item] = detail and {
                            'file': inifile,
                            'line': line_i,
                            'value': value,
                            'commented': commented,
                        } or value
                else:
                    count = 1
                    settings[item] = detail and {
                        'file': inifile,
                        'line': line_i,
                        'value': fs[1].strip(),
                        'commented': commented,
                    } or value
                if detail:
                    settings[item]['count'] = count

    return settings


def ini_get(item, detail=False, config=None, initype='php'):
    """Get value of an ini item.
    """
    if not config:
        config = loadconfig(initype=initype, detail=detail)
    if item in config:
        return config[item]
    else:
        return None


def ini_set(item, value, commented=False, config=None, initype='php'):
    """Set value of an ini item.
    """
    inifile = initype == 'php' and PHPCFG or PHPFPMCFG
    v = ini_get(item, detail=True, config=config, initype=initype)

    if v:
        # detect if value change
        if v['commented'] == commented and v['value'] == value:
            return True

        # empty value should be commented
        if value == '':
            commented = True

        # replace item in line
        lines = []
        with open(v['file'], encoding='utf-8') as f:
            for line_i, line in enumerate(f):
                if line_i == v['line']:
                    if not v['commented']:
                        if commented:
                            if v['count'] > 1:
                                # delete this line, just ignore it
                                pass
                            else:
                                # comment this line
                                lines.append(';%s = %s\n' % (item, value))
                        else:
                            lines.append('%s = %s\n' % (item, value))
                    else:
                        if commented:
                            # do not allow change comment value
                            lines.append(line)
                            pass
                        else:
                            # append a new line after comment line
                            lines.append(line)
                            lines.append('%s = %s\n' % (item, value))
                else:
                    lines.append(line)
        with open(v['file'], 'w', encoding='utf-8') as f:
            f.write(''.join(lines))
    else:
        # append to the end of file
        with open(inifile, 'a', encoding='utf-8') as f:
            f.write('\n%s%s = %s\n' % (commented and ';' or '', item, value))

    return True


def web_handler(context):
    action = context.get_argument('action', '')

    if action == 'getphpsettings':
        settings = loadconfig('php')
        context.write({'code': 0, 'msg': '', 'data': settings})

    elif action == 'getfpmsettings':
        settings = loadconfig('php-fpm')
        context.write({'code': 0, 'msg': '', 'data': settings})

    elif action == 'updatephpsettings':
        short_open_tag = context.get_argument('short_open_tag', '')
        expose_php = context.get_argument('expose_php', '')
        max_execution_time = context.get_argument('max_execution_time', '')
        memory_limit = context.get_argument('memory_limit', '')
        display_errors = context.get_argument('display_errors', '')
        post_max_size = context.get_argument('post_max_size', '')
        upload_max_filesize = context.get_argument('upload_max_filesize', '')
        date_timezone = context.get_argument('date.timezone', '')

        short_open_tag = short_open_tag.lower() == 'on' and 'On' or 'Off'
        expose_php = expose_php.lower() == 'on' and 'On' or 'Off'
        display_errors = display_errors.lower() == 'on' and 'On' or 'Off'

        if not max_execution_time == '' and not max_execution_time.isdigit():
            context.write({'code': -1, 'msg': 'max_execution_time 必须为数字！'})
            return
        if not memory_limit == '' and not memory_limit.isdigit():
            context.write({'code': -1, 'msg': 'memory_limit 必须为数字！'})
            return
        if not post_max_size == '' and not post_max_size.isdigit():
            context.write({'code': -1, 'msg': 'post_max_size 必须为数字！'})
            return
        if not upload_max_filesize == '' and not upload_max_filesize.isdigit():
            context.write({'code': -1, 'msg': 'upload_max_filesize 必须为数字！'})
            return

        memory_limit = '%sM' % memory_limit
        post_max_size = '%sM' % post_max_size
        upload_max_filesize = '%sM' % upload_max_filesize

        ini_set('short_open_tag', short_open_tag, initype='php')
        ini_set('expose_php', expose_php, initype='php')
        ini_set('max_execution_time', max_execution_time, initype='php')
        ini_set('memory_limit', memory_limit, initype='php')
        ini_set('display_errors', display_errors, initype='php')
        ini_set('post_max_size', post_max_size, initype='php')
        ini_set('upload_max_filesize', upload_max_filesize, initype='php')
        ini_set('date.timezone', date_timezone, initype='php')

        context.write({'code': 0, 'msg': 'PHP设置保存成功！'})

    elif action == 'updatefpmsettings':
        listen = context.get_argument('listen', '')
        pm = context.get_argument('pm', '')
        pm_max_children = context.get_argument('pm.max_children', '')
        pm_start_servers = context.get_argument('pm.start_servers', '')
        pm_min_spare_servers = context.get_argument('pm.min_spare_servers', '')
        pm_max_spare_servers = context.get_argument('pm.max_spare_servers', '')
        pm_max_requests = context.get_argument('pm.max_requests', '')
        request_terminate_timeout = context.get_argument('request_terminate_timeout', '')
        request_slowlog_timeout = context.get_argument('request_slowlog_timeout', '')

        pm = pm.lower() == 'on' and 'dynamic' or 'static'
        if not pm_max_children == '' and not pm_max_children.isdigit():
            context.write({'code': -1, 'msg': 'pm.max_children 必须为数字！'})
            return
        if not pm_start_servers == '' and not pm_start_servers.isdigit():
            context.write({'code': -1, 'msg': 'pm.start_servers 必须为数字！'})
            return
        if not pm_min_spare_servers == '' and not pm_min_spare_servers.isdigit():
            context.write({'code': -1, 'msg': 'pm.min_spare_servers 必须为数字！'})
            return
        if not pm_max_spare_servers == '' and not pm_max_spare_servers.isdigit():
            context.write({'code': -1, 'msg': 'pm.max_spare_servers 必须为数字！'})
            return
        if not pm_max_requests == '' and not pm_max_requests.isdigit():
            context.write({'code': -1, 'msg': 'pm.max_requests 必须为数字！'})
            return
        if not request_terminate_timeout == '' and not request_terminate_timeout.isdigit():
            context.write({'code': -1, 'msg': 'request_terminate_timeout 必须为数字！'})
            return
        if not request_slowlog_timeout == '' and not request_slowlog_timeout.isdigit():
            context.write({'code': -1, 'msg': 'request_slowlog_timeout 必须为数字！'})
            return

        ini_set('listen', listen, initype='php-fpm')
        ini_set('pm', pm, initype='php-fpm')
        ini_set('pm.max_children', pm_max_children, initype='php-fpm')
        ini_set('pm.start_servers', pm_start_servers, initype='php-fpm')
        ini_set('pm.min_spare_servers', pm_min_spare_servers, initype='php-fpm')
        ini_set('pm.max_spare_servers', pm_max_spare_servers, initype='php-fpm')
        ini_set('pm.max_requests', pm_max_requests, initype='php-fpm')
        ini_set('request_terminate_timeout', request_terminate_timeout, initype='php-fpm')
        ini_set('request_slowlog_timeout', request_slowlog_timeout, initype='php-fpm')

        context.write({'code': 0, 'msg': 'PHP FastCGI 设置保存成功！'})


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    # pp.pprint(loadconfig())
    #print ini_get('short_open_tag', detail=True)
    #print ini_set('short_open_tag', 'On', commented=False)
    #print ini_get('date.timezone', detail=True)
    #print ini_set('date.timezone', '', commented=False)

    # pp.pprint(loadconfig('php-fpm'))
    #print ini_get('pm', detail=False, initype='php-fpm')
    #print ini_set('pm', 'static', initype='php-fpm')
