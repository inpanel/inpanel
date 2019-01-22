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


class ACME(object):

    def init(self, account_key, csr=None):
        self.account_key = account_key
        self.csr = csr
        self.directory = None
        self.acct_headers = None
        self.alg = 'RS256'
        self.jwk = None
        self.thumbprint = None
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(logging.INFO)
        self.contact = 'a client of the Intranet Control Panel'
        # self.ca = "https://acme-v02.api.letsencrypt.org"
        # self.directory_url = = "https://acme-v02.api.letsencrypt.org/directory"
        # dev
        self.ca = "https://acme-staging-v02.api.letsencrypt.org"
        self.directory_url = "https://acme-staging-v02.api.letsencrypt.org/directory"

        self.get_directory()
        self.init_account(self.account_key)
        self.registe_account()
        self.get_domain()
        self.create_new_order()
        self.download_certificate()

    # helper function - run external commands
    def _cmd(self, cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    # helper functions - base64 encode for jose spec
    def _b64(self, b):
        return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")

    # helper function - make request and automatically parse json response
    def _do_request(self, url, data=None, err_msg="Error", depth=0):
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
    def _send_signed_request(self, url, payload, err_msg, depth=0):
        payload64 = self._b64(json.dumps(payload).encode('utf8'))
        new_nonce = self._do_request(self.ca_new_nonce)[2]['Replay-Nonce']
        protected = {"url": url, "alg": self.alg, "nonce": new_nonce}
        protected.update({"jwk": self.jwk} if self.acct_headers is None else {
                         "kid": self.acct_headers['Location']})
        protected64 = self._b64(json.dumps(protected).encode('utf8'))
        protected_input = "{0}.{1}".format(
            protected64, payload64).encode('utf8')
        out = self._cmd(["openssl", "dgst", "-sha256", "-sign", account_key],
                        stdin=subprocess.PIPE, cmd_input=protected_input, err_msg="OpenSSL Error")
        data = json.dumps(
            {"protected": protected64, "payload": payload64, "signature": self._b64(out)})
        try:
            return self._do_request(url, data=data.encode('utf8'), err_msg=err_msg, depth=depth)
        except IndexError:  # retry bad nonces (they raise IndexError)
            return self._send_signed_request(url, payload, err_msg, depth=(depth + 1))

    # helper function - poll until complete
    def _poll_until_not(self, url, pending_statuses, err_msg):
        while True:
            result, _, _ = self._do_request(url, err_msg=err_msg)
            if result['status'] in pending_statuses:
                time.sleep(2)
                continue
            return result

    def init_account(self, account_key=None):
        # parse account key to get public key
        self.log.info("Parsing account key...")
        if not os.path.exists(account_key) or not os.path.isfile(account_key):
            account_key = self.account_key
        if not os.path.exists(account_key):
            return None

        out = self._cmd(["openssl", "rsa", "-in", account_key,
                         "-noout", "-text"], err_msg="OpenSSL Error")
        pub_pattern = r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)"
        pub_hex, pub_exp = re.search(pub_pattern, out.decode(
            'utf8'), re.MULTILINE | re.DOTALL).groups()
        pub_exp = "{0:x}".format(int(pub_exp))
        pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
        # alg = "RS256"
        self.jwk = {
            "e": _b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
            "kty": "RSA",
            "n": _b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
        }
        accountkey_json = json.dumps(
            jwk, sort_keys=True, separators=(',', ':'))
        self.thumbprint = _b64(hashlib.sha256(
            accountkey_json.encode('utf8')).digest())

    def registe_account(self, contact=None):
        # create account, update contact details (if any), and set the global key identifier
        self.log.info("Registering account...")
        if contact == None:
            contact = self.contact
        reg_payload = {"termsOfServiceAgreed": True}
        account, code, acct_headers = self._send_signed_request(
            self.ca_new_account, reg_payload, "Error registering")
        self.log.info("Registered!" if code == 201 else "Already registered!")
        if contact is not None:
            account, _, _ = self._send_signed_request(acct_headers['Location'], {
                                                      "contact": contact}, "Error updating contact details")
            self.log.info("Updated contact details:\n{0}".format(
                "\n".join(account['contact'])))

    def get_directory(self):
        # get the ACME directory of urls
        self.log.info("Getting directory...")
        self.directory, _, _ = _do_request(
            self.directory_url, err_msg="Error getting directory")
        self.ca_new_account = self.directory['newAccount']
        self.ca_new_nonce = self.directory['newNonce']
        self.ca_new_order = self.directory['newOrder']
        self.ca_revoke_cert = self.directory['revokeCert']
        self.ca_key_change = self.directory['keyChange']
        self.log.info("Directory found!")

    def get_domain(self):
        # find domains
        self.log.info("Parsing CSR...")
        out = _cmd(["openssl", "req", "-in", self.csr, "-noout", "-text"],
                   err_msg="Error loading {0}".format(self.csr))
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
        self.log.info("Found domains: {0}".format(", ".join(domains)))

    def create_new_order(self, domains):
        # create a new order
        self.log.info("Creating new order...")
        order_payload = {"identifiers": [
            {"type": "dns", "value": d} for d in domains]}
        order, _, order_headers = self._send_signed_request(
            self.ca_new_order, order_payload, "Error creating new order")
        self.log.info("Order created!")

        # get the authorizations that need to be completed
        for auth_url in order['authorizations']:
            authorization, _, _ = _do_request(
                auth_url, err_msg="Error getting challenges")
            domain = authorization['identifier']['value']
            self.log.info("Verifying {0}...".format(domain))

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
            self._send_signed_request(
                challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
            authorization = _poll_until_not(
                auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
            if authorization['status'] != "valid":
                raise ValueError(
                    "Challenge did not pass for {0}: {1}".format(domain, authorization))
            self.log.info("{0} verified!".format(domain))

        # finalize the order with the csr
        self.log.info("Signing certificate...")
        csr_der = _cmd(["openssl", "req", "-in", self.csr, "-outform",
                        "DER"], err_msg="DER Export Error")
        self._send_signed_request(
            order['finalize'], {"csr": _b64(csr_der)}, "Error finalizing order")

        # poll the order to monitor when it's done
        order = self._poll_until_not(order_headers['Location'], [
                                     "pending", "processing"], "Error checking order status")
        if order['status'] != "valid":
            raise ValueError("Order failed: {0}".format(order))

    def download_certificate():
        # download the certificate
        certificate_pem, _, _ = self._do_request(
            order['certificate'], err_msg="Certificate download failed")
        self.log.info("Certificate signed!")
        return certificate_pem

    def revoke_certificate(self, crt):
        print(crt)


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
    signed_crt = acme_get_crt(args.account_key, args.csr, args.acme_dir, log=LOGGER, CA=args.ca,
                              disable_check=args.disable_check, directory_url=args.directory_url, contact=args.contact)
    sys.stdout.write(signed_crt)


if __name__ == "__main__":  # pragma: no cover
    aaa = ACME()
