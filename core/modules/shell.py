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


def exec_command(cmd, cwd):
    '''executive command
    '''
    cmd = shlex.split(cmd)
    cwd = cwd or '/'
    # print('shell cmd', cmd)
    try:
        p = sbps.Popen(cmd,
                       stdout=sbps.PIPE,
                       stderr=sbps.PIPE,
                       close_fds=True,
                       shell=True,
                       cwd=cwd)
        if p.wait() == 0:
            result = p.stdout.read()  # result = p.stdout.readlines()
            # print(p.cc.read())
        else:
            result = p.stderr.read()  # result = p.stderr.readlines()
        return {
            'code': p.wait(),
            'cwd': cwd,
            'data': result,
            'msg': 'success'
        }
    except:
        return {
            'code': -1,
            'data': '',
            'msg': 'error'
        }


if __name__ == '__main__':
    print(exec_command('cd /var/db', '/var'))
    # print(exec_command('who -a'))
    # print(exec_command('ls')['code'] == 0)
    # print(shlex.split('uname -a - b'))
