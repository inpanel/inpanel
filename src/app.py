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
from os.path import abspath, dirname, join

from tornado import httpserver, ioloop

import mod_web
from base import config_path, pidfile
# from repo_yum import WebRequestRepoYUM
from certificate import WebRequestSSLTLS
from configuration import configurations
from process import WebRequestProcess, save_pidfile
from utils import make_cookie_secret

print('InPanel: starting')
print('InPanel: config file is %s' % config_path)

root_path = dirname(__file__)
root_path = abspath(dirname(dirname(__file__)))
print('root_path2', root_path)

if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    # runtime_tmpdir
    root_path = sys._MEIPASS

print('InPanel: runtime root path is %s' % root_path)

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
    (r'/api/xsrf', mod_web.XsrfHandler),
    (r'/api/authstatus', mod_web.AuthStatusHandler),
    (r'/api/login', mod_web.LoginHandler),
    (r'/api/logout', mod_web.LogoutHandler),
    (r'/api/query/(.+)', mod_web.QueryHandler),
    (r'/api/utils/network/(.+?)(?:/(.+))?', mod_web.UtilsNetworkHandler),
    (r'/api/utils/process/(.+?)(?:/(.+))?', WebRequestProcess),
    (r'/api/utils/time/(.+?)(?:/(.+))?', mod_web.UtilsTimeHandler),
    (r'/api/utils/ssl/(.+?)(?:/(.+))?', WebRequestSSLTLS),
    (r'/api/repos/yum/(.+?)(?:/(.+))?', mod_web.RepoYumHander),
    (r'/api/setting/(.+)', mod_web.SettingHandler),
    (r'/api/operation/(.+)', mod_web.OperationHandler),
    (r'/page/(.+)/(.+)', mod_web.PageHandler),
    (r'/api/backend/(.+)', mod_web.BackendHandler),
    (r'/api/sitepackage/(.+)', mod_web.SitePackageHandler),
    (r'/api/client/(.+)', mod_web.ClientHandler),
    (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)', mod_web.StaticFileHandler, { 'path': settings['static_path'] }),
    (r'/api/plugins/(.*)', mod_web.StaticFileHandler, { 'path': settings['plugins_path']}),
    (r'/api/download/(.+)', mod_web.FileDownloadHandler, { 'path': '/' }),
    (r'/api/fileupload', mod_web.FileUploadHandler),
    (r'/api/version', mod_web.VersionHandler),
    (r'/', mod_web.IndexHandler),
    (r'/($)', mod_web.StaticFileHandler, { 'path': settings['index_path'] }),
    (r'/.*', mod_web.ErrorHandler, { 'status_code': 404 })
]

application = mod_web.Application(router, **settings)

# read configuration from config.ini
cfg = configurations(settings['conf_path'])
server_ip = cfg.get('server', 'ip')
server_port = cfg.get('server', 'port')
force_https = cfg.getboolean('server', 'forcehttps')
sslkey = cfg.get('server', 'sslkey')
sslcrt = cfg.get('server', 'sslcrt')

ssl = {'certfile': sslcrt, 'keyfile': sslkey} if force_https else None

def main():

    server = httpserver.HTTPServer(application, ssl_options=ssl)
    server.listen(port=server_port, address=server_ip)

    save_pidfile(pidfile, getpid())
    print('InPanel: service running on http%s://%s:%s' % ('s' if force_https else '', server_ip, server_port))
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
    # server.stop()
