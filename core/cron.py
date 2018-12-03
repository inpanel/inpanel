# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Package for cron management."""

import os
import shlex
import subprocess

CRON_DIR = '/etc/cron.d/'
CRONTAB = '/etc/crontab'


def load_config():
    config = {}
    try:
        if not os.path.isfile(CRONTAB):
            return config
    except OSError:
        return config

    with open(CRONTAB, 'r') as f:
        lines = f.readlines()

    while len(lines) > 0:
        line = lines.pop(0)
        out = line.strip()
        if not out or out.startswith('#'):
            continue

        fields = out.split('=')[0]
        if fields:
            values = out.split('=')[1]
            config[fields.lower()] = values

    return config


def update_config(configs):
    if configs.has_key('mailto'):
        return configs


def listCron():
    p = subprocess.Popen(['crontab', '-l'],
                         #  stdout=subprocess.PIPE,
                         #  stderr=subprocess.PIPE,
                         close_fds=True)
    # p.stdout.read()
    # p.stderr.read()
    return p.wait() == 0


# if __name__ == "__main__":
    # print listCron()
    # os.system("top")
    # print load_config()
