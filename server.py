#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012 - 2016, VPSMate development team
# All rights reserved.
#
# Intranet is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

import os
import sys
import subprocess
import shlex

root_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(root_path, 'lib'))

import ssl
import tornado.ioloop
import tornado.httpserver
import intranet.web
import intranet.config
from module.utils import make_cookie_secret


def write_pid():
    pidfile = '/var/run/intranet.pid'
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

    application = intranet.web.Application([
        (r'/xsrf', intranet.web.XsrfHandler),
        (r'/authstatus', intranet.web.AuthStatusHandler),
        (r'/login', intranet.web.LoginHandler),
        (r'/logout', intranet.web.LogoutHandler),
        (r'/query/(.+)', intranet.web.QueryHandler),
        (r'/utils/network/(.+?)(?:/(.+))?', intranet.web.UtilsNetworkHandler),
        (r'/utils/process/(.+?)(?:/(.+))?', intranet.web.UtilsProcessHandler),
        (r'/utils/time/(.+?)(?:/(.+))?', intranet.web.UtilsTimeHandler),
        (r'/utils/ssl/(.+?)(?:/(.+))?', intranet.web.UtilsSSLHandler),
        (r'/setting/(.+)', intranet.web.SettingHandler),
        (r'/operation/(.+)', intranet.web.OperationHandler),
        (r'/page/(.+)/(.+)', intranet.web.PageHandler),
        (r'/backend/(.+)', intranet.web.BackendHandler),
        (r'/sitepackage/(.+)', intranet.web.SitePackageHandler),
        (r'/client/(.+)', intranet.web.ClientHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)', intranet.web.StaticFileHandler, {'path': settings['static_path']}),
        (r'/($)', intranet.web.StaticFileHandler, {'path': settings['index_path']}),
        (r'/file/(.+)', intranet.web.FileDownloadHandler, {'path': '/'}),
        (r'/fileupload', intranet.web.FileUploadHandler),
        (r'/version', intranet.web.VersionHandler),
        (r'/.*', intranet.web.ErrorHandler, {'status_code': 404}),
    ], **settings)

    # read configuration from config.ini
    cfg = intranet.config.Config(settings['conf_path'])
    server_ip = cfg.get('server', 'ip')
    server_port = cfg.get('server', 'port')

    server = tornado.httpserver.HTTPServer(application)
    server.listen(server_port, address=server_ip)
    write_pid()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
