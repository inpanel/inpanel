# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for DNF(Yellow dog Updater, Modified) Repository Data'''

dnf_reporpms = {
    'base': {
        8: {
            'x86_64': [
                'https://mirrors.aliyun.com/centos/8/BaseOS/x86_64/os/Packages/centos-release-8-5.2111.el8.x86_64.rpm',
                'https://mirror.centos.org/centos/8/BaseOS/x86_64/os/Packages/centos-release-8-5.2111.el8.x86_64.rpm'
            ]
        },
        9: {
            'x86_64': [
                'https://mirrors.aliyun.com/centos/9-stream/BaseOS/x86_64/os/Packages/centos-release-stream-9.0-2.el9.noarch.rpm',
                'https://mirror.centos.org/centos/9-stream/BaseOS/x86_64/os/Packages/centos-release-stream-9.0-2.el9.noarch.rpm'
            ]
        }
    },
    'epel': {
        8: {
            'x86_64': ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm']
        },
        9: {
            'x86_64': ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm']
        },
        10: {
            'x86_64': ['https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm']
        }
    },
    'remi': {
        8: {
            'x86_64': ['https://rpms.remirepo.net/enterprise/remi-release-8.rpm']
        },
        9: {
            'x86_64': ['https://rpms.remirepo.net/enterprise/remi-release-9.rpm']
        },
        10: {
            'x86_64': ['https://rpms.remirepo.net/enterprise/remi-release-10.rpm']
        }
    },
    'powertools': {
        8: {
            'x86_64': []
        }
    },
    'crb': {
        9: {
            'x86_64': []
        },
        10: {
            'x86_64': []
        }
    },
    'mariadb': {
        8: {
            'x86_64': ['https://yum.mariadb.org/10.6/centos8-amd64/rpms/MariaDB-release-10.6-1.el8.noarch.rpm']
        },
        9: {
            'x86_64': ['https://yum.mariadb.org/10.6/centos9-amd64/rpms/MariaDB-release-10.6-1.el9.noarch.rpm']
        },
        10: {
            'x86_64': ['https://yum.mariadb.org/10.6/rhel10-amd64/rpms/MariaDB-release-10.6-1.el10.noarch.rpm']
        }
    },
    'nginx': {
        8: {
            'x86_64': ['http://nginx.org/packages/centos/8/noarch/RPMS/nginx-release-centos-8-0.el8.ngx.noarch.rpm']
        },
        9: {
            'x86_64': ['http://nginx.org/packages/centos/9/noarch/RPMS/nginx-release-centos-9-0.el9.ngx.noarch.rpm']
        },
        10: {
            'x86_64': ['http://nginx.org/packages/centos/10/noarch/RPMS/nginx-release-centos-10-0.el10.ngx.noarch.rpm']
        }
    },
    'nodejs': {
        8: {
            'x86_64': ['https://rpm.nodesource.com/pub_18.x/el/8/x86_64/nodesource-release-el8-1.noarch.rpm']
        },
        9: {
            'x86_64': ['https://rpm.nodesource.com/pub_18.x/el/9/x86_64/nodesource-release-el9-1.noarch.rpm']
        },
        10: {
            'x86_64': ['https://rpm.nodesource.com/pub_18.x/el/10/x86_64/nodesource-release-el10-1.noarch.rpm']
        }
    }
}

dnf_repoinstallcmds = {
    'ius': 'curl https://setup.ius.io | sh',
    'elastic': 'rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch && echo "[elasticsearch]\\nname=Elasticsearch repository for 8.x packages\\nbaseurl=https://artifacts.elastic.co/packages/8.x/yum\\ngpgcheck=1\\ngpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch\\nenabled=0\\nautorefresh=1\\ntype=rpm-md" > /etc/yum.repos.d/elasticsearch.repo'
}

dnf_repostr = {
    'mariadb': {
        'x86_64': '[mariadb]\n\
name=MariaDB\n\
baseurl=http://yum.mariadb.org/10.6/rhel$releasever-amd64\n\
gpgkey=https://yum.mariadb.org/RPM-GPG-KEY-MariaDB\n\
gpgcheck=1',
    },
    'nginx-stable': {
        'x86_64': '[nginx-stable]\n\
name=nginx stable repo\n\
baseurl=http://nginx.org/packages/centos/$releasever/$basearch/\n\
gpgcheck=1\n\
enabled=1\n\
gpgkey=https://nginx.org/keys/nginx_signing.key\n\
module_hotfixes=true',
    },
    'nginx-mainline': {
        'x86_64': '[nginx-mainline]\n\
name=nginx mainline repo\n\
baseurl=http://nginx.org/packages/mainline/centos/$releasever/$basearch/\n\
gpgcheck=1\n\
enabled=0\n\
gpgkey=https://nginx.org/keys/nginx_signing.key\n\
module_hotfixes=true',
    },
    'zabbix': {
        'x86_64': '[zabbix]\n\
name=Zabbix Official Repository - $basearch\n\nbaseurl=https://repo.zabbix.com/zabbix/6.4/rhel/$releasever/$basearch/\n\ngpgcheck=1\n\ngpgkey=https://repo.zabbix.com/zabbix-official-repo.key\n\nenabled=1',
    }
}

dnf_pkg_alias = {
    'nginx': ['nginx', 'nginx-stable'],
    'tomcat': ['tomcat'],
    'apache': ['httpd'],
    'lighttpd': ['lighttpd'],
    'vsftpd': ['vsftpd'],
    'mysql': ['mysql-community-server'],
    'mariadb': ['mariadb-server'],
    'redis': ['redis'],
    'memcache': ['memcached'],
    'mongodb': ['mongodb-server'],
    'php': ['php', 'php80', 'php81', 'php82', 'php83'],
    'sendmail': ['sendmail'],
    'ssh': ['openssh-server', 'openssh-clients'],
    'iptables': ['iptables'],
    'cron': ['crond'],
    'ntp': ['chrony'],
    'bind': ['bind'],
    'docker': ['docker-ce'],
    'pureftpd': ['pure-ftpd'],
    'proftpd': ['proftpd'],
    'GeoIP': ['GeoIP'],
    'mono': ['mono-core'],
    'ntfs-3g': ['ntfs-3g'],
    'davfs2': ['davfs2'],
    'nfs': ['nfs-utils'],
    'cifs': ['cifs-utils'],
    'samba': ['samba']
}

dnf_pkg_relatives = {
    'nginx': {
        'nginx': {'default': True, 'base': True},
        'nginx-mod-http-geoip': {'default': False, 'isext': True},
        'nginx-mod-http-image-filter': {'default': False, 'isext': True},
        'nginx-mod-http-perl': {'default': False, 'isext': True},
        'nginx-mod-http-xslt-filter': {'default': False, 'isext': True},
        'nginx-mod-mail': {'default': False, 'isext': True},
        'nginx-mod-stream': {'default': False, 'isext': True},
        'nginx-module-njs': {'default': False, 'isext': True}
    },
    'httpd': {
        'httpd': {'default': True, 'base': True},
        'httpd-devel': {'default': False, 'isext': True},
        'httpd-tools': {'default': False, 'isext': True},
        'mod_ssl': {'default': True, 'isext': True}
    },
    'mariadb-server': {
        'mariadb-server': {'default': True, 'base': True},
        'mariadb': {'default': True, 'base': True},
        'mariadb-common': {'default': True, 'base': True},
        'mariadb-compat': {'default': True, 'base': True}
    },
    'redis': {
        'redis': {'default': True, 'base': True}
    },
    'memcached': {
        'memcached': {'default': True, 'base': True}
    },
    'php': {
        'php': {'default': True, 'base': True},
        'php-cli': {'default': True},
        'php-common': {'default': True, 'base': True},
        'php-fpm': {'default': True},
        'php-gd': {'default': True, 'isext': True},
        'php-mbstring': {'default': True, 'isext': True},
        'php-mysqlnd': {'default': True, 'isext': True},
        'php-pdo': {'default': True},
        'php-soap': {'default': False, 'isext': True},
        'php-xml': {'default': True, 'isext': True},
        'php-zip': {'default': False, 'isext': True},
        'php-devel': {'default': False, 'isext': True}
    },
    'php82': {
        'php82': {'default': True, 'base': True},
        'php82-cli': {'default': True},
        'php82-common': {'default': True, 'base': True},
        'php82-fpm': {'default': True},
        'php82-gd': {'default': True, 'isext': True},
        'php82-mbstring': {'default': True, 'isext': True},
        'php82-mysqlnd': {'default': True, 'isext': True},
        'php82-pdo': {'default': True},
        'php82-soap': {'default': False, 'isext': True},
        'php82-xml': {'default': True, 'isext': True},
        'php82-zip': {'default': False, 'isext': True},
        'php82-devel': {'default': False, 'isext': True}
    },
    'docker-ce': {
        'docker-ce': {'default': True, 'base': True},
        'docker-ce-cli': {'default': True, 'base': True},
        'containerd.io': {'default': True, 'base': True}
    }
}