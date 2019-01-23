#!/usr/bin/env python
# Copyright Daniel Roesler
# under MIT license, see LICENSE at https://github.com/diafygi/acme-tiny
import argparse
import base64
import binascii
import copy
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import textwrap
import time

try:
    from urllib.request import urlopen, Request  # Python 3
except ImportError:
    from urllib2 import urlopen, Request  # Python 2.7+


class ACME():

    def __init__(self, account_key, csr, acme_check_dir, contact=None):
        self.account_key = account_key
        self.csr = csr
        self.acme_check_dir = acme_check_dir
        self.directory = None
        self.acct_headers = None
        self.alg = 'RS256'
        self.jwk = None
        self.thumbprint = None
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(logging.INFO)
        # Contact details (e.g. mailto:aaa@bbb.com) for your account-key
        self.contact = contact # 'a client of the Intranet Control Panel'
        # self.ca = "https://acme-v02.api.letsencrypt.org"
        # self.ca_directory = = "https://acme-v02.api.letsencrypt.org/directory"
        # dev
        self.ca = "https://acme-staging-v02.api.letsencrypt.org"
        # certificate authority directory url, default is Let's Encrypt
        self.ca_directory = "https://acme-staging-v02.api.letsencrypt.org/directory"

        self.init_api_url()
        self.init_account()
        self.registe_account()
        # self.get_domain()
        # self.create_new_order()

    def _cmd(self, cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        '''run external commands'''
        proc = subprocess.Popen(cmd_list, stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    def _b64(self, b):
        '''base64 encode for jose spec'''
        return base64.urlsafe_b64encode(b).decode('utf8').replace('=', '')

    def _request(self, url, data=None, err_msg='Error', depth=0):
        '''make request and automatically parse json response'''
        try:
            hd = {"Content-Type": "application/jose+json", "User-Agent": "inpanel"}
            res = urlopen(Request(url, data=data, headers=hd))
            res_data = res.read().decode("utf8")
            code = res.getcode()
            headers = res.headers
        except IOError as e:
            res_data = e.read().decode('utf8') if hasattr(e, 'read') else str(e)
            code, headers = getattr(e, 'code', None), {}
        try:
            res_data = json.loads(res_data)  # try to parse json results
        except ValueError:
            pass  # ignore json parsing errors
        if depth < 100 and code == 400 and res_data['type'] == 'urn:ietf:params:acme:error:badNonce':
            raise IndexError(res_data)  # allow 100 retrys for bad nonces
        if code not in [200, 201, 204]:
            raise ValueError("{0}:\nUrl: {1}\nData: {2}\nResponse Code: {3}\nResponse: {4}".format(
                err_msg, url, data, code, res_data))
        return res_data, code, headers

    def _s_request(self, url, payload, err_msg, depth=0):
        '''make signed requests'''
        payload64 = self._b64(json.dumps(payload).encode('utf8'))
        new_nonce = self._request(self.ca_new_nonce)[2]['Replay-Nonce']
        protected = {'url': url, 'alg': self.alg, "nonce": new_nonce}
        protected.update({"jwk": self.jwk} if self.acct_headers is None else { "kid": self.acct_headers['Location']})
        protected64 = self._b64(json.dumps(protected).encode('utf8'))
        protected_input = "{0}.{1}".format(protected64, payload64).encode('utf8')
        cmd = ["openssl", "dgst", "-sha256", "-sign", self.account_key]
        out = self._cmd(cmd, stdin=subprocess.PIPE, cmd_input=protected_input, err_msg="OpenSSL Error")
        data = json.dumps({"protected": protected64, "payload": payload64, "signature": self._b64(out)})
        try:
            return self._request(url, data=data.encode('utf8'), err_msg=err_msg, depth=depth)
        except IndexError:  # retry bad nonces (they raise IndexError)
            return self._s_request(url, payload, err_msg, depth=(depth + 1))

    # helper function - poll until complete
    def _poll_until_not(self, url, pending_statuses, err_msg):
        while True:
            result, _, _ = self._request(url, err_msg=err_msg)
            if result['status'] in pending_statuses:
                time.sleep(2)
                continue
            return result

    def init_api_url(self, ca_directory=None):
        # get the ACME directory of urls
        self.log.info('InPanel: Getting directory...')
        if ca_directory is None:
            ca_directory = self.ca_directory
        self.directory, _, _ = self._request(ca_directory, err_msg='get directory error')
        self.ca_new_account = self.directory['newAccount']
        self.ca_new_nonce = self.directory['newNonce']
        self.ca_new_order = self.directory['newOrder']
        self.ca_revoke_cert = self.directory['revokeCert']
        self.ca_key_change = self.directory['keyChange']
        self.log.info('InPanel: Directory found!')

    def init_account(self, account_key=None):
        # parse account key to get public key
        self.log.info("InPanel: Account key parsing...")
        if account_key is None:
            account_key = self.account_key
        if not os.path.exists(account_key) or not os.path.isfile(account_key):
            return None
        cmd = ['openssl', 'rsa', '-in', account_key, '-noout', '-text']
        out = self._cmd(cmd, err_msg='OpenSSL Error')
        pub_pattern = r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)"
        pub_hex, pub_exp = re.search(pub_pattern, out.decode('utf8'), re.MULTILINE | re.DOTALL).groups()
        pub_exp = "{0:x}".format(int(pub_exp))
        pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
        self.jwk = {
            'e': self._b64(binascii.unhexlify(pub_exp.encode('utf-8'))),
            'kty': 'RSA',
            'n': self._b64(binascii.unhexlify(re.sub(r"(\s|:)", '', pub_hex).encode('utf-8'))),
        }
        acc_key_json = json.dumps(self.jwk, sort_keys=True, separators=(',', ':'))
        self.thumbprint = self._b64(hashlib.sha256(acc_key_json.encode('utf8')).digest())
        # print('thumbprint', self.thumbprint)

    def registe_account(self, contact=None):
        # create account, update contact details (if any), and set the global key identifier
        self.log.info('InPanel: Account registering...')
        reg_payload = {'termsOfServiceAgreed': True}
        account, code, self.acct_headers = self._s_request(
            self.ca_new_account, reg_payload, 'Error registering')
        self.log.info('InPanel: Account registered !' if code == 201 else 'InPanel: Account Already registered !')
        print(self.acct_headers)
        if contact is None:
            contact = self.contact
        if contact is not None:
            url = self.acct_headers['Location']
            payload = {'contact': contact}
            account, _, _ = self._s_request(url, payload, 'Error updating contact details')
            print(account)
            self.log.info("InPanel: Updated contact details:\n{0}".format("\n".join(account['contact'])))

    def get_domain(self):
        # find domains
        self.log.info('InPanel: Parsing CSR...')
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
        self.log.info("InPanel: Found domains: {0}".format(", ".join(domains)))

    def create_new_order(self, domains, disable_check=False):
        '''create a new order
        disable_check: disable checking if the challenge file is hosted correctly before telling the CA
        '''
        self.log.info("InPanel: Creating new order...")
        order_payload = {"identifiers": [{"type": "dns", "value": d} for d in domains]}
        order, _, order_headers = self._s_request(
            self.ca_new_order, order_payload, "Error creating new order")
        self.log.info("InPanel: Order created!")

        # get the authorizations that need to be completed
        for auth_url in order['authorizations']:
            authorization, _, _ = self._request(auth_url, err_msg='Error getting challenges')
            domain = authorization['identifier']['value']
            self.log.info("InPanel: Verifying {0}...".format(domain))

            # find the http-01 challenge and write the challenge file
            challenge = [c for c in authorization['challenges'] if c['type'] == "http-01"][0]
            token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
            keyauthorization = "{0}.{1}".format(token, self.thumbprint)
            wellknown_path = os.path.join(self.acme_check_dir, token)
            with open(wellknown_path, "w") as wellknown_file:
                wellknown_file.write(keyauthorization)

            # check that the file is in place
            try:
                wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(domain, token)
                assert(disable_check or self._request(wellknown_url)[0] == keyauthorization)
            except (AssertionError, ValueError) as e:
                os.remove(wellknown_path)
                raise ValueError("Wrote file to {0}, but couldn't download {1}: {2}".format(
                    wellknown_path, wellknown_url, e))

            # say the challenge is done
            self._s_request(
                challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
            authorization = self._poll_until_not(
                auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
            if authorization['status'] != "valid":
                raise ValueError(
                    "Challenge did not pass for {0}: {1}".format(domain, authorization))
            self.log.info("InPanel: domain {0} verified!".format(domain))

        # finalize the order with the csr
        self.log.info("InPanel: Signing certificate...")
        csr_der = self._cmd(["openssl", "req", "-in", self.csr, "-outform", "DER"], err_msg="DER Export Error")
        self._s_request(order['finalize'], {"csr": self._b64(csr_der)}, "Error finalizing order")

        # poll the order to monitor when it's done
        order = self._poll_until_not(order_headers['Location'], [
                                     "pending", "processing"], "Error checking order status")
        if order['status'] != "valid":
            raise ValueError("Order failed: {0}".format(order))
        self.download_certificate(order['certificate'])

    def download_certificate(self, certificate):
        # download the certificate
        certificate_pem, _, _ = self._request(certificate, err_msg="Certificate download failed")
        self.log.info("InPanel: Certificate signed!")
        return certificate_pem

    def revoke_certificate(self, crt):
        print(crt)


# def main(argv=None):
    # parser = argparse.ArgumentParser(
    #     formatter_class=argparse.RawDescriptionHelpFormatter,
    #     description=textwrap.dedent("""\
    #         This script automates the process of getting a signed TLS certificate from Let's Encrypt using
    #         the ACME protocol. It will need to be run on your server and have access to your private
    #         account key, so PLEASE READ THROUGH IT! It's only ~200 lines, so it won't take long.

    #         Example Usage:
    #         python acme_tiny.py --account-key ./account.key --csr ./domain.csr --acme-dir /usr/share/nginx/html/.well-known/acme-challenge/ > signed_chain.crt

    #         Example Crontab Renewal (once per month):
    #         0 0 1 * * python /path/to/acme_tiny.py --account-key /path/to/account.key --csr /path/to/domain.csr --acme-dir /usr/share/nginx/html/.well-known/acme-challenge/ > /path/to/signed_chain.crt 2>> /var/log/acme_tiny.log
    #         """)
    # )
    # parser.add_argument("--account-key", required=True,
    #                     help="path to your Let's Encrypt account private key")
    # parser.add_argument("--csr", required=True,
    #                     help="path to your certificate signing request")
    # parser.add_argument("--acme-dir", required=True,
    #                     help="path to the .well-known/acme-challenge/ directory")
    # parser.add_argument("--quiet", action="store_const",
    #                     const=logging.ERROR, help="suppress output except for errors")
    # parser.add_argument("--disable-check", default=False, action="store_true", help="disable checking if the challenge file is hosted correctly before telling the CA")
    # parser.add_argument("--directory-url", default=DEFAULT_DIRECTORY_URL, help="certificate authority directory url, default is Let's Encrypt")
    # parser.add_argument("--ca", default=DEFAULT_CA, help="DEPRECATED! USE --directory-url INSTEAD!")
    # parser.add_argument("--contact", metavar="CONTACT", default=None, nargs="*", help="Contact details (e.g. mailto:aaa@bbb.com) for your account-key")

    # args = parser.parse_args(argv)
    # LOGGER.setLevel(args.quiet or LOGGER.level)
    # signed_crt = acme_get_crt(args.account_key, args.csr, args.acme_check_dir, log=LOGGER, CA=args.ca,
    #                           disable_check=args.disable_check, ca_directory=args.ca_directory, contact=args.contact)
    # sys.stdout.write(signed_crt)


if __name__ == "__main__":  # pragma: no cover
    account_key = '/Users/douzhenjiang/Projects/intranet-panel/certificate/account.key'
    csr = 'adsf'
    acme_check_dir = 'af'
    aaa = ACME(account_key, csr, acme_check_dir)

