# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# Copyright (c) 2012 - 2016, VPSMate development team
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

import os
from ConfigParser import ConfigParser

from lib.filelock import FileLock


class Config(object):

    def __init__(self, inifile='data/config.ini'):
        self.inifile = inifile
        self.cfg = ConfigParser()

        with FileLock(self.inifile):
            if os.path.exists(inifile):
                self.cfg.read(inifile)

            # initialize configurations
            default_configs = {
                'server': {
                    'ip': '*',
                    'port': '8888',
                    'lastcheckupdate': 0,
                    'updateinfo': ''
                },
                'auth': {
                    'username': 'admin',
                    'password': '',     # empty password never validated
                    'passwordcheck': 'on',
                    'accesskey': '',    # empty access key never validated
                    'accesskeyenable': 'off',
                },
                'runtime': {
                    'mode': '',
                    'loginlock': 'off',
                    'loginfails': 0,
                    'loginlockexpire': 0,
                },
                'file': {
                    'lastdir': '/root',
                    'lastfile': '',
                },
                'time': {
                    # format: timezone = Asia/Shanghai
                },
                'ecs': {
                    'accounts': '',
                },
                'intranet': {
                    # format: Instance Name = Access key
                }
            }
            needupdate = False
            for sec, secdata in default_configs.iteritems():
                if not self.cfg.has_section(sec):
                    self.cfg.add_section(sec)
                    needupdate = True
                for opt, val in secdata.iteritems():
                    if not self.cfg.has_option(sec, opt):
                        self.cfg.set(sec, opt, val)
                        needupdate = True

            # update ini file
            if needupdate:
                self.update(False)

    def update(self, lock=True):
        if lock:
            flock = FileLock(self.inifile)
            flock.acquire()

        try:
            inifp = open(self.inifile, 'w')
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

    def get(self, section, option):
        return self.cfg.get(section, option)

    def getboolean(self, section, option):
        return self.cfg.getboolean(section, option)

    def getint(self, section, option):
        return self.cfg.getint(section, option)

    def has_section(self, section):
        return self.cfg.has_section(section)

    def add_section(self, section):
        return self.cfg.add_section(section)

    def remove_option(self, section):
        return self.cfg.remove_option(section)

    def set(self, section, option, value):
        try:
            self.cfg.set(section, option, value)
        except:
            return False
        return self.update()
