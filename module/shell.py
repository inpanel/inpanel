# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Shell."""


import shlex
import subprocess


def run(cmd, shell=False):
    if shell:
        return subprocess.call(cmd, shell=shell)
    else:
        return subprocess.call(shlex.split(cmd))

