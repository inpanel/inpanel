# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for PHP operations.'''

import os
import subprocess
from glob import glob
from shlex import split

from base import config_path
from mod_config import Config

# load php module config
php_config = Config(os.path.join(config_path, 'module/php.ini'))
# print('php_config', php_config.get_config())
base_config = php_config.get('base', 'config')
base_php_fpm = php_config.get('base', 'php-fpm')

if os.path.exists(base_config):
    PHPCFG = base_config
else:
    PHPCFG = '/etc/php.ini'

if os.path.exists(base_php_fpm):
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
