# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for APT(Advanced Packaging Tool) Repository Data'''

apt_sources = {
    'debian': {
        '10': {
            'buster': {
                'main': 'deb http://deb.debian.org/debian/ buster main',
                'contrib': 'deb http://deb.debian.org/debian/ buster contrib',
                'non-free': 'deb http://deb.debian.org/debian/ buster non-free',
                'updates': 'deb http://deb.debian.org/debian/ buster-updates main contrib non-free',
                'security': 'deb http://security.debian.org/debian-security buster/updates main contrib non-free'
            }
        },
        '11': {
            'bullseye': {
                'main': 'deb http://deb.debian.org/debian/ bullseye main',
                'contrib': 'deb http://deb.debian.org/debian/ bullseye contrib',
                'non-free': 'deb http://deb.debian.org/debian/ bullseye non-free',
                'non-free-firmware': 'deb http://deb.debian.org/debian/ bullseye non-free-firmware',
                'updates': 'deb http://deb.debian.org/debian/ bullseye-updates main contrib non-free non-free-firmware',
                'security': 'deb http://security.debian.org/debian-security bullseye-security main contrib non-free non-free-firmware'
            }
        },
        '12': {
            'bookworm': {
                'main': 'deb http://deb.debian.org/debian/ bookworm main',
                'contrib': 'deb http://deb.debian.org/debian/ bookworm contrib',
                'non-free': 'deb http://deb.debian.org/debian/ bookworm non-free',
                'non-free-firmware': 'deb http://deb.debian.org/debian/ bookworm non-free-firmware',
                'updates': 'deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free non-free-firmware',
                'security': 'deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware',
                'backports': 'deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware'
            }
        },
        '13': {
            'trixie': {
                'main': 'deb http://deb.debian.org/debian/ trixie main',
                'contrib': 'deb http://deb.debian.org/debian/ trixie contrib',
                'non-free': 'deb http://deb.debian.org/debian/ trixie non-free',
                'non-free-firmware': 'deb http://deb.debian.org/debian/ trixie non-free-firmware',
                'updates': 'deb http://deb.debian.org/debian/ trixie-updates main contrib non-free non-free-firmware',
                'security': 'deb http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware',
                'backports': 'deb http://deb.debian.org/debian/ trixie-backports main contrib non-free non-free-firmware'
            }
        }
    },
    'ubuntu': {
        '18.04': {
            'bionic': {
                'main': 'deb http://archive.ubuntu.com/ubuntu/ bionic main restricted',
                'universe': 'deb http://archive.ubuntu.com/ubuntu/ bionic universe',
                'multiverse': 'deb http://archive.ubuntu.com/ubuntu/ bionic multiverse',
                'updates': 'deb http://archive.ubuntu.com/ubuntu/ bionic-updates main restricted universe multiverse',
                'security': 'deb http://security.ubuntu.com/ubuntu/ bionic-security main restricted universe multiverse',
                'backports': 'deb http://archive.ubuntu.com/ubuntu/ bionic-backports main restricted universe multiverse'
            }
        },
        '20.04': {
            'focal': {
                'main': 'deb http://archive.ubuntu.com/ubuntu/ focal main restricted',
                'universe': 'deb http://archive.ubuntu.com/ubuntu/ focal universe',
                'multiverse': 'deb http://archive.ubuntu.com/ubuntu/ focal multiverse',
                'updates': 'deb http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse',
                'security': 'deb http://security.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse',
                'backports': 'deb http://archive.ubuntu.com/ubuntu/ focal-backports main restricted universe multiverse'
            }
        },
        '22.04': {
            'jammy': {
                'main': 'deb http://archive.ubuntu.com/ubuntu/ jammy main restricted',
                'universe': 'deb http://archive.ubuntu.com/ubuntu/ jammy universe',
                'multiverse': 'deb http://archive.ubuntu.com/ubuntu/ jammy multiverse',
                'updates': 'deb http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted universe multiverse',
                'security': 'deb http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse',
                'backports': 'deb http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse'
            }
        },
        '24.04': {
            'noble': {
                'main': 'deb http://archive.ubuntu.com/ubuntu/ noble main restricted',
                'universe': 'deb http://archive.ubuntu.com/ubuntu/ noble universe',
                'multiverse': 'deb http://archive.ubuntu.com/ubuntu/ noble multiverse',
                'updates': 'deb http://archive.ubuntu.com/ubuntu/ noble-updates main restricted universe multiverse',
                'security': 'deb http://security.ubuntu.com/ubuntu/ noble-security main restricted universe multiverse',
                'backports': 'deb http://archive.ubuntu.com/ubuntu/ noble-backports main restricted universe multiverse'
            }
        }
    }
}

apt_mirrors = {
    'aliyun': {
        'debian': 'deb http://mirrors.aliyun.com/debian/ $release main contrib non-free non-free-firmware',
        'debian-updates': 'deb http://mirrors.aliyun.com/debian/ $release-updates main contrib non-free non-free-firmware',
        'debian-security': 'deb http://mirrors.aliyun.com/debian-security/ $release-security main contrib non-free non-free-firmware',
        'debian-backports': 'deb http://mirrors.aliyun.com/debian/ $release-backports main contrib non-free non-free-firmware',
        'ubuntu': 'deb http://mirrors.aliyun.com/ubuntu/ $codename main restricted universe multiverse',
        'ubuntu-updates': 'deb http://mirrors.aliyun.com/ubuntu/ $codename-updates main restricted universe multiverse',
        'ubuntu-security': 'deb http://mirrors.aliyun.com/ubuntu/ $codename-security main restricted universe multiverse',
        'ubuntu-backports': 'deb http://mirrors.aliyun.com/ubuntu/ $codename-backports main restricted universe multiverse'
    },
    'ustc': {
        'debian': 'deb https://mirrors.ustc.edu.cn/debian/ $release main contrib non-free non-free-firmware',
        'debian-updates': 'deb https://mirrors.ustc.edu.cn/debian/ $release-updates main contrib non-free non-free-firmware',
        'debian-security': 'deb https://mirrors.ustc.edu.cn/debian-security/ $release-security main contrib non-free non-free-firmware',
        'debian-backports': 'deb https://mirrors.ustc.edu.cn/debian/ $release-backports main contrib non-free non-free-firmware',
        'ubuntu': 'deb https://mirrors.ustc.edu.cn/ubuntu/ $codename main restricted universe multiverse',
        'ubuntu-updates': 'deb https://mirrors.ustc.edu.cn/ubuntu/ $codename-updates main restricted universe multiverse',
        'ubuntu-security': 'deb https://mirrors.ustc.edu.cn/ubuntu/ $codename-security main restricted universe multiverse',
        'ubuntu-backports': 'deb https://mirrors.ustc.edu.cn/ubuntu/ $codename-backports main restricted universe multiverse'
    },
    'tsinghua': {
        'debian': 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $release main contrib non-free non-free-firmware',
        'debian-updates': 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $release-updates main contrib non-free non-free-firmware',
        'debian-security': 'deb https://mirrors.tuna.tsinghua.edu.cn/debian-security/ $release-security main contrib non-free non-free-firmware',
        'debian-backports': 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $release-backports main contrib non-free non-free-firmware',
        'ubuntu': 'deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename main restricted universe multiverse',
        'ubuntu-updates': 'deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-updates main restricted universe multiverse',
        'ubuntu-security': 'deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-security main restricted universe multiverse',
        'ubuntu-backports': 'deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ $codename-backports main restricted universe multiverse'
    }
}

apt_pkg_alias = {
    'nginx': ['nginx', 'nginx-full', 'nginx-light', 'nginx-extras'],
    'tomcat': ['tomcat9', 'tomcat10'],
    'apache': ['apache2'],
    'lighttpd': ['lighttpd'],
    'vsftpd': ['vsftpd'],
    'mysql': ['mysql-server', 'mariadb-server', 'default-mysql-server'],
    'mariadb': ['mariadb-server'],
    'redis': ['redis-server'],
    'memcache': ['memcached'],
    'mongodb': ['mongodb-org'],
    'php': ['php', 'php8.1', 'php8.2', 'php8.3'],
    'sendmail': ['sendmail'],
    'ssh': ['openssh-server'],
    'iptables': ['iptables'],
    'cron': ['cron'],
    'ntp': ['chrony'],
    'bind': ['bind9'],
    'docker': ['docker-ce'],
    'pureftpd': ['pure-ftpd'],
    'proftpd': ['proftpd-basic'],
    'GeoIP': ['geoip-database'],
    'mono': ['mono-devel'],
    'ntfs-3g': ['ntfs-3g'],
    'davfs2': ['davfs2'],
    'nfs': ['nfs-kernel-server'],
    'cifs': ['cifs-utils'],
    'samba': ['samba']
}

apt_pkg_relatives = {
    'nginx': {
        'nginx': {'default': True, 'base': True},
        'nginx-full': {'default': False, 'isext': True},
        'nginx-light': {'default': False, 'isext': True},
        'nginx-extras': {'default': False, 'isext': True},
        'nginx-core': {'default': True, 'base': True}
    },
    'apache2': {
        'apache2': {'default': True, 'base': True},
        'apache2-dev': {'default': False, 'isext': True},
        'libapache2-mod-ssl': {'default': True, 'isext': True},
        'apache2-utils': {'default': False, 'isext': True}
    },
    'mariadb-server': {
        'mariadb-server': {'default': True, 'base': True},
        'mariadb-client': {'default': True, 'base': True},
        'mariadb-common': {'default': True, 'base': True}
    },
    'redis-server': {
        'redis-server': {'default': True, 'base': True},
        'redis-tools': {'default': False, 'isext': True}
    },
    'memcached': {
        'memcached': {'default': True, 'base': True},
        'libmemcached-tools': {'default': False, 'isext': True}
    },
    'php': {
        'php': {'default': True, 'base': True},
        'php-cli': {'default': True},
        'php-common': {'default': True, 'base': True},
        'php-fpm': {'default': True},
        'php-gd': {'default': True, 'isext': True},
        'php-mbstring': {'default': True, 'isext': True},
        'php-mysql': {'default': True, 'isext': True},
        'php-pdo': {'default': True},
        'php-soap': {'default': False, 'isext': True},
        'php-xml': {'default': True, 'isext': True},
        'php-zip': {'default': False, 'isext': True},
        'php-dev': {'default': False, 'isext': True}
    },
    'php8.2': {
        'php8.2': {'default': True, 'base': True},
        'php8.2-cli': {'default': True},
        'php8.2-common': {'default': True, 'base': True},
        'php8.2-fpm': {'default': True},
        'php8.2-gd': {'default': True, 'isext': True},
        'php8.2-mbstring': {'default': True, 'isext': True},
        'php8.2-mysql': {'default': True, 'isext': True},
        'php8.2-pdo': {'default': True},
        'php8.2-soap': {'default': False, 'isext': True},
        'php8.2-xml': {'default': True, 'isext': True},
        'php8.2-zip': {'default': False, 'isext': True},
        'php8.2-dev': {'default': False, 'isext': True}
    },
    'docker-ce': {
        'docker-ce': {'default': True, 'base': True},
        'docker-ce-cli': {'default': True, 'base': True},
        'containerd.io': {'default': True, 'base': True},
        'docker-compose-plugin': {'default': False, 'isext': True}
    }
}