# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.


# repository list that YUM support
yum_repolist = ('base', 'updates', 'epel', 'CentALT', 'ius', 'atomic', '10gen')

yum_reporpms = {
    'base': {
        5: {
            'x86_64': (
                # 'http://mirror.centos.org/centos/5/os/x86_64/CentOS/centos-release-notes-5.8-0.x86_64.rpm',
                # 'http://mirror.centos.org/centos/5/os/x86_64/CentOS/centos-release-5-8.el5.centos.x86_64.rpm',
                'http://mirror.neu.edu.cn/centos/5/os/x86_64/CentOS/centos-release-notes-5.11-0.x86_64.rpm',
                'http://mirror.neu.edu.cn/centos/5/os/x86_64/CentOS/centos-release-5-11.el5.centos.x86_64.rpm'
                ),
            'i386': (
                # 'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-notes-5.8-0.i386.rpm',
                # 'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-5-8.el5.centos.i386.rpm',
                'http://mirror.neu.edu.cn/centos/5/os/i386/CentOS/centos-release-notes-5.11-0.i386.rpm',
                'http://mirror.neu.edu.cn/centos/5/os/i386/CentOS/centos-release-5-11.el5.centos.i386.rpm'
                ),
            'i686': (
                # 'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-notes-5.8-0.i386.rpm',
                # 'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-5-8.el5.centos.i386.rpm',
                'http://mirror.neu.edu.cn/centos/5/os/i386/CentOS/centos-release-notes-5.11-0.i386.rpm',
                'http://mirror.neu.edu.cn/centos/5/os/i386/CentOS/centos-release-5-11.el5.centos.i386.rpm'
                ),
            },
        6: {
            # 'x86_64': ('http://mirror.centos.org/centos/6/os/x86_64/Packages/centos-release-6-9.el6.12.3.x86_64.rpm.rpm', ),
            # 'i386':   ('http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-9.el6.12.3.i686.rpm', ),
            # 'i686':   ('http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-9.el6.12.3.i686.rpm', ),
            'x86_64': ('http://mirror.centos.org/centos/6/os/x86_64/Packages/centos-release-6-10.el6.centos.12.3.x86_64.rpm', ),
            'i386':   ('http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-10.el6.centos.12.3.i686.rpm', ),
            'i686':   ('http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-10.el6.centos.12.3.i686.rpm', ),
            },
        7: {
            'x86_64': (
                'http://mirror.centos.org/centos/7/os/x86_64/Packages/centos-release-7-5.1804.el7.centos.x86_64.rpm'
                )
            }
        },
    'updates': {
        7: {
            'x86_64': (
                'http://mirror.centos.org/centos/7/updates/x86_64/Packages/centos-release-7-5.1804.1.el7.centos.x86_64.rpm',
                'http://mirror.centos.org/centos/7/updates/x86_64/Packages/centos-release-7-5.1804.4.el7.centos.x86_64.rpm',
                'http://mirror.centos.org/centos/7/updates/x86_64/Packages/centos-release-7-5.1804.5.el7.centos.x86_64.rpm',
                'http://mirror.centos.org/centos/7/updates/x86_64/Packages/centos-release-7-5.1804.el7.centos.2.x86_64.rpm'
                )
            }
        },
    'epel': {
        5: {
            'x86_64': (
                'http://centos.ustc.edu.cn/epel/6/x86_64/Packages/e/epel-release-6-8.noarch.rpm'
                ),
            'i386':   (
                'http://centos.ustc.edu.cn/epel/6/i386/Packages/e/epel-release-6-8.noarch.rpm'
                ),
            'i686':   (
                'http://centos.ustc.edu.cn/epel/6/i386/Packages/e/epel-release-6-8.noarch.rpm'
                ),
            },
        6: {
            'x86_64': (
                # 'http://centos.ustc.edu.cn/epel/6/x86_64/Packages/e/epel-release-6-8.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/epel-release-6-5.noarch.rpm'
                ),
            'i386':   (
                # 'http://centos.ustc.edu.cn/epel/6/i386/Packages/e/epel-release-6-8.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/epel-release-6-5.noarch.rpm'
                ),
            'i686':   (
                # 'http://centos.ustc.edu.cn/epel/6/i386/Packages/e/epel-release-6-8.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/epel-release-6-5.noarch.rpm'
                ),
        },
        7: {
            'x86_64': ('http://centos.ustc.edu.cn/epel/7/x86_64/Packages/e/epel-release-7-11.noarch.rpm',),
            },
        },
    'CentALT': {
        5: {
            'x86_64': (
                'http://mirror.neu.edu.cn/CentALT/5/x86_64/centalt-release-5-3.noarch.rpm'
                ),
            'i386':   (
                'http://mirror.neu.edu.cn/CentALT/5/i386/centalt-release-5-3.noarch.rpm'
                ),
            'i686':   (
                'http://mirror.neu.edu.cn/CentALT/5/i386/centalt-release-5-3.noarch.rpm'
                ),
            },
        6: {
            'x86_64': (
                'http://mirror.neu.edu.cn/CentALT/6/x86_64/centalt-release-6-1.noarch.rpm',
                'http://mirror.centos.org/centos/6/os/x86_64/Packages/centos-release-6-10.el6.centos.12.3.x86_64.rpm'
                ),
            'i386':   (
                'http://mirror.neu.edu.cn/CentALT/6/i386/centalt-release-6-1.noarch.rpm',
                'http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-10.el6.centos.12.3.i686.rpm'
                ),
            'i686':   (
                'http://mirror.neu.edu.cn/CentALT/6/i386/centalt-release-6-1.noarch.rpm',
                'http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-10.el6.centos.12.3.i686.rpm'
                )
            }
        },
    'ius': {
        5: {
            'x86_64': ('https://dl.iuscommunity.org/pub/ius/archive/CentOS/5/x86_64/ius-release-1.0-15.ius.centos5.noarch.rpm', ),
            'i386':   ('https://dl.iuscommunity.org/pub/ius/archive/CentOS/5/i386/ius-release-1.0-15.ius.centos5.noarch.rpm', ),
            'i686':   ('https://dl.iuscommunity.org/pub/ius/archive/CentOS/5/i386/ius-release-1.0-15.ius.centos5.noarch.rpm', ),
        },
        6: {
            'x86_64': (
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/ius-release-1.0-10.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/ius-release-1.0-11.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/ius-release-1.0-12.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/ius-release-1.0-13.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/ius-release-1.0-14.ius.el6.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/CentOS/6/x86_64/ius-release-1.0-15.ius.el6.noarch.rpm'
                ),
            'i386':   (
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-10.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-11.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-12.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-13.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-14.ius.el6.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/CentOS/6/i386/ius-release-1.0-15.ius.el6.noarch.rpm'
                ),
            'i686':   (
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-10.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-11.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-12.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-13.ius.el6.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-14.ius.el6.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/CentOS/6/i386/ius-release-1.0-15.ius.el6.noarch.rpm'
                ),
            },
        7: {
            'x86_64': (
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/7/x86_64/ius-release-1.0-10.ius.el7.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/7/x86_64/ius-release-1.0-11.ius.el7.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/7/x86_64/ius-release-1.0-12.ius.el7.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/7/x86_64/ius-release-1.0-13.ius.el7.noarch.rpm',
                # 'https://dl.iuscommunity.org/pub/ius/stable/Redhat/7/x86_64/ius-release-1.0-14.ius.el7.noarch.rpm',
                'https://dl.iuscommunity.org/pub/ius/stable/CentOS/7/x86_64/ius-release-1.0-15.ius.el7.noarch.rpm'
                )
            }
        }
    }

yum_repoinstallcmds = {
    # REF: http://www.atomicorp.com/channels/atomic/
    'atomic': 'wget -q -O - http://www.atomicorp.com/installers/atomic | sed \'/check_input "Do you agree to these terms?/d\' | sh',
}
yum_repostr = {
    #     'CentALT': {
    #         6: {
    #             'x86_64': '[CentALT]\n\
    # name=CentALT Packages for Enterprise Linux 6 - $basearch\n\
    # baseurl=http://mirror.neu.edu.cn/CentALT/6/x86_64/$basearch/\n\
    # enabled=1\n\
    # gpgcheck=0'
    #         }
    #     },
    '10gen': {
        'x86_64': '[10gen]\n\
name=10gen Repository\n\
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64/RPMS\n\
gpgcheck=0\n\
enabled=1',
        'i686': '[10gen]\n\
name=10gen Repository\n\
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/i686/RPMS\n\
gpgcheck=0\n\
enabled=1',
    },
}

# Alias of package we use when get versions of it
yum_pkg_alias = {
    'nginx'         : ('nginx', 'nginx-stable', ),
    'tomcat'        : ('tomcat', ),
    'apache'        : ('httpd', ),
    'vsftpd'        : ('vsftpd', ),
    'mysql'         : ('mysql-server', 'mysql55-server', 'mariadb', ),
    'redis'         : ('redis', ),
    'memcache'      : ('memcached', ),
    'mongodb'       : ('mongodb-org', 'mongo-10gen-server', 'mongo18-10gen-server', 'mongo20-10gen-server'),
    'php'           : ('php-fpm', 'php56u-fpm', 'php70u-fpm', 'php71u-fpm', ),
    'sendmail'      : ('sendmail', ),
    'ssh'           : ('openssh-server', ),
    'iptables'      : ('iptables', ),
    'cron'          : ('cronie', 'vixie-cron', ),
    'ntp'           : ('ntp', ),
}

# Relative available packages.
# Dictionary flag:
#   default: should this pkg be installed by default
#   base: is other pkg base on this pkg
#   conflicts: what pkg this pkg would conflict with
yum_pkg_relatives = {
    'nginx'         : {
        'nginx'                 : {'default': True, 'base': True, },
    },
    'nginx-stable'  : {
        'nginx-stable'          : {'default': True, 'base': True, },
    },
    'httpd'         : {
        'httpd'                 : {'default': True, 'base': True, },
    },
    'vsftpd'         : {
        'vsftpd'                : {'default': True, 'base': True, },
    },
    'mysql-server'  : {
        'mysql-server'          : {'default': True, 'base': True, },
        'mysql'                 : {'default': True, 'base': True, },
    },
    'mysql55-server': {
        'mysql55-server'        : {'default': True, 'base': True, },
        'mysql55'               : {'default': True, 'base': True, },
    },
    'mariadb'       : {
        'mariadb-server'        : {'default': True, 'base': True, },
        'mariadb'               : {'default': True, 'base': True, },
    },
    'redis'         : {
        'redis'                 : {'default': True, 'base': True, },
    },
    'memcached'     : {
        'memcached'             : {'default': True, 'base': True, },
    },
    'mongodb-server'        : {
        'mongodb-server'        : {'default': True, 'base': True, },
        'mongodb'               : {'default': True, 'base': True, },
        'libmongodb'            : {'default': True, 'base': True, },
    },
    'mongo-10gen-server'    : {
        'mongo-10gen-server'    : {'default': True, 'base': True, },
        'mongo-10gen'           : {'default': True, 'base': True, },
    },
    'mongo18-10gen-server'  : {
        'mongo18-10gen-server'  : {'default': True, 'base': True, },
        'mongo18-10gen'         : {'default': True, 'base': True, },
    },
    'mongo20-10gen-server'  : {
        'mongo20-10gen-server'  : {'default': True, 'base': True, },
        'mongo20-10gen'         : {'default': True, 'base': True, },
    },
    'php-fpm'       : {
        'php'                   : {'default': True, 'base': True, 'conflicts': ('php56u', 'php70u','php71u', ), },
        'php-bcmath'            : {'default': True, 'isext': True, },
        'php-cli'               : {'default': True, },
        'php-common'            : {'default': True, 'base': True, },
        'php-dba'               : {'default': False, 'isext': True, },
        'php-devel'             : {'default': False, 'isext': True, },
        'php-eaccelerator'      : {'default': False, 'isext': True, },
        'php-fpm'               : {'default': True, },
        'php-gd'                : {'default': True, 'isext': True, },
        'php-imap'              : {'default': False, 'isext': True, },
        'php-interbase'         : {'default': False, 'isext': True, },
        'php-intl'              : {'default': False, 'isext': True, },
        'php-ioncube'           : {'default': False, 'isext': True, },
        'php-ldap'              : {'default': False, 'isext': True, },
        'php-magickwand'        : {'default': False, 'isext': True, },
        'php-mbstring'          : {'default': True, 'isext': True, },
        'php-mcrypt'            : {'default': True, 'isext': True, },
        'php-mssql'             : {'default': False, 'isext': True, },
        'php-mysql'             : {'default': True, 'isext': True, 'conflicts': ('php-mysqlnd', ), },
        'php-mysqlnd'           : {'default': False, 'isext': True, 'conflicts': ('php-mysql', ), },
        'php-odbc'              : {'default': False, 'isext': True, },
        'php-pdo'               : {'default': True, 'isext': True, },
        'php-pear'              : {'default': False, },
        'php-pecl-amqp'         : {'default': False, 'isext': True, },
        'php-pecl-apc'          : {'default': False, 'isext': True, },
        'php-pecl-geoip'        : {'default': False, 'isext': True, },
        'php-pecl-gmagick'      : {'default': False, 'isext': True, },
        'php-pecl-imagick'      : {'default': False, 'isext': True, },
        'php-pecl-lzf'          : {'default': False, 'isext': True, },
        'php-pecl-mailparse'    : {'default': False, 'isext': True, },
        'php-pecl-memcache'     : {'default': False, 'isext': True, },
        'php-pecl-memcached'    : {'default': False, 'isext': True, },
        'php-pecl-mongo'        : {'default': False, 'isext': True, },
        'php-pecl-ncurses'      : {'default': False, 'isext': True, },
        'php-pecl-oauth'        : {'default': False, 'isext': True, },
        'php-pecl-radius'       : {'default': False, 'isext': True, },
        'php-pecl-rrd'          : {'default': False, 'isext': True, },
        'php-pecl-sphinx'       : {'default': False, 'isext': True, },
        'php-pecl-ssh2'         : {'default': False, 'isext': True, },
        'php-pecl-xdebug'       : {'default': False, 'isext': True, },
        'php-pecl-xhprof'       : {'default': False, 'isext': True, },
        'php-pgsql'             : {'default': False, 'isext': True, },
        'php-process'           : {'default': False, 'isext': True, },
        'php-pspell'            : {'default': False, 'isext': True, },
        'php-recode'            : {'default': False, 'isext': True, },
        'php-snmp'              : {'default': False, 'isext': True, },
        'php-soap'              : {'default': True, 'isext': True, },
        'php-suhosin'           : {'default': False, 'isext': True, },
        'php-xml'               : {'default': True, 'isext': True, },
        'php-xmlrpc'            : {'default': False, 'isext': True, },
        'php-zipstream'         : {'default': False, 'isext': True, },
        'php-zmq'               : {'default': False, 'isext': True, }
    },
    'php56u-fpm'        : {
        'php56u'                : {'default': True, 'base': True, 'conflicts': ('php', 'php70u','php71u')},
        'php56u-bcmath'         : {'default': True, 'isext': True, },
        'php56u-cli'            : {'default': True, },
        'php56u-common'         : {'default': True, 'base': True, },
        'php56u-dba'            : {'default': False, 'isext': True, },
        'php56u-devel'          : {'default': False, 'isext': True, },
        'php56u-eaccelerator'   : {'default': False, 'isext': True, },
        'php56u-fpm'            : {'default': True, },
        'php56u-gd'             : {'default': True, 'isext': True, },
        'php56u-imap'           : {'default': False, 'isext': True, },
        'php56u-interbase'      : {'default': False, 'isext': True, },
        'php56u-intl'           : {'default': False, 'isext': True, },
        'php56u-ioncube-loader' : {'default': False, 'isext': True, },
        'php56u-ldap'           : {'default': False, 'isext': True, },
        'php56u-mbstring'       : {'default': True, 'isext': True, },
        'php56u-mcrypt'         : {'default': True, 'isext': True, },
        'php56u-mssql'          : {'default': False, 'isext': True, },
        'php56u-mysql'          : {'default': True, 'isext': True, },
        'php56u-odbc'           : {'default': False, 'isext': True, },
        'php56u-pdo'            : {'default': True, 'isext': True, },
        'php56u-pear'           : {'default': False, },
        'php56u-pecl-apc'       : {'default': False, 'isext': True, },
        'php56u-pecl-geoip'     : {'default': False, 'isext': True, },
        'php56u-pecl-imagick'   : {'default': False, 'isext': True, },
        'php56u-pecl-memcache'  : {'default': False, 'isext': True, },
        'php56u-pecl-memcached' : {'default': False, 'isext': True, },
        'php56u-pecl-xdebug'    : {'default': False, 'isext': True, },
        'php56u-pgsql'          : {'default': False, 'isext': True, },
        'php56u-process'        : {'default': False, 'isext': True, },
        'php56u-pspell'         : {'default': False, 'isext': True, },
        'php56u-recode'         : {'default': False, 'isext': True, },
        'php56u-snmp'           : {'default': False, 'isext': True, },
        'php56u-soap'           : {'default': True, 'isext': True, },
        'php56u-suhosin'        : {'default': False, 'isext': True, },
        'php56u-xcache'         : {'default': False, 'isext': True, },
        'php56u-xml'            : {'default': True, 'isext': True, },
        'php56u-xmlrpc'         : {'default': False, 'isext': True, }
    },
    'php70u-fpm'         : {
        'php70u'                 : {'default': True, 'base': True, 'conflicts': ('php', 'php56u','php71u')},
        'php70u-bcmath'          : {'default': True, 'isext': True, },
        'php70u-cli'             : {'default': True, },
        'php70u-common'          : {'default': True, 'base': True, },
        'php70u-dba'             : {'default': False, 'isext': True, },
        'php70u-devel'           : {'default': False, 'isext': True, },
        'php70u-fpm'             : {'default': True, },
        'php70u-gd'              : {'default': True, 'isext': True, },
        'php70u-imap'            : {'default': False, 'isext': True, },
        'php70u-interbase'       : {'default': False, 'isext': True, },
        'php70u-intl'            : {'default': False, 'isext': True, },
        'php70u-ldap'            : {'default': False, 'isext': True, },
        'php70u-ioncube-loader'  : {'default': False, 'isext': True, },
        'php70u-mbstring'        : {'default': True,'isext': True,  },
        'php70u-mcrypt'          : {'default': True, 'isext': True, },
        'php70u-mssql'           : {'default': False, 'isext': True, },
        'php70u-mysql'           : {'default': True, 'isext': True, 'conflicts': ('php70u-mysqlnd')},
        'php70u-mysqlnd'         : {'default': False, 'isext': True, 'conflicts': ('php70u-mysql')},
        'php70u-odbc'            : {'default': False, 'isext': True, },
        'php70u-pdo'             : {'default': True, 'isext': True, },
        'php70u-pear'            : {'default': False, },
        'php70u-pecl-apc'        : {'default': False, 'isext': True, },
        'php70u-pecl-geoip'      : {'default': False, 'isext': True, },
        'php70u-pecl-imagick'    : {'default': False, 'isext': True, },
        'php70u-pecl-memcache'   : {'default': False, 'isext': True, },
        'php70u-pecl-mysqlnd-ms' : {'default': False, 'isext': True, },
        'php70u-pecl-xdebug'     : {'default': False, 'isext': True, },
        'php70u-pgsql'           : {'default': False, 'isext': True, },
        'php70u-process'         : {'default': False, 'isext': True, },
        'php70u-pspell'          : {'default': False, 'isext': True, },
        'php70u-recode'          : {'default': False, 'isext': True, },
        'php70u-snmp'            : {'default': False, 'isext': True, },
        'php70u-soap'            : {'default': True, 'isext': True, },
        'php70u-suhosin'         : {'default': False, 'isext': True, },
        'php70u-xcache'          : {'default': False, 'isext': True, },
        'php70u-xml'             : {'default': True, 'isext': True, },
        'php70u-xmlrpc'          : {'default': False, 'isext': True, }
    },
    'php71u-fpm'         : {
        'php71u'                 : {'default': True, 'base': True, 'conflicts': ('php', 'php56u', 'php70u')},
        'php71u-bcmath'          : {'default': True, 'isext': True, },
        'php71u-cli'             : {'default': True, },
        'php71u-common'          : {'default': True, 'base': True, },
        'php71u-dba'             : {'default': False, 'isext': True, },
        'php71u-devel'           : {'default': False, 'isext': True, },
        'php71u-fpm'             : {'default': True, },
        'php71u-gd'              : {'default': True, 'isext': True, },
        'php71u-imap'            : {'default': False, 'isext': True, },
        'php71u-interbase'       : {'default': False, 'isext': True, },
        'php71u-intl'            : {'default': False, 'isext': True, },
        'php71u-ldap'            : {'default': False, 'isext': True, },
        'php71u-json'             : {'default': False, 'isext': True, },
        'php71u-ioncube-loader'  : {'default': False, 'isext': True, },
        'php71u-mbstring'        : {'default': True,'isext': True,  },
        'php71u-mcrypt'          : {'default': True, 'isext': True, },
        'php71u-mssql'           : {'default': False, 'isext': True, },
        'php71u-mysql'           : {'default': True, 'isext': True, 'conflicts': ('php71u-mysqlnd')},
        'php71u-mysqlnd'         : {'default': False, 'isext': True, 'conflicts': ('php71u-mysql')},
        'php71u-odbc'            : {'default': False, 'isext': True, },
        'php71u-pdo'             : {'default': True, 'isext': True, },
        'php71u-pear'            : {'default': False, },
        'php71u-pecl-apcu'       : {'default': False, 'isext': True, },
        'php71u-pecl-geoip'      : {'default': False, 'isext': True, },
        'php71u-pecl-igbinary'   : {'default': False, 'isext': True, },
        'php71u-pecl-imagick'    : {'default': False, 'isext': True, },
        'php71u-pecl-mongodb'    : {'default': False, 'isext': True, },
        'php71u-pecl-redis'      : {'default': False, 'isext': True, },
        'php71u-pecl-xdebug'     : {'default': False, 'isext': True, },
        'php71u-pgsql'           : {'default': False, 'isext': True, },
        'php71u-process'         : {'default': False, 'isext': True, },
        'php71u-pspell'          : {'default': False, 'isext': True, },
        'php71u-recode'          : {'default': False, 'isext': True, },
        'php71u-snmp'            : {'default': False, 'isext': True, },
        'php71u-soap'            : {'default': True, 'isext': True, },
        'php71u-tidy'            : {'default': False, 'isext': True, },
        # 'php71u-xcache'          : {'default': False, 'isext': True, },
        'php71u-xml'             : {'default': True, 'isext': True, },
        'php71u-xmlrpc'          : {'default': False, 'isext': True, }
    },
    'sendmail'      : {
        'sendmail'              : {'default': True, 'base': True, },
    },
    'openssh-server': {
        'openssh-server'        : {'default': True, 'base': True, },
    },
    'iptables'      : {
        'iptables'              : {'default': True, 'base': True, },
    },
    'cronie'        : {
        'cronie'                : {'default': True, 'base': True, },
    },
    'vixie-cron'    : {
        'vixie-cron'            : {'default': True, 'base': True, },
    },
    'ntp'           : {
        'ntp'                   : {'default': True, 'base': True, },
    },
    # some tools
    'zip'           : {
        'zip'                   : {'default': True, 'base': True, },
        'unzip'                 : {'default': True, 'base': True, },
    },
}