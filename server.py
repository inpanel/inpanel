#!/usr/bin/env python2.6
#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

import os
import sys
root_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(root_path, 'lib'))

import ssl
import tornado.ioloop
import tornado.httpserver
import vpsmate.web
import vpsmate.config
from vpsmate.utils import make_cookie_secret


def write_pid():
    pidfile = '/var/run/vpsmate.pid'
    pidfp = open(pidfile, 'w')
    pidfp.write(str(os.getpid()))
    pidfp.close()

def main():
    # settings of tornado application
    settings = {
        'root_path': root_path,
        'data_path': os.path.join(root_path, 'data'),
        'static_path': os.path.join(root_path, 'static'),
        'xsrf_cookies': True,
        'cookie_secret': make_cookie_secret(),
    }
    
    application = vpsmate.web.Application([
        (r'/xsrf', vpsmate.web.XsrfHandler),
        (r'/authstatus', vpsmate.web.AuthStatusHandler),
        (r'/login', vpsmate.web.LoginHandler),
        (r'/logout', vpsmate.web.LogoutHandler),
        (r'/query/(.+)', vpsmate.web.QueryHandler),
        (r'/utils/network/(.+?)(?:/(.+))?', vpsmate.web.UtilsNetworkHandler),
        (r'/utils/time/(.+?)(?:/(.+))?', vpsmate.web.UtilsTimeHandler),
        (r'/setting/(.+)', vpsmate.web.SettingHandler),
        (r'/operation/(.+)', vpsmate.web.OperationHandler),
        (r'/page/(.+)/(.+)', vpsmate.web.PageHandler),
        (r'/backend/(.+)', vpsmate.web.BackendHandler),
        (r'/sitepackage/(.+)', vpsmate.web.SitePackageHandler),
        (r'/client/(.+)', vpsmate.web.ClientHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)',
            vpsmate.web.StaticFileHandler, {'path': settings['static_path']}),
        (r'/($)', vpsmate.web.StaticFileHandler,
            {'path': settings['static_path'] + '/index.html'}),
        (r'/file/(.+)', vpsmate.web.FileDownloadHandler, {'path': '/'}),
        (r'/fileupload', vpsmate.web.FileUploadHandler),
        (r'/version', vpsmate.web.VersionHandler),
        (r'/.*', vpsmate.web.ErrorHandler, {'status_code': 404}),
    ], **settings)

    # read configuration from config.ini
    cfg = vpsmate.config.Config(settings['data_path'] + '/config.ini')
    server_ip = cfg.get('server', 'ip')
    server_port = cfg.get('server', 'port')

    server = tornado.httpserver.HTTPServer(application)
    server.listen(server_port, address=server_ip)
    write_pid()
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()