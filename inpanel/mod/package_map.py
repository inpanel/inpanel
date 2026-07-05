# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
'''Module for Package Name Mapping'''

PACKAGE_MAP = {
    "nginx": {
        "rhel": "nginx",
        "debian": "nginx"
    },
    "mariadb": {
        "rhel": "mariadb-server",
        "debian": "mariadb-server"
    },
    "mysql": {
        "rhel": "mariadb-server",
        "debian": "default-mysql-server"
    },
    "mysql-community": {
        "rhel": "mysql-community-server",
        "debian": "mysql-server"
    },
    "php": {
        "rhel": "php",
        "debian": "php"
    },
    "php-fpm": {
        "rhel": "php-fpm",
        "debian": "php-fpm"
    },
    "php-cli": {
        "rhel": "php-cli",
        "debian": "php-cli"
    },
    "php-mysql": {
        "rhel": "php-mysqlnd",
        "debian": "php-mysql"
    },
    "php-pdo": {
        "rhel": "php-pdo",
        "debian": "php-pdo"
    },
    "php-mbstring": {
        "rhel": "php-mbstring",
        "debian": "php-mbstring"
    },
    "php-xml": {
        "rhel": "php-xml",
        "debian": "php-xml"
    },
    "php-gd": {
        "rhel": "php-gd",
        "debian": "php-gd"
    },
    "php-curl": {
        "rhel": "php-curl",
        "debian": "php-curl"
    },
    "php-zip": {
        "rhel": "php-zip",
        "debian": "php-zip"
    },
    "php-intl": {
        "rhel": "php-intl",
        "debian": "php-intl"
    },
    "php-redis": {
        "rhel": "php-pecl-redis",
        "debian": "php-redis"
    },
    "php-memcached": {
        "rhel": "php-pecl-memcached",
        "debian": "php-memcached"
    },
    "git": {
        "rhel": "git",
        "debian": "git"
    },
    "wget": {
        "rhel": "wget",
        "debian": "wget"
    },
    "curl": {
        "rhel": "curl",
        "debian": "curl"
    },
    "vim": {
        "rhel": "vim-enhanced",
        "debian": "vim"
    },
    "rsync": {
        "rhel": "rsync",
        "debian": "rsync"
    },
    "net-tools": {
        "rhel": "net-tools",
        "debian": "net-tools"
    },
    "epel-release": {
        "rhel": "epel-release",
        "debian": ""
    },
    "remi-release": {
        "rhel": "remi-release",
        "debian": ""
    },
    "sury-php": {
        "rhel": "",
        "debian": "ca-certificates apt-transport-https software-properties-common"
    },
    "python3": {
        "rhel": "python3",
        "debian": "python3"
    },
    "python3-pip": {
        "rhel": "python3-pip",
        "debian": "python3-pip"
    },
    "python3-devel": {
        "rhel": "python3-devel",
        "debian": "python3-dev"
    },
    "gcc": {
        "rhel": "gcc",
        "debian": "gcc"
    },
    "make": {
        "rhel": "make",
        "debian": "make"
    },
    "cmake": {
        "rhel": "cmake",
        "debian": "cmake"
    },
    "autoconf": {
        "rhel": "autoconf",
        "debian": "autoconf"
    },
    "automake": {
        "rhel": "automake",
        "debian": "automake"
    },
    "libtool": {
        "rhel": "libtool",
        "debian": "libtool"
    },
    "libxslt": {
        "rhel": "libxslt-devel",
        "debian": "libxslt1-dev"
    },
    "libxml2": {
        "rhel": "libxml2-devel",
        "debian": "libxml2-dev"
    },
    "libcurl": {
        "rhel": "libcurl-devel",
        "debian": "libcurl4-openssl-dev"
    },
    "openssl": {
        "rhel": "openssl-devel",
        "debian": "libssl-dev"
    },
    "zlib": {
        "rhel": "zlib-devel",
        "debian": "zlib1g-dev"
    },
    "bzip2": {
        "rhel": "bzip2-devel",
        "debian": "libbz2-dev"
    },
    "libpng": {
        "rhel": "libpng-devel",
        "debian": "libpng-dev"
    },
    "libjpeg": {
        "rhel": "libjpeg-turbo-devel",
        "debian": "libjpeg-dev"
    },
    "freetype": {
        "rhel": "freetype-devel",
        "debian": "libfreetype6-dev"
    },
    "GeoIP": {
        "rhel": "GeoIP-devel",
        "debian": "libgeoip-dev"
    },
    "gd": {
        "rhel": "gd-devel",
        "debian": "libgd-dev"
    },
    "icu": {
        "rhel": "icu-devel",
        "debian": "libicu-dev"
    },
    "sqlite": {
        "rhel": "sqlite-devel",
        "debian": "libsqlite3-dev"
    },
    "postgresql": {
        "rhel": "postgresql-server",
        "debian": "postgresql"
    },
    "mongodb": {
        "rhel": "mongodb-server",
        "debian": "mongodb"
    },
    "redis": {
        "rhel": "redis",
        "debian": "redis-server"
    },
    "memcached": {
        "rhel": "memcached",
        "debian": "memcached"
    },
    "nodejs": {
        "rhel": "nodejs",
        "debian": "nodejs"
    },
    "npm": {
        "rhel": "npm",
        "debian": "npm"
    },
    "certbot": {
        "rhel": "certbot",
        "debian": "certbot"
    },
    "fail2ban": {
        "rhel": "fail2ban",
        "debian": "fail2ban"
    },
    "htop": {
        "rhel": "htop",
        "debian": "htop"
    },
    "ncdu": {
        "rhel": "ncdu",
        "debian": "ncdu"
    },
    "screen": {
        "rhel": "screen",
        "debian": "screen"
    },
    "tmux": {
        "rhel": "tmux",
        "debian": "tmux"
    },
    "ntp": {
        "rhel": "chrony",
        "debian": "chrony"
    },
    "firewalld": {
        "rhel": "firewalld",
        "debian": "ufw"
    },
    "iptables": {
        "rhel": "iptables-services",
        "debian": "iptables"
    },
    "logrotate": {
        "rhel": "logrotate",
        "debian": "logrotate"
    },
    "cron": {
        "rhel": "cronie",
        "debian": "cron"
    },
    "openssh": {
        "rhel": "openssh-server",
        "debian": "openssh-server"
    },
    "sshd": {
        "rhel": "openssh-server",
        "debian": "openssh-server"
    }
}


def resolve_package_names(pm, base_names: list[str]) -> list[str]:
    """根据包管理器类型解析实际包名"""
    os_type = pm.get_os_type()
    resolved = []
    for name in base_names:
        if name in PACKAGE_MAP and os_type in PACKAGE_MAP[name]:
            pkg_name = PACKAGE_MAP[name][os_type]
            if pkg_name:
                resolved.append(pkg_name)
        else:
            resolved.append(name)
    return resolved


def is_installed(pm, package: str) -> bool:
    """检查包是否已安装"""
    success, output = pm.list_installed()
    if not success:
        return False
    package = package.lower()
    for line in output.split('\n'):
        if package in line.lower():
            return True
    return False


def install_if_not_exists(pm, packages: list[str]) -> tuple[bool, str]:
    """只安装未安装的包"""
    resolved = resolve_package_names(pm, packages)
    to_install = []
    for pkg in resolved:
        if not is_installed(pm, pkg):
            to_install.append(pkg)
    if not to_install:
        return (True, "All packages already installed")
    return pm.install(to_install)


def parse_search_output(output: str) -> list[dict]:
    """解析搜索命令输出，返回包列表"""
    packages = []
    lines = output.split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            pkg_name = parts[0]
            description = ' '.join(parts[1:]) if len(parts) > 1 else ''
            packages.append({'name': pkg_name, 'description': description})
    return packages


def parse_list_installed_output(output: str) -> list[dict]:
    """解析已安装包列表输出"""
    packages = []
    lines = output.split('\n')
    for line in lines:
        if not line.strip():
            continue
        if line.startswith('Desired=') or line.startswith('+++') or line.startswith('ii ') or line.startswith('Installed'):
            parts = line.split()
            if len(parts) >= 2:
                if line.startswith('ii '):
                    pkg_name = parts[1]
                    version = parts[2] if len(parts) > 2 else ''
                elif line.startswith('Installed'):
                    continue
                else:
                    continue
                packages.append({'name': pkg_name, 'version': version})
    return packages


def parse_info_output(output: str) -> dict:
    """解析包信息输出"""
    info = {}
    lines = output.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info