# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Package for reading and writing server configurations'''


import os
import shutil
from config import Config

from configloader import (loadconfig, raw_loadconfig, raw_saveconfig,
                          readconfig, saveconfig, writeconfig)
from server import ServerInfo
from shell import run as shell_run


class ServerSet(object):

    @classmethod
    def hostname(self, hostname=None):
        '''change hostname'''
        if hostname == None:
            return False
        else:
            hostname = hostname.replace(' ', '').replace('\n', '')
            # change network, hosts, hostname
            if saveconfig('/etc/sysconfig/network', {'HOSTNAME': hostname}) and\
                saveconfig('/etc/hosts', {'127.0.0.1': hostname, '::1': hostname}) and\
                shell_run(str('hostname %s' % hostname)) == 0:
                return True
            else:
                return False


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
            if config == None:
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
        for iface in ifaces:
            ifname = iface['name']
            config = ServerSet.ifconfig(ifname)
            if config:
                configs[ifname] = config
        return configs

    @classmethod
    def nameservers(self, nameservers=None):
        """Read or write nameservers to config file.

        Pass None to parameter config (as default) to read config,
        or pass a dict type to config to write config.
        """
        nspath = '/etc/resolv.conf'
        if nameservers == None:
            nameservers = raw_loadconfig(
                nspath, delimiter=' ', overwrite=False)
            if nameservers:
                return nameservers['nameserver']
            else:
                return []
        else:
            return raw_saveconfig(nspath,
                                  {'nameserver': nameservers},
                                  delimiter=' ', quoter='')

    @classmethod
    def timezone_regions(self):
        """Return all the timezone regions.
        """
        return ('Africa', 'America', 'Antarctica', 'Arctic', 'Asia',
                'Atlantic', 'Australia', 'Europe', 'Indian', 'Pacific', 'Etc')

    @classmethod
    def timezone_list(self, region=None):
        """Return timezone list.

        Pass None to parameter region to get the full timezone name, such as:
            Asia/Shanghai
            Asia/Chongqing
        Or else only the city name would be returned.
        """
        zonepath = '/usr/share/zoneinfo'
        timezones = []
        if region == None:
            regions = ServerSet.timezone_regions()
            for region in regions:
                regionpath = os.path.join(zonepath, region)
                for zonefile in os.listdir(regionpath):
                    if not os.path.isfile(os.path.join(regionpath, zonefile)):
                        continue
                    timezones.append('%s/%s' % (region, zonefile))
        else:
            regionpath = os.path.join(zonepath, region)
            if not os.path.exists(regionpath):
                return []
            for zonefile in os.listdir(regionpath):
                if not os.path.isfile(os.path.join(regionpath, zonefile)):
                    continue
                timezones.append(zonefile)
        return timezones

    @classmethod
    def timezone(self, inifile, timezone=None):
        """Get or set system timezone.

        Pass None to parameter config (as default) to get timezone,
        or pass timezone full name like 'Asia/Shanghai' to set timezone.
        """
        tzpath = '/etc/localtime'
        zonepath = '/usr/share/zoneinfo'

        config = Config(inifile)
        if not config.has_section('time'):
            config.add_section('time')

        if timezone == None:
            # firstly read from config file
            timezone = ''
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
            with open(tzpath) as f:
                tzdata = f.read()
            regions = ServerSet.timezone_regions()
            for region in regions:
                regionpath = os.path.join(zonepath, region)
                for zonefile in os.listdir(regionpath):
                    if not os.path.isfile(os.path.join(regionpath, zonefile)):
                        continue
                    with open(os.path.join(regionpath, zonefile)) as f:
                        if f.read() == tzdata:  # got it!
                            return '%s/%s' % (region, zonefile)
        else:
            # check and set the timezone
            timezonefile = os.path.join(zonepath, timezone)
            if not os.path.exists(timezonefile):
                return False
            try:
                shutil.copyfile(timezonefile, tzpath)
            except:
                return False

            # write timezone setting to config file
            return config.set('time', 'timezone', timezone)

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
                dev = os.path.abspath(os.path.join(
                    os.path.dirname(devlink), dev))
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
        if not 'mount' in config or config['mount'] == None:
            return None   # remove line
        if line == None:  # new line
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
        if config == None:
            # read config
            return readconfig(cfgfile, ServerSet._read_fstab, devname=devname)
        else:
            # write or remove config
            return writeconfig(cfgfile, ServerSet._read_fstab, ServerSet._write_fstab,
                               devname=devname, config=config)


if __name__ == '__main__':
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

    nameservers = ServerSet.nameservers()
    print('* Nameservers:')
    for nameserver in nameservers:
        print('  %s' % nameserver)
    print('')

    print('* Write back nameservers:')
    print('  Return: %s ' % str(ServerSet.nameservers(nameservers)))
    print('')

    timezones = ServerSet.timezone_list()
    print('* Timezone fullname list (first 10):')
    for i, timezone in enumerate(timezones):
        print('  %s' % timezone)
        if i == 9:
            break
    print('')

    timezones = ServerSet.timezone_list('Asia')
    print('* Timezone list in Asia (first 10):')
    for i, timezone in enumerate(timezones):
        print('  %s' % timezone)
        if i == 9:
            break
    print('')

    inifile = os.path.join(os.path.dirname(__file__), '../../data/config.ini')
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
