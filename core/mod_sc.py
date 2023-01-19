# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for reading and writing server configurations'''


from hashlib import md5
from os import listdir
from os.path import abspath, dirname, exists, isfile, join
from platform import uname
from shutil import copyfile

from base import kernel_name, os_name
from configloader import (loadconfig, raw_loadconfig, raw_saveconfig,
                          readconfig, saveconfig, writeconfig)
from mod_shell import run
from server import ServerInfo


def get_hostname():
    '''Get Hostname'''
    node = uname().node
    if exists('/etc/hostname'):
        with open('/etc/hostname', 'r', encoding='utf-8') as f:
            line = f.readlines(1)
            hostname = line[0].replace('\\n', '').replace('\\l', '').strip()
            if hostname and hostname is not node:
                return hostname
    return node


def set_hostname(hostname=None):
    '''Change Hostname'''
    if hostname is None:
        return False

    hostname = hostname.strip().replace(' ', '').replace('\n', '')
    if hostname == '':
        return False

    if os_name == 'CentOS':
        # change network, hosts, hostname
        if saveconfig('/etc/sysconfig/network', {'HOSTNAME': hostname}) and\
            raw_saveconfig('/etc/hosts', { '127.0.0.1': hostname, '::1': hostname }, delimiter=' ', quoter='') and\
            run(str('hostname %s' % hostname)) == 0:
            return True
        else:
            return False
    elif os_name == 'Ubuntu':
        try:
            # change hosts, hostname
            # TODO: Merge previous configurations
            with open('/etc/hostname', 'w', encoding='utf-8') as f:
                f.write(hostname)
            newdata = {
                '127.0.0.1': ['localhost', hostname],
                '::1': ['localhost', hostname]
            }
            if run('hostnamectl set-hostname %s' % hostname) == 0 and\
                raw_saveconfig('/etc/hosts', newdata, delimiter=' ', quoter=''):
                return True
            else:
                return False
        except:
            return False
    else:
        return False


def get_nameservers():
    """Read nameservers from config file.
    """

    if kernel_name in ('Linux', 'Darwin'):
        nspath = '/etc/resolv.conf'
        servers = raw_loadconfig(nspath, delimiter=' ', overwrite=False)
        if servers:
            return servers['nameserver']
    elif kernel_name == 'Windows':
        pass
    return []


def set_nameservers(nameservers=None):
    """Write nameservers to config file.
    Pass a dict type to config to write config.
    """
    if nameservers is None:
        return False

    nspath = '/etc/resolv.conf'
    data = { 'nameserver': nameservers }
    return raw_saveconfig(nspath, data, delimiter=' ', quoter='')


def get_timezone_regions():
    """Return all the timezone regions.
    """
    return ('Africa', 'America', 'Antarctica', 'Arctic', 'Asia',
            'Atlantic', 'Australia', 'Europe', 'Indian', 'Pacific', 'Etc')


def get_timezone_list(region=None):
    """Return timezone list.

    Pass None to parameter region to get the full timezone name, such as:
        Asia/Shanghai
        Asia/Chongqing
    Or else only the city name would be returned.
    """
    zonepath = '/usr/share/zoneinfo'
    timezones = []
    if region is None:
        regions = get_timezone_regions()
        for region in regions:
            regionpath = join(zonepath, region)
            for zonefile in listdir(regionpath):
                if not isfile(join(regionpath, zonefile)):
                    continue
                timezones.append('%s/%s' % (region, zonefile))
    else:
        regionpath = join(zonepath, region)
        if not exists(regionpath):
            return []
        for zonefile in listdir(regionpath):
            if not isfile(join(regionpath, zonefile)):
                continue
            timezones.append(zonefile)

    return sorted(timezones)


def get_timezone(config):
    """Get system timezone.

    Pass None to parameter config (as default) to get timezone.
    """
    tzpath = '/etc/localtime'
    zonepath = '/usr/share/zoneinfo'

    # firstly read from config file
    timezone = ''
    if not config.has_section('time'):
        config.add_section('time')

    if config.has_option('time', 'timezone'):
        timezone = config.get('time', 'timezone')
        if timezone:
            return timezone

    # or else check the system config file
    dist = ServerInfo.dist()
    if dist['name'] in ('centos', 'redhat'):
        clockinfo = raw_loadconfig('/etc/sysconfig/clock')
        if clockinfo and 'ZONE' in clockinfo:
            timezone = clockinfo['ZONE']
            return timezone
    else:
        pass

    # or else find the file match /etc/localtime
    with open(tzpath, 'rb') as f:
        tzdata = md5(f.read()).hexdigest()
    regions = get_timezone_regions()
    for region in regions:
        regionpath = join(zonepath, region)
        for zonefile in listdir(regionpath):
            if not isfile(join(regionpath, zonefile)):
                continue
            with open(join(regionpath, zonefile), 'rb') as f:
                if md5(f.read()).hexdigest() == tzdata:  # got it!
                    return '%s/%s' % (region, zonefile)

def set_timezone(config, timezone=None):
    """Set system timezone.

    Pass timezone full name like 'Asia/Shanghai' to set timezone.
    """
    if timezone is None:
        return False
    # check and set the timezone
    tzpath = '/etc/localtime'
    zonepath = '/usr/share/zoneinfo'

    timezonefile = join(zonepath, timezone)
    if not exists(timezonefile):
        return False
    try:
        copyfile(timezonefile, tzpath)
    except:
        return False

    # write timezone setting to config file
    return config.set('time', 'timezone', timezone)


class ServerSet(object):

    @classmethod
    def ifconfig(self, ifname, config=None):
        """Read or write single interface's config.

        Pass None to parameter config (as default) to read config,
        or pass a dict type to config to write config.
        """
        dist = ServerInfo.dist()
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
        else:
            return None

    @classmethod
    def ifconfigs(self):
        """Read config of all interfaces.
        """
        configs = {}
        ifaces = ServerInfo.netifaces()
        print('ifaces', ifaces)
        for iface in ifaces:
            ifname = iface['name']
            config = ServerSet.ifconfig(ifname)
            if config:
                configs[ifname] = config
        return configs

    @classmethod
    def _read_fstab(self, line, **params):
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
                dev = abspath(join(dirname(devlink), dev))
            except:
                pass
            dev = dev.replace('/dev/', '')
            if dev == params['devname']:
                return config
        elif dev.startswith('UUID='):
            uuid = dev.replace('UUID=', '')
            partinfo = ServerInfo.partinfo(devname=params['devname'])
            # partinfo = ServerInfo.partinfo(uuid=uuid, devname=params['devname'])
            if partinfo['uuid'] == uuid:
                return config

    @classmethod
    def _write_fstab(self, line, **params):
        config = params['config']
        if not 'mount' in config or config['mount'] is None:
            return None   # remove line
        if line is None:  # new line
            return '/dev/%s %s                %s    defaults        1 2' %\
                (params['devname'], config['mount'], config['fstype'])
        else:  # update existing line
            fields = line.split()
            return '%s %s                %s    %s        %s %s' %\
                (fields[0], config['mount'],
                 'fstype' in config and config['fstype'] or fields[2],
                 fields[3], fields[4], fields[5])

    @classmethod
    def fstab(self, devname, config=None):
        """Read or write config from /etc/fstab.

        Example:
        1. get config
        >>> config = fstab('sda')
        2. set config
        >>> config = {'mount': '/home', 'fstype': 'ext3'}
        >>> fstab(config)
        3. remove config
        >>> config = {'mount': None}
        >>> fstab(config)
        """
        cfgfile = '/etc/fstab'
        if config is None:
            # read config
            return readconfig(cfgfile, ServerSet._read_fstab, devname=devname)
        else:
            # write or remove config
            return writeconfig(cfgfile, ServerSet._read_fstab, ServerSet._write_fstab,
                               devname=devname, config=config)


if __name__ == '__main__':
    from .mod_config import load_config
    print('')

    config = ServerSet.ifconfig('eth0')
    print('* Config of eth0:')
    if 'mac' in config:
        print('  HWADDR: %s' % config['mac'])
    if 'ip' in config:
        print('  IPADDR: %s' % config['ip'])
    if 'mask' in config:
        print('  NETMASK: %s' % config['mask'])
    if 'gw' in config:
        print('  GATEWAY: %s' % config['gw'])
    print('')

    print('* Write back config of eth0:')
    print('  Return: %s ' % str(ServerSet.ifconfig('eth0', config)))
    print('')

    configs = ServerSet.ifconfigs()
    for ifname, config in configs.items():
        print('* Config of %s:' % ifname)
        if 'mac' in config:
            print('  HWADDR: %s' % config['mac'])
        if 'ip' in config:
            print('  IPADDR: %s' % config['ip'])
        if 'mask' in config:
            print('  NETMASK: %s' % config['mask'])
        if 'gw' in config:
            print('  GATEWAY: %s' % config['gw'])
        print('')

    nameservers = get_nameservers()
    print('* Nameservers:')
    for nameserver in nameservers:
        print('  %s' % nameserver)
    print('')

    print('* Write back nameservers:')
    print('  Return: %s ' % str(set_nameservers(nameservers)))
    print('')

    timezones = get_timezone_list()
    print('* Timezone fullname list (first 10):')
    for i, timezone in enumerate(timezones):
        print('  %s' % timezone)
        if i == 9:
            break
    print('')

    timezones = get_timezone_list('Asia')
    print('* Timezone list in Asia (first 10):')
    for i, timezone in enumerate(timezones):
        print('  %s' % timezone)
        if i == 9:
            break
    print('')

    inifile = load_config()
    timezone = ServerSet.timezone(inifile)
    print('* Timezone: %s' % timezone)
    print('')

    print('* Set timezone: %s' % timezone)
    print('  Return: %s ' % str(ServerSet.timezone(inifile, timezone)))
    print('')

    config = ServerSet.fstab('sda1')
    print('* Read sda1 fstab info:')
    print('  dev: %s' % config['dev'])
    print('  mount: %s' % config['mount'])
    print('  fstype: %s' % config['fstype'])
    print('')

    print('* Delete sda1 from /etc/fstab')
    print('  Return: %s ' % str(ServerSet.fstab('sda1', {})))
    print('')

    print('* Write back to /etc/fstab')
    print('  Return: %s ' % str(ServerSet.fstab('sda1', config)))
    print('')
