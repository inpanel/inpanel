#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

import os
import signal
import sys
import errno
import time
import shutil
import subprocess
from pathlib import Path

import logging
from tornado import httpserver, ioloop

from . import web
from .base import pidfile, logfile, logerror, config_file, config_path, logging_path, run_type, DEBUG, root_path, data_path
from .mod.process import remove_pid_file, save_pid_file, WebRequestProcess
from .mod.config import load_config
from .utils import make_cookie_secret


def _read_pid(pidfile):
    """从 pid 文件读取进程 ID，若文件不存在或内容无效则返回 None"""
    pidfile_path = Path(pidfile)
    if not pidfile_path.exists():
        return None
    try:
        with open(pidfile, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    except (ValueError, IOError):
        return None


def _is_running(pid):
    """检查指定 PID 的进程是否正在运行"""
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _wait_stop(pid, timeout=10):
    """等待进程停止，超时返回 False，成功停止返回 True"""
    for _ in range(timeout * 2):
        if not _is_running(pid):
            return True
        time.sleep(0.5)
    return False


def _print_help():
    print('''Usage: inpanel <command> [options]

Service Control:
  start     Start the InPanel service (background)
  stop      Stop the InPanel service
  status    Show the InPanel service status
  restart   Restart the InPanel service
  reload    Reload the InPanel service (restart)
  run       Run InPanel in foreground (for debug / systemd)

Configuration:
  config    Configuration management (use 'inpanel config' for help)

Package Management:
  uninstall [--purge] [--purge-config] [--purge-logs]
            Uninstall InPanel
            --purge       Remove all config and log files
            --purge-config Remove config files only
            --purge-logs   Remove log files only

Other:
  version   Show version information
  help      Show this help message

Examples:
  inpanel start
  inpanel stop
  inpanel status
  inpanel config list
  inpanel uninstall
  inpanel uninstall --purge
''')


def cmd_start():
    """以后台守护进程方式启动服务"""
    pid = _read_pid(pidfile)
    if pid and _is_running(pid):
        print(f'InPanel is already running with PID: {pid}')
        sys.exit(1)

    if pid and not _is_running(pid):
        remove_pid_file(pidfile)

    try:
        Path(logfile).parent.mkdir(parents=True, exist_ok=True)
        Path(logerror).parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print('[错误] 没有权限创建日志目录！')
        print(f'       需要创建目录: {Path(logfile).parent}')
        print('[提示] 请使用 sudo 或以 root 用户运行：')
        print('       sudo inpanel start')
        sys.exit(1)

    try:
        pid = os.fork()
        if pid > 0:
            time.sleep(1)
            child_pid = _read_pid(pidfile)
            if child_pid and _is_running(child_pid):
                print(f'InPanel: started with PID: {child_pid}')
                config = load_config(config_file)
                server_port = config.get('server', 'port')
                force_https = config.getboolean('server', 'forcehttps')
                print(f'InPanel: running on: http{"s" if force_https else ""}://*:{server_port}')
            else:
                print('InPanel: failed to start, check log file: %s' % logfile)
                sys.exit(1)
            return
    except OSError as e:
        print(f'InPanel: fork failed: {e}')
        sys.exit(1)

    # 子进程：脱离终端并运行服务器
    os.setsid()
    os.umask(0)

    # 重定向标准输入/输出/错误到日志文件
    sys.stdout.flush()
    sys.stderr.flush()
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(logfile, 'a') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(logerror, 'a') as f:
        os.dup2(f.fileno(), sys.stderr.fileno())

    run_server()


def cmd_stop():
    """停止服务"""
    pid = _read_pid(pidfile)
    if not pid:
        print('InPanel is not running (no pid file)')
        sys.exit(0)
    if not _is_running(pid):
        print('InPanel is not running (stale pid file)')
        remove_pid_file(pidfile)
        sys.exit(0)
    try:
        os.kill(pid, signal.SIGTERM)
        print(f'InPanel: stopping (PID: {pid})...')
        if _wait_stop(pid, 10):
            remove_pid_file(pidfile)
            print('InPanel: stopped')
        else:
            print('InPanel: stop timeout, trying force kill...')
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            remove_pid_file(pidfile)
            print('InPanel: force killed')
    except OSError as e:
        print(f'InPanel: stop failed: {e}')
        remove_pid_file(pidfile)
        sys.exit(1)


def cmd_status():
    """显示服务运行状态"""
    pid = _read_pid(pidfile)
    if not pid:
        print('InPanel: not running')
        sys.exit(1)
    if not _is_running(pid):
        print(f'InPanel: not running (removing stale pid file: {pid})')
        remove_pid_file(pidfile)
        sys.exit(1)
    config = load_config(config_file)
    server_port = config.get('server', 'port')
    force_https = config.getboolean('server', 'forcehttps')
    mode = config.get('runtime', 'mode')
    print(f'InPanel: running (PID: {pid})')
    print(f'InPanel: port: {server_port}, mode: {mode}, https: {force_https}')
    sys.exit(0)


def cmd_restart():
    """重启服务"""
    pid = _read_pid(pidfile)
    if pid and _is_running(pid):
        cmd_stop()
        time.sleep(1)
    cmd_start()


def cmd_reload():
    """重新加载服务（与重启相同）"""
    print('InPanel: reloading (restart)...')
    cmd_restart()


def cmd_uninstall(args=None):
    """卸载 InPanel"""
    if os.geteuid() != 0:
        print('Error: uninstall must be run as root.')
        sys.exit(1)

    purge_config = False
    purge_logs = False
    if args:
        for arg in args:
            if arg == '--purge-config' or arg == '--purge':
                purge_config = True
                purge_logs = True
            elif arg == '--purge-logs':
                purge_logs = True

    pid = _read_pid(pidfile)
    if pid and _is_running(pid):
        print('Stopping InPanel service...')
        try:
            os.kill(pid, signal.SIGTERM)
            if not _wait_stop(pid, 10):
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
        except OSError:
            pass
    remove_pid_file(pidfile)

    bin_path = '/usr/bin/inpanel'
    systemd_service = '/usr/lib/systemd/system/inpanel.service'
    systemd_service_etc = '/etc/systemd/system/inpanel.service'
    initd_script = '/etc/init.d/inpanel'

    print('Uninstalling InPanel...')

    # 移除 systemd 服务
    if os.path.exists(systemd_service):
        try:
            subprocess.run(['systemctl', 'stop', 'inpanel'], stderr=subprocess.DEVNULL)
            subprocess.run(['systemctl', 'disable', 'inpanel'], stderr=subprocess.DEVNULL)
        except Exception:
            pass
        os.remove(systemd_service)
        print(f'  removed: {systemd_service}')
    if os.path.exists(systemd_service_etc):
        os.remove(systemd_service_etc)
        print(f'  removed: {systemd_service_etc}')
    try:
        subprocess.run(['systemctl', 'daemon-reload'], stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 移除 init.d 脚本
    if os.path.exists(initd_script):
        try:
            subprocess.run(['chkconfig', '--del', 'inpanel'], stderr=subprocess.DEVNULL)
        except Exception:
            pass
        try:
            subprocess.run(['update-rc.d', '-f', 'inpanel', 'remove'], stderr=subprocess.DEVNULL)
        except Exception:
            pass
        os.remove(initd_script)
        print(f'  removed: {initd_script}')

    # 移除二进制文件 / 控制台脚本
    if os.path.exists(bin_path):
        os.remove(bin_path)
        print(f'  removed: {bin_path}')

    # 通过 pip 移除 Python 包
    if run_type == 'system':
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'inpanel'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print('  removed: inpanel python package')
        except Exception:
            # 尝试手动查找并删除
            pkg_path = Path(__file__).parent.resolve()
            if pkg_path.exists() and ('site-packages' in str(pkg_path) or 'dist-packages' in str(pkg_path)):
                egg_info = pkg_path.parent / 'inpanel.egg-info'
                if egg_info.exists():
                    shutil.rmtree(egg_info, ignore_errors=True)
                shutil.rmtree(pkg_path, ignore_errors=True)
                print(f'  removed: {pkg_path}')

    # 移除配置文件（可选）
    if purge_config and config_path and os.path.exists(config_path):
        shutil.rmtree(config_path, ignore_errors=True)
        print(f'  removed: {config_path} (config files)')

    # 移除日志文件（可选）
    if purge_logs and logging_path and os.path.exists(logging_path):
        shutil.rmtree(logging_path, ignore_errors=True)
        print(f'  removed: {logging_path} (log files)')

    pidfile_dir = os.path.dirname(pidfile)
    if os.path.exists(pidfile):
        os.remove(pidfile)

    print()
    print('InPanel uninstalled successfully.')
    if not purge_config:
        print(f'Config files are kept at: {config_path}')
        print(f'Use --purge to remove all data.')
    sys.exit(0)


def run_server():
    """以前台模式运行服务器"""
    try:
        Path(logfile).parent.mkdir(parents=True, exist_ok=True)
        Path(logerror).parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print('[错误] 没有权限创建日志目录！')
        print(f'       需要创建目录: {Path(logfile).parent}')
        print('[提示] 请使用 sudo 或以 root 用户运行：')
        print('       sudo inpanel start')
        sys.exit(1)

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
    logging.info(f'InPanel: pid file: {pidfile}')
    logging.info(f'InPanel: runtime type: {run_type}')
    logging.info(f'InPanel: runtime path: {root_path}')

    settings = {
        'debug'         : DEBUG,
        'autoreload'    : DEBUG,
        'cookie_secret' : 'debug' if DEBUG else make_cookie_secret(),
        'root_path'     : root_path,
        'data_path'     : data_path,
        'index_path'    : str(Path(root_path) / 'public' / 'templates' / 'index.html'),
        'template_path' : str(Path(root_path) / 'public' / 'templates'),
        'static_path'   : str(Path(root_path) / 'public'),
        'plugins_path'  : str(Path(data_path) / 'plugins'),
        'xsrf_cookies'  : True,
        'gzip'          : True
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
        (r'/api/sources/yum/(.+?)(?:/(.+))?', web.RepoYumHandler),
        (r'/api/sources/dnf/(.+?)(?:/(.+))?', web.RepoDnfHandler),
        (r'/api/sources/apt/(.+?)(?:/(.+))?', web.RepoAptHandler),
        (r'/api/sources/brew/(.+?)(?:/(.+))?', web.RepoBrewHandler),
        (r'/api/sources/pip/(.+?)(?:/(.+))?', web.RepoPipHandler),
        (r'/api/sources/docker/(.+?)(?:/(.+))?', web.RepoDockerHandler),
        (r'/api/sources/supported/?', web.RepoSupportedHandler),
        (r'/api/firewall/(.+)', web.FirewallHandler),
        (r'/api/setting/(.+)', web.SettingHandler),
        (r'/api/operation/(.+)', web.OperationHandler),
        (r'/api/backend/(.+)', web.BackendHandler),
        (r'/api/sitepackage/(.+)', web.SitePackageHandler),
        (r'/api/client/(.+)', web.ClientHandler),
        (r'/api/plugins', web.PluginHandler),
        (r'/api/plugins/(list|info|config|install|uninstall|toggle)', web.PluginHandler),
        (r'/api/file/download/(.+)', web.FileDownloadHandler, { 'path': '/' }),
        (r'/api/file/upload', web.FileUploadHandler),
        (r'/api/version', web.VersionHandler),
        (r'/page/plugins/(.*)', web.PluginStaticFileHandler, { 'path': settings['plugins_path']}),
        (r'/page/file/preview/(.+)', web.FilePreviewHandler),
        (r'/page/(.+)/(.+)', web.PageHandler),
        (r'/((?:css|js|js.min|lib|partials|images|favicon\.ico|robots\.txt)(?:\/.*)?)', web.StaticFileHandler, { 'path': settings['static_path'] }),
        (r'/', web.IndexHandler),
        (r'/($)', web.StaticFileHandler, { 'path': settings['index_path'] }),
        (r'/.*', web.ErrorHandler, { 'status_code': 404 })
    ]

    application = web.Application(router, **settings)

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

    server = httpserver.HTTPServer(application, ssl_options=ssl)
    try:
        server.listen(port=server_port, address=server_ip)
    except OSError as err:
        if err.errno in (errno.EADDRINUSE, 48):
            error_msg = f'端口 {server_port} 已被占用！'
            print(f'\n[错误] {error_msg}')
            print('[提示] 请先停止占用该端口的进程，或修改配置文件中的端口号。')
            print(f'[命令] lsof -i :{server_port}  # 查看占用进程')
            print('[命令] kill -9 <PID>  # 终止占用进程')
            logging.error(f'{error_msg} 请检查端口占用情况')
        elif err.errno in (errno.EACCES, 13):
            error_msg = f'没有权限绑定端口 {server_port}！'
            print(f'\n[错误] {error_msg}')
            print('[提示] 端口号小于 1024 需要 root 权限运行。')
            logging.error(f'{error_msg} 需要 root 权限')
        else:
            error_msg = f'绑定端口失败：{err}'
            print(f'\n[错误] {error_msg}')
            logging.error(error_msg)
        sys.exit(1)

    pid = os.getpid()
    save_pid_file(pidfile, pid)

    logging.info(f'InPanel: started with PID: {pid}')
    print(f'InPanel: started with PID: {pid}')

    logging.info(f'InPanel: running on: http{"s" if force_https else ""}://{server_ip}:{server_port}')
    print(f'InPanel: running on: http{"s" if force_https else ""}://{server_ip}:{server_port}')

    def shutdown_handler(signum, frame):
        logging.info('InPanel: shutting down')
        print()
        print('InPanel: shutting down')
        remove_pid_file(pidfile)
        logging.info(f"InPanel: PID file {pidfile} removed")
        ioloop.IOLoop.current().add_callback(ioloop.IOLoop.current().stop)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    ioloop.IOLoop.current().start()

    logging.info('InPanel: stopped')
    print('InPanel: stopped')
    sys.exit(0)


def main():
    # 将 'config' 子命令路由到 config 模块
    if len(sys.argv) > 1 and sys.argv[1] == 'config':
        from .config import main as config_main
        config_main(sys.argv[2:])
        return

    # 服务控制命令
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'start':
            cmd_start()
            return
        elif cmd == 'stop':
            cmd_stop()
            return
        elif cmd == 'status':
            cmd_status()
            return
        elif cmd == 'restart':
            cmd_restart()
            return
        elif cmd == 'reload':
            cmd_reload()
            return
        elif cmd == 'uninstall':
            cmd_uninstall(sys.argv[2:])
            return
        elif cmd == 'run':
            run_server()
            return
        elif cmd == 'version' or cmd == '-v' or cmd == '--version':
            from . import __version__
            print(f'InPanel v{__version__}')
            return
        elif cmd == 'help' or cmd == '-h' or cmd == '--help':
            _print_help()
            return
        else:
            print(f'Unknown command: {cmd}')
            print()
            _print_help()
            sys.exit(1)

    # 无参数：显示帮助信息
    _print_help()


if __name__ == '__main__':
    main()