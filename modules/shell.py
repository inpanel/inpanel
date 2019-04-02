# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Shell.'''


import shlex
import subprocess as sbps


def run(cmd, shell=False):
    if shell:
        return sbps.call(cmd, shell=shell)
    else:
        return sbps.call(shlex.split(cmd))


def shell_cmd(cmd):
    cmd = shlex.split(cmd)
    print('shell cmd', cmd)
    try:
        p = sbps.Popen(cmd,
                       stdout=sbps.PIPE,
                       stderr=sbps.PIPE,
                       close_fds=True)
        return {
            'code': p.wait(),
            'msg': p.stdout.read() if p.wait() == 0 else p.stderr.read()
        }
    except:
        return {
            'code': -1,
            'msg': 'error'
        }


# if __name__ == '__main__':
    # print(shell_cmd('uname -a'))
    # print(shell_cmd('who -a'))
    # print(shell_cmd('ls')['code'] == 0)
    # print(shlex.split('uname -a - b'))
