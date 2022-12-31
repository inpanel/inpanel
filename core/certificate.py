# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for certificate Management.'''

from os.path import basename, exists, isfile, join, splitext
from shutil import copy
from subprocess import PIPE, Popen

from mod_web import RequestHandler

from acme import ACME
from files import listfile


class Certificate():

    def __init__(self):
        # self.path_current = os.path.dirname(os.path.abspath(__file__))
        self.path_home = '/etc/inpanel/certs/'
        self.path_acc = join(self.path_home, 'client.key')
        self.path_crt = join(self.path_home, 'crt')
        self.path_key = join(self.path_home, 'key')
        self.path_csr = join(self.path_home, 'csr')
        self.key_size = '4096'
        self.acme = None

        if not exists(self.path_home):
            os.makedirs(self.path_home)
        if not exists(self.path_crt):
            os.makedirs(self.path_crt)
        if not exists(self.path_key):
            os.makedirs(self.path_key)
        if not exists(self.path_csr):
            os.makedirs(self.path_csr)

        self.init_account()

    def _cmd(self, cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = Popen(cmd_list, stdin=stdin, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(cmd_input)
        out = out if out else err
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out.decode('utf8')

    def _check_key(self, key):
        '''check the RSA key is ok'''
        if not exists(key):
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
        if not exists(csr) or not isfile(csr):
            csr = join(self.path_csr, csr)
        if not exists(csr):
            return {'code': -1, 'msg': 'csr_not_found'}
        try:
            # p = Popen(['openssl', 'req', '-in', csr, '-verify', '-noout'],
            #         stdout=PIPE, stderr=PIPE, close_fds=True)
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

    def init_account(self, file_key=None, forced=False):
        '''Create a Let's Encrypt account private key'''
        if file_key == None or file_key == '' or not file_key:
            file_key = self.path_acc
        return self._generate_private_key(file_key=file_key, forced=forced)

    def create_domain_key(self, domain, forced=False):
        '''Create a domain private key'''
        key = join(self.path_key, domain + '.key')
        return self._generate_private_key(file_key=key, forced=forced)

    def generate_domain_csr(self, domain=[], custom_key=None, forced=False):
        '''Generate a certificate signing request (CSR) for domains.'''
        # openssl genrsa 4096 > github.com.key
        if domain is None or len(domain) == 0:
            return {'code': -1, 'msg': 'domain_error'}
        if custom_key and isfile(custom_key):
            k = custom_key
        else:
            k = join(self.path_key, domain[0] + '.key')
        if not isfile(k):
            return {'code': -1, 'msg': 'key_not_found'}
        ckk = self._check_key(k)
        if ckk['code'] == 0 and ckk['msg'] == 'key_broken':
            return {'code': -1, 'msg': 'key_broken'}
        c = join(self.path_csr, domain[0] + '.csr')
        if isfile(c) and forced == False:
            return {'code': -1, 'msg': 'csr_exists'}

        subj = '/CN=%s' % domain[0]
        print(subj)
        cmd = ['openssl', 'req', '-new', '-sha256', '-key', k, '-subj', subj]
        conf_tmp = None
        if len(domain) > 1:
            san = ['DNS:%s' % domain[0]]
            for item in domain[1:]:
                san.append('DNS:%s' % item)
            san = 'subjectAltName=%s' % (','.join(san))
            opssl_conf = '/etc/pki/tls/openssl.cnf'
            conf_tmp = join(self.path_home, basename(opssl_conf))
            copy(opssl_conf, conf_tmp)
            with open(conf_tmp, 'a', encoding='utf-8') as f:
                f.writelines(['\n[SAN]', '\n%s' % san])
            # config = '<(cat %s <(printf "[SAN]\\n%s"))' % (opssl_conf, san)
            cmd.extend(['-reqexts', 'SAN', '-config', conf_tmp])
        out = self._cmd(cmd, err_msg="Create csr error")
        if conf_tmp is not None and exists(conf_tmp):
            os.remove(conf_tmp)
        if out is None:
            return {'code': -1, 'msg': 'csr_create_error'}
        else:
            with open(c, 'w', encoding='utf-8') as f:
                f.write(out)
            return {'code': 0, 'msg': 'csr_create_success', 'data': out}

    def show_domain_csr(self, domain_csr=None, text=True, pubkey=False, subject=False):
        if exists(domain_csr) and isfile(domain_csr):
            csr = domain_csr
        else:
            csr = join(self.path_csr, domain_csr)
        if not exists(csr):
            return {'code': -1, 'msg': 'csr_not_found'}

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

    def generate_domain_crt(self, domain):
        '''getting a signed TLS certificate from Let's Encrypt'''
        if domain is None:
            return None
        acc = self.path_acc
        csr = join(self.path_csr, domain + '.csr')
        crt = join(self.path_crt, domain + '.crt')
        ckdir = '/var/www/%s/.well-known/acme-challenge' % domain
        print(acc, csr, crt, ckdir)
        if not exists(ckdir):
            os.makedirs(ckdir)
        self.acme = ACME(acc, csr, ckdir)
        signed_crt = self.acme.get_certificate()
        if signed_crt is not None:
            with open(crt, 'w', encoding='utf-8') as f:
                f.write(signed_crt)

    def revoke_domain_cert(self, domain=''):
        print(domain)

    def get_keys_list(self):
        items = listfile(self.path_key)
        if items is None:
            return None
        res = []
        for i, item in enumerate(items):
            itm = splitext(item)
            if splitext(item)[1] == '.key':
                res.append({
                    'name': item,
                    'ans': itm[0],
                    'ext': itm[1],
                    'id': 'ididid',
                    'size': self.key_size
                })
        return res

    def get_crts_list(self):
        items = listfile(self.path_crt)
        if items is None:
            return None
        res = []
        for i, item in enumerate(items):
            itm = splitext(item)
            if splitext(item)[1] == '.crt':
                res.append({
                    'name': item,
                    'ans': itm[0],
                    'ext': itm[1],
                    'id': 'ididid',
                    'size': self.key_size
                })
        return res

    def get_csrs_list(self):
        items = listfile(self.path_csr)
        if items is None:
            return None
        res = []
        for i, item in enumerate(items):
            itm = splitext(item)
            if splitext(item)[1] == '.csr':
                res.append({
                    'name': item,
                    'ext': itm[1],
                    'created': '2019-01-24',
                    'size': self.key_size,
                    'description': 'è¯´æ˜Ž'
                })
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


class WebRequestSSLTLS(RequestHandler):
    """Handler for SSL/TLS setting.
    """
    def get(self, sec, x=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 SSL ！'})
            return
        certs = Certificate()
        if sec == 'keys':
            keys_list = certs.get_keys_list()
            if keys_list is None:
                self.write({'code': -1, 'msg': '获取私钥失败！'})
            else:
                self.write({'code': 0, 'msg': '获取私钥成功！', 'list': keys_list})
        elif sec == 'crts':
            crts_list = certs.get_crts_list()
            if crts_list is None:
                self.write({'code': -1, 'msg': '获取证书失败！'})
            else:
                self.write({'code': 0, 'msg': '获取证书成功！', 'list': crts_list})
        elif sec == 'csrs':
            csrs_list = certs.get_csrs_list()
            if csrs_list is None:
                self.write({'code': -1, 'msg': '获取证书签名请求失败！'})
            else:
                self.write({'code': 0, 'msg': '获取证书签名请求成功！', 'list': csrs_list})
        elif sec == 'host':
            host_list = certs.get_host_list()
            if host_list is None:
                self.write({'code': -1, 'msg': '获取站点失败！'})
            else:
                self.write({'code': 0, 'msg': '获取站点成功！', 'list': host_list})
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, sec, x=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 SSL ！'})
            return
        action = self.get_argument('action', '')
        certs = Certificate()

        if sec == 'keys':
            if action == 'add_domain_keys':
                # this is a test
                # for domain in ['baokan.pub', 'dougroup.com', 'effect.pub', 'zhoubao.pub', 'zhoukan.pub']:
                #     certs.create_domain_key(domain)
                self.write({'code': 0, 'msg': u'创建测试私钥成功！(正在测试的功能)'})


if __name__ == "__main__":  # pragma: no cover
    acme = Certificate()
    # acme.init_account(forced=True)
    # print(acme.init_account())
    # main(sys.argv[1:])
    # for domain in ['baokan.pub', 'dougroup.com', 'effect.pub', 'zhoubao.pub', 'zhoukan.pub']:
    #     acme.create_domain_key(domain)
    # print(acme.create_domain_key('baokan.pub'))
    # print(acme.create_domain_key('dougroup.com'))
    # print(acme.create_domain_key('effect.pub'))
    # print(acme.create_domain_key('zhoubao.pub'))
    # print(acme.create_domain_key('zhoukan.pub'))
    # print(acme.generate_domain_csr(['baokan.pub']))
    # print(acme.generate_domain_csr(['baokan.pub', 'www.baokan.pub'], forced=True))
    # print(acme.generate_domain_csr(['effect.pub', '*.effect.pub']))
    # print(acme._check_csr('effect.pub.csr'))
    # acme._check_csr('effect.pub.csr')

    # print(acme.show_domain_csr('baokan.pub.csr', subject=True))
    # acme.show_domain_csr('effect.pub.csr')
    # print(acme.create_domain_key('baokan.pub'))
    # print(acme.create_domain_key('baokan.pub', forced=True))
    # print(acme.generate_domain_csr(['baokan.pub'], forced=True))
    # print(acme.generate_domain_csr(['baokan.pub', 'www.baokan.pub', 'abc.baokan.pub'], forced=True))
    acme.generate_domain_crt('baokan.pub')
