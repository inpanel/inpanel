#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012 - 2016, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

import os
import shlex
import subprocess
import sys


root_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(root_path, 'lib'))

import tornado.httpserver
import tornado.ioloop
from core import web
from modules.config import Config
from modules.utils import make_cookie_secret


def write_pid():
    pidfile = '/var/run/inpanel.pid'
    pidfp = open(pidfile, 'w')
    pidfp.write(str(os.getpid()))
    pidfp.close()


def main():
    # settings of tornado application
    settings = {
        'root_path': root_path,
        'data_path': os.path.join(root_path, 'data'),
        'conf_path': os.path.join(root_path, 'data', 'config.ini'),
        'index_path': os.path.join(root_path, 'static', 'index.html'),
        'static_path': os.path.join(root_path, 'static'),
        'xsrf_cookies': True,
        'cookie_secret': make_cookie_secret(),
    }

    application = web.Application([
        (r'/xsrf', web.XsrfHandler),
        (r'/authstatus', web.AuthStatusHandler),
        (r'/login', web.LoginHandler),
        (r'/logout', web.LogoutHandler),
        (r'/query/(.+)', web.QueryHandler),
        (r'/utils/network/(.+?)(?:/(.+))?', web.UtilsNetworkHandler),
        (r'/utils/process/(.+?)(?:/(.+))?', web.UtilsProcessHandler),
        (r'/utils/time/(.+?)(?:/(.+))?', web.UtilsTimeHandler),
        (r'/utils/ssl/(.+?)(?:/(.+))?', web.UtilsSSLHandler),
        (r'/setting/(.+)', web.SettingHandler),
        (r'/operation/(.+)', web.OperationHandler),
        (r'/page/(.+)/(.+)', web.PageHandler),
        (r'/backend/(.+)', web.BackendHandler),
        (r'/sitepackage/(.+)', web.SitePackageHandler),
        (r'/client/(.+)', web.ClientHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)',
         web.StaticFileHandler, {'path': settings['static_path']}),
        (r'/($)', web.StaticFileHandler, {'path': settings['index_path']}),
        (r'/file/(.+)', web.FileDownloadHandler, {'path': '/'}),
        (r'/fileupload', web.FileUploadHandler),
        (r'/version', web.VersionHandler),
        (r'/.*', web.ErrorHandler, {'status_code': 404}),
    ], **settings)

    # read configuration from config.ini
    cfg = Config(settings['conf_path'])
    server_ip = cfg.get('server', 'ip')
    server_port = cfg.get('server', 'port')

    server = tornado.httpserver.HTTPServer(application)
    server.listen(server_port, address=server_ip)
    write_pid()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
