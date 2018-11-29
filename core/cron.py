# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Package for cron management."""

import shlex
import subprocess


def listCron():
    p = subprocess.Popen(['crontab'],
                        #  stdout=subprocess.PIPE,
                        #  stderr=subprocess.PIPE,
                         close_fds=True)
    # p.stdout.read()
    # p.stderr.read()
    return p.wait() == 0


if __name__ == "__main__":
    print listCron()
