#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Module for disk Management'''

import os
from pathlib import Path
from shlex import split

import pexpect

from .config import readconfig, writeconfig
from . import server


def add(disk, size=''):
    """Add a new partition on a disk.

    If the size exceed the max available space the disk left, then the
    new partition will be created with the left space.

    A disk can have 4 partitions at max.

    True will return if create successfully, or else False will return.

    Example:
    fdisk.add('/dev/sdb')   # use all of the space
    fdisk.add('/dev/sdb', '5G') # create a partition with at most 5G space
    """
    try:
        cmd = split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    rt = True
    partno_found = False
    partno = 1
    while not partno_found:
        child.sendline('n')
        i = child.expect(
            ['primary partition', 'You must delete some partition'])
        if i == 1:
            break
        child.sendline('p')

        i = child.expect(['Partition number', 'Selected partition'])
        if i == 0:
            child.sendline('%d' % partno)

        i = child.expect(['First cylinder', '(m for help)'])
        if i == 0:
            partno_found = True
        partno += 1
        if partno > 4:
            break

    if not partno_found:
        rt = False

    if rt:
        child.sendline('')
        child.expect('Last cylinder')
        child.sendline('+%s' % size)
        i = child.expect(
            ['(m for help)', 'Value out of range', 'Last cylinder'])
        if i == 1:
            child.sendline('')
            child.expect('(m for help)')
        elif i == 2:    # wrong size input
            child.sendline('')
            child.expect('(m for help)')
            rt = False

    if rt:
        child.sendline('w')
    else:
        child.sendline('q')

    if child.isalive():
        child.wait()
    return rt


def delete(partition):
    """Delete a partition.

    True will return if delete successfully, or else False will return.

    Example:
    fdisk.delete('/dev/sdb1')
    """
    disk = partition[:-1]
    partno = partition[-1:]
    try:
        cmd = split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    child.sendline('d')

    rt = True
    i = child.expect([
        'Partition number',
        'Selected partition %s' % partno,
        'No partition is defined yet',
        pexpect.TIMEOUT
    ], timeout=1)
    if i == 0:
        child.sendline(partno)
    elif i == 2 or i == 3:
        rt = False

    if rt:
        i = child.expect(['(m for help)', 'has empty type'])
        if i == 0:
            child.sendline('w')
        elif i == 1:
            rt = False

    if not rt:
        child.sendline('q')

    if child.isalive():
        child.wait()
    return rt


def scan(disk, size=''):
    """Rescan partitions on a disk.

    True will return if scan successfully, or else False will return.

    Example:
    fdisk.scan('/dev/sdb')
    """
    try:
        cmd = split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        child.wait()
        return False

    child.sendline('w')
    i = child.expect([
        'The kernel still uses the old table',
        pexpect.TIMEOUT,
        pexpect.EOF
    ], timeout=1)
    if i == 0:
        rt = False
    else:
        rt = True

    if child.isalive():
        child.wait()
    return rt


def handle_fdisk(action, devname, size='', unit=''):
    """Handle fdisk operations.

    Args:
        action: 'add', 'delete', or 'scan'
        devname: device name (e.g., 'sdb')
        size: partition size (e.g., '5')
        unit: 'M' or 'G'

    Returns:
        dict with 'code' and 'msg' keys
    """
    if action == 'add':
        if unit not in ('M', 'G'):
            return {'code': -1, 'msg': '错误的分区大小！'}

        if size == '':
            size = None  # use whole left space
        else:
            try:
                size = float(size)
            except:
                return {'code': -1, 'msg': '错误的分区大小！'}

            if unit == 'G' and size - int(size) > 0:
                size *= 1024
                unit = 'M'
            size = '%d%s' % (round(size), unit)

        if add('/dev/%s' % devname, size):
            return {'code': 0, 'msg': '在 %s 设备上创建分区成功！' % devname}
        else:
            return {'code': -1, 'msg': '在 %s 设备上创建分区失败！' % devname}

    elif action == 'delete':
        if delete('/dev/%s' % devname):
            fstab(devname, {'devname': devname, 'mount': None})
            return {'code': 0, 'msg': '分区 %s 删除成功！' % devname}
        else:
            return {'code': -1, 'msg': '分区 %s 删除失败！' % devname}

    elif action == 'scan':
        if scan('/dev/%s' % devname):
            return {'code': 0, 'msg': '扫描设备 %s 的分区成功！' % devname}
        else:
            return {'code': -1, 'msg': '扫描设备 %s 的分区失败！' % devname}

    else:
        return {'code': -1, 'msg': '未定义的操作！'}


def _read_fstab(line, **params):
    """Read fstab config for a specific device.
    
    Args:
        line: a line from /etc/fstab
        params: contains 'devname' parameter
    
    Returns:
        dict with config or None
    """
    if not line or line.startswith('#'):
        return
    fields = line.split()
    dev = fields[0]
    config = {
        'dev':    fields[0],
        'mount':  fields[1],
        'fstype': fields[2],
    }
    if dev.startswith('/dev/'):
        try:
            devlink = os.readlink(dev)
            dev = str(Path(devlink).parent.joinpath(dev).resolve())
        except:
            pass
        dev = dev.replace('/dev/', '')
        if dev == params['devname']:
            return config
    elif dev.startswith('UUID='):
        uuid = dev.replace('UUID=', '')
        partinfo = server.ServerInfo.partinfo(devname=params['devname'])
        if partinfo['uuid'] == uuid:
            return config


def _write_fstab(line, **params):
    """Write fstab config for a specific device.
    
    Args:
        line: a line from /etc/fstab (None for new line)
        params: contains 'devname' and 'config' parameters
    
    Returns:
        formatted line string or None to remove
    """
    config = params['config']
    if not 'mount' in config or config['mount'] is None:
        return None  # remove line
    if line is None:  # new line
        return '/dev/%s %s                %s    defaults        1 2' % \
            (params['devname'], config['mount'], config['fstype'])
    else:  # update existing line
        fields = line.split()
        return '%s %s                %s    %s        %s %s' % \
            (fields[0], config['mount'],
             'fstype' in config and config['fstype'] or fields[2],
             fields[3], fields[4], fields[5])


def fstab(devname, config=None):
    """Read or write config from /etc/fstab.

    Args:
        devname: device name (e.g., 'sda1')
        config: None for read, dict for write/remove
    
    Returns:
        config dict on read, boolean on write
    """
    cfgfile = '/etc/fstab'
    if config is None:
        # read config
        return readconfig(cfgfile, _read_fstab, devname=devname)
    else:
        # write or remove config
        return writeconfig(cfgfile, _read_fstab, _write_fstab,
                           devname=devname, config=config)


# ------------------------------------------------------------------
# 异步任务函数（由 web.py 的 _dispatch_task 调用）
# 命名规则：disk_<method>，对应 jobname 中的 disk_<method>_...
# ------------------------------------------------------------------

from shlex import quote as sh_quote
from . import shell


async def disk_swap(tm, action, devname):
    """启用/停用 swap（异步任务）"""
    jobname = f'disk.swap_{action}_{devname}'
    if not tm._start_job(jobname):
        return

    action_str = {'on': '启用', 'off': '停用'}
    tm._update_job(jobname, 2, f'正在{action_str.get(action, action)} {devname}...')

    if action == 'on':
        cmd = f'swapon /dev/{devname}'
    else:
        cmd = f'swapoff /dev/{devname}'

    result, output = await shell.async_command(cmd)
    if result == 0:
        tm._finish_job(jobname, 0, f'{action_str.get(action, action)} {devname} 成功！')
    else:
        tm._finish_job(jobname, -1,
                       f'{action_str.get(action, action)} {devname} 失败！',
                       data=output.strip().replace('\n', '<br>'))


async def disk_mount(tm, action, devname, mountpoint, fstype):
    """挂载/卸载磁盘（异步任务）"""
    jobname = f'disk.mount_{action}_{devname}'
    if not tm._start_job(jobname):
        return

    action_str = {'mount': '挂载', 'umount': '卸载'}
    tm._update_job(jobname, 2, f'正在{action_str.get(action, action)} {devname} 到 {mountpoint}...')

    if action == 'mount':
        fstab(devname, {
            'devname': devname,
            'mount': mountpoint,
            'fstype': fstype,
        })
        cmd = f'mount -t {fstype} /dev/{devname} {mountpoint}'
    else:
        cmd = f'umount /dev/{devname}'

    result, output = await shell.async_command(cmd)
    if result == 0:
        tm._finish_job(jobname, 0, f'{action_str.get(action, action)} {devname} 成功！')
    else:
        tm._finish_job(jobname, -1,
                       f'{action_str.get(action, action)} {devname} 失败！',
                       data=output.strip().replace('\n', '<br>'))


async def disk_format(tm, devname, fstype):
    """格式化磁盘（异步任务）"""
    jobname = f'disk.format_{devname}'
    if not tm._start_job(jobname):
        return

    tm._update_job(jobname, 2, f'正在格式化 {devname}，可能需要较长时间，请耐心等候...')

    if fstype in ('ext2', 'ext3', 'ext4'):
        cmd = f'mkfs.{fstype} -F /dev/{devname}'
    elif fstype in ('xfs', 'reiserfs', 'btrfs'):
        cmd = f'mkfs.{fstype} -f /dev/{devname}'
    elif fstype == 'swap':
        cmd = f'mkswap -f /dev/{devname}'
    else:
        cmd = f'mkfs.{fstype} /dev/{devname}'

    result, output = await shell.async_command(cmd)
    if result == 0:
        tm._finish_job(jobname, 0, f'{devname} 格式化成功！')
    else:
        tm._finish_job(jobname, -1, f'{devname} 格式化失败！',
                       data=output.strip().replace('\n', '<br>'))


if __name__ == '__main__':
    # !!!!!!!!!!! DANGEROUS TESTING !!!!!!!!!!!
    # print('* Add partition to sdb with 5G:',)
    # print(add('/dev/sdb', '5G'))

    # print('* Delete partition /dev/sdb1:')
    # print(delete('/dev/sdb1'))

    print('* Rescan partitions of /dev/sdb:')
    print(scan('/dev/sdb'))