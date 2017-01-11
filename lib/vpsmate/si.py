#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

"""Package for quering server info
"""

import os
import re
import time
import datetime
import socket
import fcntl
import struct
import platform
import glob
import shlex
import subprocess
import multiprocessing
from xml.dom.minidom import parseString


def strfdelta(tdelta, fmt):
    d = {'days': tdelta.days}
    d['hours'], rem = divmod(tdelta.seconds, 3600)
    d['minutes'], d['seconds'] = divmod(rem, 60)
    return fmt.format(**d)

def b2h(n):
    # bypes to human
    # http://code.activestate.com/recipes/578019
    # >>> b2h(10000)
    # '9.8K'
    # >>> b2h(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def div_percent(a, b):
    if b == 0: return '0%'
    return '%.2f%%' % (round(float(a)/b, 4) * 100)


class Server(object):
    @classmethod
    def hostname(self):
        with open('/proc/sys/kernel/hostname', 'r') as f:
            hostname = f.readline().strip()
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
        with open('/proc/uptime', 'r') as f:
            uptime, idletime = f.readline().split()
            up_seconds = int(float(uptime))
            idle_seconds = int(float(idletime))
            # in some machine like Linode VPS, idle time may bigger than up time
            if idle_seconds > up_seconds:
                cpu_count = multiprocessing.cpu_count()
                idle_seconds = idle_seconds/cpu_count
                # in some VPS, this value may still bigger than up time
                # may be the domain 0 machine has more cores
                # we calclate approximately for it
                if idle_seconds > up_seconds:
                    for n in range(2,10):
                        if idle_seconds/n < up_seconds:
                            idle_seconds = idle_seconds/n
                            break
            fmt = '{days} 天 {hours} 小时 {minutes} 分 {seconds} 秒'
            uptime_string = strfdelta(datetime.timedelta(seconds = up_seconds), fmt)
            idletime_string = strfdelta(datetime.timedelta(seconds = idle_seconds), fmt)
        return {
            'up': uptime_string,
            'idle': idletime_string,
            'idle_rate': div_percent(idle_seconds, up_seconds),
        }
    
    @classmethod
    def loadavg(self):
        with open('/proc/loadavg', 'r') as f:
            load_1min, load_5min, load_15min = f.readline().split()[0:3]
        return {
            '1min': load_1min,
            '5min': load_5min,
            '15min': load_15min,
        }
    
    @classmethod
    def cpustat(self, fullstat=False):
        cpustat = {}
        # REF: http://www.kernel.org/doc/Documentation/filesystems/proc.txt
        fname = ('used', 'idle')
        full_fname = ('user', 'nice', 'system', 'idle', 'iowait', 'irq',
                'softirq', 'steal', 'guest', 'guest_nice')
        cpustat['cpus'] = []
        with open('/proc/stat', 'r') as f:
            for line in f:
                if line.startswith('cpu'):
                    fields = line.strip().split()
                    name = fields[0]
                    if not fullstat and name != 'cpu': continue;
                    stat = fields[1:]
                    stat = [int(i) for i in stat]
                    statall = sum(stat)
                    if fullstat:
                        while len(stat) < 10: stat.append(0)
                        stat = dict(zip(full_fname, stat))
                    else:
                        stat = [statall-stat[3], stat[3]]
                        stat = dict(zip(fname, stat))
                    stat['all'] = statall
                    if name == 'cpu':
                        cpustat['total'] = stat
                    else:
                        cpustat['cpus'].append(stat)
                elif line.startswith('btime'):
                    btime = int(line.strip().split()[1])
                    cpustat['btime'] = time.strftime('%Y-%m-%d %X %Z',
                                                    time.localtime(btime))
        return cpustat

    @classmethod
    def meminfo(self):
        # OpenVZ may not have some varirables
        # so init them first
        mem_total = mem_free = mem_buffers = mem_cached = swap_total = swap_free = 0

        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if ':' not in line: continue
                item, value = line.split(':')
                value = int(value.split()[0]) * 1024;
                if item == 'MemTotal':
                    mem_total = value
                elif item == 'MemFree':
                    mem_free = value
                elif item == 'Buffers':
                    mem_buffers = value
                elif item == 'Cached':
                    mem_cached = value
                elif item == 'SwapTotal':
                    swap_total = value
                elif item == 'SwapFree':
                    swap_free = value

        mem_used = mem_total - mem_free
        swap_used = swap_total - swap_free
        return {
            'mem_total': b2h(mem_total),
            'mem_used': b2h(mem_used),
            'mem_free': b2h(mem_free),
            'mem_buffers': b2h(mem_buffers),
            'mem_cached': b2h(mem_cached),
            'swap_total': b2h(swap_total),
            'swap_used': b2h(swap_used),
            'swap_free': b2h(swap_free),
            'mem_used_rate': div_percent(mem_used, mem_total),
            'mem_free_rate': div_percent(mem_free, mem_total),
            'swap_used_rate': div_percent(swap_used, swap_total),
            'swap_free_rate': div_percent(swap_free, swap_total),
        }

    @classmethod
    def mounts(self, detectdev=False):
        mounts = []
        with open('/proc/mounts', 'r') as f:
            for line in f:
                dev, path, fstype = line.split()[0:3]
                if fstype in ('ext2', 'ext3', 'ext4', 'xfs',
                              'jfs', 'reiserfs', 'btrfs',
                              'simfs'): # simfs: filesystem in OpenVZ
                    if not os.path.isdir(path): continue
                    mounts.append({'dev': dev, 'path': path, 'fstype': fstype})
        for mount in mounts:
            stat = os.statvfs(mount['path'])
            total = stat.f_blocks*stat.f_bsize
            free = stat.f_bfree*stat.f_bsize
            used = (stat.f_blocks-stat.f_bfree)*stat.f_bsize
            mount['total'] = b2h(total)
            mount['free'] = b2h(free)
            mount['used'] = b2h(used)
            mount['used_rate'] = div_percent(used, total)
            if detectdev:
                dev = os.stat(mount['path']).st_dev
                mount['major'], mount['minor'] = os.major(dev), os.minor(dev)
        return mounts

    @classmethod
    def netifaces(self):
        netifaces = []
        with open('/proc/net/dev', 'r') as f:
            for line in f:
                if not ':' in line: continue
                name, data = line.split(':')
                name = name.strip()
                data = data.split()
                rx = int(data[0])
                tx = int(data[8])
                netifaces.append({
                    'name': name,
                    'rx': b2h(rx),
                    'tx': b2h(tx),
                    'timestamp': int(time.time()),
                    'rx_bytes': rx,
                    'tx_bytes': tx,
                })
        with open('/proc/net/route') as f:
            for line in f:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                gw = socket.inet_ntoa(struct.pack('<L', int(fields[2], 16)))
                for netiface in netifaces:
                    if netiface['name'] == fields[0]:
                        netiface['gw'] = gw
                        break
        # REF: http://linux.about.com/library/cmd/blcmdl7_netdevice.htm
        for i, netiface in enumerate(netifaces):
            guess_iface = False
            while True:
                try:
                    ifname = netiface['name'][:15]
                    ifnamepack = struct.pack('256s', ifname)
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sfd = s.fileno()
                    flags, = struct.unpack('H', fcntl.ioctl(
                        sfd, 0x8913,  # SIOCGIFFLAGS
                        ifnamepack
                    )[16:18])
                    netiface['status'] = ('down', 'up')[flags & 0x1]
                    netiface['ip'] = socket.inet_ntoa(fcntl.ioctl(
                        sfd, 0x8915,  # SIOCGIFADDR
                        ifnamepack
                    )[20:24])
                    netiface['bcast'] = socket.inet_ntoa(fcntl.ioctl(
                        sfd, 0x8919,  # SIOCGIFBRDADDR
                        ifnamepack
                    )[20:24])
                    netiface['mask'] = socket.inet_ntoa(fcntl.ioctl(
                        sfd, 0x891b,  # SIOCGIFNETMASK
                        ifnamepack
                    )[20:24])
                    hwinfo = fcntl.ioctl(
                        sfd, 0x8927,  # SIOCSIFHWADDR
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
                    netiface['encap'] = encaps[hwtype]
                    netiface['mac'] = ':'.join(['%02X' % ord(char) for char in hwinfo[18:24]])
    
                    if not netiface['name'].startswith('venet'): break

                    # detect interface like venet0:0, venet0:1, etc.
                    if not guess_iface:
                        guess_iface = True
                        guess_iface_name = netiface['name']
                        guess_iface_i = 0
                    else:
                        netifaces.append(netiface)
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
                    #netifaces[i] = None
                    break
                
        netifaces = [ iface for iface in netifaces if iface.has_key('mac') ]
        return netifaces

    @classmethod
    def nameservers(self):
        nameservers = []
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if not 'nameserver' in line: continue
                ns, = line.strip().split()[1:2]
                nameservers.append(ns)
        return nameservers

    @classmethod
    def distribution(self):
        dist = platform.linux_distribution()
        return ' '.join(dist)
    
    @classmethod
    def dist(self):
        dist = platform.linux_distribution(full_distribution_name=0)
        return {
            'name': dist[0].lower(),
            'version': dist[1],
        }

    @classmethod
    def uname(self):
        p = subprocess.Popen(shlex.split('uname -i'), stdout=subprocess.PIPE, close_fds=True)
        hwplatform = p.stdout.read().strip()
        p.wait()

        uname = platform.uname()
        return {
            'kernel_name': uname[0],
            'node': uname[1],
            'kernel_release': uname[2],
            'kernel_version': uname[3],
            'machine': uname[4],
            'processor': uname[5],
            'platform': hwplatform,
        }

    @classmethod
    def cpuinfo(self):
        models = []
        bitss = []
        cpuids = []
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line or 'physical id' in line or 'flags' in line:
                    item, value = line.strip().split(':')
                    item = item.strip()
                    value = value.strip()
                    if item == 'model name':
                        models.append(re.sub('\s+', ' ', value))
                    elif item == 'physical id':
                        cpuids.append(value)
                    elif item == 'flags':
                        if ' lm ' in value:
                            bitss.append('64bit')
                        else:
                            bitss.append('32bit')
        cores = [{'model': x, 'bits': y} for x, y in zip(models, bitss)]
        cpu_count = len(set(cpuids))
        if cpu_count == 0: cpu_count = 1
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
        p = subprocess.Popen(shlex.split('/sbin/blkid'), stdout=subprocess.PIPE, close_fds=True)
        p.stdout.read()
        p.wait()

        # OpenVZ may not have this file
        if not os.path.exists('/etc/blkid/blkid.tab'): return None

        with open('/etc/blkid/blkid.tab') as f:
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
        else:
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
        mounts = Server.mounts(True)
        
        # scan for uuid and filesystem of partitions
        blks = Server.partinfo()

        # OpenVZ may not have blk info
        if not blks: return disks

        for devname, blkinfo in blks.iteritems():
            dev = os.stat('/dev/%s' % devname).st_rdev
            major, minor = os.major(dev), os.minor(dev)
            blks[devname]['major'] = major
            blks[devname]['minor'] = minor

        parts = []
        with open('/proc/partitions', 'r') as f:
            for line in f:
                fields = line.split()
                if len(fields) == 0: continue
                if not fields[0].isdigit(): continue
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
            if not blks.has_key(part['name']):
                # don't check the part with child partition
                if i+1<len(parts) and parts[i+1]['name'].startswith(part['name']):
                    continue
                
                # if dev name doesn't match, check the major and minor of the dev
                devfound = False
                for devname, blkinfo in blks.iteritems():
                    if blkinfo['major'] == part['major'] and blkinfo['minor'] == part['minor']:
                        devfound = True
                        break
                if devfound: continue

                # means that it is busy
                has_busy_part = True
                break

        # scan for lvm logical volume
        lvmlvs = []
        lvmlvs_vname = {}
        if not has_busy_part and os.path.exists('/sbin/lvm'):
            p = subprocess.Popen(shlex.split('/sbin/lvm lvdisplay'), stdout=subprocess.PIPE, close_fds=True)
            lvs = p.stdout
            while True:
                line = lvs.readline()
                if not line: break
                if 'LV Name' in line or 'LV Path' in line:
                    devlink = line.replace('LV Name', '').replace('LV Path', '').strip()
                    if not os.path.exists(devlink): continue
                    dev = os.readlink(devlink)
                    dev = os.path.abspath(os.path.join(os.path.dirname(devlink), dev))
                    dev = dev.replace('/dev/', '')
                    lvmlvs_vname[dev] = devlink.replace('/dev/', '')
                    lvmlvs.append(dev)
            p.wait()
        
        # scan for the 'on' status swap partition
        swapptns = []
        with open('/proc/swaps', 'r') as f:
            for line in f:
                if not line.startswith('/dev/'): continue
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
                    parent_part['unpartition'] -= blocks*1024
                    break
            if not is_hw and not parent_part_found:
                parent_part = disks['lvm']

            if blks.has_key(name) and blks[name]['fstype'].startswith('LVM'):
                is_pv = True
            else:
                is_pv = False
            
            partition = {
                'major': major,
                'minor': minor,
                'name': name,
                'size': b2h(blocks*1024),
                'is_hw': is_hw,
                'is_pv': is_pv,
                'partcount': partcount,
            }

            if blks.has_key(name):
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
                partition['unpartition'] = blocks*1024
                disks['count'] += 1
                disks['totalsize'] += blocks*1024

            parent_part['partitions'].append(partition)

        disks['totalsize'] = b2h(disks['totalsize'])
        disks['lvscount'] = len(lvmlvs)
        for i, part in enumerate(disks['partitions']):
            unpartition = part['unpartition']
            if unpartition <= 10*1024**2:   # ignore size < 10MB
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
        # detect from dmesg first
        with open('/var/log/dmesg') as f:
            for line in f:
                if 'VMware Virtual' in line:
                    return 'VMware'
                if any(['QEMU Virtual CPU' in line,
                       'Booting paravirtualized kernel on KVM' in line]):
                    return 'KVM'
                if 'Booting paravirtualized kernel on Xen' in line:
                    return 'Xen PV'
                if 'Xen HVM' in line:
                    return 'Xen HVM'
                if 'Xen version' in line:
                    return 'Xen'
        if os.path.exists('/proc/xen/'): return 'Xen'
        if os.path.exists('/proc/vz/'): return 'Virtuozzo/OpenVZ'
        return ''


class Service(object):

    support_services = ['vpsmate', 'nginx', 'httpd',
                        'vsftpd', 'mysqld', 'redis', 'memcached', 'mongod', 'php-fpm',
                        'sendmail', 'sshd', 'iptables', 'crond', 'ntpd']

    pidnames = {
        'sendmail': ('sm-client', ),
    }

    @classmethod
    def status(self, service):
        initscript = '/etc/init.d/%s' % service
        if not os.path.exists(initscript):
            return None

        pidfile = '/var/run/%s.pid' % service
        if not os.path.exists(pidfile):
            p = glob.glob('/var/run/%s/*.pid' % service)
            if len(p)>0:
                pidfile = p[0]
            else:
                # some services have special pid filename
                if Service.pidnames.has_key(service):
                    for pidname in Service.pidnames[service]:
                        pidfile = '/var/run/%s.pid' % pidname
                        if os.path.exists(pidfile):
                            break
                        else:
                            pidfile = None
                else:
                    pidfile = None
        if not pidfile:
            # not always corrent, some services dead but the lock still exists
            ## some services don't have the pidfile
            #if os.path.exists('/var/lock/subsys/%s' % service):
            #    return 'running'

            # try execute pidof to find the pidfile
            p = subprocess.Popen(shlex.split('pidof -c -o %%PPID -x %s' % service), stdout=subprocess.PIPE, close_fds=True)
            pid = p.stdout.read().strip()
            p.wait()
            
            if not pid: return 'stopped'
        
        if pidfile:
            with file(pidfile) as f: pid = f.readline().strip()
            if not pid: return 'stopped'
            proc = '/proc/%s' % pid
            if not os.path.exists(proc):
                return 'stopped'
        
        return 'running'

    @classmethod
    def autostart_list(self):
        """Return a list of the autostart service name.
        """
        with open('/etc/inittab') as f:
            for line in f:
                if line.startswith('id:'):
                    startlevel = line.split(':')[1]
                    break
        rcpath = '/etc/rc.d/rc%s.d/' % startlevel
        services = [
            os.path.basename(os.readlink(filepath))
            for filepath in glob.glob('%s/S*' % rcpath)]
        return services
        


class Tool(object):

    @classmethod
    def supportfs(self):
        """Return a list of file system that system support.
        """
        support_list = []
        for fstype in ('ext2', 'ext3', 'ext4', 'xfs',
                       'jfs', 'reiserfs', 'btrfs'):
            if os.path.exists('/sbin/mkfs.%s' % fstype):
                support_list.append(fstype)
        support_list.append('swap')
        return support_list
    

if __name__ == '__main__':
    print
    print '* Hostname: %s' % Server.hostname()
    print

    print '* Server time: %s' % Server.datetime()
    print
    
    uptime = Server.uptime()
    print '* Uptime: %s' % uptime['up']
    print '* Idletime: %s' % uptime['idle']
    print '* Idlerate: %s' % uptime['idle_rate']
    print

    loadavg = Server.loadavg()
    print '* Last 1 min processes: %s' % loadavg['1min']
    print '* Last 15 min processes: %s' % loadavg['5min']
    print '* Last 15 min processes: %s' % loadavg['15min']
    print

    cpustat = Server.cpustat()
    tstat = cpustat['total']
    print '* Total CPU stats:'
    for k, v in tstat.iteritems():
        print '  %s: %d' % (k, v)
    for i, tstat in enumerate(cpustat['cpus']):
        print '* CPU-%d stats:' % i
        for k, v in tstat.iteritems():
            print '  %s: %d' % (k, v)
    print
    
    meminfo = Server.meminfo()
    print '* Memory total: %s' % meminfo['mem_total']
    print '* Memory used: %s (%s)' % (meminfo['mem_used'], meminfo['mem_used_rate'])
    print '* Memory free: %s (%s)' % (meminfo['mem_free'], meminfo['mem_free_rate'])
    print '* Memory buffers: %s' % meminfo['mem_buffers']
    print '* Memory cached: %s' % meminfo['mem_cached']
    print '* Swap total: %s' % meminfo['swap_total']
    print '* Swap used: %s (%s)' % (meminfo['swap_used'], meminfo['swap_used_rate'])
    print '* Swap free: %s (%s)' % (meminfo['swap_free'], meminfo['swap_free_rate'])
    print
    
    mounts = Server.mounts(True)
    for mount in mounts:
        print '* Mount device: %s' % mount['dev']
        if mount.has_key('major'): print '* Dev node: (%d, %d)' % (mount['major'], mount['minor'])
        print '* Mount point: %s' % mount['path']
        print '* Total space: %s' % mount['total']
        print '* Free space: %s' % mount['free']
        print '* Used space: %s (%s)' % (mount['used'], mount['used_rate'])
        print 
    
    netifaces = Server.netifaces()
    for netiface in netifaces:
        print '* Interface name: %s' % netiface['name']
        print '* Interface status: %s' % netiface['status']
        print '* Link encap: %s' % netiface['encap']
        print '* IP address: %s' % netiface['ip']
        print '* Broadcast: %s' % netiface['bcast']
        print '* Network mask: %s' % netiface['mask']
        if netiface.has_key('gw'): print '* Default gateway: %s' % netiface['gw']
        print '* MAC address: %s' % netiface['mac']
        print '* Data receive: %s' % netiface['rx']
        print '* Data transmit: %s' % netiface['tx']
        print 

    nameservers = Server.nameservers()
    print '* Name servers:'
    for nameserver in nameservers:
        print '  %s' % nameserver
    print 

    distribution = Server.distribution()
    print '* Linux distribution: %s' % distribution
    print 

    uname = Server.uname()
    print '* Kernel name: %s' % uname['kernel_name']
    print '* Kernel release: %s' % uname['kernel_release']
    print '* Kernel version: %s' % uname['kernel_version']
    print '* Machine: %s' % uname['machine']
    print 

    cpuinfo = Server.cpuinfo()
    print '* CPU count: %d' % cpuinfo['cpu_count']
    print '* CPU cores: %d' % cpuinfo['core_count']
    for core in cpuinfo['cores']:
        print '* CPU core: %s (%s)' % (core['model'], core['bits'])
    print 

    diskinfo = Server.diskinfo()
    count = diskinfo['count']
    totalsize = diskinfo['totalsize']
    partitions = diskinfo['partitions']
    print '* %d disks detected, total size: %s' % (count, totalsize)
    print 
    for partition in partitions:
        print '* Partition name: %s (%d, %d)' % \
                (partition['name'], partition['major'], partition['minor'])
        if partition.has_key('vname'): print '  Volumn name: %s' % partition['vname']
        print '  Partition size: %s (%s free)' % (partition['size'], partition['unpartition'])
        if partition.has_key('uuid'): print '  Partition UUID: %s' % partition['uuid']
        if partition.has_key('fstype'): print '  Partition fstype: %s' % partition['fstype']
        print '  Partition is PV: %s' % partition['is_pv']
        print '  Partition is LV: %s' % partition['is_lv']
        print '  Partition is HW: %s' % partition['is_hw']
        if partition.has_key('mount'): print '  Mount point: %s' % partition['mount']
        if partition['is_hw']: print '  Partition count: %d' % partition['partcount']
        print 
        for subpartition in partition['partitions']:
            print '  - Subpartition name: %s (%d, %d)' % \
                    (subpartition['name'], subpartition['major'], subpartition['minor'])
            if subpartition.has_key('vname'): print '  - Volumn name: %s' % subpartition['vname']
            print '  - Subpartition size: %s' % subpartition['size']
            if subpartition.has_key('uuid'): print '  - Subpartition UUID: %s' % subpartition['uuid']
            if subpartition.has_key('fstype'): print '  - Subpartition fstype: %s' % subpartition['fstype']
            print '  - Subpartition is PV: %s' % subpartition['is_pv']
            print '  - Subpartition is LV: %s' % subpartition['is_lv']
            print '  - Subpartition is HW: %s' % subpartition['is_hw']
            if subpartition.has_key('mount'): print '  - Mount point: %s' % subpartition['mount']
            if subpartition['is_hw']: print '  - Subpartition count: %d' % subpartition['partcount']
            print 
        print 

    print '* LVM partitions:'
    for partition in diskinfo['lvm']['partitions']:
        print '  - Partition name: %s (%d, %d)' % \
                (partition['name'], partition['major'], partition['minor'])
        if partition.has_key('vname'): print '  - Volumn name: %s' % partition['vname']
        print '  - Partition size: %s' % partition['size']
        if partition.has_key('uuid'): print '  - Partition UUID: %s' % partition['uuid']
        if partition.has_key('fstype'): print '  - Partition fstype: %s' % partition['fstype']
        print '  - Partition is PV: %s' % partition['is_pv']
        print '  - Partition is LV: %s' % partition['is_lv']
        print '  - Partition is HW: %s' % partition['is_hw']
        if partition.has_key('mount'): print '  - Mount point: %s' % partition['mount']
        if partition['is_hw']: print '  - Partition count: %d' % partition['partcount']
        print 
    
    autostart_services = Service.autostart_list()
    for service in Service.support_services:
        print '* Status of %s: %s (autostart: %s)' % (service, Service.status(service), str(service in autostart_services))
    print

    print '* Support file systems:'
    for fstype in Tool.supportfs():
        print '  - %s' % fstype
    print
    
    print '* Virtual Tech: %s' % Server.virt()
