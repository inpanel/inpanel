#!/usr/bin/env python
# Python 2.6 need install python-argparse
# Copyright Daniel Roesler, under MIT license, see LICENSE at https://github.com/diafygi/acme-tiny

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
    import argparse  # Python 2.7+
    from urllib.request import urlopen, Request  # Python 3
except ImportError:
    from urllib2 import urlopen, Request  # Python 2

# DEPRECATED! USE DEFAULT_DIRECTORY_URL INSTEAD
DEFAULT_CA = "https://acme-v02.api.letsencrypt.org"
DEFAULT_DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


class Certs():

    def __init__(self):
        self.path_current = os.path.dirname(os.path.realpath(__file__))
        self.path_home = '/usr/local/acme/'
        self.path_crts = self.path_current + '/crts/'
        self.key_size = '4096'
        self.account_key = self.path_current + '/' + 'account.key'

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
        key = self.path_crts + domain + '.key'
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

    def singature(self, host=''):
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


def get_acme_crt(account_key, csr, acme_dir, log=LOGGER, CA=DEFAULT_CA, disable_check=False, directory_url=DEFAULT_DIRECTORY_URL, contact=None):
    directory, acct_headers, alg, jwk = None, None, None, None  # global variables

    # helper functions - base64 encode for jose spec
    def _b64(b):
        return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")

    # helper function - run external commands
    def _cmd(cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    # helper function - make request and automatically parse json response
    def _do_request(url, data=None, err_msg="Error", depth=0):
        try:
            resp = urlopen(Request(url, data=data, headers={
                           "Content-Type": "application/jose+json", "User-Agent": "acme-tiny"}))
            resp_data, code, headers = resp.read().decode(
                "utf8"), resp.getcode(), resp.headers
        except IOError as e:
            resp_data = e.read().decode("utf8") if hasattr(e, "read") else str(e)
            code, headers = getattr(e, "code", None), {}
        try:
            resp_data = json.loads(resp_data)  # try to parse json results
        except ValueError:
            pass  # ignore json parsing errors
        if depth < 100 and code == 400 and resp_data['type'] == "urn:ietf:params:acme:error:badNonce":
            raise IndexError(resp_data)  # allow 100 retrys for bad nonces
        if code not in [200, 201, 204]:
            raise ValueError("{0}:\nUrl: {1}\nData: {2}\nResponse Code: {3}\nResponse: {4}".format(
                err_msg, url, data, code, resp_data))
        return resp_data, code, headers

    # helper function - make signed requests
    def _send_signed_request(url, payload, err_msg, depth=0):
        payload64 = _b64(json.dumps(payload).encode('utf8'))
        new_nonce = _do_request(directory['newNonce'])[2]['Replay-Nonce']
        protected = {"url": url, "alg": alg, "nonce": new_nonce}
        protected.update({"jwk": jwk} if acct_headers is None else {
                         "kid": acct_headers['Location']})
        protected64 = _b64(json.dumps(protected).encode('utf8'))
        protected_input = "{0}.{1}".format(
            protected64, payload64).encode('utf8')
        out = _cmd(["openssl", "dgst", "-sha256", "-sign", account_key],
                   stdin=subprocess.PIPE, cmd_input=protected_input, err_msg="OpenSSL Error")
        data = json.dumps(
            {"protected": protected64, "payload": payload64, "signature": _b64(out)})
        try:
            return _do_request(url, data=data.encode('utf8'), err_msg=err_msg, depth=depth)
        except IndexError:  # retry bad nonces (they raise IndexError)
            return _send_signed_request(url, payload, err_msg, depth=(depth + 1))

    # helper function - poll until complete
    def _poll_until_not(url, pending_statuses, err_msg):
        while True:
            result, _, _ = _do_request(url, err_msg=err_msg)
            if result['status'] in pending_statuses:
                time.sleep(2)
                continue
            return result

    # parse account key to get public key
    log.info("Parsing account key...")
    out = _cmd(["openssl", "rsa", "-in", account_key,
                "-noout", "-text"], err_msg="OpenSSL Error")
    pub_pattern = r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)"
    pub_hex, pub_exp = re.search(pub_pattern, out.decode(
        'utf8'), re.MULTILINE | re.DOTALL).groups()
    pub_exp = "{0:x}".format(int(pub_exp))
    pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
    alg = "RS256"
    jwk = {
        "e": _b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
        "kty": "RSA",
        "n": _b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
    }
    accountkey_json = json.dumps(jwk, sort_keys=True, separators=(',', ':'))
    thumbprint = _b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())

    # find domains
    log.info("Parsing CSR...")
    out = _cmd(["openssl", "req", "-in", csr, "-noout", "-text"],
               err_msg="Error loading {0}".format(csr))
    domains = set([])
    common_name = re.search(
        r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
    if common_name is not None:
        domains.add(common_name.group(1))
    subject_alt_names = re.search(
        r"X509v3 Subject Alternative Name: \n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE | re.DOTALL)
    if subject_alt_names is not None:
        for san in subject_alt_names.group(1).split(", "):
            if san.startswith("DNS:"):
                domains.add(san[4:])
    log.info("Found domains: {0}".format(", ".join(domains)))

    # get the ACME directory of urls
    log.info("Getting directory...")
    # backwards compatibility with deprecated CA kwarg
    directory_url = CA + "/directory" if CA != DEFAULT_CA else directory_url
    directory, _, _ = _do_request(
        directory_url, err_msg="Error getting directory")
    log.info("Directory found!")

    # create account, update contact details (if any), and set the global key identifier
    log.info("Registering account...")
    reg_payload = {"termsOfServiceAgreed": True}
    account, code, acct_headers = _send_signed_request(
        directory['newAccount'], reg_payload, "Error registering")
    log.info("Registered!" if code == 201 else "Already registered!")
    if contact is not None:
        account, _, _ = _send_signed_request(acct_headers['Location'], {
                                             "contact": contact}, "Error updating contact details")
        log.info("Updated contact details:\n{0}".format(
            "\n".join(account['contact'])))

    # create a new order
    log.info("Creating new order...")
    order_payload = {"identifiers": [
        {"type": "dns", "value": d} for d in domains]}
    order, _, order_headers = _send_signed_request(
        directory['newOrder'], order_payload, "Error creating new order")
    log.info("Order created!")

    # get the authorizations that need to be completed
    for auth_url in order['authorizations']:
        authorization, _, _ = _do_request(
            auth_url, err_msg="Error getting challenges")
        domain = authorization['identifier']['value']
        log.info("Verifying {0}...".format(domain))

        # find the http-01 challenge and write the challenge file
        challenge = [c for c in authorization['challenges']
                     if c['type'] == "http-01"][0]
        token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
        keyauthorization = "{0}.{1}".format(token, thumbprint)
        wellknown_path = os.path.join(acme_dir, token)
        with open(wellknown_path, "w") as wellknown_file:
            wellknown_file.write(keyauthorization)

        # check that the file is in place
        try:
            wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(
                domain, token)
            assert(disable_check or _do_request(
                wellknown_url)[0] == keyauthorization)
        except (AssertionError, ValueError) as e:
            os.remove(wellknown_path)
            raise ValueError("Wrote file to {0}, but couldn't download {1}: {2}".format(
                wellknown_path, wellknown_url, e))

        # say the challenge is done
        _send_signed_request(
            challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
        authorization = _poll_until_not(
            auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
        if authorization['status'] != "valid":
            raise ValueError(
                "Challenge did not pass for {0}: {1}".format(domain, authorization))
        log.info("{0} verified!".format(domain))

    # finalize the order with the csr
    log.info("Signing certificate...")
    csr_der = _cmd(["openssl", "req", "-in", csr, "-outform",
                    "DER"], err_msg="DER Export Error")
    _send_signed_request(order['finalize'], {
                         "csr": _b64(csr_der)}, "Error finalizing order")

    # poll the order to monitor when it's done
    order = _poll_until_not(order_headers['Location'], [
                            "pending", "processing"], "Error checking order status")
    if order['status'] != "valid":
        raise ValueError("Order failed: {0}".format(order))

    # download the certificate
    certificate_pem, _, _ = _do_request(
        order['certificate'], err_msg="Certificate download failed")
    log.info("Certificate signed!")
    return certificate_pem


def main(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            This script automates the process of getting a signed TLS certificate from Let's Encrypt using
            the ACME protocol. It will need to be run on your server and have access to your private
            account key, so PLEASE READ THROUGH IT! It's only ~200 lines, so it won't take long.

            Example Usage:
            python acme_tiny.py --account-key ./account.key --csr ./domain.csr --acme-dir /usr/share/nginx/html/.well-known/acme-challenge/ > signed_chain.crt

            Example Crontab Renewal (once per month):
            0 0 1 * * python /path/to/acme_tiny.py --account-key /path/to/account.key --csr /path/to/domain.csr --acme-dir /usr/share/nginx/html/.well-known/acme-challenge/ > /path/to/signed_chain.crt 2>> /var/log/acme_tiny.log
            """)
    )
    parser.add_argument("--account-key", required=True,
                        help="path to your Let's Encrypt account private key")
    parser.add_argument("--csr", required=True,
                        help="path to your certificate signing request")
    parser.add_argument("--acme-dir", required=True,
                        help="path to the .well-known/acme-challenge/ directory")
    parser.add_argument("--quiet", action="store_const",
                        const=logging.ERROR, help="suppress output except for errors")
    parser.add_argument("--disable-check", default=False, action="store_true",
                        help="disable checking if the challenge file is hosted correctly before telling the CA")
    parser.add_argument("--directory-url", default=DEFAULT_DIRECTORY_URL,
                        help="certificate authority directory url, default is Let's Encrypt")
    parser.add_argument("--ca", default=DEFAULT_CA,
                        help="DEPRECATED! USE --directory-url INSTEAD!")
    parser.add_argument("--contact", metavar="CONTACT", default=None, nargs="*",
                        help="Contact details (e.g. mailto:aaa@bbb.com) for your account-key")

    args = parser.parse_args(argv)
    LOGGER.setLevel(args.quiet or LOGGER.level)
    signed_crt = get_acme_crt(args.account_key, args.csr, args.acme_dir, log=LOGGER, CA=args.ca,
                              disable_check=args.disable_check, directory_url=args.directory_url, contact=args.contact)
    sys.stdout.write(signed_crt)


if __name__ == "__main__":  # pragma: no cover
    acme = Certs()
    # acme.init_acme_account()
    # print(acme.init_acme_account())
    # main(sys.argv[1:])
    # singature()
    # print(acme.create_domain_key('baokan.pub',forced=True))
    # print(acme.generate_domain_csr(['baokan.pub'],forced=True))
    print(acme.generate_domain_csr(['baokan.pub', 'www.baokan.pub', 'abc.baokan.pub'],forced=True))
    # print(acme.generate_domain_csr(['effect.pub', '*.effect.pub']))
    # print(acme._check_csr('effect.pub.csr'))
    # acme._check_csr('effect.pub.csr')

    print(acme.show_domain_csr('baokan.pub.csr', subject=True))
    # acme.show_domain_csr('effect.pub.csr')
    # acme.singature('baokan.pub')
