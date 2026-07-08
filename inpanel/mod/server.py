# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.
'''Module for reading and writing Server Information'''

import datetime
import fcntl
import glob
import hashlib
import multiprocessing
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import struct
import pwd
import psutil
from subprocess import PIPE, Popen
import time
from xml.dom.minidom import parseString

from ..base import (
    hostname, kernel_name, os_name, os_title, os_versint, server_info, install_type,
    run_type, version_info, config_file, root_path, pidfile, logfile, logerror, execfile
)
from .. import utils
from ..utils import b2h

from .config import load_config, loadconfig, raw_loadconfig, raw_saveconfig, saveconfig
from .shell import run

def strfdelta(tdelta, fmt):
    d = {'days': tdelta.days}
    d['hours'], rem = divmod(tdelta.seconds, 3600)
    d['minutes'], d['seconds'] = divmod(rem, 60)
    return fmt.format(**d)


def div_percent(a, b):
    if b == 0:
        return '0%'
    return '%.2f%%' % (round(float(a) / b, 4) * 100)


class ServerInfo(object):

    # item : realtime update
    server_items = {
        'hostname'      : False,
        'datetime'      : True,
        'uptime'        : True,
        'loadavg'       : True,
        'cpustat'       : True,
        'meminfo'       : True,
        'mounts'        : True, 
        'netifaces'     : True,
        'nameservers'   : True,
        'distribution'  : False,
        'uname'         : False, 
        'cpuinfo'       : False,
        'diskinfo'      : False,
        'virt'          : False,
        'panelinfo'     : True,
    }

    @classmethod
    def hostname(self):
        return hostname

    @classmethod
    def datetime(self, asstruct=False):
        if not asstruct:
            return time.strftime('%Y-%m-%d %X %Z')
        else:
            d = time.localtime()
            return {
                'year': d.tm_year,
                'mon': d.tm_mon,
                'mday': d.tm_mday,
                'hour': d.tm_hour,
                'min': d.tm_min,
                'sec': d.tm_sec,
                'tz': time.strftime('%Z', d),
                'str': time.strftime('%Y-%m-%d %X', d),
            }

    @classmethod
    def uptime(self):
        if kernel_name == 'Darwin':
            up_seconds = int(time.time() - psutil.boot_time())
            cpu_times = psutil.cpu_times()
            idle_seconds = int(cpu_times.idle)
            cpu_count = psutil.cpu_count(logical=True) or 1
            if cpu_count > 1:
                idle_seconds = int(idle_seconds / cpu_count)
            if idle_seconds > up_seconds:
                idle_seconds = up_seconds
            fmt = '{days} 天 {hours} 小时 {minutes} 分 {seconds} 秒'
            uptime_string = strfdelta(datetime.timedelta(seconds=up_seconds), fmt)
            idletime_string = strfdelta(datetime.timedelta(seconds=idle_seconds), fmt)
            return {
                'up': uptime_string,
                'idle': idletime_string,
                'idle_rate': div_percent(idle_seconds, up_seconds),
            }
        with open('/proc/uptime', 'r', encoding='utf-8') as f:
            uptime, idletime = f.readline().split()
            up_seconds = int(float(uptime))
            idle_seconds = int(float(idletime))
            # in some machine like Linode VPS, idle time may bigger than up time
            if idle_seconds > up_seconds:
                cpu_count = multiprocessing.cpu_count()
                idle_seconds = idle_seconds / cpu_count
                # in some VPS, this value may still bigger than up time
                # may be the domain 0 machine has more cores
                # we calclate approximately for it
                if idle_seconds > up_seconds:
                    for n in range(2, 10):
                        if idle_seconds / n < up_seconds:
                            idle_seconds = idle_seconds / n
                            break
            fmt = '{days} 天 {hours} 小时 {minutes} 分 {seconds} 秒'
            uptime_string = strfdelta(datetime.timedelta(seconds=up_seconds), fmt)
            idletime_string = strfdelta(datetime.timedelta(seconds=idle_seconds), fmt)
        return {
            'up': uptime_string,
            'idle': idletime_string,
            'idle_rate': div_percent(idle_seconds, up_seconds),
        }

    @classmethod
    def loadavg(self):
        loadavg = {
            '1min': 0,
            '5min': 0,
            '15min': 0
        }
        if kernel_name == 'Linux':
            with open('/proc/loadavg', 'r', encoding='utf-8') as f:
                load_1min, load_5min, load_15min = f.readline().split()[0:3]
                loadavg['1min']  = load_1min
                loadavg['5min']  = load_5min
                loadavg['15min'] = load_15min
        elif kernel_name == 'Darwin':
            load_1min, load_5min, load_15min = psutil.getloadavg()
            loadavg['1min'] = str(load_1min)
            loadavg['5min'] = str(load_5min)
            loadavg['15min'] = str(load_15min)
        elif kernel_name == 'Windows': pass

        return loadavg

    @classmethod
    def cpustat(self, fullstat=False):
        cpustat = {
            'cpus': [],
            'total': 0,
            'btime': 0,
        }
        if kernel_name == 'Linux':
            # REF: http://www.kernel.org/doc/Documentation/filesystems/proc.txt
            fname = ('used', 'idle')
            full_fname = ('user', 'nice', 'system', 'idle', 'iowait', 'irq',
                        'softirq', 'steal', 'guest', 'guest_nice')
            cpustat['cpus'] = []
            with open('/proc/stat', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('cpu'):
                        fields = line.strip().split()
                        name = fields[0]
                        if not fullstat and name != 'cpu':
                            continue
                        stat = fields[1:]
                        stat = [int(i) for i in stat]
                        statall = sum(stat)
                        if fullstat:
                            while len(stat) < 10:
                                stat.append(0)
                            stat = dict(zip(full_fname, stat))
                        else:
                            stat = [statall - stat[3], stat[3]]
                            stat = dict(zip(fname, stat))
                        stat['all'] = statall
                        if name == 'cpu':
                            cpustat['total'] = stat
                        else:
                            cpustat['cpus'].append(stat)
                    elif line.startswith('btime'):
                        btime = int(line.strip().split()[1])
                        cpustat['btime'] = time.strftime('%Y-%m-%d %X %Z', time.localtime(btime))
        elif kernel_name == 'Darwin':
            fname = ('used', 'idle')
            cpu_times = psutil.cpu_times()
            statall = sum(cpu_times)
            used = statall - cpu_times.idle
            stat = {
                'used': int(used),
                'idle': int(cpu_times.idle),
                'all': int(statall),
            }
            cpustat['total'] = stat
            boot_time = psutil.boot_time()
            cpustat['btime'] = time.strftime('%Y-%m-%d %X %Z', time.localtime(boot_time))
        elif kernel_name == 'Windows': pass

        return cpustat

    @classmethod
    def meminfo(self):
        # OpenVZ may not have some varirables
        # so init them first
        mem_total = 0
        mem_free = 0
        mem_available = 0
        mem_buffers = 0
        mem_cached = 0
        mem_slab = 0
        swap_total = 0
        swap_free = 0
        swap_swappiness = 0
        mem_available_computed = 0

        if kernel_name == 'Linux':
            with open('/proc/meminfo', 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' not in line:
                        continue
                    item, value = line.split(':')
                    value = int(value.split()[0]) * 1024
                    if item == 'MemTotal':
                        mem_total = value
                    elif item == 'MemFree':
                        mem_free = value
                    elif item == 'MemAvailable':
                        mem_available = value
                    elif item == 'Buffers':
                        mem_buffers = value
                    elif item == 'Cached':
                        mem_cached = value
                    elif item == 'Slab':
                        mem_slab = value
                    elif item == 'SwapTotal':
                        swap_total = value
                    elif item == 'SwapFree':
                        swap_free = value
            with open('/proc/sys/vm/swappiness', 'r', encoding='utf-8') as f:
                swap_swappiness = f.readline()
        elif kernel_name == 'Darwin':
            mem = psutil.virtual_memory()
            mem_total = mem.total
            mem_free = mem.free
            mem_available = mem.available
            mem_buffers = 0
            mem_cached = mem.inactive if hasattr(mem, 'inactive') else 0
            swap = psutil.swap_memory()
            swap_total = swap.total
            swap_free = swap.free
        elif kernel_name == 'Windows':
            pass

        mem_used = mem_total - mem_free
        swap_used = swap_total - swap_free
        if not mem_available:
            # MemAvailable ≈ MemFree + Buffers + Cached
            mem_available_computed = mem_free + mem_buffers + mem_cached

        return {
            'mem_total': b2h(mem_total),
            'mem_used': b2h(mem_used),
            'mem_free': b2h(mem_free),
            'mem_available': b2h(mem_available),
            'mem_available_computed': b2h(mem_available_computed),
            'mem_buffers': b2h(mem_buffers),
            'mem_cached': b2h(mem_cached),
            'mem_slab': b2h(mem_slab),
            'swap_total': b2h(swap_total),
            'swap_used': b2h(swap_used),
            'swap_free': b2h(swap_free),
            'swap_swappiness': swap_swappiness,
            'mem_used_rate': div_percent(mem_used, mem_total),
            'mem_free_rate': div_percent(mem_free, mem_total),
            'mem_available_rate': div_percent(mem_available, mem_total),
            'mem_available_computed_rate': div_percent(mem_available_computed, mem_total),
            'swap_used_rate': div_percent(swap_used, swap_total),
            'swap_free_rate': div_percent(swap_free, swap_total),
        }

    @classmethod
    def mounts(self, detectdev=False):
        _mounts = []
        if kernel_name == 'Linux':
            with open('/proc/mounts', 'r', encoding='utf-8') as f:
                for line in f:
                    dev, path, fstype = line.split()[0:3]
                    # simfs: filesystem in OpenVZ
                    if fstype in ('ext2', 'ext3', 'ext4', 'xfs', 'jfs', 'reiserfs',
                                'btrfs', 'simfs'):
                        if not Path(path).is_dir():
                            continue
                        _mounts.append({'dev': dev, 'path': path, 'fstype': fstype})
            for mount in _mounts:
                stat = os.statvfs(mount['path'])
                total = stat.f_blocks * stat.f_bsize
                free = stat.f_bfree * stat.f_bsize
                used = (stat.f_blocks - stat.f_bfree) * stat.f_bsize
                mount['total'] = b2h(total)
                mount['free'] = b2h(free)
                mount['used'] = b2h(used)
                mount['used_rate'] = div_percent(used, total)
                if detectdev:
                    dev = os.stat(mount['path']).st_dev
                    mount['major'], mount['minor'] = os.major(dev), os.minor(dev)
        elif kernel_name == 'Darwin':
            p = Popen(['df', '-k', '-P'], stdout=PIPE, close_fds=True)
            output = p.stdout.read().decode('utf-8')
            p.wait()
            lines = output.strip().split('\n')
            for line in lines[1:]:
                fields = line.split()
                if len(fields) < 6:
                    continue
                dev, total_kb, used_kb, available_kb, percent, path = fields[:6]
                if not dev.startswith('/dev/'):
                    continue
                if path in ('/Volumes/Recovery', '/System/Volumes/Preboot', '/System/Volumes/VM', '/System/Volumes/Update'):
                    continue
                total = int(total_kb) * 1024
                free = int(available_kb) * 1024
                used = int(used_kb) * 1024
                mount_info = {
                    'dev': dev,
                    'path': path,
                    'fstype': 'APFS',
                    'total': b2h(total),
                    'free': b2h(free),
                    'used': b2h(used),
                    'used_rate': div_percent(used, total),
                }
                if detectdev:
                    mount_stat = os.stat(path)
                    mount_info['major'], mount_info['minor'] = os.major(mount_stat.st_dev), os.minor(mount_stat.st_dev)
                _mounts.append(mount_info)

                # for mount in _mounts:
                #     stat = os.statvfs(mount['path'])
                #     total = stat.f_blocks * stat.f_bsize
                #     free = stat.f_bfree * stat.f_bsize
                #     used = (stat.f_blocks - stat.f_bfree) * stat.f_bsize
                #     mount['total'] = b2h(total)
                #     mount['free'] = b2h(free)
                #     mount['used'] = b2h(used)
                #     mount['used_rate'] = div_percent(used, total)
        elif kernel_name == 'Windows':
            pass

        return _mounts

    @classmethod
    def netifaces(self):
        result = []
        if kernel_name == 'Linux':
            with open('/proc/net/dev', 'r', encoding='utf-8') as f:
                for line in f:
                    if not ':' in line:
                        continue
                    name, data = line.split(':')
                    name = name.strip()
                    data = data.split()
                    rx = int(data[0])
                    tx = int(data[8])
                    result.append({
                        'name': name,
                        'rx': b2h(rx),
                        'tx': b2h(tx),
                        'timestamp': int(time.time()),
                        'rx_bytes': rx,
                        'tx_bytes': tx,
                    })
            with open('/proc/net/route', encoding='utf-8') as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                        continue
                    gw = socket.inet_ntoa(struct.pack('<L', int(fields[2], 16)))
                    for netiface in result:
                        if netiface['name'] == fields[0]:
                            netiface['gw'] = gw
                            break

        elif kernel_name == 'Darwin':
            io_counters = psutil.net_io_counters(pernic=True)
            if_addrs = psutil.net_if_addrs()
            if_stats = psutil.net_if_stats()
            
            p = Popen(['route', '-n', 'get', 'default'], stdout=PIPE, close_fds=True)
            output = p.stdout.read().decode('utf-8')
            p.wait()
            gateway = ''
            for line in output.split('\n'):
                if 'gateway:' in line:
                    gateway = line.split(':')[1].strip()
                    break
            
            for name, addrs in if_addrs.items():
                if name.startswith('lo') or name.startswith('utun') or name.startswith('awdl'):
                    continue
                
                has_ip = False
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        has_ip = True
                        break
                
                if not has_ip:
                    continue
                
                ip = ''
                mask = ''
                mac = ''
                
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        mask = addr.netmask
                    elif addr.family == psutil.AF_LINK:
                        mac = addr.address
                
                status = 'down'
                if name in if_stats:
                    status = 'up' if if_stats[name].isup else 'down'
                
                rx_bytes = 0
                tx_bytes = 0
                if name in io_counters:
                    rx_bytes = io_counters[name].bytes_recv
                    tx_bytes = io_counters[name].bytes_sent
                
                encap = 'Ethernet' if mac else 'Local Loopback'
                
                netiface = {
                    'name': name,
                    'rx': b2h(rx_bytes),
                    'tx': b2h(tx_bytes),
                    'timestamp': int(time.time()),
                    'rx_bytes': rx_bytes,
                    'tx_bytes': tx_bytes,
                    'status': status,
                    'ip': ip,
                    'mask': mask,
                    'mac': mac,
                    'encap': encap,
                }
                
                if gateway:
                    netiface['gw'] = gateway
                
                result.append(netiface)
        elif kernel_name == 'Windows':
            pass

        if kernel_name == 'Linux':
            # REF: http://linux.about.com/library/cmd/blcmdl7_netdevice.htm
            for i, netiface in enumerate(result):
                guess_iface = False
                while True:
                    try:
                        ifname = netiface['name'][:15]
                        ifnamepack = struct.pack('256s', ifname.encode('utf-8'))
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sfd = s.fileno()
                        flags, = struct.unpack(
                            'H',
                            fcntl.ioctl(
                                sfd,
                                0x8913,  # SIOCGIFFLAGS
                                ifnamepack)[16:18])
                        netiface['status'] = ('down', 'up')[flags & 0x1]
                        netiface['ip'] = socket.inet_ntoa(
                            fcntl.ioctl(
                                sfd,
                                0x8915,  # SIOCGIFADDR
                                ifnamepack)[20:24])
                        netiface['bcast'] = socket.inet_ntoa(
                            fcntl.ioctl(
                                sfd,
                                0x8919,  # SIOCGIFBRDADDR
                                ifnamepack)[20:24])
                        netiface['mask'] = socket.inet_ntoa(
                            fcntl.ioctl(
                                sfd,
                                0x891b,  # SIOCGIFNETMASK
                                ifnamepack)[20:24])
                        hwinfo = fcntl.ioctl(
                            sfd,
                            0x8927,  # SIOCSIFHWADDR
                            ifnamepack)
                        # REF: networking/interface.c, /usr/include/linux/if.h, /usr/include/linux/if_arp.h
                        encaps = {
                            '\xff\xff': 'UNSPEC',                   # -1
                            '\x01\x00': 'Ethernet',                 # 1
                            '\x00\x02': 'Point-to-Point Protocol',  # 512
                            '\x04\x03': 'Local Loopback',           # 772
                            '\x08\x03': 'IPv6-in-IPv4',             # 776
                            '\x20\x00': 'InfiniBand',               # 32
                        }
                        hwtype = hwinfo[16:18]
                        netiface['encap'] = encaps[bytes.decode(hwtype)]
                        # netiface['mac'] = ':'.join(['%02X' % ord(str(char)) for char in hwinfo[18:24]])
                        netiface['mac'] = ':'.join(['%02X' % i for i in hwinfo[18:24]])

                        if not netiface['name'].startswith('venet'):
                            break

                        # detect interface like venet0:0, venet0:1, etc.
                        if not guess_iface:
                            guess_iface = True
                            guess_iface_name = netiface['name']
                            guess_iface_i = 0
                        else:
                            result.append(netiface)
                            guest_iface_i += 1

                        netiface = {
                            'name': '%s:%d' % (guess_iface_name, guess_iface_i),
                            'rx': '0B',
                            'tx': '0B',
                            'timestamp': 0,
                            'rx_bytes': 0,
                            'tx_bytes': 0,
                        }
                    except:
                        #result[i] = None
                        break

        result = [iface for iface in result if 'mac' in iface]
        return result

    @classmethod
    def nameservers(self):
        nameservers = []
        if kernel_name in ('Linux', 'Darwin'):
            with open('/etc/resolv.conf', 'r', encoding='utf-8') as f:
                for line in f:
                    if not 'nameserver' in line:
                        continue
                    ns, = line.strip().split()[1:2]
                    nameservers.append(ns)
        elif kernel_name == 'Windows':
            pass

        return nameservers

    @classmethod
    def distribution(self):
        return os_title

    @classmethod
    def dist(self):
        return {
            'name': os_name.lower(),
            'version': os_versint,
        }

    @classmethod
    def uname(self):
        return {
            'dist': server_info['os_name'],
            'kernel_name': server_info['kernel_name'],
            'hostname': server_info['hostname'],
            'kernel_release': server_info['kernel_release'],
            'kernel_version': server_info['kernel_version'],
            'machine': server_info['machine'],
            'processor': server_info['processor'],
            'platform': server_info['os_platform']
        }

    @classmethod
    def cpuinfo(self):
        models = []
        bitss = []
        cpuids = []
        if kernel_name == 'Linux':
            with open('/proc/cpuinfo', 'r', encoding='utf-8') as f:
                for line in f:
                    if 'model name' in line or 'physical id' in line or 'flags' in line:
                        item, value = line.strip().split(':')
                        item = item.strip()
                        value = value.strip()
                        if item == 'model name':
                            models.append(re.sub(r'\s+', ' ', value))
                        elif item == 'physical id':
                            cpuids.append(value)
                        elif item == 'flags':
                            if ' lm ' in value:
                                bitss.append('64bit')
                            else:
                                bitss.append('32bit')
        elif kernel_name == 'Darwin':
            physical_cpu_count = 1
            logical_count = psutil.cpu_count(logical=True) or 1
            p = Popen(['sysctl', '-n', 'machdep.cpu.brand_string'], stdout=PIPE, close_fds=True)
            cpu_model = p.stdout.read().decode('utf-8').strip()
            p.wait()
            if not cpu_model:
                cpu_model = 'Unknown CPU'
            for _ in range(logical_count):
                models.append(cpu_model)
                bitss.append('64bit')
            for i in range(physical_cpu_count):
                cpuids.append(str(i))
        elif kernel_name == 'Windows':
            pass

        cores = [{'model': x, 'bits': y} for x, y in zip(models, bitss)]
        cpu_count = len(set(cpuids))
        if cpu_count == 0:
            cpu_count = 1
        return {
            'cores': cores,
            'cpu_count': cpu_count,
            'core_count': len(cores),
        }

    @classmethod
    def partinfo(self, uuid=None, devname=None):
        """Read partition info including uuid and filesystem.

        You can specify uuid or devname to get the identified partition info.
        If no argument provided, all partitions will return.

        We read info from /etc/blkid/blkid.tab instead of call blkid command.
        REF: http://linuxconfig.org/how-to-retrieve-and-change-partitions-universally-unique-identifier-uuid-on-linux
        """
        blks = {}
        if kernel_name == 'Linux':
            p = Popen(shlex.split('/sbin/blkid'), stdout=PIPE, close_fds=True)
            p.stdout.read()
            p.wait()

            # OpenVZ may not have this file
            if not Path('/etc/blkid/blkid.tab').exists():
                return None

            with open('/etc/blkid/blkid.tab', encoding='utf-8') as f:
                for line in f:
                    dom = parseString(line).documentElement
                    _fstype = dom.getAttribute('TYPE')
                    _uuid = dom.getAttribute('UUID')
                    _devname = dom.firstChild.nodeValue.replace('/dev/', '')
                    partinfo = {
                        'name': _devname,
                        'fstype': _fstype,
                        'uuid': _uuid,
                    }
                    if uuid and uuid == _uuid:
                        return partinfo
                    elif devname and devname == _devname:
                        return partinfo
                    else:
                        blks[_devname] = partinfo
            if uuid or devname:
                return None
        elif kernel_name == 'Darwin':
            pass
        elif kernel_name == 'Windows':
            pass

        return blks

    @classmethod
    def diskinfo(self):
        """Return a dictionary contain info of all disks and partitions.
        """
        disks = {
            'count': 0,
            'totalsize': 0,
            'partitions': [],
            'lvm': {
                'partcount': 0,
                'unpartition': 0,
                'partitions': []
            }
        }

        # read mount points
        mounts = ServerInfo.mounts(True)

        # scan for uuid and filesystem of partitions
        blks = ServerInfo.partinfo()

        # OpenVZ may not have blk info
        if not blks:
            return disks

        for devname, blkinfo in blks.items():
            dev = os.stat('/dev/%s' % devname).st_rdev
            major, minor = os.major(dev), os.minor(dev)
            blks[devname]['major'] = major
            blks[devname]['minor'] = minor

        parts = []
        with open('/proc/partitions', 'r', encoding='utf-8') as f:
            for line in f:
                fields = line.split()
                if len(fields) == 0:
                    continue
                if not fields[0].isdigit():
                    continue
                major, minor, blocks, name = fields
                major, minor, blocks = int(major), int(minor), int(blocks)
                parts.append({
                    'name': name,
                    'major': major,
                    'minor': minor,
                    'blocks': blocks,
                })

        # check if some unmounted partition is busy
        has_busy_part = False
        for i, part in enumerate(parts):
            # check if it appears in blkid list
            if not part['name'] in blks:
                # don't check the part with child partition
                if i + 1 < len(parts) and parts[i + 1]['name'].startswith(
                        part['name']):
                    continue

                # if dev name doesn't match, check the major and minor of the dev
                devfound = False
                for devname, blkinfo in blks.items():
                    if blkinfo['major'] == part['major'] and blkinfo[
                            'minor'] == part['minor']:
                        devfound = True
                        break
                if devfound:
                    continue

                # means that it is busy
                has_busy_part = True
                break

        # scan for lvm logical volume
        lvmlvs = []
        lvmlvs_vname = {}
        if not has_busy_part and Path('/sbin/lvm').exists():
            p = Popen(shlex.split('/sbin/lvm lvdisplay'), stdout=PIPE, close_fds=True)
            lvs = p.stdout
            while True:
                line = lvs.readline()
                if not line:
                    break
                if 'LV Name' in line or 'LV Path' in line:
                    devlink = line.replace('LV Name',
                                           '').replace('LV Path', '').strip()
                    if not Path(devlink).exists():
                        continue
                    dev = os.readlink(devlink)
                    dev = str(Path(devlink).parent.joinpath(dev).resolve())
                    dev = dev.replace('/dev/', '')
                    lvmlvs_vname[dev] = devlink.replace('/dev/', '')
                    lvmlvs.append(dev)
            p.wait()

        # scan for the 'on' status swap partition
        swapptns = []
        with open('/proc/swaps', 'r', encoding='utf-8') as f:
            for line in f:
                if not line.startswith('/dev/'):
                    continue
                fields = line.split()
                swapptns.append(fields[0].replace('/dev/', ''))

        for part in parts:
            name = part['name']
            major = part['major']
            minor = part['minor']
            blocks = part['blocks']

            # check if the partition is a hardware disk
            # we treat name with no digit as a hardware disk
            is_hw = True
            partcount = 0
            unpartition = 0
            if len([x for x in name if x.isdigit()]) > 0 or name in lvmlvs:
                is_hw = False

            # determine which disk this partition belong to
            # and calcular the unpartition disk space
            parent_part = disks
            parent_part_found = False
            for i, ptn in enumerate(disks['partitions']):
                if name.startswith(ptn['name']):
                    parent_part_found = True
                    parent_part = disks['partitions'][i]
                    parent_part['partcount'] += 1
                    parent_part['unpartition'] -= blocks * 1024
                    break
            if not is_hw and not parent_part_found:
                parent_part = disks['lvm']

            if name in blks and blks[name]['fstype'].startswith('LVM'):
                is_pv = True
            else:
                is_pv = False

            partition = {
                'major': major,
                'minor': minor,
                'name': name,
                'size': b2h(blocks * 1024),
                'is_hw': is_hw,
                'is_pv': is_pv,
                'partcount': partcount,
            }

            if name in blks:
                partition['fstype'] = blks[name]['fstype']
                partition['uuid'] = blks[name]['uuid']

            if name in lvmlvs:
                partition['is_lv'] = True
                partition['vname'] = lvmlvs_vname[name]
            else:
                partition['is_lv'] = False

            for mount in mounts:
                if mount['major'] == major and mount['minor'] == minor:
                    partition['mount'] = mount['path']
                    # read filesystem type from blkid
                    #partition['fstype'] = mount['fstype']
                    break
            if name in swapptns:
                partition['fstype'] = 'swap'
                partition['mount'] = 'swap'

            if is_hw:
                partition['partitions'] = []
                partition['unpartition'] = blocks * 1024
                disks['count'] += 1
                disks['totalsize'] += blocks * 1024

            parent_part['partitions'].append(partition)

        disks['totalsize'] = b2h(disks['totalsize'])
        disks['lvscount'] = len(lvmlvs)
        for i, part in enumerate(disks['partitions']):
            unpartition = part['unpartition']
            if unpartition <= 10 * 1024**2:  # ignore size < 10MB
                unpartition = '0'
            else:
                unpartition = b2h(unpartition)
            disks['partitions'][i]['unpartition'] = unpartition
        return disks

    @classmethod
    def virt(self):
        """ Detect the virtual tech of system.
        REF: http://www.dmo.ca/blog/detecting-virtualization-on-linux/
        """
        if kernel_name == 'Linux':
            # detect from dmesg first
            if Path('/var/log/dmesg').exists():
                with open('/var/log/dmesg', encoding='utf-8') as f:
                    for line in f:
                        if 'VMware Virtual' in line:
                            return 'VMware'
                        if any([
                                'QEMU Virtual CPU' in line,
                                'Booting paravirtualized kernel on KVM' in line
                        ]):
                            return 'KVM'
                        if 'Booting paravirtualized kernel on Xen' in line:
                            return 'Xen PV'
                        if 'Xen HVM' in line:
                            return 'Xen HVM'
                        if 'Xen version' in line:
                            return 'Xen'
            if Path('/proc/xen/').exists():
                return 'Xen'
            if Path('/proc/vz/').exists():
                return 'Virtuozzo/OpenVZ'
        elif kernel_name == 'Darwin':
            return 'Darwin'
        elif kernel_name == 'Windows':
            return 'Windows'

        return ''

    @classmethod
    def panelinfo(self):
        pid = os.getpid()
        proc = psutil.Process(pid)
        
        start_time = proc.create_time()
        start_time_str = time.strftime('%Y-%m-%d %X %Z', time.localtime(start_time))
        
        uptime_seconds = int(time.time() - start_time)
        fmt = '{days} 天 {hours} 小时 {minutes} 分 {seconds} 秒'
        uptime_string = strfdelta(datetime.timedelta(seconds=uptime_seconds), fmt)
        
        try:
            uid = proc.uids().real
            pwd_info = pwd.getpwuid(uid)
            username = pwd_info.pw_name
        except:
            username = 'unknown'
        
        try:
            mem_info = proc.memory_info()
            mem_rss = b2h(mem_info.rss)
            mem_vms = b2h(mem_info.vms)
        except:
            mem_rss = '0B'
            mem_vms = '0B'
        
        try:
            cpu_percent = proc.cpu_percent(interval=0)
        except:
            cpu_percent = '0%'
        
        try:
            cmdline = ' '.join(proc.cmdline())
        except:
            cmdline = 'unknown'
        
        config = load_config(config_file)
        server_ip = config.get('server', 'ip') or '*'
        server_port = config.get('server', 'port') or '8080'
        try:
            force_https = config.getboolean('server', 'forcehttps')
        except:
            force_https = False
        
        bind_addr = f"{server_ip}:{server_port}"
        display_ip = server_info['hostname'] if server_ip == '*' else server_ip
        access_url = f"http{'s' if force_https else ''}://{display_ip}:{server_port}"
        
        if run_type == 'source':
            run_mode = '源码运行'
        elif run_type == 'system':
            run_mode = '系统模式'
        elif run_type == 'binary':
            run_mode = '二进制模式'
        else:
            run_mode = '未知模式'
        
        install_mode = ''
        if run_type == 'system' and install_type != 'unknown':
            install_names = {
                'pip': 'pip',
                'apt': 'apt',
                'yum': 'yum',
                'dnf': 'dnf',
                'pacman': 'pacman',
                'zypper': 'zypper',
            }
            install_mode = install_names.get(install_type, install_type)
        
        return {
            'pid': pid,
            'start_time': start_time_str,
            'uptime': uptime_string,
            'run_user': username,
            'mem_rss': mem_rss,
            'mem_vms': mem_vms,
            'cpu_percent': str(cpu_percent) + '%' if isinstance(cpu_percent, (int, float)) else cpu_percent,
            'run_mode': run_mode,
            'install_mode': install_mode,
            'run_command': cmdline,
            'bind_addr': bind_addr,
            'access_url': access_url,
            'version': version_info['version'],
            'releasetime': version_info['releasetime'],
            'config_file': config_file,
            'root_path': root_path,
            'pid_file': pidfile,
            'log_file': logfile,
            'error_log_file': logerror,
            'exec_file': execfile,
        }


    @classmethod
    def set_hostname(cls, hostname=None):
        '''Change Hostname'''
        if hostname is None:
            return False

        hostname = hostname.strip().replace(' ', '').replace('\n', '')
        if hostname == '':
            return False

        if os_name == 'CentOS':
            if saveconfig('/etc/sysconfig/network', {'HOSTNAME': hostname}) and \
                raw_saveconfig('/etc/hosts', { '127.0.0.1': hostname, '::1': hostname }, delimiter=' ', quoter='') and \
                run(str('hostname %s' % hostname)) == 0:
                return True
            else:
                return False
        elif os_name == 'Ubuntu':
            try:
                with open('/etc/hostname', 'w', encoding='utf-8') as f:
                    f.write(hostname)
                newdata = {
                    '127.0.0.1': ['localhost', hostname],
                    '::1': ['localhost', hostname]
                }
                if run('hostnamectl set-hostname %s' % hostname) == 0 and \
                    raw_saveconfig('/etc/hosts', newdata, delimiter=' ', quoter=''):
                    return True
                else:
                    return False
            except:
                return False
        else:
            return False

    @classmethod
    def set_nameservers(cls, nameservers=None):
        """Write nameservers to config file.
        """
        if nameservers is None:
            return False

        nspath = '/etc/resolv.conf'
        data = { 'nameserver': nameservers }
        return raw_saveconfig(nspath, data, delimiter=' ', quoter='')

    @classmethod
    def ifconfig(cls, ifname, config=None):
        """Read or write single interface's config.
        """
        dist = cls.dist()
        if dist['name'] in ('centos', 'redhat'):
            cfile = '/etc/sysconfig/network-scripts/ifcfg-%s' % ifname
            cmap = {
                'DEVICE': 'name',
                'HWADDR': 'mac',
                'IPADDR': 'ip',
                'NETMASK': 'mask',
                'GATEWAY': 'gw',
            }
            if config is None:
                return loadconfig(cfile, cmap)
            else:
                cmap_reverse = dict((v, k) for k, v in cmap.items())
                return saveconfig(cfile, config, cmap_reverse)
        elif dist['name'] == 'macos':
            if config is None:
                ifaces = cls.netifaces()
                for iface in ifaces:
                    if iface['name'] == ifname:
                        return {
                            'name': iface['name'],
                            'ip': iface.get('ip', ''),
                            'mask': iface.get('mask', ''),
                            'gw': iface.get('gw', ''),
                            'mac': iface.get('mac', ''),
                        }
                return None
            else:
                return True
        else:
            return None

    @classmethod
    def ifconfigs(cls):
        """Read config of all interfaces.
        """
        configs = {}
        ifaces = cls.netifaces()
        for iface in ifaces:
            ifname = iface['name']
            config = cls.ifconfig(ifname)
            if config:
                configs[ifname] = config
        return configs


    @classmethod
    def network_handle_get(cls, sec, ifname=None):
        """Handle network GET requests."""
        if sec == 'hostname':
            return {'hostname': cls.hostname()}
        elif sec == 'ifnames':
            ifconfigs = cls.ifconfigs()
            return {'ifnames': sorted(ifconfigs.keys())}
        elif sec == 'ifconfig':
            ifconfig = cls.ifconfig(ifname)
            if ifconfig is not None:
                return ifconfig
            return None
        elif sec == 'nameservers':
            return {'nameservers': cls.nameservers()}
        return None

    @classmethod
    def network_handle_post(cls, sec, ifname=None, args=None):
        """Handle network POST requests."""
        if args is None:
            args = {}

        if sec == 'hostname':
            hostname = args.get('hostname', '')
            if hostname != '':
                if cls.set_hostname(hostname):
                    return {'code': 0, 'msg': '主机名保存成功！'}
                else:
                    return {'code': -1, 'msg': '主机名保存失败！'}
            else:
                return {'code': -1, 'msg': '主机名不能为空！'}

        elif sec == 'ifconfig':
            ip = args.get('ip', '')
            mask = args.get('mask', '')
            gw = args.get('gw', '')

            if not utils.is_valid_ip(ip):
                return {'code': -1, 'msg': '%s 不是有效的IP地址！' % ip}
            if not utils.is_valid_netmask(mask):
                return {'code': -1, 'msg': '%s 不是有效的子网掩码！' % mask}
            if gw != '' and not utils.is_valid_ip(gw):
                return {'code': -1, 'msg': '网关IP %s 不是有效的IP地址！' % gw}

            if cls.ifconfig(ifname, {'ip': ip, 'mask': mask, 'gw': gw}):
                return {'code': 0, 'msg': 'IP设置保存成功！'}
            else:
                return {'code': -1, 'msg': 'IP设置保存失败！'}

        elif sec == 'nameservers':
            nameservers = args.get('nameservers', '')
            nameservers = nameservers.split(',')

            for i, nameserver in enumerate(nameservers):
                if nameserver == '':
                    del nameservers[i]
                    continue
                if not utils.is_valid_ip(nameserver):
                    return {'code': -1, 'msg': '%s 不是有效的IP地址！' % nameserver}

            if cls.set_nameservers(nameservers):
                return {'code': 0, 'msg': 'DNS设置保存成功！'}
            else:
                return {'code': -1, 'msg': 'DNS设置保存失败！'}

        return None


    @classmethod
    def reboot(cls):
        """Reboot the server."""
        p = Popen('reboot', stdout=PIPE, stderr=PIPE, close_fds=True)
        info = p.stdout.read()
        p.stderr.read()
        if p.wait() == 0:
            return {'code': 0, 'msg': '已向系统发送重启指令，系统即将重启！'}
        else:
            return {'code': -1, 'msg': '向系统发送重启指令失败！'}



    @classmethod
    def get_timezone_regions(cls):
        """Return all the timezone regions."""
        return ('Africa', 'America', 'Antarctica', 'Arctic', 'Asia',
                'Atlantic', 'Australia', 'Europe', 'Indian', 'Pacific', 'Etc')

    @classmethod
    def get_timezone_list(cls, region=None):
        """Return timezone list.

        Pass None to parameter region to get the full timezone name, such as:
            Asia/Shanghai
            Asia/Chongqing
        Or else only the city name would be returned.
        """
        zonepath = Path('/usr/share/zoneinfo')
        timezones = []
        if region is None:
            regions = cls.get_timezone_regions()
            for region in regions:
                regionpath = zonepath / region
                for zonefile in regionpath.iterdir():
                    if not zonefile.is_file():
                        continue
                    timezones.append('%s/%s' % (region, zonefile.name))
        else:
            regionpath = zonepath / region
            if not regionpath.exists():
                return []
            for zonefile in regionpath.iterdir():
                if not zonefile.is_file():
                    continue
                timezones.append(zonefile.name)

        return sorted(timezones)

    @classmethod
    def get_timezone(cls, config):
        """Get system timezone."""
        tzpath = Path('/etc/localtime')
        zonepath = Path('/usr/share/zoneinfo')

        # firstly read from config file
        timezone = ''
        if config is not None:
            if not config.has_section('time'):
                config.add_section('time')

            if config.has_option('time', 'timezone'):
                timezone = config.get('time', 'timezone')
                if timezone:
                    return timezone

        # or else check the system config file
        dist = cls.dist()
        if dist['name'] in ('centos', 'redhat'):
            clockinfo = raw_loadconfig('/etc/sysconfig/clock')
            if clockinfo and 'ZONE' in clockinfo:
                timezone = clockinfo['ZONE']
                return timezone
        else:
            pass

        # or else find the file match /etc/localtime
        with open(tzpath, 'rb') as f:
            tzdata = hashlib.md5(f.read()).hexdigest()
        regions = cls.get_timezone_regions()
        for region in regions:
            regionpath = zonepath / region
            for zonefile in regionpath.iterdir():
                if not zonefile.is_file():
                    continue
                with open(zonefile, 'rb') as f:
                    if hashlib.md5(f.read()).hexdigest() == tzdata:
                        return '%s/%s' % (region, zonefile.name)
        return ''

    @classmethod
    def set_timezone(cls, config, timezone=None):
        """Set system timezone.

        Pass timezone full name like 'Asia/Shanghai' to set timezone.
        """
        if timezone is None:
            return False

        tzpath = Path('/etc/localtime')
        zonepath = Path('/usr/share/zoneinfo')

        timezonefile = zonepath / timezone
        if not timezonefile.exists():
            return False
        try:
            shutil.copyfile(timezonefile, tzpath)
        except:
            return False

        # write timezone setting to config file
        return config.set('time', 'timezone', timezone)

    @classmethod
    def handle_time_get(cls, sec, region=None, config=None):
        """Handle time-related GET requests.
        
        Args:
            sec: section ('datetime', 'timezone', or 'timezone_list')
            region: optional region for timezone list
            config: config object
        
        Returns:
            dict with requested data
        """
        if sec == 'datetime':
            return cls.datetime(asstruct=True)
        elif sec == 'timezone':
            return {'timezone': cls.get_timezone(config)}
        elif sec == 'timezone_list':
            if region is None:
                return {'regions': cls.get_timezone_regions()}
            else:
                return {'cities': cls.get_timezone_list(region)}
        return None

    @classmethod
    def handle_time_post(cls, config, sec, timezone=''):
        """Handle time-related POST requests.
        
        Args:
            config: config object
            sec: section ('timezone')
            timezone: timezone string
        
        Returns:
            dict with 'code' and 'msg' keys
        """
        if sec == 'timezone':
            if cls.set_timezone(config, timezone):
                return {'code': 0, 'msg': '时区设置保存成功！'}
            else:
                return {'code': -1, 'msg': '时区设置保存失败！'}
        return None

class ServerTool(object):
    @classmethod
    def supportfs(self):
        """Return a list of file system that system support.
        """
        support_list = []
        for fstype in ('ext2', 'ext3', 'ext4', 'xfs', 'jfs', 'reiserfs',
                       'btrfs'):
            if Path('/sbin/mkfs.%s' % fstype).exists():
                support_list.append(fstype)
        support_list.append('swap')
        return support_list

if __name__ == '__main__':
    print('')
    print('* Hostname: %s' % ServerInfo.hostname())
    print('')

    print('* Server time: %s' % ServerInfo.datetime())
    print('')

    uptime = ServerInfo.uptime()
    print('* Uptime: %s' % uptime['up'])
    print('* Idletime: %s' % uptime['idle'])
    print('* Idlerate: %s' % uptime['idle_rate'])
    print('')

    loadavg = ServerInfo.loadavg()
    print('* Last 1 min processes: %s' % loadavg['1min'])
    print('* Last 15 min processes: %s' % loadavg['5min'])
    print('* Last 15 min processes: %s' % loadavg['15min'])
    print('')

    cpustat = ServerInfo.cpustat()
    tstat = cpustat['total']
    print('* Total CPU stats:')
    for k, v in tstat.items():
        print('  %s: %d' % (k, v))
    for i, tstat in enumerate(cpustat['cpus']):
        print('* CPU-%d stats:' % i)
        for k, v in tstat.items():
            print('  %s: %d' % (k, v))
    print('')

    meminfo = ServerInfo.meminfo()
    print('* Memory total: %s' % meminfo['mem_total'])
    print('* Memory used: %s (%s)' % (meminfo['mem_used'], meminfo['mem_used_rate']))
    print('* Memory free: %s (%s)' % (meminfo['mem_free'], meminfo['mem_free_rate']))
    print('* Memory available: %s (%s)' % (meminfo['mem_available'], meminfo['mem_available_rate']))
    print('* Memory buffers: %s' % meminfo['mem_buffers'])
    print('* Memory cached: %s' % meminfo['mem_cached'])
    print('* Memory slab: %s' % meminfo['mem_slab'])
    print('* Swap total: %s' % meminfo['swap_total'])
    print('* Swap used: %s (%s)' % (meminfo['swap_used'], meminfo['swap_used_rate']))
    print('* Swap free: %s (%s)' % (meminfo['swap_free'], meminfo['swap_free_rate']))
    print('* Swappiness: %s' % meminfo['swap_swappiness'])
    print()
    print('')
    mounts = ServerInfo.mounts(True)
    for mount in mounts:
        print('* Mount device: %s' % mount['dev'])
        if 'major' in mount:
            print('* Dev node: (%d, %d)' % (mount['major'], mount['minor']))
        print('* Mount point: %s' % mount['path'])
        print('* Total space: %s' % mount['total'])
        print('* Free space: %s' % mount['free'])
        print('* Used space: %s (%s)' % (mount['used'], mount['used_rate']))
        print('')

    netifaces = ServerInfo.netifaces()
    for netiface in netifaces:
        print('* Interface name: %s' % netiface['name'])
        print('* Interface status: %s' % netiface['status'])
        print('* Link encap: %s' % netiface['encap'])
        print('* IP address: %s' % netiface['ip'])
        print('* Broadcast: %s' % netiface['bcast'])
        print('* Network mask: %s' % netiface['mask'])
        if 'gw' in netiface:
            print('* Default gateway: %s' % netiface['gw'])
        print('* MAC address: %s' % netiface['mac'])
        print('* Data receive: %s' % netiface['rx'])
        print('* Data transmit: %s' % netiface['tx'])
        print('')

    nameservers = ServerInfo.nameservers()
    print('* Name servers:')
    for nameserver in nameservers:
        print('  %s' % nameserver)
    print('')

    uname = ServerInfo.uname()
    print('* Kernel name: %s' % uname['kernel_name'])
    print('* Kernel release: %s' % uname['kernel_release'])
    print('* Kernel version: %s' % uname['kernel_version'])
    print('* Machine: %s' % uname['machine'])
    print('')

    cpuinfo = ServerInfo.cpuinfo()
    print('* CPU count: %d' % cpuinfo['cpu_count'])
    print('* CPU cores: %d' % cpuinfo['core_count'])
    for c in cpuinfo['cores']:
        print('* CPU core: %s (%s)' % (c['model'], c['bits']))
    print('')

    diskinfo = ServerInfo.diskinfo()
    count = diskinfo['count']
    totalsize = diskinfo['totalsize']
    partitions = diskinfo['partitions']
    print('* %d disks detected, total size: %s' % (count, totalsize))
    print('')
    for partition in partitions:
        print('* Partition name: %s (%d, %d)' %
              (partition['name'], partition['major'], partition['minor']))
        if 'vname' in partition:
            print('  Volumn name: %s' % partition['vname'])
        print('  Partition size: %s (%s free)' %
              (partition['size'], partition['unpartition']))
        if 'uuid' in partition:
            print('  Partition UUID: %s' % partition['uuid'])
        if 'fstype' in partition:
            print('  Partition fstype: %s' % partition['fstype'])
        print('  Partition is PV: %s' % partition['is_pv'])
        print('  Partition is LV: %s' % partition['is_lv'])
        print('  Partition is HW: %s' % partition['is_hw'])
        if 'mount' in partition:
            print('  Mount point: %s' % partition['mount'])
        if partition['is_hw']:
            print('  Partition count: %d' % partition['partcount'])
        print()
        for subpartition in partition['partitions']:
            print('  - Subpartition name: %s (%d, %d)' %
                  (subpartition['name'], subpartition['major'],
                   subpartition['minor']))
            if 'vname' in subpartition:
                print('  - Volumn name: %s' % subpartition['vname'])
            print('  - Subpartition size: %s' % subpartition['size'])
            if 'uuid' in subpartition:
                print('  - Subpartition UUID: %s' % subpartition['uuid'])
            if 'fstype' in subpartition:
                print('  - Subpartition fstype: %s' % subpartition['fstype'])
            print('  - Subpartition is PV: %s' % subpartition['is_pv'])
            print('  - Subpartition is LV: %s' % subpartition['is_lv'])
            print('  - Subpartition is HW: %s' % subpartition['is_hw'])
            if 'mount' in subpartition:
                print('  - Mount point: %s' % subpartition['mount'])
            if subpartition['is_hw']:
                print('  - Subpartition count: %d' % subpartition['partcount'])
            print()
        print()

    print('* LVM partitions:')
    for partition in diskinfo['lvm']['partitions']:
        print('  - Partition name: %s (%d, %d)' %
              (partition['name'], partition['major'], partition['minor']))
        if 'vname' in partition:
            print('  - Volumn name: %s' % partition['vname'])
        print('  - Partition size: %s' % partition['size'])
        if 'uuid' in partition:
            print('  - Partition UUID: %s' % partition['uuid'])
        if 'fstype' in partition:
            print('  - Partition fstype: %s' % partition['fstype'])
        print('  - Partition is PV: %s' % partition['is_pv'])
        print('  - Partition is LV: %s' % partition['is_lv'])
        print('  - Partition is HW: %s' % partition['is_hw'])
        if 'mount' in partition:
            print('  - Mount point: %s' % partition['mount'])
        if partition['is_hw']:
            print('  - Partition count: %d' % partition['partcount'])
        print()

    print('* Support file systems:')
    for fstype in ServerTool.supportfs():
        print('  - %s' % fstype)
    print()

    print('* Virtual Tech: %s' % ServerInfo.virt())
