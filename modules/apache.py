# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Apache Management.'''


import json
import os
import os.path
import re
import string

# import glob
# import sys
# import shutil
from utils import is_valid_domain, is_valid_ipv4, is_valid_ipv6

try:
    from io import StringIO
except:
    from cStringIO import StringIO


DEBUG = False

HTTPD_CONF_DIR = '/etc/httpd/'
# HTTPD_CONF_DIR = '/Users/douzhenjiang/Projects/inpanel/'
HTTPD_CONF = '/etc/httpd/conf/httpd.conf'
SERVERCONF = '/etc/httpd/conf.d/'
COMMENTFLAG = '#v#'
GENBY = 'GENDBYINPANEL'
ABC = '/etc/httpd/conf.d/abc.com.conf'

CONFIGS = {
    'ServerTokens': 'OS',
    'ServerRoot': '/etc/httpd',
    'Timeout': 60,
    'DefaultType': 'text/plain',
    'DocumentRoot': '/var/www/html',
    'DirectoryIndex': 'index.html index.html.var',
    'AddDefaultCharset': 'UTF-8',
    'Listen': 80,
    'ServerAdmin': 'root@localhost',
    'ServerName': 'www@localhost',
    'NameVirtualHost': '*:80',
    'KeepAlive': 'Off',
    'MaxKeepAliveRequests': 100,
    'KeepAliveTimeout': 15,
    'UseCanonicalName': 'Off',
    'AccessFileName': '.htaccess',
    'TypesConfig': '/etc/mime.types',
    'ErrorLog': 'logs/error_log',
    'LogLevel': 'debug',  # info, notice, warn, error, crit, alert, emerg
    'ServerSignature': 'On',
    'IndexOptions': 'FancyIndexing VersionSort NameWidth=* HTMLTable Charset=UTF-8',
    'Alias': 'alias',
    'AddLanguage': '',
    'LoadModule': '',
    'ScriptAlias': '',
    'AddType': '',
    'AddIcon': '',
    'AddIconByType': ''
}
CON_DIRECTIVES = {
    'Directory': '',
    'Files': '',
    'Limit': '',
    'Location': '',
    'VirtualHost': '',
    'IfModule': ''
}
VH_OPTIONS = {
    'CustomLog': '',
    'ServerAdmin': 'admin@localhost',
    'ServerName': '',
    'DirectoryIndex': 'index.html',
    'DocumentRoot': '/var/www',
    'ErrorLog': '',
    'Options': '',
    'ServerAlias': [],
    'Location': '',
    'SuexecUserGroup': '',
}
DIRECTORY = {
    'Options': 'Indexes FollowSymLinks MultiViews',
    'AllowOverride': 'None',
    'Order': 'allow,deny',
    'Allow': 'from all',
}
VH_TMP = '''<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www
    <Directory />
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    <Directory /var/www/>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride None
        Order allow,deny
        allow from all
    </Directory>
</VirtualHost>
'''

GZIP = '''<IfModule mod_deflate.c>
    DeflateCompressionLevel 6
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/php
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE text/javascript
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/atom_xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
    AddOutputFilterByType DEFLATE application/x-httpd-php
    AddOutputFilterByType DEFLATE application/x-font-ttf
    AddOutputFilterByType DEFLATE image/svg+xml
    AddOutputFilterByType DEFLATE image/gif image/png image/jpe image/swf image/jpeg image/bmp
    # Don’t compress images and other
    BrowserMatch ^Mozilla/4 gzip-only-text/html
    BrowserMatch ^Mozilla/4\.0[678] no-gzip
    BrowserMatch \bMSIE !no-gzip !gzip-only-text/html
    SetEnvIfNoCase Request_URI .(?:html|htm)$ no-gzip dont-varySetEnvIfNoCase 
    #SetEnvIfNoCase Request_URI .(?:gif|jpe?g|png)$ no-gzip dont-vary
    SetEnvIfNoCase Request_URI .(?:exe|t?gz|zip|bz2|sit|rar)$ no-gzip dont-vary
    SetEnvIfNoCase Request_URI .(?:pdf|doc)$ no-gzip dont-vary
</IfModule>'''

RE_VH_START = re.compile(r'<VirtualHost(\s+)(\S+)>')
RE_VH_CLOSE = re.compile(r'</VirtualHost>')
RE_DT_START = re.compile(r'<Directory(\s+)(\S+)>')
RE_DT_CLOSE = re.compile(r'</Directory>')


def getservers(config=None):
    '''Get servers from apache configuration files.
    '''

    servers = []
    # SERVERCONF = '/Users/douzhenjiang/Projects/inpanel/test'
    # aaa = '/etc/httpd/conf.d/aaa.com.conf'
    # bbb = '/etc/httpd/conf.d/bbb.com.conf'

    clist = os.listdir(SERVERCONF)  # 列出文件夹下所有的目录与文件
    for i in range(0, len(clist)):
        path = os.path.join(SERVERCONF, clist[i])
        if os.path.isfile(path) and os.path.splitext(path)[1] == '.conf':
            v = _parse_virtualhost_config(path)
            if v is not False:
                servers.extend(v)

    # servers = _parse_virtualhost_config(aaa) + _parse_virtualhost_config(bbb)
    return servers


def getserver(ip, port, server_name, config=None):
    """Get server setting from nginx config files.
    """
    # if not config or config['_isdirty']:
    #     config = loadconfig(NGINXCONF, False)
    scontext = _parse_virtualhost_config(SERVERCONF + server_name + '.conf')
    if not scontext:
        return False
    return scontext[0]
    # server = {}
    # server['_inpanel'] = scontext['_inpanel']
    # server['server_names'] = []
    # if 'server_name' in scontext:
    #     for name in scontext['server_name']:
    #         server['server_names'].extend(name.split())


def _parse_virtualhost_config(conf=''):
    '''parser VirtualHost config to python object (array)
    '''
    try:
        if not conf or not os.path.isfile(conf):
            return False
    except OSError:
        return False

    with open(conf, 'r') as f:
        lines = f.readlines()
        # lines = filter(lambda i: re.search('^((?!#).)*$', i), lines)
        # print(lines)

    id_v = 0
    enable = False
    virtualHosts = []
    vhost = []
    result = {}
    id_d = 0
    enable_d = False
    v_dirs = {}
    result_d = {}
    directorys = {}  # 附加信息
    line_disabled = False
    gen_by_inpanel = False
    while len(lines) > 0:
        out = lines.pop(0)
        if out.startswith(COMMENTFLAG):
            # deal with our speical comment string
            while out.startswith(COMMENTFLAG):
                out = out[3:]
            out = out.strip()
            line_disabled = True

        if not out or out.startswith('#'):
            continue

        # deal with comment and detect inpanel flag in comment
        fields = out.split('#', 1)
        if len(fields) > 1 and fields[1].strip() == GENBY:
            gen_by_inpanel = True

        out = fields[0].strip()
        match = RE_VH_START.search(out)
        if match:  # if '<VirtualHost' in out:
            id_d = 0
            v_dirs = {}
            result_d[id_v] = []
            directorys[id_v] = []
            name_port = match.groups()[1].strip().strip('"').strip('\'')
            print(name_port)
            port = name_port.split(':')[-1]
            ip = name_port[0:-(len(port) + 1)]
            ip = ip.lstrip('[').rstrip(']')  # for IPv6
            vhost.append(ip)
            vhost.append(port)
            enable = True
            enable_d = False
            continue

        # start of Directory in VirtualHost
        match_d = RE_DT_START.search(out)
        if enable is True and match_d:
            v_dirs = {}
            path = match_d.groups()[1].strip().strip('"')
            v_dirs[id_d] = []
            v_dirs[id_d].append(path)
            enable_d = True
            continue

        # end of Directory in VirtualHost
        # if '</Directory>' in out:
        if enable_d is True and RE_DT_CLOSE.search(out):
            result_d[id_v].append(v_dirs[id_d])
            id_d += 1
            enable_d = False
            v_dirs = {}
            continue

        # merge of Directory in VirtualHost
        if enable_d:
            v_dirs[id_d].append(out)
            continue

        # end of VirtualHost
        if RE_VH_CLOSE.search(out):
            enable_d = False
            if len(vhost) > 0:
                result[id_v] = vhost
                if id_v in result_d:
                    d = _parse_directory(result_d[id_v])
                    directorys[id_v] = d
                else:
                    directorys[id_v] = []
                id_v += 1
            enable = False
            vhost = []
            continue

        # merge of VirtualHost
        if enable:
            vhost.append(out)
            continue

    # print('directorys', directorys)
    if len(result) == 0:
        return []
    for i in result:
        server = {
            'IP': result[i][0],  # IP
            'Port': result[i][1],  # Port
            'Directory': directorys[i],
            '_inpanel': gen_by_inpanel,
            'status': 'off' if line_disabled else 'on'
        }
        for line in result[i]:
            for i in VH_OPTIONS:
                if i in line:
                    if i == 'DirectoryIndex':
                        server[i] = ' '.join(str(n) for n in line.split()[1:])
                    elif i == 'ServerAlias':
                        server[i] = line.split()[1:]
                    else:
                        server[i] = line.split()[1].strip(' ').strip('"')
                    continue
        if 'ServerName' not in server or not server['ServerName']:
            server['ServerName'] = server['ServerAlias'][0]
        virtualHosts.append(server)

    return virtualHosts


def _parse_directory(directory):
    if not directory:
        return []

    results = []
    for r in directory:
        drct = {'Path': r[0]}
        for line in r:
            for i in DIRECTORY:
                if i in line:
                    if i == 'Order':
                        drct[i] = ','.join(str(n) for n in line.split()[1:])
                    elif i in ('Options', 'Allow'):
                        drct[i] = ' '.join(str(n) for n in line.split()[1:])
                    else:
                        drct[i] = line.split()[1].strip(string.punctuation)
                    continue
        results.append(drct)
    return results


def virtual_host_config(site, key, val, port=80):
    '''
    site: abc.com
    key: VirtualHost or DocumentRoot or ServerAdmin or Directory
    val: /var/www
    '''
    keys = ['VirtualHost', 'DocumentRoot', 'ServerAdmin', 'Directory']
    if key not in keys or not site or not val:
        return False

    conf = SERVERCONF + site + '.conf'
    try:
        os.stat(conf)
    except OSError:
        print('site config file not exist')
        return False

    old_conf = open(conf).read()

    with open(conf + '.bak', 'w') as f:
        # backup
        f.write(old_conf)

    if key == 'VirtualHost':
        conf = SERVERCONF + val + '.conf'
        val = str(val) + ':' + str(port)
        # os.renames(SERVERCONF + site + '.conf', conf + '.bak')

    # make new config
    new_conf = re.sub(key + ' "(.*?)"',
                      key + ' "' + val + '"',
                      old_conf)

    # save new config file
    with open(conf, 'w') as f:
        f.write(new_conf)
        # delete old site config file
        if key == 'VirtualHost' and os.stat(conf) and os.stat(SERVERCONF + site + '.conf.bak'):
            os.remove(SERVERCONF + site + '.conf')
        return True


# https://blog.csdn.net/brucemj/article/details/37933519
# https://oomake.com/question/266681


def replace_docroot(vhost, new_docroot):
    '''yield new lines of an httpd.conf file where docroot lines matching
        the specified vhost are replaced with the new_docroot
    '''
    vhost_start = re.compile(r'<VirtualHost\s+(.*?)>')
    vhost_end = re.compile(r'</VirtualHost>')
    docroot_re = re.compile(r'(DocumentRoot\s+)(\S+)')
    file = open(HTTPD_CONF_DIR + vhost + '.conf').read()
    conf_file = StringIO(file)
    in_vhost = False
    curr_vhost = None
    for line in conf_file:
        # 起始行查找host
        vhost_start_match = vhost_start.search(line)
        if vhost_start_match:
            curr_vhost = vhost_start_match.groups()[0]
            in_vhost = True
            print(curr_vhost, vhost)
        if in_vhost and (curr_vhost == vhost):
            docroot_match = docroot_re.search(line)
            if docroot_match:
                sub_line = docroot_re.sub(r'\1%s' % new_docroot, line)
                line = sub_line
            vhost_end_match = vhost_end.search(line)
            if vhost_end_match:
                in_vhost = False
            yield line


def loadconfig(conf=None, getlineinfo=False):
    """Load apache config and return a dict.
    """
    if not conf:
        conf = HTTPD_CONF
    if not os.path.exists(conf):
        return False
    return _parse_apache_config(conf, getlineinfo)


def _parse_apache_config(conf, getlineinfo):
    '''parse Apache httpd.conf'''

    # if key not in CONFIGS or not val:
    #     return False
    # conf = HTTPD_CONF
    # conf = HTTPD_CONF_DIR + '/httpd.conf'
    try:
        os.stat(conf)
    except OSError:
        return None

    configs = {}
    Alias = []
    AddLanguage = []
    LoadModule = []
    AddIcon = []
    Listen = []
    IfModule = []
    with open(conf) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            for i in CONFIGS:
                if line.startswith(i):
                    ll = line.split()
                    if i in ['IndexOptions', 'DirectoryIndex']:
                        configs[i] = ' '.join(str(n) for n in ll[1:])
                    elif i == 'AddIcon':
                        AddIcon.append([ll[1], ll[2:]])
                    elif i == 'AddIconByType':
                        configs[i] = ' '.join(str(n) for n in ll[1:])
                    elif i == 'Alias':
                        Alias.append([ll[1], ll[2].strip('"')])
                    elif i == 'AddLanguage':
                        AddLanguage.append(ll[1:])
                    elif i == 'LoadModule':
                        LoadModule.append(ll[1:])
                    elif i == 'Listen':
                        port = ll[1].split(':')[-1]
                        ip = ll[1][0:-(len(port) + 1)].lstrip('[').rstrip(']')
                        Listen.append({'port': port, 'ip': ip})
                    else:
                        # print(ll[1].strip(string.punctuation))
                        configs[i] = ll[1].strip(string.punctuation)

        configs['Alias'] = Alias
        configs['Listen'] = Listen
        configs['AddIcon'] = AddIcon
        configs['LoadModule'] = LoadModule
        configs['AddLanguage'] = AddLanguage
        configs['IfModule'] = IfModule
        configs['Gzip'] = _context_check_gzip(LoadModule, IfModule)
        return configs


def _context_check_gzip(LoadModule, IfModule):
    mod_status = (
        ['ext_filter_module', 'modules/mod_ext_filter.so'] in LoadModule and
        ['deflate_module', 'modules/mod_deflate.so'] in LoadModule and
        ['headers_module', 'modules/mod_headers.so'] in LoadModule
    )
    # check deflate config in IfModule
    mod_deflate = True
    return mod_status and mod_deflate


def _context_getservers(disabled=None, config=None, getlineinfo=True):
    """Get server context configs.
    """
    if not config or config['_isdirty']:
        config = loadconfig(HTTPD_CONF, getlineinfo)
    http = config['_'][0]['http'][0]
    if not 'server' in http:
        return []
    servers = http['server']
    if disabled == None or not getlineinfo:
        return servers
    else:
        return [server for server in servers
                if server['_param']['disabled'] == disabled]


def addserver(name, ip, port, alias=None, admin=None, root=None, index=None, directory=None, error_log=None, custom_log=None, version=None):
    '''Add a new VirtualHost.'''

    ip = ip or '*'
    if is_valid_ipv6(ip) and not is_valid_ipv4(ip):
        ip = '[' + ip + ']'
    if port:
        port = int(port) or 80
    else:
        return False
    # start generate the config string
    servercfg = ['<VirtualHost %s:%s> # %s' % (ip, port, GENBY)]
    if is_valid_domain(name):
        servercfg.append('    ServerName %s' % name)
    else:
        return False
    if root:
        servercfg.append('    DocumentRoot %s' % root)
    else:
        return False
    if admin:
        servercfg.append('    ServerAdmin %s' % admin)
    if alias:
        servercfg.append('    ServerAlias %s' % (' '.join(alias)))
    if index:
        servercfg.append('    DirectoryIndex %s' % (' '.join(index.split())))
    else:
        servercfg.append('    DirectoryIndex index.html index.htm index.php')
    if error_log:
        servercfg.append('    ErrorLog %s' % error_log)
    if custom_log:
        servercfg.append('    CustomLog %s' % custom_log)
    if directory and len(directory) > 0:
        d = _extend_directory(directory)
        servercfg.extend(['    %s' % i for i in d])
    # end of server context
    servercfg.append('</VirtualHost>')

    #print '\n'.join(servercfg)
    configfile = os.path.join(SERVERCONF, '%s.conf' % name)
    configfile_exists = os.path.exists(configfile)

    # check if need to add a new line at the end of the file to
    # avoid first line go to the same former } line
    if configfile_exists:
        with open(configfile) as f:
            f.seek(-1, 2)
            if f.read(1) != '\n':
                servercfg.insert(0, '')
    with open(configfile, configfile_exists and 'a' or 'w') as f:
        f.write('\n'.join(servercfg))
    return True


def _extend_directory(directory):
    '''extend Directory config to line for configfile.
    Usage
    ----------
    > d = _extend_directory(directory)\n
    > servercfg.extend(d) # for Apache Config\n
    > servercfg.extend(['    %s' % i for i in d]) # for VirtualHost Config
    '''
    drct_cfg = []
    for drct in directory:
        drct_cfg.append('<Directory %s>' % drct.path)
        if drct.options:
            drct_cfg.append('    Options %s' % drct.options)
        drct_cfg.append('</Directory>')
    return drct_cfg


def updateserver(name, ip, port, alias=None, admin=None, root=None, index=None, directory=None, error_log=None, custom_log=None, version=None):
    '''Update an existing server.

    If the old config is not in the right place, we would automatically delete it and
    create the new config to coresponding config file under /etc/nginx/conf.d/.
    '''
    pass

if __name__ == '__main__':
    # test_path = '/Users/douzhenjiang/test/inpanel/test/httpd.conf'
    # tmp = loadconfig(test_path)
    # print(tmp)
    # print(json.dumps(tmp))
    # virtual_host_config('aaa.com', 'DocumentRoot', '/v/asfs34535')
    # virtual_host_config('aaa.com', 'ServerAdmin', '4567896543')
    # virtual_host_config('aaa.com', 'VirtualHost', 'bbb.com', 567)

    # for line in replace_docroot('aaa.com', 'docroot'):
    #     print(line)

    # aaa = '/Users/douzhenjiang/test/inpanel/test/aaa.com.conf'
    # tmp1 = _parse_virtualhost_config(aaa)
    # print(json.dumps(tmp1))

    # print getservers()

    # path = os.path.join(SERVERCONF, clist[i])
    # print os.path.splitext('/Users/douzhenjiang/Projects/inpanel/test/aaa.com')
    SERVERCONF = '/Users/douzhenjiang/test/inpanel/test'
    addserver('11inpanel.org', '1.1.1.1', 80,
              alias=['cc.com', 'bb.com'],
              admin='root',
              root='/var/www/inpanel.org',
              index='index.html index.php',
              directory=None,
              error_log='abc/aaa.log',
              custom_log='abc/aaa_error.log',
              version=None)
