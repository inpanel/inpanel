# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Apache HTTP Server Management.'''


import os
import re
from glob import glob
from io import StringIO
from json import loads
from os import remove, stat, unlink
from string import punctuation

from base import COMMENTFLAG, GENBY, config_path
from mod_config import Config
from utils import is_valid_domain, is_valid_ip, is_valid_ipv4, is_valid_ipv6

# load httpd module config
httpd_config = Config(os.path.join(config_path, 'module/httpd.ini'))
# print('httpd_config', httpd_config.get_config())
base_path = httpd_config.get('base', 'path')
base_config = httpd_config.get('base', 'config')
base_servers = httpd_config.get('base', 'servers')

if os.path.exists(base_path):
    HTTPDCONF = base_path
else:
    HTTPDCONF = '/etc/httpd/'

if os.path.exists(base_config):
    APACHECONF = base_config
else:
    APACHECONF = '/etc/httpd/conf/httpd.conf'

if os.path.exists(base_servers):
    SERVERCONF = base_servers
else:
    SERVERCONF = '/etc/httpd/conf.d/'


CONFIGS = {
    'servertokens': 'os',
    'serverroot': '/etc/httpd',
    'timeout': 60,
    'defaulttype': 'text/plain',
    'documentroot': '/var/www/html',
    'directoryindex': 'index.html index.htm index.php',
    'adddefaultcharset': 'utf-8',
    'listen': 80,
    'serveradmin': 'root@localhost',
    'servername': 'www@localhost',
    'namevirtualhost': '*:80',
    'keepalive': 'off',
    'maxkeepaliverequests': 100,
    'keepalivetimeout': 15,
    'usecanonicalname': 'off',
    'accessfilename': '.htaccess',
    'typesconfig': '/etc/mime.types',
    'errorlog': 'logs/error_log',
    'loglevel': 'debug',  # info, notice, warn, error, crit, alert, emerg
    'serversignature': 'on',
    'indexoptions': 'fancyindexing versionsort namewidth=* htmltable charset=utf-8',
    'alias': 'alias',
    'addlanguage': '',
    'loadmodule': '',
    'scriptalias': '',
    'addtype': '',
    'addicon': '',
    'addiconbytype': '',
    'include': '',
    'aaa': '',
    'bbb': ''
}
DIRECTIVES = {
    'acceptfilter':   ('server'),
    'acceptpathinfo': ('server', 'virtualhost', 'directory', 'htaccess'),
    'accessfilename': ('server', 'virtualhost'),
    'adddefaultcharset': ('server', 'virtualhost', 'directory', 'htaccess'),
    'allowencodedslashes': ('server', 'virtualhost'),
    'allowoverride': ('directory'),
    'allowoverridelist': ('directory'),
    'cgimapextension': ('directory', 'htaccess'),
    'cgipassauth': ('directory', 'htaccess'),
    'cgivar': ('directory', 'htaccess'),
    'contentdigest': ('server', 'virtualhost', 'directory', 'htaccess'),
    'defaultruntimedir': ('server'),
    'defaulttype': ('server', 'virtualhost', 'directory', 'htaccess'),
    'define': ('server', 'virtualhost', 'directory'),
    'directory': ('server', 'virtualhost'),
    'directorymatch': ('server', 'virtualhost'),
    'documentroot': ('server', 'virtualhost'),
    'else': ('server', 'virtualhost', 'directory', 'htaccess'),
    'elseif': ('server', 'virtualhost', 'directory', 'htaccess'),
    'enablemmap': ('server', 'virtualhost', 'directory', 'htaccess'),
    'enablesendfile': ('server', 'virtualhost', 'directory', 'htaccess'),
    'error': ('server', 'virtualhost', 'directory', 'htaccess'),
    'errordocument': ('server', 'virtualhost', 'directory', 'htaccess'),
    'errorlog': ('server', 'virtualhost'),
    'errorlogformat': ('server', 'virtualhost'),
    'extendedstatus': ('server'),
    'fileetag': ('server', 'virtualhost', 'directory', 'htaccess'),
    'files': ('server', 'virtualhost', 'directory', 'htaccess'),
    'filesmatch': ('server', 'virtualhost', 'directory', 'htaccess'),
    'forcetype': ('directory', 'htaccess'),
    'gprofdir': ('server', 'virtualhost'),
    'hostnamelookups': ('server', 'virtualhost', 'directory'),
    'httpprotocoloptions': ('server', 'virtualhost'),
    'if': ('server', 'virtualhost', 'directory', 'htaccess'),
    'ifdefine': ('server', 'virtualhost', 'directory', 'htaccess'),
    'ifdirective': ('server', 'virtualhost', 'directory', 'htaccess'),
    'iffile': ('server', 'virtualhost', 'directory', 'htaccess'),
    'ifmodule': ('server', 'virtualhost', 'directory', 'htaccess'),
    'ifsection': ('server', 'virtualhost', 'directory', 'htaccess'),
    'include': ('server', 'virtualhost', 'directory'),
    'includeoptional': ('server', 'virtualhost', 'directory'),
    'keepalive': ('server', 'virtualhost'),
    'keepalivetimeout': ('server', 'virtualhost'),
    'limit': ('directory', 'htaccess'),
    'limitexcept': ('directory', 'htaccess'),
    'limitinternalrecursion': ('server', 'virtualhost'),
    'limitrequestbody': ('server', 'virtualhost', 'directory', 'htaccess'),
    'limitrequestfields': ('server', 'virtualhost'),
    'limitrequestfieldsize': ('server', 'virtualhost'),
    'limitrequestline': ('server', 'virtualhost'),
    'limitxmlrequestbody': ('server', 'virtualhost', 'directory', 'htaccess'),
    'location': ('server', 'virtualhost'),
    'locationmatch': ('server', 'virtualhost'),
    'loglevel': ('server', 'virtualhost', 'directory'),
    'maxkeepaliverequests': ('server', 'virtualhost'),
    'maxrangeoverlaps': ('server', 'virtualhost', 'directory'),
    'maxrangereversals': ('server', 'virtualhost', 'directory'),
    'maxranges': ('server', 'virtualhost', 'directory'),
    'mergeslashes': ('server', 'virtualhost'),
    'mergetrailers': ('server', 'virtualhost'),
    'mutex': ('server'),
    'namevirtualhost': ('server'),
    'options': ('server', 'virtualhost', 'directory', 'htaccess'),
    'protocol': ('server', 'virtualhost'),
    'protocols': ('server', 'virtualhost'),
    'protocolshonororder': ('server', 'virtualhost'),
    'qualifyredirecturl': ('server', 'virtualhost', 'directory'),
    'regexdefaultoptions': ('server'),
    'registerhttpmethod': ('server'),
    'rlimitcpu': ('server', 'virtualhost', 'directory', 'htaccess'),
    'rlimitmem': ('server', 'virtualhost', 'directory', 'htaccess'),
    'rlimitnproc': ('server', 'virtualhost', 'directory', 'htaccess'),
    'scriptinterpretersource': ('server', 'virtualhost', 'directory', 'htaccess'),
    'seerequesttail': ('server'),
    'serveradmin': ('server', 'virtualhost'),
    'serveralias': ('virtualhost'),
    'servername': ('server', 'virtualhost'),
    'serverpath': ('virtualhost'),
    'serverroot': ('server'),
    'serversignature': ('server', 'virtualhost', 'directory', 'htaccess'),
    'servertokens': ('server'),
    'sethandler': ('server', 'virtualhost', 'directory', 'htaccess'),
    'setinputfilter': ('server', 'virtualhost', 'directory', 'htaccess'),
    'setoutputfilter': ('server', 'virtualhost', 'directory', 'htaccess'),
    'timeout': ('server', 'virtualhost'),
    'traceenable': ('server', 'virtualhost'),
    'undefine': ('server'),
    'usecanonicalname': ('server', 'virtualhost', 'directory'),
    'usecanonicalphysicalport': ('server', 'virtualhost', 'directory'),
    'virtualhost': ('server'),
    'aaa': (),
    'bbb': ()
}

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

def web_handler(context):
    '''for web server'''
    action = context.get_argument('action', '')
    if action == 'getservers':
        sites = getservers()
        context.write({'code': 0, 'msg': '', 'data': sites})

    elif action in ('enableserver', 'disableserver', 'deleteserver'):
        ip = context.get_argument('ip', '')
        port = context.get_argument('port', '')
        name = context.get_argument('server_name', '')
        handler = getattr(locals(), action)
        opstr = {
            'enableserver': '启用',
            'disableserver': '停用',
            'deleteserver': '删除',
        }
        if handler(name, ip, port):
            context.write({'code': 0, 'msg': f'站点 {name}:{port} {opstr[action]}成功！'})
        else:
            context.write({'code': -1, 'msg': f'站点 {name}:{port} {opstr[action]}失败！'})

    elif action == 'get_settings':
        # items = context.get_argument('items', '')
        # items = items.split(',')
        config = loadconfig()
        context.write({'code': 0, 'msg': '', 'data': config})

    elif action == 'getserver':
        ip = context.get_argument('ip', '')
        port = context.get_argument('port', '')
        name = context.get_argument('name', '')
        serverinfo = getserver(ip, port, name)
        if serverinfo:
            context.write({'code': 0, 'msg': '站点信息读取成功！', 'data': serverinfo})
        else:
            context.write({'code': -1, 'msg': '站点不存在！'})

    elif action in ('addserver', 'updateserver'):
        setting = loads(context.get_argument('setting', '')) or {}

        ip = setting.get('ip', '')
        if ip not in ('', '*', '0.0.0.0') and not is_valid_ip(ip):
            context.write({'code': -1, 'msg': f'{ip} 不是有效的IP地址！'})
            return

        port = int(setting.get('port', 0))
        if port <= 0 or port > 65535:
            context.write({'code': -1, 'msg': f'{setting.get("port")} 不是有效的端口号!'})
            return

        servername = setting.get('servername')
        # print('servername', servername)
        if not is_valid_domain(servername):
            context.write({'code': -1, 'msg': f'{servername} 不是有效的域名！'})
            return

        documentroot = setting.get('documentroot', '')
        if not documentroot:
            context.write({'code': -1, 'msg': f'{documentroot} 不是有效的目录！'})
            return
        autocreate = setting.get('autocreate')
        if not os.path.exists(documentroot):
            if autocreate:
                try:
                    mkdir(documentroot)
                except:
                    context.write({'code': -1, 'msg': f'站点目录 {documentroot} 创建失败！'})
                    return
            else:
                context.write({'code': -1, 'msg': f'站点目录 {documentroot} 不存在！'})
                return

        directoryindex = setting.get('directoryindex')
        serveralias = setting.get('serveralias')
        serveradmin = setting.get('serveradmin')
        errorlog = setting.get('errorlog')
        customlog = setting.get('customlog')
        directory = setting.get('directory')

        version = context.get_argument('version', '')  # apache version
        for diret in directory:
            if 'path' in diret and diret['path']:
                if not os.path.exists(diret['path']) and 'autocreate' in diret and diret['autocreate']:
                    try:
                        mkdir(diret['path'])
                    except:
                        context.write({'code': -1, 'msg': '路径 %s 创建失败！' % diret['path']})
                        return
            else:
                context.write({'code': -1, 'msg': '请选择路径！'})
                return
        if action == 'addserver':
            if not addserver(servername, ip, port, serveralias=serveralias, serveradmin=serveradmin, documentroot=documentroot, directoryindex=directoryindex, directory=directory,
                errorlog=errorlog, customlog=customlog, version=version):
                context.write({'code': -1, 'msg': '新站点添加失败！请检查站点域名是否重复。', 'data': setting})
            else:
                context.write({'code': 0, 'msg': '新站点添加成功！', 'data': setting})
        else:
            c_ip = context.get_argument('ip', '')
            c_port = context.get_argument('port', '')
            c_name = context.get_argument('name', '')
            if not updateserver(c_name, c_ip, c_port, serveralias=serveralias, serveradmin=serveradmin, documentroot=documentroot, directoryindex=directoryindex, directory=directory,
                errorlog=errorlog, customlog=customlog, version=version):
                context.write({'code': -1, 'msg': '站点设置更新失败！请检查配置信息（如域名是否重复？）', 'data': setting})
            else:
                context.write({'code': 0, 'msg': '站点设置更新成功！', 'data': setting})


def loadconfig(conf=None, getlineinfo=False):
    '''Load Apache config and return a dict.
    '''
    if not conf:
        conf = APACHECONF
    if not os.path.exists(conf):
        return False
    return _loadconfig(conf, getlineinfo)


def _loadconfig(conf, getlineinfo, config=None, context_stack=None):
    '''parse Apache httpd.conf and include configs'''
    if config is None:
        configs = {}
    else:
        configs = config

    result = {}
    directorys = {}  # 附加信息

    RE_VH_START = re.compile(r'<VirtualHost(\s+)(\S+)>')
    RE_VH_CLOSE = re.compile(r'</VirtualHost>')
    RE_DT_START = re.compile(r'<Directory(\s+)(\S+)>')
    RE_DT_CLOSE = re.compile(r'</Directory>')
    with open(conf, 'r', encoding='utf-8') as f:
        id_v = 0
        enable = False
        vhost = []
        id_d = 0
        enable_d = False
        v_dirs = {}
        result_d = {}
        for line_i, line in enumerate(f):
            out = line.strip()

            line_disabled = False
            if out.startswith(COMMENTFLAG):
                # deal with our speical comment string
                while out.startswith(COMMENTFLAG):
                    out = out[3:]
                out = out.strip()
                line_disabled = True

            if not out or out.startswith('#'):
                continue

            # deal with comment and detect inpanel flag in comment
            gen_by_inpanel = False
            fields = out.split('#', 1)
            if len(fields) > 1 and fields[1].strip() == GENBY:
                gen_by_inpanel = True

            out = fields[0].strip()
            line = out.strip(';').lstrip('<').lstrip('</').rstrip('>')
            fields = line.split()
            key = fields[0].lower()
            value = ' '.join(fields[1:]).strip(';')
            # print(key, value, line)

            match = RE_VH_START.search(out)
            if match:
                id_d = 0
                v_dirs = {}
                result_d[id_v] = []
                directorys[id_v] = []
                name_port = match.groups()[1].strip('"').strip('\'')
                # print(name_port)
                port = name_port.split(':')[-1]
                ip = name_port[0:-(len(port) + 1)]
                ip = ip.lstrip('[').rstrip(']')  # for IPv6
                vhost = [ip, port, gen_by_inpanel, line_disabled]
                enable = True
                enable_d = False
                continue

            # start of Directory in VirtualHost
            match_d = RE_DT_START.search(out)
            if enable is True and match_d:
                v_dirs = {}
                path = match_d.groups()[1].strip().strip('"')
                v_dirs[id_d] = []
                v_dirs[id_d].append('path ' + path)
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
                continue

            # merge of VirtualHost
            if enable:
                # print('merge', out)
                vhost.append(out)
                continue

            if key in CONFIGS:
                if key in ('indexoptions', 'directoryindex'):
                    configs[key] = ' '.join(str(n) for n in fields[1:])
                elif key == 'addicon':
                    if key in configs:
                        configs[key].append({'path': fields[1], 'exts': fields[2:]})
                    else:
                        configs[key] = [{'path': fields[1], 'exts': fields[2:]}]
                elif key == 'addiconbytype':
                    configs[key] = ' '.join(str(n) for n in fields[1:])
                elif key == 'alias':
                    if key in configs:
                        configs[key].append({'alias': fields[1], 'origin': fields[2].strip('"')})
                    else:
                        configs[key] = [{'alias': fields[1], 'origin': fields[2].strip('"')}]
                elif key == ('addlanguage', 'loadmodule'):
                    if key in configs:
                        configs[key].append(fields[1:])
                    else:
                        configs[key] = [fields[1:]]
                elif key == 'listen':
                    port = fields[1].split(':')[-1]
                    ip = fields[1][0:-(len(port) + 1)].lstrip('[').rstrip(']')
                    if key in configs:
                        configs[key].append({'port': port, 'ip': ip})
                    else:
                        configs[key] = [{'port': port, 'ip': ip}]
                elif key == 'include':
                    include_file = fields[1] if fields[1].startswith('/') else os.path.join(HTTPDCONF, fields[1])
                    include_files = glob(include_file)
                    # order by domain name, excluding tld
                    # getdm = lambda x: x.split('/')[-1].split('.')[-3::-1]
                    # include_files = sorted(include_files, lambda x,y: cmp(getdm(x), getdm(y)))
                    for subconf in include_files:
                        if os.path.exists(subconf):
                            # print(subconf, getlineinfo, configs, context_stack)
                            # print('configs', configs)
                            _loadconfig(subconf, getlineinfo, configs, context_stack)
                else:
                    configs[key] = fields[1].strip(punctuation)

    # print('directorys', directorys)
    if 'virtualhost' not in configs:
        configs['virtualhost'] = []

    if len(result) > 0:
        # print('result', result)
        for i in result.items():
            if directorys[i]:
                server = {'directory': directorys[i]}
            else:
                server = {}
            for j, line in enumerate(result[i]):
                if j == 0:
                    server['ip'] = result[i][0]
                elif j == 1:
                    server['port'] = result[i][1]
                elif j == 2:
                    server['_inpanel'] = result[i][2]
                elif j == 3:
                    server['disabled'] = result[i][3]
                    server['status'] = 'off' if result[i][3] else 'on'
                else:
                    fields = line.split()
                    key = fields[0].lower()
                    if key == 'directoryindex':
                        server['directoryindex'] = ' '.join(str(n) for n in fields[1:])
                    elif key == 'serveralias':
                        server['serveralias'] = fields[1:]
                    elif key == 'customlog':
                        server['customlog'] = ' '.join(fields[1:])
                    elif key in ('serveradmin', 'servername', 'documentroot', 'errorlog', 'options', 'location', 'suexecusergroup'):
                        server[key] = fields[1].strip(' ').strip('"')

            configs['virtualhost'].append(server)

    # configs['gzip'] = _context_check_gzip(LoadModule, IfModule)
    return configs


def _parse_directory(directory):
    '''read and detect directory config
    '''
    if not directory:
        return []

    results = []
    for r in directory:
        drct = {
            'path': '',
            'allow': [],
            'deny': []
        }
        for line in r:
            line = line.split()
            key = line[0].lower()
            if key == 'path':
                drct['path'] = line[1].strip()
            elif key == 'order':
                drct['order'] = (','.join(str(n) for n in line[1:])).lower()
            elif key in ('allow', 'deny'):
                # drct[key].append(line[2].strip()) # only multi-line IPs
                drct[key].extend([i for i in line[2:]]) # support multi-line IPs and multiple IPs per line
            elif key in ('allowoverride'):
                drct[key] = line[1].strip()
            elif key == 'options':
                options = (' '.join(str(n) for n in line[1:])).lower()
                if '-indexes' in options:
                    drct['indexes'] = '-'
                elif 'indexes' in options or '+indexes' in options:
                    drct['indexes'] = '+'
                if '-followsymlinks' in options:
                    drct['followsymlinks'] = '-'
                elif 'followsymlinks' in options or '+followsymlinks' in options:
                    drct['followsymlinks'] = '+'
                if '-execcgi' in options:
                    drct['execcgi'] = '-'
                elif 'execcgi' in options or '+execcgi' in options:
                    drct['execcgi'] = '+'
        order = drct.get('order', '')
        if order in ('allow,deny', 'deny,allow'):
            drct['allow_enable'] = True
            drct['deny_enable'] = True
        results.append(drct)
    # print(results)
    return results


def getservers(config=None):
    '''Get servers from apache configuration files.
    '''
    if not config:
        config = loadconfig()
    return _context_getservers(config=config)


def getserver(ip, port, server_name, config=None):
    '''Get server setting from Apache configuration files.
    '''
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig()
    server = _context_getserver(ip, port, server_name, config=config)
    return server[0] if len(server) >= 1 else None


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
        stat(conf)
    except OSError:
        print('site config file not exist')
        return False

    old_conf = open(conf, encoding='utf-8').read()

    with open(conf + '.bak', 'w', encoding='utf-8') as f:
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
    with open(conf, 'w', encoding='utf-8') as f:
        f.write(new_conf)
        # delete old site config file
        if key == 'VirtualHost' and stat(conf) and stat(SERVERCONF + site + '.conf.bak'):
            remove(SERVERCONF + site + '.conf')
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
    file = open(HTTPDCONF + vhost + '.conf', encoding='utf-8').read()
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


def _context_check_gzip(LoadModule, IfModule):
    mod_status = (
        ['ext_filter_module', 'modules/mod_ext_filter.so'] in LoadModule and
        ['deflate_module', 'modules/mod_deflate.so'] in LoadModule and
        ['headers_module', 'modules/mod_headers.so'] in LoadModule
    )
    # check deflate config in IfModule
    mod_deflate = True
    return mod_status and mod_deflate

def _context_gethttp(config=None):
    """Get http context config.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    print('config', config)
    return config['_'][0]

def _context_getservers(disabled=None, config=None, getlineinfo=True):
    '''Get server context configs.
    '''

    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, getlineinfo)
    servers = []
    if 'virtualhost' in config and len(config['virtualhost']) > 0:
        servers = config['virtualhost']
    if disabled == None or not getlineinfo:
        return servers
    else:
        return [server for server in servers if server['disabled'] == disabled]

def _context_getserver(ip, port, servername, config=None, disabled=None, getlineinfo=True):
    '''Get a server context config by ip:port and servername.

    If disabled is None, return all servers
    If disabled is True, return only disabled servers
    If disabled is False, return only normal servers
    '''
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, getlineinfo)
    cnfservers = _context_getservers(disabled=disabled, config=config, getlineinfo=getlineinfo)
    # print(cnfservers)
    if not ip or ip in ('*', '0.0.0.0'):
        ip = '*'
    if is_valid_ipv6(ip) and not is_valid_ipv4(ip):
        ip = '[' + ip + ']'
    port = str(port)
    return [s for s in cnfservers if ip == s['ip'] and port == s['port'] and s['servername'] == servername or 'serveralias' in s and servername in s['serveralias']]
        # if getlineinfo:
        #     s_names = ' '.join([v['value'] for v in s['server_name']]).split()
        #     listens = [v['value'].split()[0] for v in s['listen']]
        # else:
        #     s_names = ' '.join([v for v in s['server_name']]).split()
        #     listens = [v.split()[0] for v in s['listen']]
        # find_listen = ip and ['%s:%s' % (ip, port)] or [port, '*:%s' % port, '0.0.0.0:%s' % port]
        # if server_name == s_names and ip == s_ip and port == s_port: # any([i in listens for i in find_listen]):
        #     return s
    # return False


def _context_getupstreams(server_name, config=None, disabled=None, getlineinfo=True):
    """Get upstream list related to a server.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, getlineinfo)
    upstreams = http_get('upstream', config)
    if not upstreams: return False
    if getlineinfo:
        upstreams = [upstream for upstream in upstreams 
            if upstream['_param']['value'].startswith('backend_of_%s_' % server_name)]
    else:
        upstreams = [upstream for upstream in upstreams 
            if upstream['_param'].startswith('backend_of_%s_' % server_name)]

    if disabled == None or not getlineinfo:
        return upstreams
    else:
        return [upstream for upstream in upstreams
                if upstream['_param']['disabled']==disabled]

def _comment(filepath, start, end):
    """Commend some lines in the file.
    """
    if not os.path.exists(filepath):
        return False
    data = []
    with open(filepath, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= start and i <= end:
                if not line.startswith(COMMENTFLAG):
                    data.append(COMMENTFLAG)
            data.append(line)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(''.join(data))
    return True

def _uncomment(filepath, start, end):
    """Uncommend some lines in the file.
    """
    if not os.path.exists(filepath):
        return False
    data = []
    with open(filepath, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= start and i <= end:
                while line.startswith(COMMENTFLAG):
                    line = line[3:]
            data.append(line)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(''.join(data))
    return True

def _delete(filepath, start, end, delete_emptyfile=True):
    """Delete some lines in the file.

    If delete_emptyfile is set to True, then the empty file will 
    be deleted from file system.
    """
    if not os.path.exists(filepath):
        return False
    data = []
    with open(filepath, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= start and i <= end:
                continue
            data.append(line)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(''.join(data))
    if delete_emptyfile:
        if ''.join(data).strip() == '':
            unlink(filepath)
    return True

def _getcontextrange(context, config):
    """Return the range of the input context, including the file path.

    Return format:
    [filepath, line_start, line_end]
    """
    file_i = context['_range']['begin']['file']
    filepath = config['_files'][file_i]
    line_start = context['_range']['begin']['line'][0]
    line_end = context['_range']['end']['line'][0]
    return [filepath, line_start, line_end]

def _context_commentserver(ip, port, server_name, config=None):
    """Comment a context using InPanel's special comment string '#v#'
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    scontext = _context_getserver(ip, port, server_name, config=config)
    if not scontext: return False
    filepath, line_start, line_end = _getcontextrange(scontext, config)
    return _comment(filepath, line_start, line_end)

def _context_uncommentserver(ip, port, server_name, config=None):
    """Uncomment a InPanel's special-commented context.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    scontext = _context_getserver(ip, port, server_name, config=config)
    if not scontext: return False
    filepath, line_start, line_end = _getcontextrange(scontext, config)
    return _uncomment(filepath, line_start, line_end)

def _context_deleteserver(ip, port, server_name, config=None, disabled=None):
    """Delete a server context.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    scontext = _context_getserver(ip, port, server_name, config=config, disabled=disabled)
    if not scontext: return False
    filepath, line_start, line_end = _getcontextrange(scontext, config)
    config['_isdirty'] = True
    return _delete(filepath, line_start, line_end)

def _context_commentupstreams(server_name, config=None):
    """Comment upstreams by server names.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    upstreams = _context_getupstreams(server_name, config=config)
    if not upstreams: return True
    for upstream in upstreams:
        filepath, line_start, line_end = _getcontextrange(upstream, config)
        if not _comment(filepath, line_start, line_end): return False
    return True

def _context_uncommentupstreams(server_name, config=None):
    """Uncomment upstreams by server names.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    upstreams = _context_getupstreams(server_name, config=config)
    if not upstreams: return True
    for upstream in upstreams:
        filepath, line_start, line_end = _getcontextrange(upstream, config)
        if not _uncomment(filepath, line_start, line_end): return False
    return True

def _context_deleteupstreams(server_name, config=None, disabled=None):
    """Delete upstreams by server name.
    """
    while True:
        # we need to reload config after delete one upstream
        if config is None or ('_isdirty' in config and config['_isdirty']):
            config = loadconfig(APACHECONF, True)
        upstreams = _context_getupstreams(server_name, config=config, disabled=disabled)
        if not upstreams: return True
        for upstream in upstreams:
            filepath, line_start, line_end = _getcontextrange(upstream, config)
            config['_isdirty'] = True
            if not _delete(filepath, line_start, line_end): return False
            break   # only delete the first one
    return True


def _replace(positions, lines):
    """Replace the lines specified in list positions to new lines.

    Structure of positions:
    [
        (filepath, line_start, line_count),
        ...
    ]
    Parameter positions can not be empty.

    * If the new lines is empty, old lines with be deleted.
    * If the new lines is less than the old lines, the rest old lines
      will also be deleted.
    * If the new lines is more than the old lines, then new value will 
      append after the last line of the old lines.
    """
    # merge line positions by filepath
    # struct: {'/path/to/file': [3, 4, 10, ...], ...}
    files = {}
    for pos in positions:
        filepath, line_start, line_count = pos
        if not filepath in files:
            files[filepath] = []
        for i in range(line_count):
            files[filepath].append(line_start+i)
    # replace line by line
    for filepath, line_nums in files.items():
        flines = []
        with open(filepath, encoding='utf-8') as f:
            for i, fline in enumerate(f):
                if i in line_nums:
                    if len(lines) > 0:
                        # replace with a new line
                        line = lines[0]
                        lines = lines[1:]
                        # detect the space at the start of the old line
                        # this aim to keep the indent of the line
                        space = ''
                        for c in fline:
                            if c not in (' ', '\t'):
                                break
                            space += c
                        flines.append(''.join([space, line, '\n']))
                    else:
                        # no more new line, delete the old line
                        continue
                else:
                    if i > line_nums[-1] and len(lines) > 0:
                        # exceed the last old line, insert the rest new lines here
                        # detect the indent of the last line
                        space = ''
                        if len(flines)>0: # last line exists
                            for c in flines[-1]:
                                if c not in (' ', '\t'):
                                    break
                                space += c
                        for line in lines:
                            flines.append(''.join([space, line, '\n']))
                        lines = []
                    flines.append(fline)
        # write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(flines))


def _insert(filepath, line_start, lines):
    """Insert the lines to the specified position.
    """
    flines = []
    with open(filepath, encoding='utf-8') as f:
        for i, fline in enumerate(f):
            if i == line_start:
                # detect the indent of the last not empty line
                space = ''
                flines_len = len(flines)
                if flines_len>0: # last line exists
                    line_i = -1
                    while flines[line_i].strip() == '' and -line_i <= flines_len:
                        line_i -= 1
                    for c in flines[line_i]:
                            if c not in (' ', '\t'):
                                break
                            space += c
                    if flines[line_i].strip().endswith('{'):
                        space += '    '
                for line in lines:
                    flines.append(''.join([space, line, '\n']))
            flines.append(fline)
    # write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(''.join(flines))


def http_get(directive, config=None):
    """Get directive values in http context.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF)
    hcontext = _context_gethttp(config)
    if directive in hcontext:
        return hcontext[directive]
    else:
        return None


def http_getfirst(directive, config=None):
    """Get the first value of the directive in http context.
    """
    values = http_get(directive, config)
    if values:
        return values[0]
    return None


def http_set(directive, values, config=None):
    """Set a directive in http context.

    If directive exists, the value will be replace in place.
    If directive not exists, new directive will be created at the beginning of http context.

    Parameter values can be a list or a string.
    If values is set to empty list or None or empty string, then the directive will be deleted.
    """
    if config is None or ('_isdirty' in config and config['_isdirty']):
        config = loadconfig(APACHECONF, True)
    hcontext = _context_gethttp(config)

    if not values:
        values = []
    elif isinstance(values, str):
        values = [values]
    values = ['%s %s;' % (directive, v) for v in values]

    if directive in hcontext:
        # update or delete value
        dvalues = hcontext[directive]
        lines = [(config['_files'][dvalue['file']], dvalue['line'][0], dvalue['line'][1]) for dvalue in dvalues]
        _replace(lines, values)
    else:
        # add directive to the beginning of http context
        # some directive like proxy_cache_path should be declare before use the resource,
        # so we should insert it at the beginning
        begin = hcontext['_range']['begin']
        _insert(config['_files'][begin['file']], begin['line'][0]+begin['line'][1], values)

    config['_isdirty'] = True


def disableserver(ip, port, servername):
    """Disable a server.
    """
    _context_commentupstreams(servername)
    return _context_commentserver(ip, port, servername)


def enableserver(ip, port, servername):
    """Enable a server.
    """
    _context_uncommentupstreams(servername)
    return _context_uncommentserver(ip, port, servername)


def deleteserver(server_name, ip, port):
    '''Delete a server.'''
    print(SERVERCONF + server_name + '.conf')
    try:
        unlink(SERVERCONF + server_name + '.conf')
        return True
    except:
        return False


def servername_exists(ip, port, server_name, config=None):
    '''Check if the server_name at given ip:port is already exists.
    '''
    return _context_getserver(ip, port, server_name, config=config) and True or False


def addserver(serveraname, ip, port, serveralias=None, serveradmin=None, documentroot=None, directoryindex=None, directory=None, errorlog=None, customlog=None, version=None):
    '''Add a new VirtualHost.'''
    if not is_valid_domain(serveraname):
        return False
    ip = ip or '*'
    if is_valid_ipv6(ip) and not is_valid_ipv4(ip):
        ip = '[' + ip + ']'
    if port:
        port = str(port) or '80'
    else:
        return False
    if not documentroot:
        return False
    # check if any of servername - ip - port pair already exists
    if servername_exists(ip, port, serveraname):
        return False

    # start generate the config string
    servercfg = [f'<VirtualHost {ip}:{port}> # {GENBY}']
    servercfg.append(f'    ServerName {serveraname}')
    servercfg.append(f'    DocumentRoot {documentroot}')
    if serveradmin:
        servercfg.append(f'    ServerAdmin {serveradmin}')
    if serveralias:
        servercfg.append(f'    ServerAlias {" ".join(serveralias)}')
    if directoryindex:
        servercfg.append(f'    DirectoryIndex {" ".join(directoryindex.split())}')
    else:
        servercfg.append('    DirectoryIndex index.html index.htm index.php')
    if errorlog:
        servercfg.append(f'    ErrorLog {errorlog}')
    if customlog:
        servercfg.append(f'    CustomLog {customlog}')
    if directory and len(directory) > 0:
        d = _extend_directory(directory)
        servercfg.extend(['    %s' % i for i in d])
    # end of server context
    servercfg.append('</VirtualHost>')

    #print '\n'.join(servercfg)
    configfile = os.path.join(SERVERCONF, serveraname + '.conf')
    configfile_exists = os.path.exists(configfile)

    # check if need to add a new line at the end of the file to
    # avoid first line go to the same former } line
    if configfile_exists:
        with open(configfile, encoding='utf-8') as f:
            f.seek(-1, 2)
            if f.read(1) != '\n':
                servercfg.insert(0, '')
    with open(configfile, configfile_exists and 'a' or 'w', encoding='utf-8') as f:
        f.write('\n'.join(servercfg))
    return True


def _extend_directory(directory):
    '''extend Directory config to line for build configfile.
    Usage
    ----------
    > d = _extend_directory(directory)\n
    > servercfg.extend(d) # for Apache Config\n
    > servercfg.extend(['    %s' % i for i in d]) # for VirtualHost Config
    '''
    drct_cfg = []
    for drct in directory:
        if 'path' in drct and drct['path']:
            drct_cfg.append('<Directory %s>' % drct['path'])
        else:
            continue
        options = []
        if drct.get('indexes'): # '+' or '-'
            options.append(str(drct['indexes']) + 'indexes')
        if drct.get('followsymlinks'):
            options.append(str(drct['followsymlinks']) + 'followsymlinks')
        if drct.get('execcgi'):
            options.append(str(drct['execcgi']) + 'execcgi')
        if len(options) > 0:
            drct_cfg.append('    Options ' + ' '.join(options))
        if drct.get('order'):
            drct_cfg.append('    Order ' + drct['order'])
        if len(drct.get('allow', [])) > 0:
            drct_cfg.extend(['    allow from %s' % i for i in drct['allow']])
        if len(drct.get('deny', [])) > 0:
            drct_cfg.extend(['    deny from %s' % i for i in drct['deny']])
        drct_cfg.append('</Directory>')
    return drct_cfg


def updateserver(old_name, old_ip, old_port, serveraname, ip, port, serveralias=None, serveradmin=None, documentroot=None, directoryindex=None, directory=None, errorlog=None, customlog=None, version=None):
    '''Update an existing server.

    If the old config is not in the right place, we would automatically delete it and
    create the new config to coresponding config file under /etc/httpd/conf.d/.
    '''
    # compare the old context and the new context
    # to check if the ip:port/server_name change and conflict status
    config = loadconfig(APACHECONF, True)
    oldscontext = _context_getserver(old_ip, old_port, old_name, config)
    if not oldscontext:
        return False
    scontext = _context_getserver(ip, port, serveraname)
    # server context found, but not equals to the old
    # this means conflict occur
    if scontext and scontext != oldscontext:
        return False

if __name__ == '__main__':
    HTTPDCONF = '/Users/douzhenjiang/Projects/inpanel/test'
    APACHECONF = '/Users/douzhenjiang/Projects/inpanel/test/httpd.conf'
    SERVERCONF = '/Users/douzhenjiang/Projects/inpanel/test/conf.d/'
    print(locals())
    # tmp = loadconfig()
    # print('config', tmp)
    # print(dumps(tmp))
    # virtual_host_config('aaa.com', 'DocumentRoot', '/v/asfs34535')
    # virtual_host_config('aaa.com', 'ServerAdmin', '4567896543')
    # virtual_host_config('aaa.com', 'VirtualHost', 'bbb.com', 567)

    # for line in replace_docroot('aaa.com', 'docroot'):
    #     print(line)

    # aaa = '/Users/douzhenjiang/Projects/inpanel/test/aaa.com.conf'
    # tmp1 = loadconfig()
    # print(dumps(tmp1))
    # s= tmp1['virtualhost']
    # # s = scontext['virtualhost']
    # s= [i for i in s if i['port']=='870' and i['ip']=='1.1.1.1' and i['servername']=='inpanel.org']
    # print(s)
    # s = getserver('1.1.1.1', '80', 'aaaaaaaa.aa')
    # s = servername_exists('1.1.1.1', 80, 'aaaaaaaa.aa')
    # print(s)
    # s = addserver('aaaaaaaa.aa', '1.1.1.1', 801, documentroot='/Users/douzhenjiang/Projects/inpanel/test')
    # s = getserver('1.1.1.1', 80, 'aaaaaaaa.aa')
    # s = dumps(s)
    # print(s)
    # for i in s:
    #     print('port' in i)
    #     # if i.port=='80':
    #     #     print(i)
    #     #     break
    # print([i for i in s if i['port']=='870' and i['ip']=='1.1.1.1' and i['servername']=='inpanel.org'])

    # print dumps(_context_getservers(disabled=None))

    # path = os.path.join(SERVERCONF, clist[i])
    # print os.path.splitext('/Users/douzhenjiang/Projects/inpanel/test/aaa.com')
    # SERVERCONF = '/Users/douzhenjiang/Projects/inpanel/test'
    # print(servername_exists('1.1.1.1', 80, 'inpanel.org'))
    # addserver('inpanel.org', '1.1.1.1', 80,
    #           serveralias=['cc.com', 'bb.com'],
    #           serveradmin='root',
    #           documentroot='/var/www/inpanel.org',
    #           directoryindex='index.html index.php',
    #           directory=[{'path': '/var/www/inpanel.org/abc',
    #                       'options': 'aadsfsdf asdfdsf'}],
    #           errorlog='abc/aaa.log',
    #           customlog='abc/aaa_error.log',
    #           version=None)
    # print(enableserver('*', 80, 'zhoukan.pub'))

