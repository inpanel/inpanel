#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

import sys
from os import getpid
from os.path import dirname, join, abspath

# root_path = dirname(__file__)
root_path = abspath(dirname(dirname(__file__)))

from tornado import httpserver
from tornado import ioloop

import web
# from repo_yum import WebRequestRepoYUM
from certificate import WebRequestSSLTLS
from configuration import configurations
from process import WebRequestProcess
from utils import make_cookie_secret
from __init__ import config_path


def write_pid():
    pidfile = '/var/run/inpanel.pid'
    pidfp = open(pidfile, 'w')
    pidfp.write(str(getpid()))
    pidfp.close()

def main():
    # settings of tornado application
    settings = {
        'debug': False,
        'root_path': root_path,
        'data_path': join(root_path, 'data'),
        # 'conf_path': join(root_path, 'data', 'config.ini'),
        'conf_path': config_path,
        'index_path': join(root_path, 'static', 'index.html'),
        'template_path': join(root_path, 'templates'),
        'static_path': join(root_path, 'static'),
        'plugins_path': join(root_path, 'plugins'),
        'xsrf_cookies': True,
        'cookie_secret': make_cookie_secret(),
        'gzip': True
    }

    router = [
        (r'/api/xsrf', web.XsrfHandler),
        (r'/api/authstatus', web.AuthStatusHandler),
        (r'/api/login', web.LoginHandler),
        (r'/api/logout', web.LogoutHandler),
        (r'/api/query/(.+)', web.QueryHandler),
        (r'/api/utils/network/(.+?)(?:/(.+))?', web.UtilsNetworkHandler),
        (r'/api/utils/process/(.+?)(?:/(.+))?', WebRequestProcess),
        (r'/api/utils/time/(.+?)(?:/(.+))?', web.UtilsTimeHandler),
        (r'/api/utils/ssl/(.+?)(?:/(.+))?', WebRequestSSLTLS),
        (r'/api/repos/yum/(.+?)(?:/(.+))?', web.RepoYumHander),
        (r'/api/setting/(.+)', web.SettingHandler),
        (r'/api/operation/(.+)', web.OperationHandler),
        (r'/page/(.+)/(.+)', web.PageHandler),
        (r'/api/backend/(.+)', web.BackendHandler),
        (r'/api/sitepackage/(.+)', web.SitePackageHandler),
        (r'/api/client/(.+)', web.ClientHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)',
         web.StaticFileHandler, {'path': settings['static_path']}),
        (r'/api/plugins/(.*)', web.StaticFileHandler, {'path': settings['plugins_path']}),
        (r'/api/download/(.+)', web.FileDownloadHandler, {'path': '/'}),
        (r'/api/fileupload', web.FileUploadHandler),
        (r'/api/version', web.VersionHandler),
        (r'/', web.IndexHandler),
        (r'/($)', web.StaticFileHandler, {'path': settings['index_path']}),
        (r'/.*', web.ErrorHandler, {'status_code': 404})
    ]

    application = web.Application(router, **settings)

    # read configuration from config.ini
    cfg = configurations(settings['conf_path'])
    server_ip = cfg.get('server', 'ip')
    server_port = cfg.get('server', 'port')
    force_https = cfg.getboolean('server', 'forcehttps')
    sslkey = cfg.get('server', 'sslkey')
    sslcrt = cfg.get('server', 'sslcrt')

    ssl = {'certfile': sslcrt,'keyfile': sslkey} if force_https else None
    server = httpserver.HTTPServer(application, ssl_options=ssl)
    server.listen(port=server_port, address=server_ip)
    write_pid()
    print('InPanel running on http%s://%s:%s' % ('s' if force_https else '', server_ip, server_port))
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
