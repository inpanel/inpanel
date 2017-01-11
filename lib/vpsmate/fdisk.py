#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

"""Package for fdisk operations.
"""

import os
if __name__ == '__main__':
    import sys
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import pexpect
import shlex


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
        cmd = shlex.split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        if child.isalive(): child.wait()
        return False
    
    rt = True
    partno_found = False
    partno = 1
    while not partno_found:
        child.sendline('n')
        i = child.expect(['primary partition', 'You must delete some partition'])
        if i == 1: break
        child.sendline('p')

        i = child.expect(['Partition number', 'Selected partition'])
        if i == 0: child.sendline('%d' % partno)

        i = child.expect(['First cylinder', '(m for help)'])
        if i == 0: partno_found = True
        partno += 1
        if partno > 4: break
    
    if not partno_found: rt = False

    if rt:
        child.sendline('')
        child.expect('Last cylinder')
        child.sendline('+%s' % size)
        i = child.expect(['(m for help)', 'Value out of range', 'Last cylinder'])
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

    if child.isalive(): child.wait()
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
        cmd = shlex.split('fdisk \'%s\'' % disk)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['(m for help)', 'Unable to open'])
    if i == 1:
        if child.isalive(): child.wait()
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

    if not rt: child.sendline('q')

    if child.isalive(): child.wait()
    return rt


def scan(disk, size=''):
    """Rescan partitions on a disk.
    
    True will return if scan successfully, or else False will return.
    
    Example:
    fdisk.scan('/dev/sdb')
    """
    try:
        cmd = shlex.split('fdisk \'%s\'' % disk)
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
        
    if child.isalive(): child.wait()
    return rt


if __name__ == '__main__':
# !!!!!!!!!!! DANGEROUS TESTING !!!!!!!!!!!
#    print '* Add partition to sdb with 5G:',
#    print add('/dev/sdb', '5G')
    
#    print '* Delete partition /dev/sdb1:',
#    print delete('/dev/sdb1')

    print '* Rescan partitions of /dev/sdb:',
    print scan('/dev/sdb')
    print 