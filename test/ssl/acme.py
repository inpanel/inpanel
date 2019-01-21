#!/usr/bin/env python
# Python 2.6 need install python-argparse
# Copyright Daniel Roesler, under MIT license, see LICENSE at https://github.com/diafygi/acme-tiny
import argparse
import subprocess
import json
import os
import sys
import base64
import binascii
import time
import hashlib
import re
import copy
import textwrap
import logging
try:
    from urllib.request import urlopen, Request  # Python 3
except ImportError:
    from urllib2 import urlopen, Request  # Python 2.7+

# DEPRECATED! USE DEFAULT_DIRECTORY_URL INSTEAD
DEFAULT_CA = "https://acme-v02.api.letsencrypt.org"
DEFAULT_DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


class ACME():

    def __init__(self):
        self.path_current = os.path.dirname(os.path.realpath(__file__))
        self.path_home = '/usr/local/acme/'
        self.path_crts = self.path_current + '/crts/'
        self.key_size = '4096'
        self.account_key = self.path_current + '/' + 'account.key'

        self.acme_account_key()

    def _check(self, file_key):
        if file_key and os.path.exists(file_key):
            try:
                exists = self._cmd(
                    ['openssl', 'rsa', '-in', file_key, '-check'])
                if 'RSA key ok' in exists and forced == False:
                    return True
            except:
                pass

    # helper function - run external commands
    def _cmd(self, cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    def _generate_private_key(self, file_key=None, forced=False):
        print(forced, 111)
        '''Generate private key'''
        if file_key == None or file_key == '':
            print(222)
            return False
        if file_key and os.path.exists(file_key):
            print(333)
            try:
                exists = self._cmd(
                    ['openssl', 'rsa', '-in', file_key, '-check'])
                if 'RSA key ok' in exists and forced == False:
                    print(444)
                    return True
            except:
                pass
        try:
            print(555, file_key)
            cmd_l = ['openssl', 'genrsa', '-out', file_key, self.key_size]
            print(545, cmd_l)
            res = self._cmd(cmd_l, err_msg='Generate private key error')
            print(578, res)
            if res is None:
                print(666, res)
                return False
            else:
                return True
        except:
            return False

    def acme_account_key(self, file_key=None, forced=False):
        '''Create a Let's Encrypt account private key'''
        file_key = self.account_key if file_key == None or file_key == '' else file_key
        return self._generate_private_key(file_key=file_key, forced=forced)

    def create_domain_key(self, domain, forced=False):
        '''Create a domain private key'''
        key = self.path_crts + domain + '.key'
        return self._generate_private_key(file_key=key, forced=forced)

    def create_domain_csr(self, domain=[], domain_key=None):
        '''Create a certificate signing request (CSR) for domains.'''
        # openssl genrsa 4096 > github.com.key
        if len(domain) == 0:
            return None
        k = domain_key if domain_key and os.path.exists(
            domain_key) else self.path_crts + domain[0] + '.key'
        c = self.path_crts + domain[0] + '.csr'
        if len(domain) == 1:
            cmd_list = ['openssl', 'req', '-new', '-sha256',
                        '-key', k, '-subj', '/CN=' + domain[0]]
            tt = self._cmd(
                cmd_list, err_msg="Create certificate signing request Error")
            if tt is None:
                return False
            else:
                with open(c, 'w') as f:
                    f.write(tt)
                return True
        if len(domain) > 1:
            sans = []
            for i in domain:
                sans.append('DNS:%s' % i)
            sans = ','.join(sans)
            domain_sans = 'Dept/CN=%s/subjectAltName=%s' % (domain[0], sans)
            cmd_list = ['openssl', 'req', '-new', '-sha256',
                        '-key', k, '-subj', '-out', c, domain_sans]
            print(cmd_list)
            tt = self._cmd(
                cmd_list, err_msg="Create certificate signing request Error")
            if tt is None:
                return False
            else:
                # with open(c, 'w') as f:
                #     f.write(tt)
                return True

    def singature(self):
        path_current = self.path_current
        signed_crt = get_acme_crt(path_current + '/account.key', path_current +
                                  '/dougroup.com.csr', '/var/www/dougroup.com/.well-known/acme-challenge/')
        if signed_crt is not None:
            with open(path_current + '/dougroup.com.crt', 'w') as f:
                f.write(signed_crt)

    def show_domain_csr(self, domain_key, text=False, pubkey=False, subject=False):
        try:
            cmd_list = ['openssl', 'req', '-in', domain_key]
            if text is True:
                cmd_list.append('-text')
            if pubkey is True:
                cmd_list.append('-noout -pubkey')
            if subject is True:
                cmd_list.append('-noout -subject')
            res = self._cmd(cmd_list, err_msg='Generate private key error')
            if res is None:
                return False
            else:
                return res
        except:
            return None


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
    acme = ACME()
    # acme.acme_account_key()
    # main(sys.argv[1:])
    # singature()
    # acme = ACME()
    # print(acme.create_domain_key('effect.pub'))
    print(acme.create_domain_csr(['effect.pub', 'abc.effect.pub']))
