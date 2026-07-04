#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

import os
import signal
import sys
import errno
from pathlib import Path

import logging
import web
from base import DEBUG, PIDFILE, logfile, logerror, config_file, config_path, root_path, run_type
from mod.config import load_config
from mod.process import WebRequestProcess, save_pid_file, remove_pid_file
from tornado import httpserver, ioloop
from utils import make_cookie_secret

logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

error_handler = logging.FileHandler(logerror)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
logging.getLogger().addHandler(error_handler)

print('InPanel: starting')
logging.info('InPanel: starting')
logging.info(f'InPanel: config file: {config_file}')
logging.info(f'InPanel: pid file: {PIDFILE}')

logging.info(f'InPanel: runtime type: {run_type}')
logging.info(f'InPanel: runtime path: {root_path}')

# settings of tornado application
settings = {
    'debug'         : DEBUG,
    'autoreload'    : DEBUG,
    'cookie_secret' : 'debug' if DEBUG else make_cookie_secret(),
    'root_path'     : root_path,
    'data_path'     : config_path,
    'index_path'    : str(Path(root_path) / 'templates' / 'index.html'),
    'template_path' : str(Path(root_path) / 'templates'),
    'static_path'   : str(Path(root_path) / 'public'),
    'plugins_path'  : str(Path(root_path) / 'plugins'),
    'xsrf_cookies'  : True,
    'gzip'          : True # or use 'compress_response': True
}

router = [
    (r'/api/xsrf', web.XsrfHandler),
    (r'/api/authstatus', web.AuthStatusHandler),
    (r'/api/login', web.LoginHandler),
    (r'/api/logout', web.LogoutHandler),
    (r'/api/query/(.+)', web.QueryHandler),
    (r'/api/network/(.+?)(?:/(.+))?', web.UtilsNetworkHandler),
    (r'/api/process/(.+?)(?:/(.+))?', WebRequestProcess),
    (r'/api/time/(.+?)(?:/(.+))?', web.UtilsTimeHandler),
    (r'/api/ssl/(.+?)(?:/(.+))?', web.SSLTLSHandler),
    (r'/api/repos/yum/(.+?)(?:/(.+))?', web.RepoYumHandler),
    (r'/api/repos/dnf/(.+?)(?:/(.+))?', web.RepoDnfHandler),
    (r'/api/repos/apt/(.+?)(?:/(.+))?', web.RepoAptHandler),
    (r'/api/firewall/(.+)', web.FirewallHandler),
    (r'/api/setting/(.+)', web.SettingHandler),
    (r'/api/operation/(.+)', web.OperationHandler),
    (r'/page/file/preview/(.+)', web.FilePreviewHandler),
    (r'/page/(.+)/(.+)', web.PageHandler),
    (r'/api/backend/(.+)', web.BackendHandler),
    (r'/api/sitepackage/(.+)', web.SitePackageHandler),
    (r'/api/client/(.+)', web.ClientHandler),
    (r'/api/plugins/(.*)', web.StaticFileHandler, { 'path': settings['plugins_path']}),
    (r'/api/file/download/(.+)', web.FileDownloadHandler, { 'path': '/' }),
    (r'/api/file/upload', web.FileUploadHandler),
    (r'/api/version', web.VersionHandler),
    (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)', web.StaticFileHandler, { 'path': settings['static_path'] }),
    # (r'/ws', WsockHandler, dict(loop=loop)),
    (r'/', web.IndexHandler),
    (r'/($)', web.StaticFileHandler, { 'path': settings['index_path'] }),
    (r'/.*', web.ErrorHandler, { 'status_code': 404 })
]

application = web.Application(router, **settings)

# read configuration from config.ini
config = load_config(config_file)
mode   = config.get('runtime', 'mode')

logging.info(f'InPanel: runtime mode: {mode}')
print(f'InPanel: runtime mode: {mode}')

server_ip   = config.get('server', 'ip')
server_port = config.get('server', 'port')
if server_ip == '*':
    server_ip = ''
force_https = config.getboolean('server', 'forcehttps')
sslkey      = config.get('server', 'sslkey')
sslcrt      = config.get('server', 'sslcrt')

ssl = {'certfile': sslcrt, 'keyfile': sslkey} if force_https else None

def main():
    # from tornado import options
    # options.parse_command_line()
    # options.logging = None

    server = httpserver.HTTPServer(application, ssl_options=ssl)
    try:
        server.listen(port=server_port, address=server_ip)
    except OSError as err:
        if err.errno in (errno.EADDRINUSE, 48):
            error_msg = f'端口 {server_port} 已被占用！'
            print(f'\n[错误] {error_msg}')
            print(f'[提示] 请先停止占用该端口的进程，或修改配置文件中的端口号。')
            print(f'[命令] lsof -i :{server_port}  # 查看占用进程')
            print(f'[命令] kill -9 <PID>  # 终止占用进程')
            logging.error(f'{error_msg} 请检查端口占用情况')
        elif err.errno in (errno.EACCES, 13):
            error_msg = f'没有权限绑定端口 {server_port}！'
            print(f'\n[错误] {error_msg}')
            print(f'[提示] 端口号小于 1024 需要 root 权限运行。')
            print(f'[命令] sudo python3.11 core/app.py')
            logging.error(f'{error_msg} 需要 root 权限')
        else:
            error_msg = f'绑定端口失败：{err}'
            print(f'\n[错误] {error_msg}')
            logging.error(error_msg)
        sys.exit(1)

    pid = os.getpid()
    if run_type == 'source':
        save_pid_file(PIDFILE, pid)

    logging.info(f'InPanel: started with PID: {pid}')
    print(f'InPanel: started with PID: {pid}')

    logging.info(f'InPanel: running on: http{"s" if force_https else ""}://{server_ip}:{server_port}')
    print(f'InPanel: running on: http{"s" if force_https else ""}://{server_ip}:{server_port}')

    def shutdown_handler(signum, frame):
        logging.info('InPanel: shutting down')
        print()
        print('InPanel: shutting down')
        if run_type == 'source':
            remove_pid_file(PIDFILE)
            logging.info(f"InPanel: PID file {PIDFILE} removed")
        ioloop.IOLoop.current().add_callback(ioloop.IOLoop.current().stop)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    ioloop.IOLoop.current().start()
    
    logging.info('InPanel: stopped')
    print('InPanel: stopped')
    sys.exit(0)


if __name__ == '__main__':
    main()
