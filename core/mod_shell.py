# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for Shell.'''

import shlex
import subprocess as sbps
from asyncio import coroutine, create_subprocess_shell, create_task
from asyncio import subprocess as async_subprocess


async def async_command(command):
    '''async command'''
    proc = await create_subprocess_shell(command,
                                         stdout=async_subprocess.PIPE,
                                         stderr=async_subprocess.PIPE,
                                         shell=True)
    output, _ = await proc.communicate()
    return (proc.returncode, output.decode('utf-8'))


async def async_task(func, *args, **kwds):
    '''Make an asynchronous function.'''
    @coroutine
    def wrapper():
        '''
        user @asyncio.coroutine
        or async
        '''
        # print('执行')
        # await asyncio.sleep(10)
        # print('执行2')
        callback = None
        if hasattr(kwds, 'callback'):
            callback = kwds['callback']
        if callback:
            del kwds['callback']
        result = func(*args, **kwds)
        print('result-origin', result)
        if callback:
            return callback(result)
        else:
            return result
    result = await create_task(wrapper())
    # print('执行-结束')
    # print('result-1', result)
    return result


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
        return {'code': p.wait(), 'cwd': cwd, 'data': result, 'msg': 'success'}
    except:
        return {'code': -1, 'data': '', 'msg': 'error'}


if __name__ == '__main__':
    print(exec_command('cd /var/db', '/var'))
    # print(exec_command('who -a'))
    # print(exec_command('ls')['code'] == 0)
    # print(shlex.split('uname -a - b'))
