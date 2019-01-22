# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# Intranet is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Module for certificate configuration management."""

import os
import subprocess

from lib.acme import get_crt as get_acme_crt


class Certificate():

    def __init__(self):
        # self.path_current = os.path.dirname(os.path.realpath(__file__))
        self.path_home = '/usr/local/intranet/data/certificate/'
        self.path_crts = os.path.join(self.path_home, 'crts')
        self.key_size = '4096'
        self.account_key = os.path.join(self.path_home, 'account.key')

        if not os.path.exists(self.path_crts):
            os.makedirs(self.path_crts)

        self.init_acme_account()

    def _cmd(self, cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        out = out if out else err
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out.decode('utf8')

    def _check_key(self, key):
        '''check the RSA key is ok'''
        if not os.path.exists(key):
            return {'code': -1, 'msg': 'key_not_found'}
        try:
            out = self._cmd(['openssl', 'rsa', '-in', key, '-check', '-noout'])
            if 'RSA key ok' in out:
                return {'code': 0, 'msg': 'key_ok', 'data': 'ok'}
            else:
                return {'code': 0, 'msg': 'key_broken'}
        except:
            return {'code': -1, 'msg': 'key_check_error'}

    def _check_csr(self, csr):
        '''verify the CSR is ok'''
        csr = csr if os.path.exists(csr) or os.path.isfile(
            csr) else self.path_crts + csr
        if not os.path.exists(csr):
            return {'code': -1, 'msg': 'csr_not_found'}
        try:
            # p = subprocess.Popen(['openssl', 'req', '-in', csr, '-verify', '-noout'],
            #         stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            # out = p.stdout.read()
            # msg = p.stderr.read()
            # out = out if out else msg
            # if p.wait() == 0:
            #     if 'verify OK' in out:
            #         return True
            #     else:
            #         return False
            # else:
            #     return None
            out = self._cmd(
                ['openssl', 'req', '-in', csr, '-verify', '-noout'])
            if 'verify OK' in out:
                return {'code': 0, 'msg': 'verify_success'}
            else:
                return {'code': -1, 'msg': 'verify_error'}
        except:
            return {'code': -1, 'msg': 'verify_error'}

    def _generate_private_key(self, file_key=None, forced=False):
        '''Generate private key'''
        if file_key == None or file_key == '':
            return {'code': -1, 'msg': 'need_key_name'}
        ckk = self._check_key(file_key)
        if ckk['code'] == 0 and ckk['data'] == 'ok' and forced == False:
            return {'code': -1, 'msg': 'key_exists'}
        try:
            cmd_ = ['openssl', 'genrsa', '-out', file_key, self.key_size]
            out = self._cmd(cmd_, err_msg='Generate private key error')
            if out is None:
                return {'code': -1, 'msg': 'key_generate_error'}
            else:
                return {'code': 0, 'msg': 'key_generate_success'}
        except:
            return {'code': -1, 'msg': 'key_generate_error'}

    def init_acme_account(self, file_key=None, forced=False):
        '''Create a Let's Encrypt account private key'''
        file_key = self.account_key if file_key == None or file_key == '' else file_key
        return self._generate_private_key(file_key=file_key, forced=forced)

    def create_domain_key(self, domain, forced=False):
        '''Create a domain private key'''
        key = os.path.join(self.path_crts, domain + '.key')
        return self._generate_private_key(file_key=key, forced=forced)

    def generate_domain_csr(self, domain=[], domain_key=None, forced=False):
        '''Generate a certificate signing request (CSR) for domains.'''
        # openssl genrsa 4096 > github.com.key
        if domain is None or len(domain) == 0:
            return {'code': -1, 'msg': 'domain_error'}
        g_domain = domain[0]
        if domain_key and os.path.isfile(domain_key):
            k = domain_key
        else:
            k = self.path_crts + g_domain + '.key'
        if not os.path.isfile(k):
            return {'code': -1, 'msg': 'key_not_found'}
        c = self.path_crts + g_domain + '.csr'
        if os.path.isfile(c) and forced == False:
            return {'code': -1, 'msg': 'csr_exists'}
        if len(domain) == 1:
            cmd_list = ['openssl', 'req', '-new', '-sha256',
                        '-key', k, '-subj', '/CN=' + g_domain]
            out = self._cmd(
                cmd_list, err_msg="Create certificate signing request Error")
            if out is None:
                return {'code': -1, 'msg': 'csr_create_error'}
            else:
                with open(c, 'w') as f:
                    f.write(out)
                return {'code': 0, 'msg': 'csr_create_success', 'data': out}
        if len(domain) > 1:
            sans = []
            for i in domain:
                sans.append('DNS:%s' % i)
            sans = ','.join(sans)
            # aa = 'openssl req -new -out effect.pub.csr -key effect.pub.key -config openssl.cnf'
            domain_sans = '/CN=%s/subjectAltName=%s' % (g_domain, sans)
            cmd_list = ['openssl', 'req', '-new',
                        '-sha256', '-key', k, '-subj', domain_sans]
            out = self._cmd(
                cmd_list, err_msg="Create certificate signing request Error")
            if out is None:
                return {'code': -1, 'msg': 'csr_create_error'}
            else:
                with open(c, 'w') as f:
                    f.write(out)
                return {'code': 0, 'msg': 'csr_create_success', 'data': out}

    def show_domain_csr(self, domain_csr=None, text=True, pubkey=False, subject=False):
        # domain_csr = self.path_crts + domain_csr
        if not domain_csr:
            return {'code': -1, 'msg': 'csr_not_found'}
        csr = domain_csr if os.path.exists(domain_csr) and os.path.isfile(
            domain_csr) else self.path_crts + domain_csr
        ckcsr = self._check_csr(csr)
        if not ckcsr['code'] == 0:
            return ckcsr
        try:
            cmd_ = ['openssl', 'req', '-in', csr]
            if text == True and pubkey is not True and subject is not True:
                cmd_.append('-text')
            if pubkey is True:
                cmd_.extend(['-noout', '-pubkey'])
            if subject is True:
                cmd_.extend(['-noout', '-subject'])
            out = self._cmd(cmd_, err_msg='Generate private key error')
            if out is None:
                return {'code': -1, 'msg': 'csr_read_error'}
            else:
                return {'code': 0, 'msg': 'csr_read_success', 'data': out}
        except:
            return {'code': -1, 'msg': 'csr_read_error'}

    def generate_domain_cert(self, host=''):
        '''getting a signed TLS certificate from Let's Encrypt'''
        if not host:
            return None
        acc = self.account_key
        csr = '%s%s.csr' % (self.path_crts, host)
        crt = '%s%s.crt' % (self.path_crts, host)
        ckdir = '/var/www/%s/.well-known/acme-challenge' % host
        print(acc, csr, crt, ckdir)
        if not os.path.exists(ckdir):
            os.makedirs(ckdir)
        signed_crt = get_acme_crt(acc, csr, ckdir)
        if signed_crt is not None:
            with open(crt, 'w') as f:
                f.write(signed_crt)

    def revoke_domain_cert(self, host=''):
        print(host)

    def get_keys_list(self):
        res = None
        path = os.path.abspath(self.path_crts)
        if not os.path.exists(path) or not os.path.isdir(path):
            return False
        items = sorted(os.listdir(path))
        res = []
        for i, item in enumerate(items):
            # print(os.path.splitext(item))
            itm = os.path.splitext(item)
            if os.path.splitext(item)[1] == '.key':
                res.append({
                    'domain': itm[0],
                    'ans': itm[0],
                    'ext': itm[1],
                    'id': 'ididid',
                    'size': self.key_size
                })
        return res

    def get_crts_list(self):
        res = None
        res = [{
            'domain': 'baokan.pub',
            'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
            'size': 2048
        }, {
            'domain': 'zhoubao.pub',
            'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
            'size': 2048
        }]
        return res

    def get_csrs_list(self):
        res = None
        res = [{
            'domain': 'baokan.pub',
            'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
            'size': 2048
        }, {
            'domain': 'zhoubao.pub',
            'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
            'size': 2048
        }]
        return res

    def get_host_list(self):
        res = None
        res = [{
            'domain': 'baokan.pub',
            'id': '9a6d6_7f1c1_e1fd1b154418d4d88d32153bec4b20ac',
            'size': 2048
        }, {
            'domain': 'zhoubao.pub',
            'id': '9a6d6_7f1c1_e1fd1bfgj418d4d45632153bec4b20ac',
            'size': 2048
        }]
        return res

    def get_config(self):
        return dict()


    def set_config(self):
        return dict()



if __name__ == "__main__":  # pragma: no cover
    acme = Certificate()
    # acme.init_acme_account()
    # print(acme.init_acme_account())
    # main(sys.argv[1:])
    for domain in ['baokan.pub', 'dougroup.com', 'effect.pub', 'zhoubao.pub', 'zhoukan.pub']:
        acme.create_domain_key(domain)
    # print(acme.create_domain_key('baokan.pub'))
    # print(acme.create_domain_key('dougroup.com'))
    # print(acme.create_domain_key('effect.pub'))
    # print(acme.create_domain_key('zhoubao.pub'))
    # print(acme.create_domain_key('zhoukan.pub'))
    # print(acme.generate_domain_csr(['baokan.pub'],forced=True))
    # print(acme.generate_domain_csr(['baokan.pub', 'www.baokan.pub'], forced=True))
    # print(acme.generate_domain_csr(['effect.pub', '*.effect.pub']))
    # print(acme._check_csr('effect.pub.csr'))
    # acme._check_csr('effect.pub.csr')

    print(acme.show_domain_csr('baokan.pub.csr', subject=True))
    # acme.show_domain_csr('effect.pub.csr')
    # acme.generate_domain_cert('baokan.pub')
