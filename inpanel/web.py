# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Web 查询模块'''

import binascii
import os
import re
import time
from base64 import b64decode, b64encode
from hashlib import md5
from json import dumps, loads
from logging import info as loginfo
from pathlib import Path
from shlex import quote
from uuid import uuid4

from .mod import login
from .mod import query
from . import mod


def _get_mod(name):
    """延迟导入 mod 子模块，避免启动时因环境不兼容而崩溃"""
    m = getattr(mod, name, None)
    if m is None:
        m = __import__('inpanel.mod.' + name, fromlist=[name])
        setattr(mod, name, m)
    return m


def _get_task_manager():
    from .mod.task import TaskManager
    return TaskManager

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
        """将 JSON 数据解析为参数列表。"""
        self.config = config.load_config()
        self.lastfile = config.lastfile_config()

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
        # 检查访问令牌
        if self.get_argument("_access", None) or self.request.headers.get("X-ACCESS-TOKEN"):
            if self.config.get('auth', 'accesskeyenable') != 'on':
                raise tornado.web.HTTPError(403, "Access Token Not Allowed")
        else:
            # 检查 xsrf cookie
            token = (self.get_argument("_xsrf", None) or self.request.headers.get("X-XSRF-TOKEN"))
            if not token:
                raise tornado.web.HTTPError(403, "'_xsrf' argument missing from POST")
            if self.xsrf_token != token:
                raise tornado.web.HTTPError(403, "XSRF cookie does not match POST argument")

    def authed(self):
        # 检查访问令牌
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
            # 获取 30 分钟内的 cookie
            if cur_authed.decode('utf-8') == 'yes':
                # 每 5 分钟重新生成 cookie 时间戳
                if self.get_secure_cookie('authed', None, 5.0/1440) == None:
                    self.set_secure_cookie('authed', 'yes', None)

    def getlastactive(self):
        # 从 cookie 获取最后活跃时间
        cv = self.get_cookie('authed', False)
        try:
            return int(cv.split('|')[1])
        except:
            return 0

    @property
    def xsrf_token(self):
        if not hasattr(self, "_xsrf_token"):
            token = self.get_cookie("XSRF-TOKEN") # 或 self.request.headers.get("X-XSRF-TOKEN")
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
            'htmlTitle': '{{ htmlTitle }}', # JS 模板代码
            'releasetime': version_info['releasetime'],
            'template_path': ''
        }
        self.render("index.html", **data)

class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        self.set_header('Server', app_name)

    def authed(self):
        # 检查访问令牌
        self.config = config.load_config()
        access_token = (self.get_argument("_access", None) or self.request.headers.get("X-ACCESS-TOKEN"))
        if access_token and self.config.get('auth', 'accesskeyenable') == 'on':
            if access_token != self.config.get('auth', 'accesskey'):
                raise tornado.web.HTTPError(403, 'Access Token Error')
                # print('access_token 匹配')
                # return
        else:
            cur_authed = self.get_secure_cookie('authed', None, 30.0/1440)
            if not cur_authed:
                raise tornado.web.HTTPError(403, "Please login first")
            # 获取 30 分钟内的 cookie
            if cur_authed.decode('utf-8') == 'yes':
                # 每 5 分钟重新生成 cookie 时间戳
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
    '''文件预览处理器
    待办：支持多文件
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
    """将 XSRF token 写入 cookie。"""
    def get(self):
        self.xsrf_token


class AuthStatusHandler(RequestHandler):
    """检查客户端是否已授权。"""
    def check_xsrf_cookie(self):
        pass

    def get(self):
        self.write({'lastactive': self.getlastactive()})

    def post(self):
        # 授权并更新 cookie
        try:
            self.authed()
            self.write({'authed': 'yes'})
        except:
            self.write({'authed': 'no'})


class ClientHandler(RequestHandler):
    """获取客户端信息。"""
    def get(self, argument):
        if argument == 'ip':
            self.write(self.request.remote_ip)


class LoginHandler(RequestHandler):
    """验证用户名和密码。"""
    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        result = login.handle_login(self.config, username, password)
        if result['code'] >= 0:
            self.set_secure_cookie('authed', 'yes', None)
        self.write(result)


class LogoutHandler(RequestHandler):
    """登出。"""
    def post(self):
        self.authed()
        login.handle_logout()
        self.clear_cookie('authed')


class SitePackageHandler(RequestHandler):
    """查询网站软件包信息的接口。"""

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

        # 从缓存获取
        if Path(packages_cachefile).exists():
            # 检查文件修改时间
            mtime = os.stat(packages_cachefile).st_mtime
            if time.time() - mtime < 86400:  # 缓存 24 小时
                with open(packages_cachefile, encoding='utf-8') as f:
                    packages = f.read()

        # 从 API 获取
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

        packages = loads(packages)
        self.write({'code': 0, 'msg':'', 'data': packages})

        self.finish()

    def getdownloadtask(self):
        name = self.get_argument('name', '')
        version = self.get_argument('version', '')

        if not name or not version:
            self.write({'code': -1, 'msg': '获取安装包下载地址失败！'})
            return

        # 从缓存获取软件包列表
        packages_cachefile = str(Path(self.settings['package_path']) / '.meta')
        if not Path(packages_cachefile).exists():
            self.write({'code': -1, 'msg': '获取安装包下载地址失败！'})
            return
        with open(packages_cachefile, encoding='utf-8') as f:
            packages = f.read()
        packages = loads(packages)

        # 检查 name 和 version 是否可用
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
    """查询服务器信息的接口。
    
    可查询一个或多个项，以逗号分隔。
    示例：
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
    """网络配置处理器。"""
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
    """系统时间设置处理器。"""
    def get(self, sec, region=None):
        self.authed()
        result = server.ServerInfo.handle_time_get(sec, region, self.config)
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
    """InPanel 设置。"""
    async def get(self, section):
        self.authed()
        await setting.handle_get(self, section)

    def post(self, section):
        self.authed()
        setting.handle_post(self, section)


class ServiceHandler(RequestHandler):
    """服务管理处理器。

    路由：/api/service/<action>

    GET 支持：
        - list: 获取分类服务列表（固定服务 + 其他服务 + 用户自定义服务）
        - detail/<service_id>: 获取服务详情（配置文件、日志、路径等）
        - status/<service_id>: 获取单个服务状态
        - autostart_list: 获取开机自启服务列表

    POST 支持：
        - start, stop, restart: 服务启停控制
        - chkconfig: 开机自启管理
        - set_category: 设置用户自定义分类
        - install, uninstall: 安装/卸载服务
    """
    def get(self, action, service_id=None):
        self.authed()
        if action == 'list':
            from .mod import service as svc_mod
            data = svc_mod.get_service_list()
            self.write({'code': 0, 'data': data})
        elif action == 'detail' and service_id:
            from .mod import service as svc_mod
            detail = svc_mod.get_service_detail(service_id)
            if detail:
                self.write({'code': 0, 'data': detail})
            else:
                self.write({'code': -1, 'msg': f'服务 {service_id} 不存在'})
        elif action == 'status' and service_id:
            from .mod import service as svc_mod
            status = svc_mod.get_status(service_id)
            self.write({'code': 0, 'data': {'status': status}})
        elif action == 'autostart_list':
            from .mod import service as svc_mod
            data = svc_mod.get_autostart_list()
            self.write({'code': 0, 'data': data})
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, service_id=None):
        self.authed()
        from .mod import service as svc_mod
        from .mod.service_manager import get_service_manager

        manager = get_service_manager()
        if not manager:
            self.write({'code': -1, 'msg': '当前系统不支持服务管理'})
            return

        if action in ('start', 'stop', 'restart'):
            name = self.get_argument('name', '') or (service_id or '')
            service_label = self.get_argument('service', '') or (service_id or '')
            if not service_label:
                self.write({'code': -1, 'msg': '服务名称不能为空'})
                return
            # 使用 task 异步处理，避免阻塞请求
            from functools import partial
            tm = _get_task_manager()(self.settings, self.config)
            func_name = f'service_{action}'
            func = getattr(svc_mod, func_name, None)
            if func is None:
                self.write({'code': -1, 'msg': f'未定义的操作：{func_name}'})
                return
            coro = partial(func, tm=tm, service=service_label, name=name)
            tm.run_job(coro)
            jobname = f'service.{action}_{service_label}'
            self.write({'code': 0, 'msg': f'任务 {jobname} 已创建，正在处理中...'})

        elif action == 'chkconfig':
            service_label = self.get_argument('service', '') or (service_id or '')
            autostart = self.get_argument('autostart', '')
            if not service_label:
                self.write({'code': -1, 'msg': '服务名称不能为空'})
                return
            autostart_str = {'on': '启用', 'off': '禁用'}
            if autostart == 'on':
                ok, msg = manager.enable(service_label)
            else:
                ok, msg = manager.disable(service_label)
            if ok:
                self.write({'code': 0, 'msg': f'成功{autostart_str.get(autostart, autostart)} {service_label} 自动启动！'})
            else:
                self.write({'code': -1, 'msg': msg})

        elif action == 'set_category':
            svc_id = self.get_argument('service', '') or (service_id or '')
            category = self.get_argument('category', '')
            if not svc_id:
                self.write({'code': -1, 'msg': '服务名称不能为空'})
                return
            ok = svc_mod.set_custom_category(svc_id, category)
            if ok:
                self.write({'code': 0, 'msg': f'服务 {svc_id} 分类已更新'})
            else:
                self.write({'code': -1, 'msg': '设置分类失败'})

        elif action == 'install':
            service_label = self.get_argument('service', '') or (service_id or '')
            if not service_label:
                self.write({'code': -1, 'msg': '服务名称不能为空'})
                return
            # 使用 task 异步处理
            from functools import partial
            tm = _get_task_manager()(self.settings, self.config)
            name = self.get_argument('name', '') or service_label
            coro = partial(svc_mod.service_install, tm=tm, service=service_label, name=name)
            tm.run_job(coro)
            jobname = f'service.install_{service_label}'
            self.write({'code': 0, 'msg': f'任务 {jobname} 已创建，正在处理中...'})

        elif action == 'uninstall':
            service_label = self.get_argument('service', '') or (service_id or '')
            if not service_label:
                self.write({'code': -1, 'msg': '服务名称不能为空'})
                return
            # 使用 task 异步处理
            from functools import partial
            tm = _get_task_manager()(self.settings, self.config)
            name = self.get_argument('name', '') or service_label
            coro = partial(svc_mod.service_uninstall, tm=tm, service=service_label, name=name)
            tm.run_job(coro)
            jobname = f'service.uninstall_{service_label}'
            self.write({'code': 0, 'msg': f'任务 {jobname} 已创建，正在处理中...'})

        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class OperationHandler(RequestHandler):
    '''服务器操作处理器。'''

    def post(self, op):
        """执行服务器操作。"""
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
        self.write(_get_mod('disk').handle_fdisk(action, devname, size, unit))

    def service(self):
        _get_mod('service').web_handler(self)

    def user(self):
        _get_mod('user').web_handler(self)

    def file(self):
        _get_mod('file').web_handler(self)

    def apache(self):
        _get_mod('httpd').web_handler(self)

    def nginx(self):
        _get_mod('nginx').web_handler(self)

    def mysql(self):
        _get_mod('mysql').web_handler(self)

    def php(self):
        _get_mod('php').web_handler(self)

    def ssh(self):
        _get_mod('ssh').web_handler(self)

    def cron(self):
        _get_mod('cron').web_handler(self)

    def vsftpd(self):
        _get_mod('vsftpd').web_handler(self)

    def named(self):
        _get_mod('named').web_handler(self)

    def lighttpd(self):
        _get_mod('lighttpd').web_handler(self)

    def proftpd(self):
        _get_mod('proftpd').web_handler(self)

    def pureftpd(self):
        _get_mod('pureftpd').web_handler(self)

    def docker(self):
        _get_mod('docker').web_handler(self)

    def shell(self):
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许执行 shell 命令 ！'})
            return
        action = self.get_argument('action', '')
        cmd = self.get_argument('cmd', '')
        cwd = self.get_argument('cwd', '')
        if action == 'exec_command':
            self.write({'code': 0, 'msg': '命令已发送', 'data': _get_mod('shell').exec_command(cmd, cwd)})

class PageHandler(RequestHandler):
    """返回单页。"""
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
            # 将它们重定向到 http://mod.php.net/index.php?***
            if self.request.query.startswith('=PHP'):
                self.redirect('http://www.mod.php.net/index.php?%s' % self.request.query)
            else:
                self.write(_get_mod('php').phpinfo())


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
    """阿里云 CPS 推广计划。"""
    def get(self):
        self.redirect('http://www.aliyun.com/cps/rebate?from_uid=zop0qMW4KbY=')


class AccountHandler(RequestHandler):
    """ECS 账号处理器。"""
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            result, data, reqid = await _get_mod('shell').async_task(srv.DescribeRegions)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            result, data, reqid = await _get_mod('shell').async_task(srv.DescribeZones, RegionCode=region_code)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            result, data, reqid = await _get_mod('shell').async_task(srv.DescribeInstances, RegionCode=region_code, PageNumber=page_number, PageSize=page_size)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            result, data, reqid = await _get_mod('shell').async_task(srv.DescribeImages, RegionCode=region_code, PageNumber=page_number, PageSize=page_size)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            result, data, reqid = await _get_mod('shell').async_task(srv.DescribeDisks, InstanceName=instance_name)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            result, data, reqid = await _get_mod('shell').async_task(srv.DescribeSnapshots, InstanceName=instance_name, DiskCode=disk_code)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            if section == 'startinstance':
                result, data, reqid = await _get_mod('shell').async_task(srv.StartInstance, instance_name)
            elif section == 'stopinstance':
                result, data, reqid = await _get_mod('shell').async_task(srv.StopInstance, instance_name, ForceStop=force)
            elif section == 'rebootinstance':
                result, data, reqid = await _get_mod('shell').async_task(srv.RebootInstance, instance_name, ForceStop=force)
            elif section == 'resetinstance':
                result, data, reqid = await _get_mod('shell').async_task(srv.ResetInstance, instance_name, ImageCode=image_code)
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

            srv = _get_mod('aliyuncs').ECS(access_key_id, access_key_secret)
            if section == 'createsnapshot':
                result, data, reqid = await _get_mod('shell').async_task(srv.CreateSnapshot, InstanceName=instance_name, DiskCode=disk_code)
            elif section == 'deletesnapshot':
                result, data, reqid = await _get_mod('shell').async_task(srv.DeleteSnapshot, InstanceName=instance_name, DiskCode=disk_code, SnapshotCode=snapshot_code)
            elif section == 'cancelsnapshot':
                result, data, reqid = await _get_mod('shell').async_task(srv.CancelSnapshotRequest, InstanceName=instance_name, SnapshotCode=snapshot_code)
            elif section == 'rollbacksnapshot':
                result, data, reqid = await _get_mod('shell').async_task(srv.RollbackSnapshot, InstanceName=instance_name, DiskCode=disk_code, SnapshotCode=snapshot_code)
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
    """InPanel 首页。"""
    def get(self, instance_name, ip, port):
        path = os.path.join(self.settings['inpanel_path'], 'index.html')
        with open(path, encoding='utf-8') as f:
            html = f.read()
        html = html.replace('<link rel="stylesheet" href="', '<link rel="stylesheet" href="/inpanel/')
        html = html.replace('<script src="', '<script src="/inpanel/')
        html = html.replace("var template_path = '';", "var template_path = '/inpanel';")
        self.write(html)


class InPanelHandler(RequestHandler):
    """InPanel 操作代理。"""
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
    """YUM 源处理器。

    路由：/api/sources/yum/<action>[/<name>]

    GET 支持：overview, list, item, search, install, refresh, mirrors
    POST 支持：switch, mirror-add, mirror-del, repo-add, repo-edit, repo-del, edit
    """
    def get(self, action, name=None):
        self.authed()
        from .mod import yum
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 YUM ！'})
            return
        if action in ('list', 'item', 'overview', 'refresh', 'search', 'install', 'mirrors', 'third_party'):
            yum.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, name=None):
        self.authed()
        from .mod import yum
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 YUM ！'})
            return

        if action in ('switch', 'mirror-add', 'mirror-del', 'repo-add', 'repo-edit', 'repo-del', 'edit', 'third_party', 'third_party-install'):
            yum.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoDnfHandler(RequestHandler):
    """DNF 源处理器。

    GET 支持：overview, list, item, search, install, refresh, mirrors
    POST 支持：switch, mirror-add, mirror-del, repo-add, repo-edit, repo-del, edit
    """
    def get(self, action, name=None):
        self.authed()
        from .mod import dnf
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 DNF ！'})
            return
        if action in ('list', 'item', 'overview', 'refresh', 'search', 'install', 'mirrors', 'third_party'):
            dnf.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, name=None):
        self.authed()
        from .mod import dnf
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 DNF ！'})
            return

        if action in ('switch', 'mirror-add', 'mirror-del', 'repo-add', 'repo-edit', 'repo-del', 'edit', 'third_party', 'third_party-install'):
            dnf.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoAptHandler(RequestHandler):
    """APT 源处理器。

    GET 支持：overview, list, item, search, install, refresh, mirrors
    POST 支持：switch, mirror-add, mirror-del, repo-add, repo-edit, repo-del, edit
    """
    def get(self, action, name=None):
        self.authed()
        from .mod import apt
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 APT ！'})
            return
        if action in ('list', 'item', 'overview', 'refresh', 'search', 'install', 'mirrors', 'third_party'):
            apt.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, name=None):
        self.authed()
        from .mod import apt
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 APT ！'})
            return

        if action in ('switch', 'mirror-add', 'mirror-del', 'repo-add', 'repo-edit', 'repo-del', 'edit', 'parse', 'generate', 'third_party', 'third_party-install'):
            apt.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoBrewHandler(RequestHandler):
    """Homebrew 源处理器。

    Homebrew 概念：
    - 软件仓库列表 = brew tap 列表（内置仓库不可编辑/不可删除）
    - 镜像源切换 = 在内置仓库详情中修改 git remote URL

    GET 支持：overview, list, item, services, search, install, refresh, mirrors
    POST 支持：service, install, switch, mirror-add, mirror-del, tap-add, tap-del, repo-edit
    """
    def get(self, action, name=None):
        self.authed()
        from .mod import brew
        if action in ('overview', 'list', 'item', 'services', 'search', 'install', 'refresh', 'mirrors', 'third_party'):
            brew.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, name=None):
        self.authed()
        from .mod import brew
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 Homebrew ！'})
            return
        if action in ('service', 'install', 'switch', 'enable', 'mirror-add', 'mirror-edit', 'mirror-del',
                   'add', 'del', 'tap-add', 'tap-del', 'repo-edit', 'third_party-install'):
            brew.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoPipHandler(RequestHandler):
    """pip 源处理器。

    GET 支持：overview, list, item, search, install, refresh
    POST 支持：install, add, enable, del
    """
    def get(self, action, name=None):
        self.authed()
        from .mod import pip
        if action in ('overview', 'list', 'item', 'search', 'install', 'refresh'):
            pip.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, name=None):
        self.authed()
        from .mod import pip
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 pip ！'})
            return
        if action in ('install', 'add', 'enable', 'del'):
            pip.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoDockerHandler(RequestHandler):
    """Docker 镜像源处理器。

    路由：/api/sources/docker/<action>[/<name>]

    GET 支持：overview, list, item
    POST 支持：switch, enable, add, edit, del
    """
    def get(self, action, name=None):
        self.authed()
        from .mod import docker_source
        if action in ('overview', 'list', 'item'):
            docker_source.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})

    def post(self, action, name=None):
        self.authed()
        from .mod import docker_source
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置 Docker ！'})
            return
        if action in ('switch', 'enable', 'add', 'edit', 'del'):
            docker_source.web_handler(self, action)
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


class RepoSupportedHandler(RequestHandler):
    """支持的包管理器处理器。"""
    def get(self):
        self.authed()
        from .mod import system as sysmod
        family = sysmod.get_os_family()
        supported = {
            'brew': False,
            'pip': False,
            'yum': False,
            'dnf': False,
            'apt': False,
            'docker': False,
        }
        if family == 'darwin':
            supported['brew'] = True
            supported['pip'] = True
            supported['docker'] = True
        elif family == 'rhel':
            supported['yum'] = True
            supported['dnf'] = True
            supported['pip'] = True
            supported['docker'] = True
        elif family == 'debian':
            supported['apt'] = True
            supported['pip'] = True
            supported['docker'] = True
        else:
            # 回退：通过命令可用性检测
            from shutil import which
            supported['brew'] = which('brew') is not None
            supported['pip'] = which('pip') is not None or which('pip3') is not None
            supported['yum'] = which('yum') is not None
            supported['dnf'] = which('dnf') is not None
            supported['apt'] = which('apt') is not None
            supported['docker'] = which('docker') is not None
        # 确保 pip 在各系统上可用
        if not supported['pip']:
            from shutil import which
            supported['pip'] = which('pip') is not None or which('pip3') is not None
        self.write({'code': 0, 'msg': '', 'data': {'family': family, 'supported': supported}})


class FirewallHandler(RequestHandler):
    """防火墙管理处理器。"""
    def get(self, action):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置防火墙！'})
            return
        
        _get_mod('firewall').web_handler(self, action)
    
    def post(self, action):
        self.authed()
        if self.config.get('runtime', 'mode') == 'demo':
            self.write({'code': -1, 'msg': '演示模式不允许设置防火墙！'})
            return
        
        _get_mod('firewall').web_handler(self, action)


class TaskHandler(RequestHandler):
    """后台异步任务管理器 —— HTTP 接口层。

    负责接收请求、解析参数、委托 TaskManager 执行。
    不包含任务逻辑，只做参数验证和路由。
    """
    def initialize(self):
        super().initialize()
        self.task_manager = _get_task_manager()(self.settings, self.config)
        self._json_args = None

    def _get_arg(self, name, default=''):
        """获取参数，优先从 JSON body 解析，其次从 form/query 参数。"""
        if self._json_args is None:
            try:
                body = self.request.body
                if body:
                    self._json_args = tornado.escape.json_decode(body)
            except Exception:
                self._json_args = {}
        if isinstance(self._json_args, dict) and name in self._json_args:
            return self._json_args[name]
        return self.get_argument(name, default)

    def get(self, jobname):
        """查询任务状态或获取任务列表。

        GET /api/task/list         → 获取所有任务
        GET /api/task/{jobname}    → 获取指定任务状态
        """
        self.authed()
        if jobname == 'list':
            self.write({'code': 0, 'data': self.task_manager.list_jobs()})
        else:
            self.write(self.task_manager.get_job(jobname))

    def post(self, jobname):
        """创建后台异步任务。

        POST /api/task/{jobname}   → 创建并启动任务
        POST /api/task/cancel      → 取消指定任务
        POST /api/task/clear       → 清除已完成任务

        路由约定：jobname 按 模块.函数.action_参数 三段式命名，如 service_install_lighttpd。
        解析时从后往前匹配 TaskManager 上的方法名，剩余段作为位置参数传入。
        额外的关键字参数从 POST body 中获取。
        """
        self.authed()

        # 管理类操作（非异步任务）
        if jobname == 'cancel':
            target = self._get_arg('jobname', '')
            if target:
                result = self.task_manager.cancel_job(target)
                self.write({'code': 0 if result else -1, 'msg': '任务已取消' if result else '无法取消该任务'})
            else:
                self.write({'code': -1, 'msg': '请指定要取消的任务名称'})
            return
        elif jobname == 'clear':
            count = self.task_manager.clear_finished()
            self.write({'code': 0, 'msg': f'已清除 {count} 个已完成任务'})
            return

        # ---- 约定解析路由 ----
        from .mod.task import dispatch_task
        ok, msg = dispatch_task(jobname, self.task_manager,
                                post_body=self.request.body,
                                arguments=self.request.arguments)
        self.write({'code': 0 if ok else -1, 'msg': msg})

    def _get_arg(self, name, default=''):
        """获取参数，优先从 JSON body 解析，其次从 form/query 参数。"""
        import json as json_mod
        if not hasattr(self, '_json_args'):
            try:
                body = self.request.body
                if body:
                    self._json_args = json_mod.loads(body)
            except Exception:
                self._json_args = {}
        if isinstance(self._json_args, dict) and name in self._json_args:
            return self._json_args[name]
        return self.get_argument(name, default)



class SSLTLSHandler(RequestHandler):
    """SSL/TLS 设置处理器。"""
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


class PluginStaticFileHandler(StaticFileHandler):
    '''插件的静态文件处理器（含认证检查）。'''
    
    def initialize(self, path, default_filename=None):
        super().initialize(path, default_filename)
    
    async def get(self, path, include_body=True):
        self.authed()
        path_parts = path.split('/')
        if len(path_parts) >= 2:
            plugin_name = path_parts[0]
            rest = '/'.join(path_parts[1:])
            path = f'{plugin_name}/pages/{rest}'
        await super().get(path, include_body)
        # try:
        #     await super().get(path, include_body)
        # except tornado.web.HTTPError as e:
        #     if e.status_code == 404:
        #         self.set_status(404)
        #         # self.write({'code': 404, 'msg': f'插件静态资源不存在: {path}'})
        #         self.write(f'插件静态资源不存在: {path}')
        #     else:
        #         raise


class PluginHandler(RequestHandler):
    '''插件管理 API 处理器。'''
    
    def _get_plugin_manager(self):
        '''获取插件管理器实例。'''
        if not hasattr(self.application, 'plugin_manager'):
            from .mod.plugins import PluginManager
            self.application.plugin_manager = PluginManager(self.application)
            self.application.plugin_manager.load_plugins()
        return self.application.plugin_manager
    
    def get(self, action=None):
        self.authed()
        
        pm = self._get_plugin_manager()
        
        if action == 'list':
            self.write({'code': 0, 'data': pm.get_plugins_list()})
        elif action == 'info':
            plugin_id = self.get_argument('id', '')
            self.write(pm.get_plugin_info(plugin_id))
        elif action == 'config':
            plugin_id = self.get_argument('id', '')
            self.write(pm.get_plugin_config(plugin_id))
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})


    
    def post(self, action=None):
        self.authed()
        
        pm = self._get_plugin_manager()
        
        if action == 'install':
            url = self.get_argument('url', '')
            version = self.get_argument('version', None)
            self.write(pm.install_plugin(url, version))
        elif action == 'uninstall':
            plugin_id = self.get_argument('id', '')
            self.write(pm.uninstall_plugin(plugin_id))
        elif action == 'toggle':
            try:
                data = loads(self.request.body) if self.request.body else {}
                plugin_id = data.get('id', '')
                enable = data.get('enable', True)
            except:
                plugin_id = self.get_argument('id', '')
                enable = self.get_argument('enable', 'true').lower() == 'true'
            self.write(pm.toggle_plugin(plugin_id, enable))
        elif action == 'config':
            plugin_id = self.get_argument('id', '')
            config_data = {}
            for key in self.request.arguments:
                if key != 'id':
                    config_data[key] = self.get_argument(key, '')
            self.write(pm.save_plugin_config(plugin_id, config_data))
        else:
            self.write({'code': -1, 'msg': '未定义的操作！'})



