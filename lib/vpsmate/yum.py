#-*- coding: utf-8 -*-
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
                'http://mirror.centos.org/centos/5/os/x86_64/CentOS/centos-release-notes-5.8-0.x86_64.rpm',
                'http://mirror.centos.org/centos/5/os/x86_64/CentOS/centos-release-5-8.el5.centos.x86_64.rpm',
            ),
            'i386': (
                'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-notes-5.8-0.i386.rpm',
                'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-5-8.el5.centos.i386.rpm',
            ),
            'i686': (
                'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-notes-5.8-0.i386.rpm',
                'http://mirror.centos.org/centos/5/os/i386/CentOS/centos-release-5-8.el5.centos.i386.rpm',
            ),
        },
        6: {
            'x86_64': ('http://mirror.centos.org/centos/6/os/x86_64/Packages/centos-release-6-3.el6.centos.9.x86_64.rpm', ),
            'i386':   ('http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-3.el6.centos.9.i686.rpm', ),
            'i686':   ('http://mirror.centos.org/centos/6/os/i386/Packages/centos-release-6-3.el6.centos.9.i686.rpm', ),
        }
    },
    'epel': {
        5: {
            'x86_64': ('http://dl.fedoraproject.org/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm', ),
            'i386':   ('http://dl.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm', ),
            'i686':   ('http://dl.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm', ),
        },
        6: {
            'x86_64': ('http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm', ),
            'i386':   ('http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm', ),
            'i686':   ('http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm', ),
        },
    },
    'CentALT': {
        5: {
            #'x86_64': ('http://centos.alt.ru/repository/centos/5/x86_64/centalt-release-5-3.noarch.rpm', ),
            #'i386':   ('http://centos.alt.ru/repository/centos/5/i386/centalt-release-5-3.noarch.rpm', ),
            #'i686':   ('http://centos.alt.ru/repository/centos/5/i386/centalt-release-5-3.noarch.rpm', ),
            'x86_64': ('http://mirrors.vpsmate.org/CentALT/repository/centos/5/x86_64/centalt-release-5-3.noarch.rpm', ),
            'i386':   ('http://mirrors.vpsmate.org/CentALT/repository/centos/5/i386/centalt-release-5-3.noarch.rpm', ),
            'i686':   ('http://mirrors.vpsmate.org/CentALT/repository/centos/5/i386/centalt-release-5-3.noarch.rpm', ),
        },
        6: {
            #'x86_64': ('http://centos.alt.ru/pub/repository/centos/6/x86_64/centalt-release-6-1.noarch.rpm', ),
            #'i386':   ('http://centos.alt.ru/pub/repository/centos/6/i386/centalt-release-6-1.noarch.rpm', ),
            #'i686':   ('http://centos.alt.ru/pub/repository/centos/6/i386/centalt-release-6-1.noarch.rpm', ),
            'x86_64': ('http://mirrors.vpsmate.org/CentALT/repository/centos/6/x86_64/centalt-release-6-1.noarch.rpm', ),
            'i386':   ('http://mirrors.vpsmate.org/CentALT/repository/centos/6/i386/centalt-release-6-1.noarch.rpm', ),
            'i686':   ('http://mirrors.vpsmate.org/CentALT/repository/centos/6/i386/centalt-release-6-1.noarch.rpm', ),
        },
    },
    'ius': {
        5: {
            'x86_64': ('http://dl.iuscommunity.org/pub/ius/stable/Redhat/5/x86_64/ius-release-1.0-10.ius.el5.noarch.rpm', ),
            'i386':   ('http://dl.iuscommunity.org/pub/ius/stable/Redhat/5/i386/ius-release-1.0-10.ius.el5.noarch.rpm', ),
            'i686':   ('http://dl.iuscommunity.org/pub/ius/stable/Redhat/5/i386/ius-release-1.0-10.ius.el5.noarch.rpm', ),
        },
        6: {
            'x86_64': ('http://dl.iuscommunity.org/pub/ius/stable/Redhat/6/x86_64/ius-release-1.0-10.ius.el6.noarch.rpm', ),
            'i386':   ('http://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-10.ius.el6.noarch.rpm', ),
            'i686':   ('http://dl.iuscommunity.org/pub/ius/stable/Redhat/6/i386/ius-release-1.0-10.ius.el6.noarch.rpm', ),
        },
    },
}
yum_repoinstallcmds = {
    # REF: http://www.atomicorp.com/channels/atomic/
    'atomic': 'wget -q -O - http://www.atomicorp.com/installers/atomic | sed \'/check_input "Do you agree to these terms?/d\' | sh',
}
yum_repostr = {
    '10gen': {
        'x86_64': '[10gen]\n\
name=10gen Repository\n\
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64\n\
gpgcheck=0\n\
enabled=1',
        'i386': '[10gen]\n\
name=10gen Repository\n\
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/i686\n\
gpgcheck=0\n\
enabled=1',
    },
}

# Alias of package we use when get versions of it
yum_pkg_alias = {
    'nginx'         : ('nginx', 'nginx-stable', ),
    'apache'        : ('httpd', ),
    'vsftpd'        : ('vsftpd', ),
    'mysql'         : ('mysql-server', 'mysql55-server', ),
    'redis'         : ('redis', ),
    'memcache'      : ('memcached', ),
    'mongodb'       : ('mongodb-server', 'mongo-10gen-server', 'mongo18-10gen-server', 'mongo20-10gen-server'),
    'php'           : ('php-fpm', 'php53u-fpm', 'php54-fpm', ),
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
        'php'                   : {'default': True, 'base': True, 'conflicts': ('php53u', 'php54', ), },
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
        'php-simplepie'         : {'default': False, 'isext': True, },
        'php-snmp'              : {'default': False, 'isext': True, },
        'php-soap'              : {'default': True, 'isext': True, },
        'php-suhosin'           : {'default': False, 'isext': True, },
        'php-xml'               : {'default': True, 'isext': True, },
        'php-xmlrpc'            : {'default': False, 'isext': True, },
        'php-zipstream'         : {'default': False, 'isext': True, },
        'php-zmq'               : {'default': False, 'isext': True, },
        'php-zts'               : {'default': False, 'isext': True, },
        'php-zend-guard-loader' : {'default': False, 'isext': True, },
    },
    'php53u-fpm'        : {
        'php53u'                : {'default': True, 'base': True, 'conflicts': ('php', 'php54', ), },
        'php53u-bcmath'         : {'default': True, 'isext': True, },
        'php53u-cli'            : {'default': True, },
        'php53u-common'         : {'default': True, 'base': True, },
        'php53u-dba'            : {'default': False, 'isext': True, },
        'php53u-devel'          : {'default': False, 'isext': True, },
        'php53u-eaccelerator'   : {'default': False, 'isext': True, },
        'php53u-fpm'            : {'default': True, },
        'php53u-gd'             : {'default': True, 'isext': True, },
        'php53u-imap'           : {'default': False, 'isext': True, },
        'php53u-interbase'      : {'default': False, 'isext': True, },
        'php53u-intl'           : {'default': False, 'isext': True, },
        'php53u-ioncube-loader' : {'default': False, 'isext': True, },
        'php53u-ldap'           : {'default': False, 'isext': True, },
        'php53u-mbstring'       : {'default': True, 'isext': True, },
        'php53u-mcrypt'         : {'default': True, 'isext': True, },
        'php53u-mssql'          : {'default': False, 'isext': True, },
        'php53u-mysql'          : {'default': True, 'isext': True, },
        'php53u-odbc'           : {'default': False, 'isext': True, },
        'php53u-pdo'            : {'default': True, 'isext': True, },
        'php53u-pear'           : {'default': False, },
        'php53u-pecl-apc'       : {'default': False, 'isext': True, },
        'php53u-pecl-geoip'     : {'default': False, 'isext': True, },
        'php53u-pecl-imagick'   : {'default': False, 'isext': True, },
        'php53u-pecl-memcache'  : {'default': False, 'isext': True, },
        'php53u-pecl-memcached' : {'default': False, 'isext': True, },
        'php53u-pecl-xdebug'    : {'default': False, 'isext': True, },
        'php53u-pgsql'          : {'default': False, 'isext': True, },
        'php53u-process'        : {'default': False, 'isext': True, },
        'php53u-pspell'         : {'default': False, 'isext': True, },
        'php53u-recode'         : {'default': False, 'isext': True, },
        'php53u-simplepie'      : {'default': False, 'isext': True, },
        'php53u-snmp'           : {'default': False, 'isext': True, },
        'php53u-soap'           : {'default': True, 'isext': True, },
        'php53u-suhosin'        : {'default': False, 'isext': True, },
        'php53u-xcache'         : {'default': False, 'isext': True, },
        'php53u-xml'            : {'default': True, 'isext': True, },
        'php53u-xmlrpc'         : {'default': False, 'isext': True, },
        'php53u-zts'            : {'default': False, 'isext': True, },
        'php-zend-guard-loader' : {'default': False, 'isext': True, },
    },
    'php54-fpm'         : {
        'php54'                 : {'default': True, 'base': True, 'conflicts': ('php', 'php53u', ), },
        'php54-bcmath'          : {'default': True, 'isext': True, },
        'php54-cli'             : {'default': True, },
        'php54-common'          : {'default': True, 'base': True, },
        'php54-dba'             : {'default': False, 'isext': True, },
        'php54-devel'           : {'default': False, 'isext': True, },
        'php54-fpm'             : {'default': True, },
        'php54-gd'              : {'default': True, 'isext': True, },
        'php54-imap'            : {'default': False, 'isext': True, },
        'php54-interbase'       : {'default': False, 'isext': True, },
        'php54-intl'            : {'default': False, 'isext': True, },
        'php54-ldap'            : {'default': False, 'isext': True, },
        'php54-ioncube-loader'  : {'default': False, 'isext': True, },
        'php54-mbstring'        : {'default': True,'isext': True,  },
        'php54-mcrypt'          : {'default': True, 'isext': True, },
        'php54-mssql'           : {'default': False, 'isext': True, },
        'php54-mysql'           : {'default': True, 'isext': True, 'conflicts': ('php54-mysqlnd', ), },
        'php54-mysqlnd'         : {'default': False, 'isext': True, 'conflicts': ('php54-mysql', ), },
        'php54-odbc'            : {'default': False, 'isext': True, },
        'php54-pdo'             : {'default': True, 'isext': True, },
        'php54-pear'            : {'default': False, },
        'php54-pecl-apc'        : {'default': False, 'isext': True, },
        'php54-pecl-geoip'      : {'default': False, 'isext': True, },
        'php54-pecl-imagick'    : {'default': False, 'isext': True, },
        'php54-pecl-memcache'   : {'default': False, 'isext': True, },
        'php54-pecl-mysqlnd-ms' : {'default': False, 'isext': True, },
        'php54-pecl-xdebug'     : {'default': False, 'isext': True, },
        'php54-pgsql'           : {'default': False, 'isext': True, },
        'php54-pgsql84'         : {'default': False, 'isext': True, },
        'php54-process'         : {'default': False, 'isext': True, },
        'php54-pspell'          : {'default': False, 'isext': True, },
        'php54-recode'          : {'default': False, 'isext': True, },
        'php54-simplepie'       : {'default': False, 'isext': True, },
        'php54-snmp'            : {'default': False, 'isext': True, },
        'php54-soap'            : {'default': True, 'isext': True, },
        'php54-suhosin'         : {'default': False, 'isext': True, },
        'php54-xcache'          : {'default': False, 'isext': True, },
        'php54-xml'             : {'default': True, 'isext': True, },
        'php54-xmlrpc'          : {'default': False, 'isext': True, },
        'php54-zts'             : {'default': False, 'isext': True, },
        'php-zend-guard-loader' : {'default': False, 'isext': True, },
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