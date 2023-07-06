#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, doudoudzj
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

import sys
from os import getpid
from os.path import dirname, join

root_path = dirname(__file__)
sys.path.insert(0, join(root_path, 'lib'))

import tornado.httpserver
import tornado.ioloop
from core import web
from core.modules.repo_yum import RepoYumHander
from core.modules.certificate import WebRequestSSLTLS
from core.modules.configuration import configurations
from core.modules.process import WebRequestProcess
from core.utils import make_cookie_secret


def write_pid():
    pidfile = '/var/run/inpanel.pid'
    pidfp = open(pidfile, 'w')
    pidfp.write(str(getpid()))
    pidfp.close()


def main():
    # settings of tornado application
    settings = {
        'root_path': root_path,
        'data_path': join(root_path, 'data'),
        'conf_path': join(root_path, 'data', 'config.ini'),
        'index_path': join(root_path, 'public', 'index.html'),
        'static_path': join(root_path, 'public'),
        'plugins_path': join(root_path, 'plugins'),
        'xsrf_cookies': True,
        'cookie_secret': make_cookie_secret(),
        'gzip': True
    }

    application = web.Application([
        (r'/api/xsrf', web.XsrfHandler),
        (r'/api/authstatus', web.AuthStatusHandler),
        (r'/api/login', web.LoginHandler),
        (r'/api/logout', web.LogoutHandler),
        (r'/api/query/(.+)', web.QueryHandler),
        (r'/api/network/(.+?)(?:/(.+))?', web.UtilsNetworkHandler),
        (r'/api/process/(.+?)(?:/(.+))?', WebRequestProcess),
        (r'/api/time/(.+?)(?:/(.+))?', web.UtilsTimeHandler),
        (r'/api/ssl/(.+?)(?:/(.+))?', WebRequestSSLTLS),
        (r'/api/repos/yum/(.+?)(?:/(.+))?', RepoYumHander),
        (r'/api/setting/(.+)', web.SettingHandler),
        (r'/api/operation/(.+)', web.OperationHandler),
        (r'/page/file/preview/(.+)', web.FilePreviewHandler),
        (r'/page/(.+)/(.+)', web.PageHandler),
        (r'/api/backend/(.+)', web.BackendHandler),
        (r'/api/sitepackage/(.+)', web.SitePackageHandler),
        (r'/api/client/(.+)', web.ClientHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)', web.StaticFileHandler, { 'path': settings['static_path'] }),
        (r'/api/plugins/(.*)', web.StaticFileHandler, { 'path': settings['plugins_path']}),
        (r'/api/file/download/(.+)', web.FileDownloadHandler, { 'path': '/' }),
        (r'/api/file/upload', web.FileUploadHandler),
        (r'/api/version', web.VersionHandler),
        # (r'/ws', WsockHandler, dict(loop=loop)),
        (r'/', web.IndexHandler, {'path': settings['index_path']}),
        (r'/($)', web.StaticFileHandler, { 'path': settings['index_path'] }),
        (r'/.*', web.ErrorHandler, { 'status_code': 404 })
    ], **settings)

    # read configuration from config.ini
    cfg = configurations(settings['conf_path'])
    server_ip = cfg.get('server', 'ip')
    server_port = cfg.get('server', 'port')
    force_https = cfg.getboolean('server', 'forcehttps')
    sslkey = cfg.get('server', 'sslkey')
    sslcrt = cfg.get('server', 'sslcrt')

    ssl = {'certfile': sslcrt,'keyfile': sslkey} if force_https else None
    server = tornado.httpserver.HTTPServer(application, ssl_options=ssl)
    server.listen(server_port, address=server_ip)
    write_pid()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
