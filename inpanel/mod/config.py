# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Configurations Management.'''

from configparser import RawConfigParser
from pathlib import Path

from ..base import config_file, runlogs_path, update_info_path, config_path, run_type
from ..lib.filelock import FileLock


def load_config(inifile=None, configs=None):
    '''the configurations for InPanel'''
    if run_type == 'source':
        ssl_cert_path = str(Path(config_path) / 'certificate')
    else:
        ssl_cert_path = '/etc/inpanel/certificate'

    default_configs = {
        'server': {
            'ip': '*',
            'port': '14433',
            'forcehttps': 'off',  # force use https
            'sslkey': str(Path(ssl_cert_path) / 'inpanel.key'),
            'sslcrt': str(Path(ssl_cert_path) / 'inpanel.crt')
        },
        'auth': {
            'username': 'admin',
            'password': 'a17351f4e092ba7d87a7a90c170a5cf6:1bdf574a782e8f006676ee1225743a6b',  # admin
            'passwordcheck': 'on',
            'accesskey': '',  # empty access key never validated
            'accesskeyenable': 'off',
        },
        'runtime': {
            'mode': 'prod',  # format: demo | prod
            'loginlock': 'off',
            'loginfails': '0',
            'loginlockexpire': '0',
        },
        'time': {
            'timezone': ''  # format: timezone = Asia/Shanghai
        },
        'ecs': {
            'accounts': ''
        },
        'inpanel': {
            'Instance Name': 'Access key'
        }
    } if configs is None else configs

    return Config(config_file if inifile is None else inifile, default_configs)

def runlogs_config():
    # to recode running data logs
    return load_config(runlogs_path, {
        'file': {
            'lastdir': str(Path.home()), # user Home path
            'lastfile': '',
        }
    })


def update_info_config():
    # to record version update information separately from config
    return load_config(update_info_path, {
        'update': {
            'lastcheck': '0',
            'updateinfo': '',
        }
    })

class Config(object):
    def __init__(self, inifile=None, configs=None):
        if inifile is None:
            return None

        inifile_path = Path(inifile)
        if not inifile_path.parent.exists():
            inifile_path.parent.mkdir(parents=True, exist_ok=True)

        self.inifile = inifile
        self.cfg = RawConfigParser()

        with FileLock(self.inifile):
            if inifile_path.exists():
                self.cfg.read(self.inifile)

            # initialize configurations
            default_configs = {} if configs is None else configs
            needupdate = False
            for sec, secdata in default_configs.items():
                if not self.cfg.has_section(sec):
                    self.cfg.add_section(sec)
                    needupdate = True
                for opt, val in secdata.items():
                    if not self.cfg.has_option(sec, opt):
                        self.cfg.set(sec, opt, str(val))
                        needupdate = True

            # update ini file
            if needupdate:
                self.update(False)

    def update(self, lock=True):
        if lock:
            flock = FileLock(self.inifile)
            flock.acquire()

        try:
            inifp = open(self.inifile, 'w', encoding='utf-8')
            self.cfg.write(inifp)
            inifp.close()
            if lock:
                flock.release()
            return True
        except:
            if lock:
                flock.release()
            return False

    def has_option(self, section, option):
        return self.cfg.has_option(section, option)

    def remove_option(self, section, option):
        return self.cfg.remove_option(section, option)

    def get(self, section, option):
        if self.cfg.has_option(section, option):
            return self.cfg.get(section, option)
        else:
            return None

    def getboolean(self, section, option):
        return self.cfg.getboolean(section, option)

    def getint(self, section, option):
        return self.cfg.getint(section, option)

    def has_section(self, section):
        return self.cfg.has_section(section)

    def add_section(self, section):
        return self.cfg.add_section(section)

    def remove_section(self, section=None):
        if section is None:
            return False
        else:
            return self.cfg.remove_section(section)

    def set(self, section, option, value):
        try:
            self.cfg.set(section, option, value)
        except:
            return False
        return self.update()

    def get_section_list(self):
        '''Return a list of section names, excluding [DEFAULT]'''
        return self.cfg.sections()

    def get_option_list(self, section):
        '''Return a list of option names for the given section name.'''
        return self.cfg.options(section)

    def get_config_list(self):
        '''Return a list of all config for the given config file.'''
        config_list = []
        sections = self.cfg.sections()
        for section in sections:
            sec = {'section': section, 'option': {}}
            options = self.cfg.options(section)
            for key in options:
                sec['option'][key] = self.cfg.get(section, key)
            config_list.append(sec)
        return config_list

    def get_config(self):
        '''Return a dict of all config for the given config file.'''
        config = {}
        for section in self.cfg.sections():
            config[section] = {}
            for item in self.cfg.options(section):
                config[section][item] = self.cfg.get(section, item)
        return config

    def addsection(self, section, data):
        '''add one section'''
        try:
            if not self.cfg.has_section(section):
                self.cfg.add_section(section)
            for option, value in data.items():
                self.cfg.set(section, option, value)
            return self.update(False)
        except:
            return False

    def addsections(self, section):
        '''add some sections'''
        try:
            for sec, data in section.items():
                if not self.cfg.has_section(sec):
                    self.cfg.add_section(sec)
                for option, value in data.items():
                    self.cfg.set(sec, option, value)
            return self.update(False)
        except:
            return False

def raw_loadconfig(filepath, return_sort=False, delimiter='=', quoter=' "\'', overwrite=True):
    """Read config from file.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return None
    config = {}
    if return_sort:
        sortlist = []
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            pair = line.strip().split(delimiter)
            if len(pair) != 2:
                continue
            k, v = [x.strip(quoter) for x in pair]
            if return_sort:
                sortlist.append(k)
            if overwrite:
                config[k] = v
            else:
                if not k in config:
                    config[k] = []
                config[k].append(v)
    if return_sort:
        return (config, sortlist)
    else:
        return config


def raw_saveconfig(filepath, config, sortlist=[], delimiter='=', quoter='"'):
    """Write config to file.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return False
    lines = []

    # write the item in sortlist first
    if len(sortlist) > 0:
        for k in sortlist:
            if k in config:
                line = '%s%s%s%s%s\n' % (k, delimiter, quoter, config[k], quoter)
                del config[k]
                lines.append(line)

    # then write the rest items
    for k, v in config.items():
        if isinstance(v, list):
            for vv in v:
                line = '%s%s%s%s%s\n' % (k, delimiter, quoter, vv, quoter)
                lines.append(line)
        else:
            line = '%s%s%s%s%s\n' % (k, delimiter, quoter, v, quoter)
            lines.append(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return True


def loadconfig(filepath, keymap=None, delimiter='=', quoter=' "\''):
    """Load config from file and parse it to dict.
    """
    raw_config = raw_loadconfig(filepath)
    if raw_config is None:
        return None
    if keymap is None:
        config = dict((k, v) for k, v in raw_config.items())
    else:
        config = dict((keymap[k], v) for k, v in raw_config.items() if k in keymap)
    return config


def saveconfig(filepath, config, keymap=None, delimiter='=', read_quoter=' "\'', write_quoter='"'):
    """Save config to file."""
    raw_config, sortlist = raw_loadconfig(filepath, return_sort=True, delimiter=delimiter, quoter=read_quoter)
    if raw_config is None:
        return False
    for k, v in config.items():
        if keymap is None:
            raw_config[k] = v
        else:
            if k in keymap:
                raw_config[keymap[k]] = v
            else:
                return False
    return raw_saveconfig(filepath, raw_config, sortlist, delimiter=delimiter, quoter=write_quoter)


def readconfig(filepath, readfunc, **params):
    """Read config from file.
    """
    filepath = Path(filepath)
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            rt = readfunc(line.strip(), **params)
            if rt is not None:
                return rt


def writeconfig(filepath, readfunc, writefunc, **params):
    """Write config to file.
    """
    filepath = Path(filepath)
    lines = []
    linemeet = False
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            rt = readfunc(line.strip(), **params)
            if rt is not None:
                linemeet = True
                line = writefunc(line, **params)
                if line is not None:
                    lines.append(line+'\n')
            else:
                lines.append(line)

    # generate a new line if no line meet
    if not linemeet:
        line = writefunc(None, **params)
        if line is not None:
            lines.append(line+'\n')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return True


__all__ = ['load_config', 'runlogs_config', 'update_info_config', 'Config', 'raw_loadconfig', 'raw_saveconfig', 'loadconfig', 'saveconfig', 'readconfig', 'writeconfig']

if __name__ == '__main__':
    import json
    default_config = {
        '1.1.1.1': {
            'server': '1.1.1.1',
            'port': 8023,
            'accesskey': 'O64Td9EWEj8THu+RlHuoO8tjJzUmdsx37pTluP+aVc0='
        },
        '1.1.1.2': {
            'server': '1.1.1.1',
            'port': 8023,
            'accesskey': 'O64Td9EWEj8THu+RlHuoO8tjJzUmdsx37pTluP+aVc0='
        }
    }
    config = Config('data/clients.ini', {})
    print(config)
    print(config.get_section_list())
    config.update()
    config.addsection('accccc', {'abc': 2345, 'ccc': 34567654345})
    config.addsections(default_config)
    print(config.get_section_list())
    # print(config.update())
    print('abc')
    config_list = config.get_config_list()
    print(json.dumps(config_list))
    config_dict = config.get_config()
    print(json.dumps(config_dict))
