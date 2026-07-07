# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Module for Settings Management."""

import time
from hashlib import md5
from hmac import new as hmac_new
from base64 import b64decode
from pathlib import Path

import tornado.httpclient
import tornado.escape
from ..base import app_api
from .. import utils
from .config import upgrade_config
from . import server


async def handle_get(context, section):
    """Handle GET requests for settings."""
    if section == 'auth':
        username = context.config.get('auth', 'username')
        passwordcheck = context.config.getboolean('auth', 'passwordcheck')
        context.write({'username': username, 'passwordcheck': passwordcheck})
        context.finish()

    elif section == 'runtime':
        mode = context.config.get('runtime', 'mode')
        loginlockexpire = context.config.getint('runtime', 'loginlockexpire')
        loginfails = context.config.getint('runtime', 'loginfails')
        loginlock = context.config.getboolean('runtime', 'loginlock')
        if not mode:
            mode = 'prod'
            context.config.set('runtime', 'mode', 'prod')
        context.write({
            'mode': mode,
            'loginlockexpire': loginlockexpire,
            'loginfails': loginfails,
            'loginlock': loginlock
        })
        context.finish()

    elif section == 'server':
        ip = context.config.get('server', 'ip')
        port = context.config.get('server', 'port')
        forcehttps = context.config.getboolean('server', 'forcehttps')
        sslkey = context.config.get('server', 'sslkey')
        sslcrt = context.config.get('server', 'sslcrt')
        context.write({'forcehttps': forcehttps, 'ip': ip, 'port': port, 'sslkey': sslkey, 'sslcrt': sslcrt})
        context.finish()

    elif section == 'accesskey':
        accesskey = context.config.get('auth', 'accesskey')
        accesskeyenable = context.config.getboolean('auth', 'accesskeyenable')
        context.write({'accesskey': accesskey, 'accesskeyenable': accesskeyenable})
        context.finish()

    elif section == 'upver':
        force = context.get_argument('force', '')
        update_info = upgrade_config()
        lastcheck = update_info.get('update', 'lastcheck')
        lastcheck = 0 if lastcheck == '' else int(lastcheck)

        # detect new version daily
        if force or time.time() > lastcheck + 86400:
            http_client = tornado.httpclient.AsyncHTTPClient()
            try:
                response = await http_client.fetch(app_api['latest'])
                if response.error:
                    context.write({'code': -1, 'msg': '获取新版本信息失败！'})
                else:
                    data = response.body.decode('utf-8')
                    if not data:
                        context.write({'code': -1, 'msg': '获取新版本信息失败！'})
                    else:
                        update_info.set('update', 'lastcheck', int(time.time()))
                        update_info.set('update', 'updateinfo', data)
                        try:
                            data = tornado.escape.json_decode(data)
                            context.write({'code': 0, 'msg':'', 'data': data})
                        except:
                            context.write({'code': -1, 'msg': '获取新版本信息失败！'})
            except:
                context.write({'code': -1, 'msg': '获取新版本信息失败！'})
        else:
            data = update_info.get('update', 'updateinfo')
            try:
                data = tornado.escape.json_decode(data)
            except:
                data = None

            context.write({'code': 0, 'msg': '', 'data': data})

        context.finish()


def handle_post(context, section):
    """Handle POST requests for settings."""
    if section == 'auth':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许修改用户名和密码！'})
            return

        username = context.get_argument('username', '')
        password = context.get_argument('password', '')
        passwordc = context.get_argument('passwordc', '')
        passwordcheck = context.get_argument('passwordcheck', '')

        if username == '':
            context.write({'code': -1, 'msg': '用户名不能为空！'})
            return
        if password != passwordc:
            context.write({'code': -1, 'msg': '两次密码输入不一致！'})
            return

        if passwordcheck != 'on':
            passwordcheck = 'off'
        context.config.set('auth', 'passwordcheck', passwordcheck)

        if username != '':
            context.config.set('auth', 'username', username)
        if password != '':
            key = md5(utils.randstr().encode('utf-8')).hexdigest()
            pwd = hmac_new(key.encode('utf-8'), password.encode('utf-8'), md5).hexdigest()
            context.config.set('auth', 'password', '%s:%s' % (pwd, key))

        context.write({'code': 0, 'msg': '账号设置更新成功！'})

    elif section == 'server':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许修改服务绑定地址！'})
            return

        ip = context.get_argument('ip', '*')
        if ip != '*' and ip != '':
            if not utils.is_valid_ip(ip):
                context.write({'code': -1, 'msg': '%s 不是有效的IP地址！' % ip})
                return
            netifaces = server.ServerInfo.netifaces()
            ips = [netiface['ip'] for netiface in netifaces]
            if not ip in ips:
                msg = '<p>%s 不是该服务器的IP地址！</p><p>可用的IP地址有：<br>%s</p>' % (ip, '<br>'.join(ips))
                context.write({'code': -1, 'msg': msg})
                return

        port = context.get_argument('port', '14433')
        port = int(port)
        if not port > 5000 and port < 65535:
            context.write({'code': -1, 'msg': '端口范围必须在 5000 到 65535 之间！'})
            return

        context.config.set('server', 'ip', ip)
        context.config.set('server', 'port', port)

        sslkey = context.get_argument('sslkey', '')
        if sslkey == '' or Path(sslkey).is_file():
            context.config.set('server', 'sslkey', sslkey)
        else:
            context.write({'code': -1, 'msg': 'SSL私钥文件不存在，请仔细检查！'})
            return

        sslcrt = context.get_argument('sslcrt', '')
        if sslcrt == '' or Path(sslcrt).is_file():
            context.config.set('server', 'sslcrt', sslcrt)
        else:
            context.write({'code': -1, 'msg': 'SSL证书文件不存在，请仔细检查！'})
            return

        forcehttps = context.get_argument('forcehttps', '')
        if forcehttps == 'on':
            if not sslkey or not Path(sslkey).is_file():
                context.config.set('server', 'forcehttps', 'off')
                context.write({'code': -1, 'msg': '请填写SSL私钥文件！'})
                return
            elif not sslcrt or not Path(sslcrt).is_file():
                context.config.set('server', 'forcehttps', 'off')
                context.write({'code': -1, 'msg': '请填写SSL证书文件！'})
                return
            context.config.set('server', 'forcehttps', forcehttps)
        else:
            context.config.set('server', 'forcehttps', 'off')

        context.write({'code': 0, 'msg': '服务设置更新成功！将在重启服务后生效。'})

    elif section == 'runtime':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许修改到其他模式！'})
            return

        mode = context.get_argument('mode', 'prod')
        if mode not in ('prod', 'demo'):
            mode = 'prod'
        context.config.set('runtime', 'mode', mode)

        context.write({'code': 0, 'msg': '运行设置更新成功！'})

    elif section == 'accesskey':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许修改远程控制设置！'})
            return

        accesskey = context.get_argument('accesskey', '')
        accesskeyenable = context.get_argument('accesskeyenable', '')

        if accesskeyenable == 'on' and accesskey == '':
            context.write({'code': -1, 'msg': '远程控制密钥不能为空！'})
            return

        if accesskey != '':
            try:
                if len(b64decode(accesskey)) != 32:
                    raise Exception()
            except:
                context.write({'code': -1, 'msg': '远程控制密钥格式不正确！'})
                return

        if accesskeyenable != 'on':
            accesskeyenable = 'off'
        context.config.set('auth', 'accesskeyenable', accesskeyenable)
        context.config.set('auth', 'accesskey', accesskey)

        context.write({'code': 0, 'msg': '远程控制设置更新成功！'})