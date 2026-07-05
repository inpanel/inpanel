# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Module for login handling'''

import time
from datetime import datetime
from hashlib import md5
import hmac


def handle_login(config, username, password):
    """Handle login request.
    
    Args:
        config: config object
        username: username from request
        password: password from request
    
    Returns:
        dict with 'code' and 'msg' keys
    """
    loginlock = config.get('runtime', 'loginlock')

    if config.get('runtime', 'mode') == 'demo':
        loginlock = 'off'

    # check if login is locked
    if loginlock == 'on':
        loginlockexpire = config.getint('runtime', 'loginlockexpire')
        if time.time() < loginlockexpire:
            return {
                'code': -1,
                'msg': '登录已被锁定，请在 %s 后重试登录。<br>'\
                    '如需立即解除锁定，请在服务器上执行以下命令：<br>'\
                    'inpanel config loginlock off' %
                    datetime.fromtimestamp(loginlockexpire)
                        .strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            config.set('runtime', 'loginlock', 'off')
            config.set('runtime', 'loginlockexpire', 0)

    loginfails = config.getint('runtime', 'loginfails')
    cfg_username = config.get('auth', 'username')
    cfg_password = config.get('auth', 'password')
    
    if not username:
        return {'code': -1, 'msg': '账号不能为空！'}
    elif not password:
        return {'code': -1, 'msg': '密码不能为空！'}
    elif cfg_password == '':
        return {
            'code': -1,
            'msg': '登录密码还未设置，请在服务器上执行以下命令进行设置：<br>inpanel config password \'您的密码\''
        }
    elif username != cfg_username:
        return {'code': -1, 'msg': '用户不存在！'}
    else:
        cfg_password, key = cfg_password.split(':')
        if hmac.new(key.encode('utf-8'), password.encode('utf-8'), md5).hexdigest() == cfg_password:
            if loginfails > 0:
                config.set('runtime', 'loginfails', 0)
            
            passwordcheck = config.getboolean('auth', 'passwordcheck')
            if passwordcheck:
                return {'code': 1, 'msg': '%s，您已登录成功！' % username}
            else:
                return {'code': 0, 'msg': '%s，您已登录成功！' % username}
        else:
            if config.get('runtime', 'mode') == 'demo':
                return {'code': -1, 'msg': '用户名或密码错误！'}
            
            loginfails = loginfails + 1
            config.set('runtime', 'loginfails', loginfails)
            if loginfails >= 5:
                # lock 24 hours
                config.set('runtime', 'loginlock', 'on')
                config.set('runtime', 'loginlockexpire', int(time.time()) + 86400)
                return {'code': -1, 'msg': '用户名或密码错误！<br>'\
                    '已连续错误 5 次，登录已被禁止！'}
            else:
                return {'code': -1, 'msg': '用户名或密码错误！<br>'\
                    '连续错误 5 次后将被禁止登录，还有 %d 次机会。' % (5 - loginfails)}


def handle_logout():
    """Handle logout request.
    
    Returns:
        None (logout is handled by clearing cookie)
    """
    pass
