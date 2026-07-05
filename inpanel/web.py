# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Module for Web Querying'''

import binascii
import os
import re
import time
from base64 import b64decode, b64encode
from datetime import datetime
from functools import partial
from hashlib import md5
from json import dumps, loads
from logging import info as loginfo
from pathlib import Path
from shlex import quote
from uuid import uuid4

from . import aliyuncs
from .mod import disk
from .mod import ftp
from .mod import yum
from .mod import login
from .mod import query
from .mod import firewall
from .mod.task import TaskManager
from . import mod
import tornado
import tornado.escape
import tornado.httpclient
import tornado.ioloop
import tornado.web
from . import utils
from .base import app_api, app_name, machine, os_name, os_versint, version_info
from .lib import pyDes
from .mod import config, setting, server
from .mod.certificate import Certificate
from tornado.escape import to_unicode as _d
from tornado.escape import utf8 as _u


class Application(tornado.web.Application):
    def __init__(self, handlers=None, default_host="", transforms=None, **settings):
        settings['arch'] = machine
        settings['os_name'] = os_name.lower()
        if machine == 'i686' and os_versint == 5:
            settings['arch'] = 'i386'
        settings['data_path'] = str(Path(settings['data_path']))
        settings['package_path'] = str(Path(settings['data_path']) / 'packages')

        tornado.web.Application.__init__(self, handlers, default_host, transforms, **settings)

class RequestHandler(tornado.web.RequestHandler):

    def initialize(self):
        """Parse JSON data to argument list.
        """
        self.config = config.load_config()
        self.runlogs = config.runlogs_config()

        content_type = self.request.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                arguments = loads(self.request.body.decode('utf-8'))
                for name, value in arguments.items():
                    if isinstance(value, str):
                        value = value
                    elif isinstance(value, bool):
                        value = value and 'on' or 'off'
                    else:
                        value = ''
                    self.request.arguments.setdefault(name, []).append(value)
            except:
                pass

    def set_default_headers(self):
        self.set_header('Server', app_name)
        if 'Origin' in self.request.headers:
            self.set_header('Access-Control-Allow-Origin', self.request.headers.get('Origin'))
            self.set_header('Access-Control-Allow-Headers', 'X-ACCESS-TOKEN, Content-Type')
            self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def check_xsrf_cookie(self):
        # check for the access token
        if self.get_argument("_access", None) or self.request.headers.get("X-ACCESS-TOKEN"):
            if self.config.get('auth', 'accesskeyenable') != 'on':
                raise tornado.web.HTTPError(403, "Access Token Not Allowed")
        else:
            # check xsrf cookie
            token = (self.get_argument("_xsrf", None) or self.request.headers.get("X-XSRF-TOKEN"))
            if not token:
                raise tornado.web.HTTPError(403, "'_xsrf' argument missing from POST")
            if self.xsrf_token != token:
                raise tornado.web.HTTPError(403, "XSRF cookie does not match POST argument")

    def authed(self):
        # check for the access token
        access_token = (self.get_argument("_access", None) or self.request.headers.get("X-ACCESS-TOKEN"))

        if access_token:
            if self.config.get('auth', 'accesskeyenable') != 'on':
                raise tornado.web.HTTPError(403, 'Access Token Not Allowed')
            elif access_token != self.config.get('auth', 'accesskey'):
                raise tornado.web.HTTPError(403, 'Access Token Error')
        else:
            cur_authed = self.get_secure_cookie('authed', None, 30.0/1440)
            if not cur_authed:
                raise tornado.web.HTTPError(403, "Please Login First")
            # get the cookie within 30 mins
            if cur_authed.decode('utf-8') == 'yes':
                # regenerate the cookie timestamp per 5 mins
                if self.get_secure_cookie('authed', None, 5.0/1440) == None:
                    self.set_secure_cookie('authed', 'yes', None)

    def getlastactive(self):
        # get last active from cookie
        cv = self.get_cookie('authed', False)
        try:
            return int(cv.split('|')[1])
        except:
            return 0

    @property
    def xsrf_token(self):
        if not hasattr(self, "_xsrf_token"):
            token = self.get_cookie("XSRF-TOKEN") #  or self.request.headers.get("X-XSRF-TOKEN"))
            # token = (self.get_cookie("XSRF-TOKEN") or self.request.headers.get("X-XSRF-TOKEN"))
            if not token:
                token = binascii.b2a_hex(uuid4().bytes)
                expires_days = 30 if self.current_user else None
                self.set_cookie("XSRF-TOKEN", token, expires_days=expires_days)
            self._xsrf_token = token
        return self._xsrf_token


class IndexHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Server', app_name)

    def get(self):
        data = {
            'htmlTitle': '{{ htmlTitle }}', # js template code
            'releasetime': version_info['releasetime'],
            'template_path': ''
        }
        self.render("index.html", **data)

class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header('Server', app_name)

    def authed(self):
        # check for the access token
        self.config = config.load_config()
        access_token = (self.get_argument("_access", None) or self.request.headers.get("X-ACCESS-TOKEN"))
        if access_token and self.config.get('auth', 'accesskeyenable') == 'on':
            if access_token != self.config.get('auth', 'accesskey'):
                raise tornado.web.HTTPError(403, 'Access Token Error')
                # print('access_token matched')
                # return
        else:
            cur_authed = self.get_secure_cookie('authed', None, 30.0/1440)
            if not cur_authed:
                raise tornado.web.HTTPError(403, "Please login first")
            # get the cookie within 30 mins
            if cur_authed.decode('utf-8') == 'yes':
                # regenerate the cookie timestamp per 5 mins
                if self.get_secure_cookie('authed', None, 5.0 / 1440) is None:
                    self.set_secure_cookie('authed', 'yes', None)


class ErrorHandler(tornado.web.ErrorHandler):
    def set_default_headers(self):
        self.set_header('Server', app_name)


class FallbackHandler(tornado.web.FallbackHandler):
    def set_default_headers(self):
        self.set_header('Server', app_name)


class RedirectHandler(tornado.web.RedirectHandler):
    def set_default_headers(self):
        self.set_header('Server', app_name)


class FileDownloadHandler(StaticFileHandler):

    def get(self, path):
        self.authed()
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % Path(path))
        self.set_header('Content-Transfer-Encoding', 'binary')
        print('FileDownloadHandler', self.root, path)
        return StaticFileHandler.get(self, path)
        # buf_size = 4096
        # with open(str(Path(self.root, path), 'rb', encoding='utf-8') as f:
        #     while True:
        #         data = f.read(buf_size)
        #         if not data:
        #             break
        #         self.write(data)
        # self.finish()

class FileUploadHandler(RequestHandler):
    def post(self):
        self.authed()
        path = self.get_argument('path', '/')

        self.write('<body style="font-size:14px;overflow:hidden;margin:0;padding:0;">')

        if not 'ufile' in self.request.files:
            self.write('请选择要上传的文件！')
        else:
            self.write('正在上传...<br>')
            for item in self.request.files['ufile']:
                filename = re.split(r'[\\/]', item['filename'])[-1]
                with open(str(Path(path) / filename), 'wb') as f:
                    f.write(item['body'])
                self.write('%s 上传成功！<br>' % item['filename'])

        self.write('</body>')


class FilePreviewHandler(RequestHandler):
    '''FilePreviewHandler
    TODO: support multi
    '''
    def get(self, path):
        self.authed()
        p = str(Path('/') / path)
        if not Path(p).exists():
            # logger.error("Kerberos failure: %s", err)
            raise tornado.web.HTTPError(404, 'File Not Found', reason='File Not Found')
        buffer = ''
        mtype = 'image/png'
        with open(p, 'rb') as f:
            buffer = f.read()
        data = {
            'mtype': 'image/png',
            'data': f'data:{mtype};base64,{str(b64encode(buffer), "utf-8")}'
        }
        self.render('file/preview.html', **data)


class VersionHandler(RequestHandler):
    def get(self):
        self.authed()
        self.write({'code': 0, 'msg': '', 'data': version_info})


class XsrfHandler(RequestHandler):
    """Write a XSRF token to cookie
    """
    def get(self):
        self.xsrf_token


class AuthStatusHandler(RequestHandler):
    """Check if client has been authorized
    """
    def check_xsrf_cookie(self):
        pass

    def get(self):
        self.write({'lastactive': self.getlastactive()})

    def post(self):
        # authorize and update cookie
        try:
            self.authed()
            self.write({'authed': 'yes'})
        except:
            self.write({'authed': 'no'})


class ClientHandler(RequestHandler):
    """Get client infomation.
    """
    def get(self, argument):
        if argument == 'ip':
            self.write(self.request.remote_ip)


class LoginHandler(RequestHandler):
    """Validate username and password.
    """
    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        result = login.handle_login(self.config, username, password)
        if result['code'] >= 0:
            self.set_secure_cookie('authed', 'yes', None)
        self.write(result)


class LogoutHandler(RequestHandler):
    """Logout
    """
    def post(self):
        self.authed()
        login.handle_logout()
        self.clear_cookie('authed')


class SitePackageHandler(RequestHandler):
    """Interface for querying site packages information.
    """

    def get(self, op):
        self.authed()
        if hasattr(self, op):
            getattr(self, op)()
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    async def getlist(self):
        if not Path(self.settings['package_path']).exists():
            Path(self.settings['package_path']).mkdir(parents=True, exist_ok=True)

        packages = ''
        packages_cachefile = str(Path(self.settings['package_path']) / '.meta')

        # fetch from cache
        if Path(packages_cachefile).exists():
            # check the file modify time
            mtime = os.stat(packages_cachefile).st_mtime
            if time.time() - mtime < 86400:  # cache 24 hours
                with open(packages_cachefile, encoding='utf-8') as f:
                    packages = f.read()

        # fetch from api
        if not packages:
            http_client = tornado.httpclient.AsyncHTTPClient()
            response = await http_client.fetch(app_api['site_packages'])
            if response.error:
                self.write({'code': -1, 'msg': '获取网站系统列表失败！'})
                self.finish()
                return
            else:
                packages = response.body.decode('utf-8')
                with open(packages_cachefile, 'w', encoding='utf-8') as f:
                    f.write(packages)

        packages = tornado.escape.json_decode(packages)
        self.write({'code': 0, 'msg':'', 'data': packages})

        self.finish()

    def getdownloadtask(self):
        name = self.get_argument('name', '')
        version = self.get_argument('version', '')

        if not name or not version:
            self.write({'code': -1, 'msg': '获取安装包下载地址失败！'})
            return

        # fetch package list from cache
        packages_cachefile = str(Path(self.settings['package_path']) / '.meta')
        if not Path(packages_cachefile).exists():
            self.write({'code': -1, 'msg': '获取安装包下载地址失败！'})
            return
        with open(packages_cachefile, encoding='utf-8') as f:
            packages = f.read()
        packages = tornado.escape.json_decode(packages)

        # check if name and version is available
        package = None
        for cate in packages:
            for pkg in cate['packages']:
                if pkg['code'] == name:
                    for v in pkg['versions']:
                        if v['code'] == version:
                            package = v
                            break
                if package: break
            if package: break
        if not package:
            self.write({'code': -1, 'msg': '获取安装包下载地址失败！'})
            return

        filename = '%s-%s' % (name, version)
        workpath = str(Path(self.settings['package_path']) / filename)
        if not Path(workpath).exists(): Path(workpath).mkdir(parents=True, exist_ok=True)

        filenameext = '%s%s' % (filename, package['ext'])
        filepath = str(Path(self.settings['package_path']) / filenameext)

        self.write({'code': 0, 'msg': '', 'data': {
            'url': '%s&name=%s&version=%s' % (app_api['download_package'], name, version),
            'path': filepath,
            'temp': workpath,
        }})


class QueryHandler(RequestHandler):
    """Interface for querying server information.
    
    Query one or more items, seperated by comma.
    Examples:
    /api/query/*
    /api/query/server.*
    /api/query/mod.service.*
    /api/query/server.datetime,server.diskinfo
    /api/query/config.fstab(sda1)
    """
    def get(self, items):
        self.authed()
        result = query.handle_query(items)
        self.write(result)


class UtilsNetworkHandler(RequestHandler):
    """Handler for network ifconfig.
    """
    def get(self, sec, ifname):
        self.authed()
        result = server.ServerInfo.network_handle_get(sec, ifname)
        if result is not None:
            self.write(result)

    def post(self, sec, ifname):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许修改网络设置！'})
            return

        args = {
            'hostname': self.get_argument('hostname', ''),
            'ip': self.get_argument('ip', ''),
            'mask': self.get_argument('mask', ''),
            'gw': self.get_argument('gw', ''),
            'nameservers': self.get_argument('nameservers', '')
        }
        result = server.ServerInfo.network_handle_post(sec, ifname, args)
        if result is not None:
            self.write(result)

class UtilsTimeHandler(RequestHandler):
    """Handler for system datetime mod.setting.
    """
    def get(self, sec, region=None):
        self.authed()
        result = server.ServerInfo.handle_time_get(sec, region)
        if result is not None:
            self.write(result)

    def post(self, sec, ifname):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许时区设置！'})
            return

        timezone = self.get_argument('timezone', '')
        result = server.ServerInfo.handle_time_post(self.config, sec, timezone)
        if result is not None:
            self.write(result)
class SettingHandler(RequestHandler):
    """Settings for InPanel
    """
    async def get(self, section):
        self.authed()
        await setting.handle_get(self, section)

    def post(self, section):
        self.authed()
        setting.handle_post(self, section)


class OperationHandler(RequestHandler):
    ''''Server operation handler
    '''

    def post(self, op):
        """Run a server operation
        """
        self.authed()
        if hasattr(self, op):
            getattr(self, op)()
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def reboot(self):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许重启服务器！'})
            return
        self.write(server.ServerInfo.reboot())

    def fdisk(self):
        action = self.get_argument('action', '')
        devname = self.get_argument('devname', '')

        if action == 'add':
            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': '演示模式不允许添加分区！'})
                return

        elif action == 'delete':
            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': '演示模式不允许删除分区！'})
                return

        size = self.get_argument('size', '')
        unit = self.get_argument('unit', '')
        self.write(disk.handle_fdisk(action, devname, size, unit))

    def service(self):
        mod.service.web_handler(self)


    def user(self):
        mod.user.web_handler(self)

    def file(self):
        mod.file.web_handler(self)

    def apache(self):
        mod.httpd.web_handler(self)

    def nginx(self):
        mod.nginx.web_handler(self)


    def mysql(self):
        mod.mysql.web_handler(self)


    def php(self):
        mod.php.web_handler(self)


    def ssh(self):
        mod.ssh.web_handler(self)


    def cron(self):
        mod.cron.web_handler(self)

    def vsftpd(self):
        mod.vsftpd.web_handler(self)

    def named(self):
        mod.named.web_handler(self)

    def lighttpd(self):
        mod.lighttpd.web_handler(self)

    def proftpd(self):
        mod.proftpd.web_handler(self)

    def pureftpd(self):
        mod.pureftpd.web_handler(self)

    def shell(self):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许执行 shell 命令 ！'})
            return
        action = self.get_argument('action', '')
        cmd = self.get_argument('cmd', '')
        cwd = self.get_argument('cwd', '')
        if action == 'exec_command':
            self.write({'code': 0, 'msg': '命令已发送', 'data': mod.shell.exec_command(cmd, cwd)})

class PageHandler(RequestHandler):
    """Return single page.
    """
    def get(self, op, action):
        try:
            self.authed()
        except:
            self.write('<!DOCTYPE html><html><head><title>Permission Denied</title><meta charset="utf-8"/></head><body>没有权限，请<a href="/">登录</a>后再查看该页！<body></html>')
            return
        if hasattr(self, op):
            getattr(self, op)(action)
        else:
            self.write('未定义的操作！')

    def php(self, action):
        if action == 'phpinfo':
            # =PHPE9568F34-D428-11d2-A769-00AA001ACF42 (PHP Logo)
            # =PHPE9568F35-D428-11d2-A769-00AA001ACF42 (Zend logo)
            # =PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000 (PHP Credits)
            # redirect them to http://mod.php.net/index.php?***
            if self.request.query.startswith('=PHP'):
                self.redirect('http://www.mod.php.net/index.php?%s' % self.request.query)
            else:
                self.write(mod.php.phpinfo())


class BackupHandler(RequestHandler):
    def get(self):
        self.authed()

        if self.config.get('runtime', 'mode') == 'demo':
            self.write('演示模式不允许执行此操作！')
            return

        path = os.path.join(self.settings['data_path'], 'config.ini')
        if os.path.isfile(path):
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-disposition', 'attachment; filename=inpanel_backup_%s.bak' % time.strftime('%Y%m%d'))
            self.set_header('Content-Transfer-Encoding', 'binary')
            with open(path, encoding='utf-8') as f:
                self.write(f.read())
        else:
            self.write('配置文件不存在！')

    def authed(self):
        access_token = (self.get_argument("_access", None) or self.request.headers.get("X-ACCESS-TOKEN"))
        if access_token and self.config.get('auth', 'accesskeyenable') == 'on':
            if access_token != self.config.get('auth', 'accesskey'):
                raise tornado.web.HTTPError(403, 'Access Token Error')
        else:
            cur_authed = self.get_secure_cookie('authed', None, 30.0/1440)
            if not cur_authed:
                raise tornado.web.HTTPError(403, "Please Login First")
            if cur_authed.decode('utf-8') == 'yes':
                if self.get_secure_cookie('authed', None, 5.0/1440) == None:
                    self.set_secure_cookie('authed', 'yes', None)


class RestoreHandler(RequestHandler):
    def post(self):
        self.authed()

        if self.config.get('runtime', 'mode') == 'demo':
            self.write('演示模式不允许执行此操作！')
            return

        path = os.path.join(self.settings['data_path'], 'config.ini')

        self.write('<body style="font-size:14px;overflow:hidden;margin:0;padding:0;">')

        if not 'ufile' in self.request.files:
            self.write('请选择备份配置文件！')
        else:
            self.write('正在上传...')
            file = self.request.files['ufile'][0]
            testpath = path+'.test'
            with open(testpath, 'wb') as f:
                f.write(file['body'])

            try:
                with open(path, 'wb') as f:
                    f.write(file['body'])
                self.write('还原成功！')
            except:
                self.write('配置文件有误，还原失败！')

            os.unlink(testpath)

        self.write('</body>')


class BuyECSHandler(RequestHandler):
    """Aliyun CPS program.
    """
    def get(self):
        self.redirect('http://www.aliyun.com/cps/rebate?from_uid=zop0qMW4KbY=')


class AccountHandler(RequestHandler):
    """ECS Account handler.
    """
    def get(self):
        self.authed()
        status = self.get_argument('status', '')

        accounts = self.config.get('ecs', 'accounts')
        try:
            accounts = loads(accounts)
        except:
            accounts = []

        accounts = sorted(accounts, key=lambda k:k['name'])
        if status:
            status = status == 'enable'
            accounts = filter(lambda a: a['status'] == status, accounts)

        if self.config.get('runtime', 'mode') == 'demo':
            for i, account in enumerate(accounts):
                accounts[i]['access_key_secret'] = '演示模式下密钥被保护'

        self.write({'code': 0, 'msg': '成功加载 ECS 帐号列表！', 'data': accounts})

    def post(self):
        self.authed()
        action = self.get_argument('action', '')

        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许修改 ECS 帐号！'})
            return

        if action == 'add' or action == 'update':
            name = self.get_argument('name', '')
            access_key_id = self.get_argument('access_key_id', '')
            access_key_secret = self.get_argument('access_key_secret', '')
            status = self.get_argument('status', '')
            newaccount = {
                'name': name,
                'access_key_id': access_key_id,
                'access_key_secret': access_key_secret,
                'status': status == 'on',
            }
            if action == 'update':
                old_access_key_id = self.get_argument('old_access_key_id', '')

            accounts = self.config.get('ecs', 'accounts')
            try:
                accounts = loads(accounts)
            except:
                accounts = []

            if action == 'add':
                for account in accounts:
                    if account['access_key_id'] == access_key_id:
                        self.write({'code': -1, 'msg': '添加失败！该 Access Key ID 已存在！'})
                        return
                accounts.append(newaccount)
            else:
                found = False
                for i, account in enumerate(accounts):
                    if account['access_key_id'] == old_access_key_id:
                        accounts[i] = newaccount
                        found = True
                        break
                if not found:
                    self.write({'code': -1, 'msg': '更新失败！该 Access Key ID 不存在！'})
                    return

            self.config.set('ecs', 'accounts', dumps(accounts))
            if action == 'add':
                self.write({'code': 0, 'msg': '新帐号添加成功！'})
            else:
                self.write({'code': 0, 'msg': '帐号更新成功！'})

        elif action == 'delete':
            access_key_id = self.get_argument('access_key_id', '')
            accounts = self.config.get('ecs', 'accounts')
            try:
                accounts = loads(accounts)
            except:
                accounts = []

            found = False
            for i, account in enumerate(accounts):
                if account['access_key_id'] == access_key_id:
                    del accounts[i]
                    found = True
                    break
            if not found:
                self.write({'code': -1, 'msg': '删除失败！该 Access Key ID 不存在！'})
                return

            self.config.set('ecs', 'accounts', dumps(accounts))
            self.write({'code': 0, 'msg': '帐号删除成功！'})


class ECSHandler(RequestHandler):
    def _get_secret(self, access_key_id):
        accounts = self.config.get('ecs', 'accounts')
        try:
            accounts = loads(accounts)
        except:
            accounts = []

        for account in accounts:
            if account['access_key_id'] == access_key_id:
                return account['access_key_secret']
        return False

    async def get(self, section):
        self.authed()

        if section == 'regions':
            access_key_id = self.get_argument('access_key_id', '')
            if not access_key_id:
                self.write({'code': -1, 'msg': 'Access Key ID 不能为空！'})
                self.finish()
                return

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            result, data, reqid = await mod.shell.async_task(srv.DescribeRegions)
            if not result:
                self.write({'code': -1, 'msg': '地域列表加载失败！（%s）' % data['Message']})
                self.finish()
                return

            if 'Regions' in data:
                regions = data['Regions']
            else:
                regions = []

            self.write({'code': 0, 'msg': '成功加载地域列表！', 'data': {'regions': regions}})
            self.finish()

        elif section == 'zones':
            access_key_id = self.get_argument('access_key_id', '')
            region_code = self.get_argument('region_code', '')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            result, data, reqid = await mod.shell.async_task(srv.DescribeZones, RegionCode=region_code)
            if not result:
                self.write({'code': -1, 'msg': '可用区列表加载失败！（%s）' % data['Message']})
                self.finish()
                return

            if 'Zones' in data:
                zones = data['Zones']
            else:
                zones = []

            self.write({'code': 0, 'msg': '成功加载可用区列表！', 'data': {'zones': zones}})
            self.finish()

        elif section == 'instances':
            access_key_id = self.get_argument('access_key_id', '')
            region_code = self.get_argument('region_code', '')
            page_number = self.get_argument('page_number', '1')
            page_size = self.get_argument('page_size', '10')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            result, data, reqid = await mod.shell.async_task(srv.DescribeInstances, RegionCode=region_code, PageNumber=page_number, PageSize=page_size)
            if not result:
                self.write({'code': -1, 'msg': '云服务器列表加载失败！（%s）' % data['Message']})
                self.finish()
                return

            if 'Instances' in data:
                instances = data['Instances']
            else:
                instances = []

            self.write({'code': 0, 'msg': '成功加载云服务器列表！', 'data': {
                'instances': instances,
                'total_number': data['InstanceTotalNumber'],
                'page_number': data['PageNumber'],
                'page_size': data['PageSize'],
            }})
            self.finish()

        elif section == 'images':
            access_key_id = self.get_argument('access_key_id', '')
            region_code = self.get_argument('region_code', '')
            page_number = self.get_argument('page_number', '1')
            page_size = self.get_argument('page_size', '10')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            result, data, reqid = await mod.shell.async_task(srv.DescribeImages, RegionCode=region_code, PageNumber=page_number, PageSize=page_size)
            if not result:
                self.write({'code': -1, 'msg': '系统镜像列表加载失败！（%s）' % data['Message']})
                self.finish()
                return

            if 'Images' in data:
                images = data['Images']
            else:
                images = []

            self.write({'code': 0, 'msg': '成功加载系统镜像列表！', 'data': {
                'images': images,
                'total_number': data['ImageTotalNumber'],
                'page_number': data['PageNumber'],
                'page_size': data['PageSize'],
            }})
            self.finish()

        elif section == 'disks':
            access_key_id = self.get_argument('access_key_id', '')
            instance_name = self.get_argument('instance_name', '')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            result, data, reqid = await mod.shell.async_task(srv.DescribeDisks, InstanceName=instance_name)
            if not result:
                self.write({'code': -1, 'msg': '磁盘列表加载失败！（%s）' % data['Message']})
                self.finish()
                return

            if 'Disks' in data:
                disks = data['Disks']
            else:
                disks = []

            self.write({'code': 0, 'msg': '成功加载磁盘列表！', 'data': {'disks': disks}})
            self.finish()

        elif section == 'snapshots':
            access_key_id = self.get_argument('access_key_id', '')
            instance_name = self.get_argument('instance_name', '')
            disk_code = self.get_argument('disk_code', '')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            result, data, reqid = await mod.shell.async_task(srv.DescribeSnapshots, InstanceName=instance_name, DiskCode=disk_code)
            if not result:
                self.write({'code': -1, 'msg': '磁盘快照列表加载失败！（%s）' % data['Message']})
                self.finish()
                return

            if 'Snapshots' in data:
                snapshots = data['Snapshots']
            else:
                snapshots = []

            snapshots = sorted(snapshots, key=lambda k:k['CreateTime'], reverse=True)

            self.write({'code': 0, 'msg': '成功加载磁盘快照列表！', 'data': {'snapshots': snapshots}})
            self.finish()

        elif section == 'accessinfo':
            instance_name = self.get_argument('instance_name', '')
            if not instance_name:
                self.write({'code': -1, 'msg': '服务器不存在！'})
                self.finish()
                return

            if not self.config.has_option('inpanel', instance_name):
                accessinfo = {'accesskey': '', 'accessnet': 'public', 'accessport': '14433'}
            else:
                data = self.config.get('inpanel', instance_name)
                data = data.split('|')
                accessinfo = {
                    'accesskey': data[0],
                    'accessnet': data[1],
                    'accessport': data[2],
                }

            self.write({'code': 0, 'msg': '', 'data': accessinfo})
            self.finish()

        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})
            self.finish()

    async def post(self, section):
        self.authed()

        if section in ('startinstance', 'stopinstance', 'rebootinstance', 'resetinstance'):

            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                self.finish()
                return

            access_key_id = self.get_argument('access_key_id', '')
            instance_name = self.get_argument('instance_name', '')
            if section in ('stopinstance', 'rebootinstance'):
                force = self.get_argument('force', '') and 'true' or None
            elif section == 'resetinstance':
                image_code = self.get_argument('image_code', '')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            opstr = {'startinstance': '启动', 'stopinstance': '停止', 'rebootinstance': '重启', 'resetinstance': '重置'}

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            if section == 'startinstance':
                result, data, reqid = await mod.shell.async_task(srv.StartInstance, instance_name)
            elif section == 'stopinstance':
                result, data, reqid = await mod.shell.async_task(srv.StopInstance, instance_name, ForceStop=force)
            elif section == 'rebootinstance':
                result, data, reqid = await mod.shell.async_task(srv.RebootInstance, instance_name, ForceStop=force)
            elif section == 'resetinstance':
                result, data, reqid = await mod.shell.async_task(srv.ResetInstance, instance_name, ImageCode=image_code)
            if not result:
                self.write({'code': -1, 'msg': '云服务器 %s %s失败！（%s）' % (instance_name, opstr[section], data['Message'])})
                self.finish()
                return

            self.write({'code': 0, 'msg': '云服务器%s指令发送成功！' % opstr[section], 'data': data})
            self.finish()

        elif section in ('createsnapshot', 'deletesnapshot', 'cancelsnapshot', 'rollbacksnapshot'):

            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                self.finish()
                return

            access_key_id = self.get_argument('access_key_id', '')
            instance_name = self.get_argument('instance_name', '')
            disk_code = self.get_argument('disk_code', '')
            if section in ('deletesnapshot', 'cancelsnapshot', 'rollbacksnapshot'):
                snapshot_code = self.get_argument('snapshot_code', '')

            access_key_secret = self._get_secret(access_key_id)
            if access_key_secret == False:
                self.write({'code': -1, 'msg': '该帐号不存在！'})
                self.finish()
                return

            opstr = {'createsnapshot': '创建', 'deletesnapshot': '删除', 'cancelsnapshot': '取消', 'rollbacksnapshot': '回滚'}

            srv = aliyuncs.ECS(access_key_id, access_key_secret)
            if section == 'createsnapshot':
                result, data, reqid = await mod.shell.async_task(srv.CreateSnapshot, InstanceName=instance_name, DiskCode=disk_code)
            elif section == 'deletesnapshot':
                result, data, reqid = await mod.shell.async_task(srv.DeleteSnapshot, InstanceName=instance_name, DiskCode=disk_code, SnapshotCode=snapshot_code)
            elif section == 'cancelsnapshot':
                result, data, reqid = await mod.shell.async_task(srv.CancelSnapshotRequest, InstanceName=instance_name, SnapshotCode=snapshot_code)
            elif section == 'rollbacksnapshot':
                result, data, reqid = await mod.shell.async_task(srv.RollbackSnapshot, InstanceName=instance_name, DiskCode=disk_code, SnapshotCode=snapshot_code)
            if not result:
                self.write({'code': -1, 'msg': '快照%s失败！（%s）' % (opstr[section], data['Message'])})
                self.finish()
                return

            self.write({'code': 0, 'msg': '快照%s指令发送成功！' % opstr[section], 'data': data})
            self.finish()

        elif section == 'accessinfo':

            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                self.finish()
                return

            instance_name = self.get_argument('instance_name', '')
            accesskey = self.get_argument('accesskey', '')
            accessnet = self.get_argument('accessnet', '')
            accessport = self.get_argument('accessport', '')

            if not instance_name:
                self.write({'code': -1, 'msg': '服务器不存在！'})
                self.finish()
                return

            self.config.set('inpanel', instance_name, '%s|%s|%s' % (accesskey, accessnet, accessport))

            self.write({'code': 0, 'msg': 'InPanel 远程控制设置保存成功！'})
            self.finish()

        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})
            self.finish()


class InPanelIndexHandler(RequestHandler):
    """Index page of InPanel.
    """
    def get(self, instance_name, ip, port):
        path = os.path.join(self.settings['inpanel_path'], 'index.html')
        with open(path, encoding='utf-8') as f:
            html = f.read()
        html = html.replace('<link rel="stylesheet" href="', '<link rel="stylesheet" href="/inpanel/')
        html = html.replace('<script src="', '<script src="/inpanel/')
        html = html.replace("var template_path = '';", "var template_path = '/inpanel';")
        self.write(html)


class InPanelHandler(RequestHandler):
    """Operation proxy of InPanel.
    """
    def handle_response(self, response):
        if response.error and not isinstance(response.error, tornado.httpclient.HTTPError):
            loginfo("response has error %s", response.error)
            self.set_status(500)
            self.write("Internal server error:\n" + str(response.error))
            self.finish()
        else:
            self.set_status(response.code)
            for header in ('Date', 'Cache-Control', 'Content-Type', 'Etag', 'Location'):
                v = response.headers.get(header)
                if v:
                    self.set_header(header, v)
            if response.body:
                self.write(response.body.decode('utf-8'))
            self.finish()

    def forward(self, port=None, host=None):
        try:
            tornado.httpclient.AsyncHTTPClient().fetch(
                tornado.httpclient.HTTPRequest(
                    url = "%s://%s:%s%s" % (
                        self.request.protocol, host or "127.0.0.1",
                        port or 80, self.request.uri),
                    method=self.request.method,
                    body=self.request.body,
                    headers=self.request.headers,
                    follow_redirects=False),
                self.handle_response)
        except tornado.httpclient.HTTPError as x:
            loginfo("tornado signalled HTTPError %s", x)
            if hasattr(x, 'response') and x.response:
                self.handle_response(x.response)
        except:
            self.set_status(500)
            self.write("Internal server error\n")
            self.finish()

    def gen_token(self, instance_name):
        if not self.config.has_option('inpanel', instance_name):
            self.set_status(403)
            self.finish()
            return
        else:
            data = self.config.get('inpanel', instance_name)
            data = data.split('|')
            accesskey = data[0]

        accesskey = b64decode(accesskey)
        key = accesskey[:24]
        iv = accesskey[24:]
        k = pyDes.triple_des(key, pyDes.CBC, iv, pad=None, padmode=pyDes.PAD_PKCS5)
        access_token = k.encrypt('timestamp:%d' % int(time.time()))
        access_token = b64encode(access_token)
        return access_token

    def get(self, instance_name, ip, port, uri):
        self.authed()
        self.request.body = None
        self.request.uri = '/'+uri
        self.request.headers['X-ACCESS-TOKEN'] = self.gen_token(instance_name)
        self.forward(port, ip)

    def post(self, instance_name, ip, port, uri):
        self.authed()
        self.request.uri = '/'+uri
        self.request.headers['X-ACCESS-TOKEN'] = self.gen_token(instance_name)
        self.forward(port, ip)


class RepoYumHandler(RequestHandler):
    """Handler for YUM Request.
    """
    def get(self, sec, repo=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 YUM ！'})
            return
        if sec == 'list':
            items = yum.get_list()
            if items is None:
                self.write({'code': -1, 'msg': '获取配置失败！'})
            else:
                self.write({'code': 0, 'msg': '', 'data': items})
        elif sec == 'item':
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo == None:
                self.write({'code': -1, 'msg': '配置文件不能为空！'})
                return
            data = yum.get_item(repo)
            if data is None:
                self.write({'code': -1, 'msg': '配置文件不存在！'})
            else:
                self.write({'code': 0, 'msg': '', 'data': data})
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, sec, repo=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 YUM ！'})
            return

        if sec in ('edit', 'add'):
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo is None:
                self.write({'code': -1, 'msg': '配置文件不能为空！'})
                return
            serverid = self.get_argument('serverid', '')
            if serverid == '':
                self.write({'code': -1, 'msg': '仓库标识ID不能为空！'})
                return
            name = self.get_argument('name', '')
            if name == '':
                self.write({'code': -1, 'msg': '仓库名称不能为空！'})
                return
            baseurl = self.get_argument('baseurl', '')
            if baseurl == '':
                self.write({'code': -1, 'msg': '仓库路径不能为空！'})
                return
            enabled = self.get_argument('enabled', True)
            gpgcheck = self.get_argument('gpgcheck', False)
            data = {
                serverid: {
                    'name': name,
                    'enabled': 0 if not enabled else 1,
                    'baseurl': baseurl,
                    'gpgcheck': 0 if not gpgcheck else 1,
                    'gpgkey': ''
                }
            }
            if sec == 'edit':
                if not yum.item_exists(repo):
                    self.write({'code': -1, 'msg': '配置文件不存在！'})
                    return
                if yum.set_item(repo, data) is True:
                    self.write({'code': 0, 'msg': '配置修改成功！'})
                else:
                    self.write({'code': -1, 'msg': '配置修改失败！'})
            else:
                if yum.item_exists(repo):
                    self.write({'code': -1, 'msg': '配置文件已存在！'})
                    return
                if yum.add_item(repo, data) is True:
                    self.write({'code': 0, 'msg': '配置添加成功！'})
                else:
                    self.write({'code': -1, 'msg': '配置添加失败！'})
        elif sec == 'del':
            if repo is None:
                repo = self.get_argument('repo', None)
            if repo is None:
                self.write({'code': -1, 'msg': '配置文件不能为空！'})
                return
            if not yum.item_exists(repo):
                self.write({'code': -1, 'msg': '配置文件不存在！'})
                return
            if yum.del_item(repo) is True:
                self.write({'code': 0, 'msg': '配置文件已移入回收站！'})
            else:
                self.write({'code': -1, 'msg': '删除失败！'})
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoDnfHandler(RequestHandler):
    """Handler for DNF Repository Request.
    """
    def get(self, sec, repo=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 DNF ！'})
            return
        if sec == 'list':
            result = mod.dnf.web_handler({'action': 'list'})
            self.write(result)
        elif sec == 'item':
            if repo is None:
                repo = self.get_argument('repo', None)
            result = mod.dnf.web_handler({'action': 'item', 'repo': repo})
            self.write(result)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, sec, repo=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 DNF ！'})
            return

        context = {
            'action': sec,
            'repo': repo if repo else self.get_argument('repo', ''),
            'serverid': self.get_argument('serverid', ''),
            'name': self.get_argument('name', ''),
            'baseurl': self.get_argument('baseurl', ''),
            'enabled': self.get_argument('enabled', True),
            'gpgcheck': self.get_argument('gpgcheck', False)
        }
        
        result = mod.dnf.web_handler(context)
        self.write(result)


class RepoAptHandler(RequestHandler):
    """Handler for APT Repository Request.
    """
    def get(self, sec, source=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 APT ！'})
            return
        if sec == 'list':
            result = mod.apt.web_handler({'action': 'list'})
            self.write(result)
        elif sec == 'item':
            if source is None:
                source = self.get_argument('source', None)
            result = mod.apt.web_handler({'action': 'item', 'source': source})
            self.write(result)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, sec, source=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 APT ！'})
            return

        context = {
            'action': sec,
            'source': source if source else self.get_argument('source', ''),
            'content': self.get_argument('content', ''),
            'sources': self.get_argument('sources', [])
        }
        
        result = mod.apt.web_handler(context)
        self.write(result)


class FirewallHandler(RequestHandler):
    """Handler for Firewall Management."""
    def get(self, action):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置防火墙！'})
            return
        
        context = {'action': action}
        result = mod.firewall.web_handler(context)
        self.write(result)
    
    def post(self, action):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置防火墙！'})
            return
        
        context = {
            'action': action,
            'port': self.get_argument('port', ''),
            'protocol': self.get_argument('protocol', 'tcp'),
            'zone': self.get_argument('zone', ''),
            'ip': self.get_argument('ip', ''),
            'action_type': self.get_argument('action_type', 'allow')
        }
        
        result = mod.firewall.web_handler(context)
        self.write(result)


class BackendHandler(RequestHandler):
    """Backend process manager
    """
    def initialize(self):
        self.task_manager = TaskManager(self.settings, self.config)

    def get(self, jobname):
        """Get the status of the new process
        """
        self.authed()
        self.write(self.task_manager._get_job(jobname))

    def post(self, jobname):
        """Create a new backend process
        """
        print('jobname: ', jobname)
        self.authed()

        # centos/redhat only job
        if jobname in ('yum_repolist', 'yum_installrepo', 'yum_info',
                       'yum_install', 'yum_uninstall', 'yum_ext_info'):
            if self.settings['os_name'] not in ('centos', 'redhat'):
                self.write({'code': -1, 'msg': '不支持的系统类型！'})
                return

        if self.config.get('runtime', 'mode') == 'demo':
            if jobname in ('update', 'datetime', 'swapon', 'swapoff', 'mount', 'umount', 'format'):
                self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                return

        if jobname == 'update':
            self.task_manager._call(self.task_manager.update)
        elif jobname in ('service_restart', 'service_start', 'service_stop'):
            name = self.get_argument('name', '')
            service = self.get_argument('service', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if service in ('network', 'sshd', 'inpanel', 'iptables'):
                    self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                    return

            if service not in mod.service.Service.service_items:
                self.write({'code': -1, 'msg': '未支持的服务！'})
                return
            if not name: name = service
            dummy, action = jobname.split('_')
            if service != '':
                self.task_manager._call(partial(self.task_manager.service, action, service, name))
        elif jobname == 'datetime':
            newdatetime = self.get_argument('datetime', '')
            # check datetime format
            try:
                datetime.strptime(newdatetime, '%Y-%m-%d %H:%M:%S')
            except:
                self.write({'code': -1, 'msg': '时间格式有错误！'})
                return
            self.task_manager._call(partial(self.task_manager.datetime, newdatetime))
        elif jobname in ('swapon', 'swapoff'):
            devname = self.get_argument('devname', '')
            if jobname == 'swapon':
                action = 'on'
            else:
                action = 'off'
            self.task_manager._call(partial(self.task_manager.swapon, action, devname))
        elif jobname in ('mount', 'umount'):
            devname = self.get_argument('devname', '')
            mountpoint = self.get_argument('mountpoint', '')
            fstype = self.get_argument('fstype', '')
            if jobname == 'mount':
                action = 'mount'
            else:
                action = 'umount'
            self.task_manager._call(partial(self.task_manager.mount, action, devname, mountpoint, fstype))
        elif jobname == 'format':
            devname = self.get_argument('devname', '')
            fstype = self.get_argument('fstype', '')
            self.task_manager._call(partial(self.task_manager.format, devname, fstype))
        elif jobname == 'yum_repolist':
            self.task_manager._call(self.task_manager.yum_repolist)
        elif jobname == 'yum_installrepo':
            repo = self.get_argument('repo', '')
            self.task_manager._call(partial(self.task_manager.yum_installrepo, repo))
        elif jobname == 'yum_info':
            pkg = self.get_argument('pkg', '')
            repo = self.get_argument('repo', '*')
            option = self.get_argument('option', '')
            if option == 'update':
                if not pkg in [v for k,vv in yum.yum_pkg_alias.items() for v in vv]:
                    self.write({'code': -1, 'msg': '未支持的软件包！'})
                    return
            else:
                option = 'install'
                if not pkg in yum.yum_pkg_alias:
                    self.write({'code': -1, 'msg': '未支持的软件包！'})
                    return
                if repo not in yum.yum_repolist + ('installed', '*'):
                    self.write({'code': -1, 'msg': '未知的软件源 %s！' % repo})
                    return
            self.task_manager._call(partial(self.task_manager.yum_info, pkg, repo, option))
        elif jobname in ('yum_install', 'yum_uninstall', 'yum_update'):
            repo = self.get_argument('repo', '')
            pkg = self.get_argument('pkg', '')
            ext = self.get_argument('ext', '')
            version = self.get_argument('version', '')
            release = self.get_argument('release', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if pkg in ('sshd', 'iptables'):
                    self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                    return

            if not pkg in yum.yum_pkg_relatives:
                self.write({'code': -1, 'msg': '软件包不存在！'})
                return
            if ext and not ext in yum.yum_pkg_relatives[pkg]:
                self.write({'code': -1, 'msg': '扩展不存在！'})
                return
            if jobname == 'yum_install':
                if repo not in yum.yum_repolist:
                    self.write({'code': -1, 'msg': '未知的软件源 %s！' % repo})
                    return
                handler = self.task_manager.yum_install
            elif jobname == 'yum_uninstall':
                handler = self.task_manager.yum_uninstall
            elif jobname == 'yum_update':
                handler = self.task_manager.yum_update
            self.task_manager._call(partial(handler, repo, pkg, version, release, ext))
        elif jobname == 'yum_ext_info':
            pkg = self.get_argument('pkg', '')
            if not pkg in yum.yum_pkg_relatives:
                self.write({'code': -1, 'msg': '软件包不存在！'})
                return
            self.task_manager._call(partial(self.task_manager.yum_ext_info, pkg))
        elif jobname in ('move', 'copy'):
            srcpath = self.get_argument('srcpath', '')
            despath = self.get_argument('despath', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if jobname == 'move':
                    if not srcpath.startswith('/var/www') or not despath.startswith('/var/www'):
                        self.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                        return
                elif jobname == 'copy':
                    if not despath.startswith('/var/www'):
                        self.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                        return

            if not Path(srcpath).exists():
                if not Path(srcpath.strip('*')).exists():
                    self.write({'code': -1, 'msg': '源路径不存在！'})
                    return
            if jobname == 'copy':
                handler = self.task_manager.copy
            elif jobname == 'move':
                handler = self.task_manager.move
            self.task_manager._call(partial(handler, srcpath, despath))
        elif jobname == 'remove':
            paths = self.get_argument('paths', '')
            paths = paths.split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                for p in paths:
                    if not p.startswith('/var/www') and not p.startswith(self.settings['package_path']):
                        self.write({'code': -1, 'msg': '演示模式不允许在 /var/www 以外的目录下执行删除操作！'})
                        return

            self.task_manager._call(partial(self.task_manager.remove, paths))
        elif jobname == 'compress':
            zippath = self.get_argument('zippath', '')
            paths = self.get_argument('paths', '')
            paths = paths.split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                if not zippath.startswith('/var/www'):
                    self.write({'code': -1, 'msg': '演示模式不允许在 /var/www 以外的目录下创建压缩包！'})
                    return
                for p in paths:
                    if not p.startswith('/var/www'):
                        self.write({'code': -1, 'msg': '演示模式不允许在 /var/www 以外的目录下创建压缩包！'})
                        return

            self.task_manager._call(partial(self.task_manager.compress, zippath, paths))
        elif jobname == 'decompress':
            zippath = self.get_argument('zippath', '')
            despath = self.get_argument('despath', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if not zippath.startswith('/var/www') and not zippath.startswith(self.settings['package_path']) or \
                   not despath.startswith('/var/www') and not despath.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': '演示模式不允许在 /var/www 以外的目录下执行解压操作！'})
                    return

            self.task_manager._call(partial(self.task_manager.decompress, zippath, despath))
        elif jobname == 'ntpdate':
            server = self.get_argument('server', '')
            self.task_manager._call(partial(self.task_manager.ntpdate, server))
        elif jobname == 'chown':
            paths = self.get_argument('paths', '')
            paths = paths.split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                for p in paths:
                    if not p.startswith('/var/www'):
                        self.write({'code': -1, 'msg': '演示模式不允许在 /var/www 以外的目录下执行此操作！'})
                        return

            a_user = self.get_argument('user', '')
            a_group = self.get_argument('group', '')
            recursively = self.get_argument('recursively', '')
            option = recursively == 'on' and '-R' or ''
            self.task_manager._call(partial(self.task_manager.chown, paths, a_user, a_group, option))
        elif jobname == 'chmod':
            paths = self.get_argument('paths', '')
            paths = paths.split(',')

            if self.config.get('runtime', 'mode') == 'demo':
                for p in paths:
                    if not p.startswith('/var/www'):
                        self.write({'code': -1, 'msg': '演示模式不允许在 /var/www 以外的目录下执行此操作！'})
                        return

            perms = self.get_argument('perms', '')
            recursively = self.get_argument('recursively', '')
            option = recursively == 'on' and '-R' or ''
            self.task_manager._call(partial(self.task_manager.chmod, paths, perms, option))
        elif jobname == 'wget':
            url = self.get_argument('url', '')
            path = self.get_argument('path', '')

            if self.config.get('runtime', 'mode') == 'demo':
                if not path.startswith('/var/www') and not path.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': '演示模式不允许下载到 /var/www 以外的目录！'})
                    return

            self.task_manager._call(partial(self.task_manager.wget, url, path))
        elif jobname == 'mysql_fupdatepwd':
            password = self.get_argument('password', '')
            passwordc = self.get_argument('passwordc', '')
            if password != passwordc:
                self.write({'code': -1, 'msg': '两次密码输入不一致！'})
                return
            self.task_manager._call(partial(self.task_manager.mysql_fupdatepwd, password))
        elif jobname == 'mysql_databases':
            password = self.get_argument('password', '')
            self.task_manager._call(partial(self.task_manager.mysql_databases, password))
        elif jobname == 'mysql_dbinfo':
            password = self.get_argument('password', '')
            dbname = self.get_argument('dbname', '')
            self.task_manager._call(partial(self.task_manager.mysql_dbinfo, password, dbname))
        elif jobname == 'mysql_users':
            password = self.get_argument('password', '')
            dbname = self.get_argument('dbname', '')
            self.task_manager._call(partial(self.task_manager.mysql_users, password, dbname))
        elif jobname == 'mysql_rename':
            password = self.get_argument('password', '')
            dbname = self.get_argument('dbname', '')
            newname = self.get_argument('newname', '')
            if dbname == newname:
                self.write({'code': -1, 'msg': '数据库名无变化！'})
                return
            self.task_manager._call(partial(self.task_manager.mysql_rename, password, dbname, newname))
        elif jobname == 'mysql_create':
            password = self.get_argument('password', '')
            dbname = self.get_argument('dbname', '')
            collation = self.get_argument('collation', '')
            self.task_manager._call(partial(self.task_manager.mysql_create, password, dbname, collation))
        elif jobname == 'mysql_export':
            password = self.get_argument('password', '')
            dbname = self.get_argument('dbname', '')
            path = self.get_argument('path', '')

            if not path:
                self.write({'code': -1, 'msg': '请选择数据库导出目录！'})
                return

            if self.config.get('runtime', 'mode') == 'demo':
                if not path.startswith('/var/www') and not path.startswith(self.settings['package_path']):
                    self.write({'code': -1, 'msg': '演示模式不允许导出到 /var/www 以外的目录！'})
                    return

            self.task_manager._call(partial(self.task_manager.mysql_export, password, dbname, path))
        elif jobname == 'mysql_drop':
            password = self.get_argument('password', '')
            dbname = self.get_argument('dbname', '')
            self.task_manager._call(partial(self.task_manager.mysql_drop, password, dbname))
        elif jobname == 'mysql_createuser':
            password = self.get_argument('password', '')
            user = self.get_argument('user', '')
            host = self.get_argument('host', '')
            pwd = self.get_argument('pwd', '')
            self.task_manager._call(partial(self.task_manager.mysql_createuser, password, user, host, pwd))
        elif jobname == 'mysql_userprivs':
            password = self.get_argument('password', '')
            username = self.get_argument('username', '')
            if not '@' in username:
                self.write({'code': -1, 'msg': '用户不存在！'})
                return
            user, host = username.split('@', 1)
            self.task_manager._call(partial(self.task_manager.mysql_userprivs, password, user, host))
        elif jobname == 'mysql_updateuserprivs':
            password = self.get_argument('password', '')
            username = self.get_argument('username', '')
            privs = self.get_argument('privs', '')
            try:
                privs = tornado.escape.json_decode(privs)
            except:
                self.write({'code': -1, 'msg': '权限数据有误！'})
                return
            dbname = self.get_argument('dbname', '')
            if not '@' in username:
                self.write({'code': -1, 'msg': '用户不存在！'})
                return
            user, host = username.split('@', 1)
            privs = [
                priv.replace('_priv', '').replace('_', ' ').upper()
                    .replace('CREATE TMP TABLE', 'CREATE TEMPORARY TABLES')
                    .replace('SHOW DB', 'SHOW DATABASES')
                    .replace('REPL CLIENT', 'REPLICATION CLIENT')
                    .replace('REPL SLAVE', 'REPLICATION SLAVE')
                for priv, value in privs.items() if '_priv' in priv and value == 'Y']
            self.task_manager._call(partial(self.task_manager.mysql_updateuserprivs, password, user, host, privs, dbname))
        elif jobname == 'mysql_setuserpassword':
            password = self.get_argument('password', '')
            username = self.get_argument('username', '')
            if not '@' in username:
                self.write({'code': -1, 'msg': '用户不存在！'})
                return
            user, host = username.split('@', 1)
            pwd = self.get_argument('pwd', '')
            self.task_manager._call(partial(self.task_manager.mysql_setuserpassword, password, user, host, pwd))
        elif jobname == 'mysql_dropuser':
            password = self.get_argument('password', '')
            username = self.get_argument('username', '')
            if not '@' in username:
                self.write({'code': -1, 'msg': '用户不存在！'})
                return
            user, host = username.split('@', 1)
            user, host = mod.user.strip(), host.strip()
            if user == 'root' and host != '%':
                self.write({'code': -1, 'msg': '该用户不允许删除！'})
                return
            self.task_manager._call(partial(self.task_manager.mysql_dropuser, password, user, host))
        elif jobname == 'ssh_genkey':
            path = self.get_argument('path', '')
            password = self.get_argument('password', '')
            if not path:
                path = '/root/.ssh/sshkey_inpanel'
            self.task_manager._call(partial(self.task_manager.ssh_genkey, path, password))
        elif jobname == 'ssh_chpasswd':
            path = self.get_argument('path', '')
            oldpassword = self.get_argument('oldpassword', '')
            newpassword = self.get_argument('newpassword', '')
            if not path:
                path = '/root/.ssh/sshkey_inpanel'
            self.task_manager._call(partial(self.task_manager.ssh_chpasswd, path, oldpassword, newpassword))
        elif jobname in ('inpanel_install', 'inpanel_uninstall', 'inpanel_config'):
            if self.config.get('runtime', 'mode') == 'demo':
                self.write({'code': -1, 'msg': '演示模式不允许此类操作！'})
                return
            ssh_ip = self.get_argument('ssh_ip', '')
            ssh_port = self.get_argument('ssh_port', '22')
            ssh_user = self.get_argument('ssh_user', '')
            ssh_password = self.get_argument('ssh_password', '')
            instance_name = self.get_argument('instance_name', '')
            if jobname == 'inpanel_install':
                accessnet = self.get_argument('accessnet', 'public')
                accesskey = utils.gen_accesskey()
                accessport = '14433'
            elif jobname == 'inpanel_config':
                if not self.config.has_option('inpanel', instance_name):
                    self.write({'code': -1, 'msg': '该服务器还未配置远程控制！'})
                    return
                accessdata = self.config.get('inpanel', instance_name)
                accessdata = accessdata.split('|')
                accesskey = accessdata[0]
            if jobname == 'inpanel_install':
                self.task_manager._call(partial(self.task_manager.inpanel_install, ssh_ip, ssh_port, ssh_user, ssh_password, instance_name, accessnet, accessport, accesskey))
            elif jobname == 'inpanel_uninstall':
                self.task_manager._call(partial(self.task_manager.inpanel_uninstall, ssh_ip, ssh_port, ssh_user, ssh_password, instance_name))
            elif jobname == 'inpanel_config':
                self.task_manager._call(partial(self.task_manager.inpanel_config, ssh_ip, ssh_port, ssh_user, ssh_password, accesskey))
        elif jobname == 'uploadtoftp':
            address = self.get_argument('address', '')
            account = self.get_argument('account', '')
            password = self.get_argument('password', '')
            source = self.get_argument('source', '')
            target = self.get_argument('target', '')
            self.task_manager._call(partial(self.task_manager.uploadtoftp, address, account, password, source, target))
        else:   # undefined job
            self.write({'code': -1, 'msg': '未定义的操作！'})
            return

        self.write({'code': 0, 'msg': ''})


class SSLTLSHandler(RequestHandler):
    """Handler for SSL/TLS setting.
    """
    def get(self, sec, x=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 SSL ！'})
            return
        certs = Certificate()
        if sec == 'keys':
            keys_list = certs.get_keys_list()
            if keys_list is None:
                self.write({'code': -1, 'msg': '获取私钥失败！'})
            else:
                self.write({'code': 0, 'msg': '获取私钥成功！', 'list': keys_list})
        elif sec == 'crts':
            crts_list = certs.get_crts_list()
            if crts_list is None:
                self.write({'code': -1, 'msg': '获取证书失败！'})
            else:
                self.write({'code': 0, 'msg': '获取证书成功！', 'list': crts_list})
        elif sec == 'csrs':
            csrs_list = certs.get_csrs_list()
            if csrs_list is None:
                self.write({'code': -1, 'msg': '获取证书签名请求失败！'})
            else:
                self.write({'code': 0, 'msg': '获取证书签名请求成功！', 'list': csrs_list})
        elif sec == 'host':
            host_list = certs.get_host_list()
            if host_list is None:
                self.write({'code': -1, 'msg': '获取站点失败！'})
            else:
                self.write({'code': 0, 'msg': '获取站点成功！', 'list': host_list})
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, sec, x=None):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 SSL ！'})
            return
        action = self.get_argument('action', '')
        certs = Certificate()

        if sec == 'keys':
            if action == 'add_domain_keys':
                self.write({'code': 0, 'msg': u'创建测试私钥成功！(正在测试的功能)'})

