# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Shadowsocks-libev Plugins'''

plugins_info = {
    'name': 'Shadowsocks-libev',
    'router': 'shadowsocks-libev',
    'config': {
        'centos': '/etc/shadowsocks-libev/config.json',
        'debian': '/etc/default/shadowsocks-libev',
        'ubuntu': '/etc/default/shadowsocks-libev',
        'freebsd': '/usr/local/etc/shadowsocks-libev'
    },
    'script': {
        'sysvinit': {
            'start': '/etc/init.d/shadowsocks-libev start',
            'stop': '/etc/init.d/shadowsocks-libev stop',
            'restart': '/etc/init.d/shadowsocks-libev restart',
            'status': '/etc/init.d/shadowsocks-libev status'
        },
        'systemd': {
            'start': 'systemctl start shadowsocks-libev',
            'stop': 'systemctl stop shadowsocks-libev',
            'restart': 'systemctl restart shadowsocks-libev',
            'status': 'systemctl status shadowsocks-libev',
        }
    },
    'install': {
        'yum': {
            'repos': '',
            'import': {
                'from': 'https://copr.fedorainfracloud.org/coprs/librehat/shadowsocks/repo/epel-6/librehat-shadowsocks-epel-6.repo',
                'to': ''
            },
            'shell': [
                'yum install epel-release -y',
                'yum install gcc gettext autoconf libtool automake make pcre-devel asciidoc xmlto c-ares-devel libev-devel libsodium-devel mbedtls-devel -y',
                'yum update',
                'yum install shadowsocks-libev'
            ],
        },
        'dnf': {
            'repos': '',
            'shell': [
                'yum install epel-release -y',
                'yum install gcc gettext autoconf libtool automake make pcre-devel asciidoc xmlto c-ares-devel libev-devel libsodium-devel mbedtls-devel -y',
                'yum update',
                'yum install shadowsocks-libev'
            ],
        },
        'apt': {
            'repos': '/etc/default/shadowsocks-libev',
            'shell': [
                'sh -c \'printf "deb http://deb.debian.org/debian stretch-backports main" > /etc/apt/sources.list.d/stretch-backports.list\'',
                'apt update',
                'apt -t stretch-backports install shadowsocks-libev'
            ]
        },
        'brew': {
            'repos': '',
            'shell': [
                'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"',
                'brew install shadowsocks-libev'
            ]
        },
    }
}
