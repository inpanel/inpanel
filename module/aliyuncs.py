# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2018, doudoudzj
# Copyright (c) 2012, ECSMate development team
# All rights reserved.
#
# ECSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''ECS SDK'''

import time
import hmac
import base64
import hashlib
import urllib
import json
import inspect
from random import random


class ECS(object):

    def __init__(self, AccessKeyID, AccessKeySecret, gateway='https://ecs.aliyuncs.com'):
        self.AccessKeyID = AccessKeyID
        self.AccessKeySecret = AccessKeySecret
        self.gateway = gateway

    @classmethod
    def _urlencode(self, string):
        return urllib.quote(string, '~')

    def _sign(self, params):
        paramstrings = []
        for k, v in sorted(params.items()):
            paramstrings.append('%s=%s' %
                                (ECS._urlencode(k), ECS._urlencode(v)))
        datastrings = [
            ECS._urlencode('GET'),
            ECS._urlencode('/'),
            ECS._urlencode('&'.join(paramstrings)),
        ]
        datastring = '&'.join(datastrings)
        signature = hmac.new(self.AccessKeySecret+'&',
                             datastring, hashlib.sha1).digest()
        return base64.b64encode(signature)

    def _http_get(self, params):
        url = self.gateway + '/?'

        sysparams = {
            'Format': 'JSON',
            'Version': '2012-09-13',
            'AccessKeyID': self.AccessKeyID,
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': time.strftime('%Y-%m-%dT%XZ'),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(random()).replace('0.', ''),
        }
        params.update(sysparams)
        params['Signature'] = self._sign(params)
        params = urllib.urlencode(params)

        url += params
        f = urllib.urlopen(url)
        data = f.read()
        f.close()

        return json.loads(data)

    def _parse_response(self, apiname, response):
        if response.has_key('Error'):
            respdata = response['Error']
            reqid = respdata['RequestID']
            del respdata['RequestID']
            return [False, respdata, reqid]
        else:
            respdata = response[apiname+'Response']
            return [True, respdata[apiname+'Result'], respdata['ResponseMetadata']['RequestID']]

    def _make_params(self, params):
        params = dict((k, str(v))
                      for k, v in params.items() if k != 'self' and v != None)
        params['Action'] = inspect.stack()[1][3]
        return params

    def _execute(self, params):
        response = self._http_get(params)
        return self._parse_response(params['Action'], response)

    def CreateInstance(self, RegionCode, DiskSize, InstanceType, GroupCode, ImageCode,
                       MaxBandwidthIn=None, MaxBandwidthOut=None, InstanceName=None, HostName=None,
                       Password=None, ZoneCode=None):
        params = self._make_params(locals())
        return self._execute(params)

    def StartInstance(self, InstanceName):
        params = self._make_params(locals())
        return self._execute(params)

    def StopInstance(self, InstanceName, ForceStop=None):
        params = self._make_params(locals())
        return self._execute(params)

    def RebootInstance(self, InstanceName, ForceStop=None):
        params = self._make_params(locals())
        return self._execute(params)

    def ResetInstance(self, InstanceName, ImageCode=None, DiskType=None):
        params = self._make_params(locals())
        return self._execute(params)

    def ResetPassword(self, InstanceName, NewPassword=None):
        params = self._make_params(locals())
        return self._execute(params)

    def DeleteInstance(self, InstanceName):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeInstanceStatus(self, RegionCode=None, ZoneCode=None, PageNumber=None, PageSize=None):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeInstanceAttribute(self, InstanceName):
        params = self._make_params(locals())
        return self._execute(params)

    def ModifyInstanceAttribute(self, InstanceName, InstanceType):
        params = self._make_params(locals())
        return self._execute(params)

    def ModifyBandwidth(self, InstanceName, MaxBandwidthOut, MaxBandwidthIn):
        params = self._make_params(locals())
        return self._execute(params)

    def ModifyHostName(self, InstanceName, HostName):
        params = self._make_params(locals())
        return self._execute(params)

    def CreateDisk(self, InstanceName, Size, SnapshotCode=None):
        params = self._make_params(locals())
        return self._execute(params)

    def DeleteDisk(self, InstanceName, DiskCode):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeDisks(self, InstanceName):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeImages(self, RegionCode=None, PageNumber=None, PageSize=None):
        params = self._make_params(locals())
        return self._execute(params)

    def AllocateAddress(self, InstanceName):
        params = self._make_params(locals())
        return self._execute(params)

    def ReleaseAddress(self, PublicIpAddress):
        params = self._make_params(locals())
        return self._execute(params)

    def CreateSecurityGroup(self, GroupCode, RegionCode, Description):
        params = self._make_params(locals())
        return self._execute(params)

    def AuthorizeSecurityGroup(self, GroupCode, RegionCode, IpProtocol, PortRange,
                               SourceGroupCode=None, SourceCidrIp=None, Policy=None, NicType=None, Priority=None):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeSecurityGroupAttribute(self, GroupCode, RegionCode, NicType=None):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeSecurityGroups(self, RegionCode, PageNumber=None, PageSize=None):
        params = self._make_params(locals())
        return self._execute(params)

    def ModifySecurityGroupAttribute(self, RegionCode, GroupCode, Adjust):
        params = self._make_params(locals())
        return self._execute(params)

    def RevokeSecurityGroup(self, GroupCode, RegionCode, IpProtocol, PortRange,
                            SourceGroupCode=None, SourceCidrIp=None, Policy=None, NicType=None):
        params = self._make_params(locals())
        return self._execute(params)

    def DeleteSecurityGroup(self, GroupCode, RegionCode):
        params = self._make_params(locals())
        return self._execute(params)

    def CreateSnapshot(self, InstanceName, DiskCode):
        params = self._make_params(locals())
        return self._execute(params)

    def DeleteSnapshot(self, DiskCode, InstanceName, SnapshotCode):
        params = self._make_params(locals())
        return self._execute(params)

    def CancelSnapshotRequest(self, InstanceName, SnapshotCode):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeSnapshots(self, InstanceName, DiskCode):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeSnapshotAttribute(self, RegionCode, SnapshotCode):
        params = self._make_params(locals())
        return self._execute(params)

    def RollbackSnapshot(self, InstanceName, DiskCode, SnapshotCode):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeRegions(self):
        params = self._make_params(locals())
        return self._execute(params)

    def DescribeZones(self, RegionCode):
        params = self._make_params(locals())
        return self._execute(params)


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    AccessKeyID = ''
    AccessKeySecret = ''

    ecs = ECS(AccessKeyID, AccessKeySecret)

    if 0:
        print '## Regions\n'
        regions = ecs.DescribeRegions()[1]
        pp.pprint(regions)
        print

        for region in regions['Regions']:
            print '## Zones in %s\n' % region['RegionCode']
            zones = ecs.DescribeZones(region['RegionCode'])
            if not zones[0]:
                pp.pprint(zones)
                continue
            zones = zones[1]
            pp.pprint(zones)
            print

            for zone in zones['Zones']:
                print '## Instances in %s\n' % zone['ZoneCode']
                instances = ecs.DescribeInstanceStatus(
                    region['RegionCode'], zone['ZoneCode'])[1]
                pp.pprint(instances)
                print

            print

    #pp.pprint(ecs.DescribeInstanceStatus(PageSize=10, PageNumber=1))
    #pp.pprint(ecs.DescribeInstanceStatus('cn-hangzhou-dg-a01', 'cn-hangzhou-dg101-a'))
    # pp.pprint(ecs.StartInstance('AY1209220917063704221'))
    # pp.pprint(ecs.StopInstance('AY1209220917063704221'))
    # pp.pprint(ecs.RebootInstance('AY1209220917063704221'))
    # pp.pprint(ecs.DescribeInstanceAttribute('AY1209220917063704221'))
    #pp.pprint(ecs.DescribeImages(PageSize=10, PageNumber=9))
    # pp.pprint(ecs.DescribeDisks('AY1209220917063704221'))
    #pp.pprint(ecs.DescribeSnapshots('AY1209220917063704221', '1006-60002839'))
