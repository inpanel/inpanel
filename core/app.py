#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

import sys
from os import getpid
from os.path import abspath, dirname, join

import mod_web
from base import config_path, debug, pidfile
# from mod_yum import WebRequestRepoYUM
from certificate import WebRequestSSLTLS
from configuration import main_config
from mod_process import WebRequestProcess, save_pidfile
from tornado import httpserver, ioloop
from utils import make_cookie_secret

print('InPanel: starting')
print('InPanel: config file : %s' % config_path)
print('InPanel: pid file    : %s' % pidfile)

root_path = dirname(__file__)
root_path = abspath(dirname(dirname(__file__)))
run_type = 'source'

if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    # runtime_tmpdir
    run_type = 'binary'
    root_path = sys._MEIPASS

# print('InPanel: root path: %s' % root_path)
print('InPanel: runtime type: %s' % run_type)
print('InPanel: runtime path: %s' % root_path)

# settings of tornado application
settings = {
    'debug': debug,
    'autoreload': debug,
    'cookie_secret': 'debug' if debug else make_cookie_secret(),
    'root_path': root_path,
    'data_path': join(root_path, 'data'),
    'index_path': join(root_path, 'templates', 'index.html'),
    'template_path': join(root_path, 'templates'),
    'static_path': join(root_path, 'public'),
    'plugins_path': join(root_path, 'plugins'),
    'xsrf_cookies': True,
    'gzip': True # or use 'compress_response': True
}

router = [
    (r'/api/xsrf', mod_web.XsrfHandler),
    (r'/api/authstatus', mod_web.AuthStatusHandler),
    (r'/api/login', mod_web.LoginHandler),
    (r'/api/logout', mod_web.LogoutHandler),
    (r'/api/query/(.+)', mod_web.QueryHandler),
    (r'/api/network/(.+?)(?:/(.+))?', mod_web.UtilsNetworkHandler),
    (r'/api/process/(.+?)(?:/(.+))?', WebRequestProcess),
    (r'/api/time/(.+?)(?:/(.+))?', mod_web.UtilsTimeHandler),
    (r'/api/ssl/(.+?)(?:/(.+))?', WebRequestSSLTLS),
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
config = main_config(config_path)
mode   = config.get('runtime', 'mode')

print('InPanel: runtime mode: %s' % mode)

server_ip   = config.get('server', 'ip')
server_port = config.get('server', 'port')
force_https = config.getboolean('server', 'forcehttps')
sslkey      = config.get('server', 'sslkey')
sslcrt      = config.get('server', 'sslcrt')

ssl = {'certfile': sslcrt, 'keyfile': sslkey} if force_https else None

def main():
    # from tornado import options
    # options.parse_command_line()
    # options.logging = None

    server = httpserver.HTTPServer(application, ssl_options=ssl)
    server.listen(port=server_port, address=server_ip)

    pid = getpid()

    save_pidfile(pidfile, pid)
    print('InPanel: running pid : %s' % pid)
    print('InPanel: running on  : http%s://%s:%s' % ('s' if force_https else '', server_ip, server_port))
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
