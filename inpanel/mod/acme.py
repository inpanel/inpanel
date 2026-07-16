# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''通过 ACME 协议从 Let's Encrypt 获取已签名 TLS 证书的模块。'''

import re
from base64 import urlsafe_b64encode
from binascii import unhexlify
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import os
from subprocess import PIPE, STDOUT, Popen
from time import sleep

try:
    from urllib.request import urlopen, Request  # Python 3
except ImportError:
    from urllib2 import urlopen, Request  # Python 2


class ACME():

    # 参考: https://github.com/diafygi/acme-tiny，MIT 许可证，作者: Daniel Roesler
    def __init__(self, account_key, csr, acme_check_dir, contact=None):
        self.account_key = account_key
        self.csr = csr
        self.acme_check_dir = acme_check_dir
        self.directory = None
        self.acct_headers = None
        self.alg = 'RS256'
        self.jwk = None
        self.thumbprint = None
        self.certificate = None

        # 账号的联系方式（例如 mailto:aaa@bbb.com）
        self.contact = contact
        # self.ca = "https://acme-v02.api.letsencrypt.org"
        # self.ca_directory = "https://acme-v02.api.letsencrypt.org/directory"
        # 开发环境
        self.ca = "https://acme-staging-v02.api.letsencrypt.org"
        # 证书颁发机构目录 URL，默认为 Let's Encrypt
        self.ca_directory = "https://acme-staging-v02.api.letsencrypt.org/directory"

        self.init_api_url()
        self.init_account()
        self.registe_account()
        self.parse_csr(order=True)
        # self.create_new_order()

    def _cmd(self, cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        '''执行外部命令'''
        proc = Popen(cmd_list, stdin=stdin, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    def _b64(self, b):
        '''JOSE 规范的 base64 编码'''
        return urlsafe_b64encode(b).decode('utf8').replace('=', '')

    def _request(self, url, data=None, err_msg='Error', depth=0):
        '''发送请求并自动解析 JSON 响应'''
        try:
            hd = {
                "Content-Type": "application/jose+json",
                "User-Agent": "inpanel"
            }
            res = urlopen(Request(url, data=data, headers=hd))
            res_data = res.read().decode('utf8')
            code = res.getcode()
            headers = res.headers
        except IOError as e:
            res_data = e.read().decode('utf8') if hasattr(e, 'read') else str(e)
            code, headers = getattr(e, 'code', None), {}
        try:
            res_data = loads(res_data)  # try to parse json results
        except ValueError:
            pass  # ignore json parsing errors
        if depth < 100 and code == 400 and res_data['type'] == 'urn:ietf:params:acme:error:badNonce':
            raise IndexError(res_data)  # 允许对无效 nonce 重试 100 次
        if code not in [200, 201, 204]:
            raise ValueError("{0}:\nUrl: {1}\nData: {2}\nResponse Code: {3}\nResponse: {4}".format(
                err_msg, url, data, code, res_data))
        return res_data, code, headers

    def _s_request(self, url, payload, err_msg, depth=0):
        '''发送签名请求'''
        payload64 = self._b64(dumps(payload).encode('utf8'))
        new_nonce = self._request(self.ca_new_nonce)[2]['Replay-Nonce']
        protected = {'url': url, 'alg': self.alg, "nonce": new_nonce}
        protected.update({"jwk": self.jwk} if self.acct_headers is None else {"kid": self.acct_headers['Location']})
        protected64 = self._b64(dumps(protected).encode('utf8'))
        protected_input = "{0}.{1}".format(protected64, payload64).encode('utf8')
        cmd = ['openssl', 'dgst', '-sha256', '-sign', self.account_key]
        out = self._cmd(cmd, stdin=PIPE, cmd_input=protected_input, err_msg='OpenSSL Error')
        data = dumps({
            'protected': protected64,
            'payload': payload64,
            'signature': self._b64(out)
        })
        try:
            return self._request(url, data=data.encode('utf8'), err_msg=err_msg, depth=depth)
        except IndexError:  # 重试无效 nonce（无效 nonce 会抛出 IndexError）
            return self._s_request(url, payload, err_msg, depth=(depth + 1))

    # 辅助函数 - 轮询直到完成
    def _poll_until_not(self, url, pending_statuses, err_msg):
        while True:
            result, _, _ = self._request(url, err_msg=err_msg)
            if result['status'] in pending_statuses:
                sleep(2)
                continue
            return result

    def init_api_url(self, ca_directory=None):
        # 获取 ACME 目录 URL
        print('API directory getting...')
        ca = ca_directory
        if ca is None:
            ca = self.ca_directory
        ca_dir, _, _ = self._request(ca, err_msg='get directory error')
        self.ca_new_account = ca_dir['newAccount']
        self.ca_new_nonce = ca_dir['newNonce']
        self.ca_new_order = ca_dir['newOrder']
        self.ca_revoke_cert = ca_dir['revokeCert']
        self.ca_key_change = ca_dir['keyChange']
        self.directory = ca_dir
        print('API directory ready!')

    def init_account(self, account_key=None):
        # 解析账号密钥以获取公钥
        print('Account key parsing...')
        acc_key = account_key
        if acc_key is None:
            acc_key = self.account_key
        acc_key_path = Path(acc_key)
        if not acc_key_path.exists() or not acc_key_path.is_file():
            return None
        cmd = ['openssl', 'rsa', '-in', acc_key, '-noout', '-text']
        out = self._cmd(cmd, err_msg='openssl error')
        pub_pattern = r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)"
        pub_hex, pub_exp = re.search(pub_pattern, out.decode('utf8'), re.MULTILINE | re.DOTALL).groups()
        pub_exp = "{0:x}".format(int(pub_exp))
        pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
        self.jwk = {
            'e': self._b64(unhexlify(pub_exp.encode('utf-8'))),
            'kty': 'RSA',
            'n': self._b64(unhexlify(re.sub(r"(\s|:)", '', pub_hex).encode('utf-8'))),
        }
        acc_key_json = dumps(self.jwk, sort_keys=True, separators=(',', ':'))
        self.thumbprint = self._b64(sha256(acc_key_json.encode('utf8')).digest())
        # print('thumbprint', self.thumbprint)
        print('Account key ready...')

    def registe_account(self, contact=None):
        # 创建账号，更新联系信息（如有），并设置全局密钥标识
        print('Account registration...')
        reg_payload = {'termsOfServiceAgreed': True}
        account, code, self.acct_headers = self._s_request(
            self.ca_new_account, reg_payload, 'Error registering')
        if code == 201:
            print('Account registration is successful !')
        else:
            print('Account is already registered!')
        # print(self.acct_headers)
        if contact is None:
            contact = self.contact
        if contact is not None:
            url = self.acct_headers['Location']
            payload = {'contact': contact}
            account, _, _ = self._s_request(url, payload, 'Error updating contact details')
            print(account)
            print("Updated contact details:\n{0}".format("\n".join(account['contact'])))

    def parse_csr(self, order=False):
        # 查找域名
        print('Domains CSR parsing...')
        cmd = ['openssl', 'req', '-in', self.csr, '-noout', '-text']
        out = self._cmd(cmd, err_msg="Error loading {0}".format(self.csr))
        domains = set([])
        common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
        if common_name is not None:
            domains.add(common_name.group(1))
        subject_alt_names = re.search(
            r"X509v3 Subject Alternative Name: \n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE | re.DOTALL)
        if subject_alt_names is not None:
            for san in subject_alt_names.group(1).split(", "):
                if san.startswith("DNS:"):
                    domains.add(san[4:])
        print("Found domains: {0}".format(", ".join(domains)))
        # print('domains', domains)
        if order == True:
            self.create_new_order(domains)

    def create_new_order(self, domains, disable_check=False):
        '''创建新订单
        disable_check: 在通知 CA 之前禁用挑战文件是否正确托管的检查
        '''
        print("Creating new order...")
        order_payload = {"identifiers": [
            {"type": "dns", "value": d} for d in domains]}
        order, _, order_headers = self._s_request(
            self.ca_new_order, order_payload, "Error creating new order")
        print("Order created!")

        # 获取需要完成的授权
        for auth_url in order['authorizations']:
            authorization, _, _ = self._request(auth_url, err_msg='Error getting challenges')
            domain = authorization['identifier']['value']
            print("Domain {0} Verifying...".format(domain))

            # 找到 http-01 挑战并写入挑战文件
            challenge = [c for c in authorization['challenges'] if c['type'] == "http-01"][0]
            token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
            key_auth = "{0}.{1}".format(token, self.thumbprint)
            wellknown_path = str(Path(self.acme_check_dir) / token)
            with open(wellknown_path, 'w', encoding='utf-8') as f:
                f.write(key_auth)

            # 检查 wellknown 文件是否在指定位置
            try:
                wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(domain, token)
                assert(disable_check or self._request(wellknown_url)[0] == key_auth)
            except (AssertionError, ValueError) as e:
                os.remove(wellknown_path)
                raise ValueError("Wrote file to {0}, but couldn't download {1}: {2}".format(
                    wellknown_path, wellknown_url, e))

            # 告知挑战已完成
            self._s_request(
                challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
            authorization = self._poll_until_not(auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
            if authorization['status'] != "valid":
                raise ValueError("Challenge did not pass for {0}: {1}".format(domain, authorization))
            print("Domain {0} verified!".format(domain))

        # 使用 CSR 完成订单
        print('Certificate signing...')
        csr_der = self._cmd(['openssl', 'req', '-in', self.csr, '-outform', 'DER'], err_msg='DER Export Error')
        self._s_request(order['finalize'], {'csr': self._b64(csr_der)}, 'Error finalizing order')
        # 轮询订单以监控其完成状态
        order = self._poll_until_not(order_headers['Location'], ['pending', 'processing'], 'Error checking order status')
        if order['status'] != 'valid':
            raise ValueError("Order failed: {0}".format(order))
        self.certificate = order['certificate']

    def get_certificate(self, certificate=None):
        # 下载证书
        crt_url = self.certificate if certificate is None else certificate
        if crt_url is None:
            return None
        certificate_pem, _, _ = self._request(crt_url, err_msg='Certificate download failed')
        print('Certificate signed!')
        return certificate_pem

    def ertificate_revoke(self, crt):
        '''吊销证书'''
        print(crt)
        print('Certificate revoked!')

    def certificate_renew(self, crt):
        '''续签证书'''
        print(crt)
        print('Certificate updated!')

# if __name__ == "__main__":
#     # import certificate
#     # cert = certificate.Certificate()
#     # # # cert.create_domain_key('test.com')
#     # cert.generate_domain_csr(['test.com', 'aaa.com'], forced=True)
#     account_key = '/Users/douzhenjiang/Projects/inpanel/data/certificate/client.key'
#     csr = '/Users/douzhenjiang/Projects/inpanel/data/certificate/csr/test.com.csr'
#     acme_check_dir = '/Users/douzhenjiang/Projects/inpanel/data'
#     # aaa = ACME(account_key, csr, acme_check_dir)

#     key = '/Users/douzhenjiang/Projects/inpanel/test/example_com.key'
#     csr = '/Users/douzhenjiang/Projects/inpanel/test/example_com.csr'
#     aaa = ACME(key, csr, acme_check_dir)

#     # C=CN, ST=Beijing, L=Beijing, O=Example Inc, OU=Network Dept,
#     # CN=example.com/subjectAltName=DNS.1=sub1.example.com,DNS.2=sub2.example.com,DNS.3=sub.another-example.com
#     # CN=test.com/subjectAltName=DNS:test.com,DNS:aaa.com
