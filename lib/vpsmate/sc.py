#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

"""Package for reading and writing server configurations
"""

import os
import si
import shutil
from config import Config


def raw_loadconfig(filepath, return_sort=False, delimiter='=', quoter=' "\'', overwrite=True):
    """Read config from file.
    """
    if not os.path.exists(filepath): return None
    config = {}
    if return_sort: sortlist = []
    with open(filepath) as f:
        for line in f:
            pair = line.strip().split(delimiter)
            if len(pair) != 2: continue
            k, v = [x.strip(quoter) for x in pair]
            if return_sort: sortlist.append(k)
            if overwrite:
                config[k] = v
            else:
                if not config.has_key(k): config[k] = []
                config[k].append(v)
    if return_sort:
        return (config, sortlist)
    else:
        return config

def raw_saveconfig(filepath, config, sortlist=[], delimiter='=', quoter='"'):
    """Write config to file.
    """
    if not os.path.exists(filepath): return False
    lines = []

    # write the item in sortlist first
    if len(sortlist) > 0:
        for k in sortlist:
            if config.has_key(k):
                line = '%s="%s"\n' % (k, config[k])
                del config[k]
                lines.append(line)

    # then write the rest items
    for k,v in config.iteritems():
        if isinstance(v, list):
            for vv in v:
                line = '%s%s%s%s%s\n' % (k,delimiter,quoter,vv,quoter)
                lines.append(line)
        else:
            line = '%s%s%s%s%s\n' % (k,delimiter,quoter,v,quoter)
            lines.append(line)

    with open(filepath, 'w') as f: f.writelines(lines)
    return True

def loadconfig(filepath, keymap, delimiter='=', quoter=' "\''):
    """Load config from file and parse it to dict.
    """
    raw_config = raw_loadconfig(filepath)
    if raw_config == None: return None
    config = dict((keymap[k],v) for k,v in raw_config.iteritems() if keymap.has_key(k))
    return config

def saveconfig(filepath, keymap, config, delimiter='=', read_quoter=' "\'', write_quoter='"'):
    """Save config to file.
    """
    raw_config, sortlist = raw_loadconfig(filepath, return_sort=True, delimiter=delimiter, quoter=read_quoter)
    if raw_config == None: return False
    for k,v in config.iteritems():
        if keymap.has_key(k):
            raw_config[keymap[k]] = v
    return raw_saveconfig(filepath, raw_config, sortlist, delimiter=delimiter, quoter=write_quoter)

def readconfig(filepath, readfunc, **params):
    """Read config from file.
    """
    with open(filepath) as f:
        for line in f:
            rt = readfunc(line.strip(), **params)
            if rt != None:
                return rt

def writeconfig(filepath, readfunc, writefunc, **params):
    """Write config to file.
    """
    lines = []
    linemeet = False
    with open(filepath) as f:
        for line in f:
            rt = readfunc(line.strip(), **params)
            if rt != None:
                linemeet = True
                line = writefunc(line, **params)
                if line != None: lines.append(line+'\n')
            else:
                lines.append(line)

    # generate a new line if no line meet
    if not linemeet:
        line = writefunc(None, **params)
        if line != None: lines.append(line+'\n')
        
    with open(filepath, 'w') as f: f.writelines(lines)
    return True


class Server(object):

    @classmethod
    def ifconfig(self, ifname, config=None):
        """Read or write single interface's config.
        
        Pass None to parameter config (as default) to read config,
        or pass a dict type to config to write config.
        """
        dist = si.Server.dist()
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
                cmap_reverse = dict((v,k) for k, v in cmap.iteritems())
                return saveconfig(cfile, cmap_reverse, config)
        else:
            return None

    @classmethod
    def ifconfigs(self):
        """Read config of all interfaces.
        """
        configs = {}
        ifaces = si.Server.netifaces()
        for iface in ifaces:
            ifname = iface['name']
            config = Server.ifconfig(ifname)
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
            nameservers = raw_loadconfig(nspath, delimiter=' ', overwrite=False)
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
            regions = Server.timezone_regions()
            for region in regions:
                regionpath = os.path.join(zonepath, region)
                for zonefile in os.listdir(regionpath):
                    if not os.path.isfile(os.path.join(regionpath, zonefile)): continue
                    timezones.append('%s/%s' % (region, zonefile))
        else:
            regionpath = os.path.join(zonepath, region)
            if not os.path.exists(regionpath): return []
            for zonefile in os.listdir(regionpath):
                if not os.path.isfile(os.path.join(regionpath, zonefile)): continue
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
            if timezone: return timezone

            # or else check the system config file
            dist = si.Server.dist()
            if dist['name'] in ('centos', 'redhat'):
                clockinfo = raw_loadconfig('/etc/sysconfig/clock')
                if clockinfo and clockinfo.has_key('ZONE'):
                    timezone = clockinfo['ZONE']
                    return timezone
            else:
                pass

            # or else find the file match /etc/localtime
            with open(tzpath) as f: tzdata = f.read()
            regions = Server.timezone_regions()
            for region in regions:
                regionpath = os.path.join(zonepath, region)
                for zonefile in os.listdir(regionpath):
                    if not os.path.isfile(os.path.join(regionpath, zonefile)): continue
                    with open(os.path.join(regionpath, zonefile)) as f:
                        if f.read() == tzdata:  # got it!
                            return '%s/%s' % (region, zonefile)
        else:
            # check and set the timezone
            timezonefile = os.path.join(zonepath, timezone)
            if not os.path.exists(timezonefile): return False
            try:
                shutil.copyfile(timezonefile, tzpath)
            except:
                return False

            # write timezone setting to config file
            return config.set('time', 'timezone', timezone)

    @classmethod 
    def _read_fstab(self, line, **params):
        if not line or line.startswith('#'): return
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
                dev = os.path.abspath(os.path.join(os.path.dirname(devlink), dev))
            except:
                pass
            dev = dev.replace('/dev/', '')
            if dev == params['devname']:
                return config
        elif dev.startswith('UUID='):
            uuid = dev.replace('UUID=', '')
            partinfo = si.Server.partinfo(devname=params['devname'])
            if partinfo['uuid'] == uuid:
                return config

    @classmethod 
    def _write_fstab(self, line, **params):
        config = params['config']
        if not config.has_key('mount') or config['mount'] == None: return None   # remove line
        if line == None: # new line
            return '/dev/%s %s                %s    defaults        1 2' %\
                    (params['devname'], config['mount'], config['fstype'])
        else: # update existing line
            fields = line.split()
            return '%s %s                %s    %s        %s %s' %\
                    (fields[0], config['mount'], 
                     config.has_key('fstype') and config['fstype'] or fields[2],
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
            return readconfig(cfgfile, Server._read_fstab, devname=devname)
        else:
            # write or remove config
            return writeconfig(cfgfile, Server._read_fstab, Server._write_fstab,
                               devname=devname, config=config)


if __name__ == '__main__':
    print
    
    config = Server.ifconfig('eth0')
    print '* Config of eth0:'
    if config.has_key('mac'): print '  HWADDR: %s' % config['mac']
    if config.has_key('ip'): print '  IPADDR: %s' % config['ip']
    if config.has_key('mask'): print '  NETMASK: %s' % config['mask']
    if config.has_key('gw'): print '  GATEWAY: %s' % config['gw']
    print

    print '* Write back config of eth0:'
    print '  Return: %s ' % str(Server.ifconfig('eth0', config))
    print
    
    configs = Server.ifconfigs()
    for ifname, config in configs.iteritems():
        print '* Config of %s:' % ifname
        if config.has_key('mac'): print '  HWADDR: %s' % config['mac']
        if config.has_key('ip'): print '  IPADDR: %s' % config['ip']
        if config.has_key('mask'): print '  NETMASK: %s' % config['mask']
        if config.has_key('gw'): print '  GATEWAY: %s' % config['gw']
        print
    
    nameservers = Server.nameservers()
    print '* Nameservers:'
    for nameserver in nameservers:
        print '  %s' % nameserver
    print

    print '* Write back nameservers:'
    print '  Return: %s ' % str(Server.nameservers(nameservers))
    print
    
    timezones = Server.timezone_list()
    print '* Timezone fullname list (first 10):'
    for i, timezone in enumerate(timezones):
        print '  %s' % timezone
        if i == 9: break
    print
    
    timezones = Server.timezone_list('Asia')
    print '* Timezone list in Asia (first 10):'
    for i, timezone in enumerate(timezones):
        print '  %s' % timezone
        if i == 9: break
    print
    
    inifile = os.path.join(os.path.dirname(__file__), '../../data/config.ini')
    timezone = Server.timezone(inifile)
    print '* Timezone: %s' % timezone
    print

    print '* Set timezone: %s' % timezone
    print '  Return: %s ' % str(Server.timezone(inifile, timezone))
    print
    
    config = Server.fstab('sda1')
    print '* Read sda1 fstab info:'
    print '  dev: %s' % config['dev']
    print '  mount: %s' % config['mount']
    print '  fstype: %s' % config['fstype']
    print
    
    print '* Delete sda1 from /etc/fstab'
    print '  Return: %s ' % str(Server.fstab('sda1', {}))
    print 
    
    print '* Write back to /etc/fstab'
    print '  Return: %s ' % str(Server.fstab('sda1', config))
    print 
