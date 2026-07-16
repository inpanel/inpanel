# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the New BSD License.
# The full license can be found in 'LICENSE'.

"""Docker 容器管理模块"""

import json
from subprocess import getstatusoutput

from ..base import kernel_name


def _run_docker(args):
    """执行 docker 命令并返回 (status, output)

    Args:
        args: docker 命令参数字符串，如 'ps -a'

    Returns:
        tuple: (status_code, output_string)
    """
    if kernel_name not in ('Linux', 'Darwin'):
        return (1, '当前系统不支持 Docker')
    cmd = f'docker {args}'
    return getstatusoutput(cmd)


def _run_docker_json(args):
    """执行 docker 命令并解析 JSON 输出

    Args:
        args: docker 命令参数字符串（需包含 --format {{json .}} 等）

    Returns:
        tuple: (status_code, list_or_msg)
    """
    status, output = _run_docker(args)
    if status != 0:
        return (status, output)
    if not output or not output.strip():
        return (0, [])
    lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
    result = []
    for line in lines:
        try:
            result.append(json.loads(line))
        except (ValueError, json.JSONDecodeError):
            continue
    return (0, result)


def is_installed():
    """检查 Docker 是否已安装"""
    status, _ = getstatusoutput('which docker')
    return status == 0


def get_version():
    """获取 Docker 版本信息"""
    status, output = _run_docker('-v')
    if status != 0:
        return None
    # Docker version 20.10.7, build f0df350
    return output.strip()


def get_version_info():
    """获取 Docker 详细版本信息（JSON）"""
    status, output = _run_docker('version --format "{{json .}}"')
    if status != 0:
        return None
    try:
        return json.loads(output.strip())
    except (ValueError, json.JSONDecodeError):
        return None


def get_info():
    """获取 Docker 系统信息"""
    status, output = _run_docker('info --format "{{json .}}"')
    if status != 0:
        return None
    try:
        return json.loads(output.strip())
    except (ValueError, json.JSONDecodeError):
        return None


def get_status():
    """获取 Docker 服务运行状态

    Returns:
        bool: True 表示运行中，False 表示未运行
    """
    status, _ = _run_docker('info')
    return status == 0


def service_control(action):
    """控制 Docker 服务（启动/停止/重启）

    Args:
        action: 'start' | 'stop' | 'restart'

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    if kernel_name == 'Darwin':
        # macOS 上 Docker Desktop 需要通过应用启动
        if action == 'start':
            status, output = getstatusoutput('open -a Docker')
        elif action == 'stop':
            status, output = getstatusoutput('osascript -e \'quit app "Docker"\'')
        else:
            status, output = getstatusoutput('osascript -e \'quit app "Docker"\'; sleep 2; open -a Docker')
    else:
        status, output = getstatusoutput(f'systemctl {action} docker')

    action_msg = {'start': '启动', 'stop': '停止', 'restart': '重启'}
    if status == 0:
        return {'code': 0, 'msg': f'Docker 服务已{action_msg.get(action, action)}'}
    else:
        return {'code': -1, 'msg': f'Docker 服务{action_msg.get(action, action)}失败：{output}'}


def get_overview():
    """获取 Docker 概览信息

    Returns:
        dict: 包含版本、状态、容器数、镜像数等
    """
    overview = {
        'installed': is_installed(),
        'version': None,
        'running': False,
        'containers': 0,
        'running_containers': 0,
        'images': 0,
        'networks': 0,
        'volumes': 0,
    }

    if not overview['installed']:
        return overview

    overview['version'] = get_version()
    overview['running'] = get_status()

    if not overview['running']:
        return overview

    # 获取容器统计
    status, containers = _run_docker('ps -a --format "{{.Status}}"')
    if status == 0 and containers:
        lines = [line.strip() for line in containers.strip().split('\n') if line.strip()]
        overview['containers'] = len(lines)
        overview['running_containers'] = sum(1 for l in lines if l.startswith('Up'))

    # 获取镜像数
    status, images = _run_docker('images -q')
    if status == 0 and images:
        overview['images'] = len([l for l in images.strip().split('\n') if l.strip()])

    # 获取网络数
    status, networks = _run_docker('network ls -q')
    if status == 0 and networks:
        overview['networks'] = len([l for l in networks.strip().split('\n') if l.strip()])

    # 获取数据卷数
    status, volumes = _run_docker('volume ls -q')
    if status == 0 and volumes:
        overview['volumes'] = len([l for l in volumes.strip().split('\n') if l.strip()])

    return overview


def list_containers(all_containers=False):
    """获取容器列表

    Args:
        all_containers: 是否包含已停止的容器

    Returns:
        list: 容器信息列表
    """
    flag = '-a' if all_containers else ''
    args = f'ps {flag} --format "{{json .}}"'
    status, result = _run_docker_json(args)
    if status != 0:
        return []
    # 获取每个容器的资源占用（stats --no-stream）
    return result


def container_stats(container_id):
    """获取单个容器的资源占用

    Args:
        container_id: 容器 ID 或名称

    Returns:
        dict: 包含 CPU、内存占用等
    """
    args = f'stats --no-stream --format "{{json .}}" {container_id}'
    status, result = _run_docker_json(args)
    if status != 0 or not result:
        return {}
    return result[0] if result else {}


def containers_with_stats(all_containers=False):
    """获取容器列表及其资源占用

    Args:
        all_containers: 是否包含已停止的容器

    Returns:
        list: 容器信息列表（含 stats）
    """
    containers = list_containers(all_containers)
    if not containers:
        return []
    # 批量获取 stats
    ids = ' '.join([c.get('ID', '') for c in containers if c.get('ID')])
    if ids:
        args = f'stats --no-stream --format "{{json .}}" {ids}'
        status, stats = _run_docker_json(args)
        if status == 0 and stats:
            stats_map = {s.get('Container', ''): s for s in stats}
            for c in containers:
                cid = c.get('ID', '')
                # stats 中 Container 字段是短 ID
                c['stats'] = stats_map.get(cid[:12], stats_map.get(cid, {}))
    return containers


def container_control(container_id, action):
    """控制容器（启动/停止/重启/删除）

    Args:
        container_id: 容器 ID 或名称
        action: 'start' | 'stop' | 'restart' | 'remove'

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    action_map = {
        'start': ('start', '启动'),
        'stop': ('stop', '停止'),
        'restart': ('restart', '重启'),
        'remove': ('rm -f', '删除'),
    }
    if action not in action_map:
        return {'code': -1, 'msg': f'未知的容器操作：{action}'}

    cmd, label = action_map[action]
    status, output = _run_docker(f'{cmd} {container_id}')
    if status == 0:
        return {'code': 0, 'msg': f'容器 {container_id} 已{label}'}
    else:
        return {'code': -1, 'msg': f'容器 {container_id} {label}失败：{output}'}


def list_images():
    """获取本地镜像列表

    Returns:
        list: 镜像信息列表
    """
    args = 'images --format "{{json .}}"'
    status, result = _run_docker_json(args)
    if status != 0:
        return []
    return result


def remove_image(image_id):
    """删除本地镜像

    Args:
        image_id: 镜像 ID

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    status, output = _run_docker(f'rmi {image_id}')
    if status == 0:
        return {'code': 0, 'msg': f'镜像 {image_id} 已删除'}
    else:
        return {'code': -1, 'msg': f'镜像 {image_id} 删除失败：{output}'}


def search_images(keyword):
    """在 Docker Hub 仓库搜索镜像

    Args:
        keyword: 搜索关键词

    Returns:
        list: 仓库镜像列表
    """
    if not keyword:
        return []
    args = f'search --format "{{json .}}" --limit 25 {keyword}'
    status, result = _run_docker_json(args)
    if status != 0:
        return []
    return result


def pull_image(image_name):
    """拉取镜像（同步，可能耗时较长）

    Args:
        image_name: 镜像名称（含 tag）

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    status, output = _run_docker(f'pull {image_name}')
    if status == 0:
        return {'code': 0, 'msg': f'镜像 {image_name} 拉取成功'}
    else:
        return {'code': -1, 'msg': f'镜像 {image_name} 拉取失败：{output}'}


def list_networks():
    """获取 Docker 网络列表

    Returns:
        list: 网络信息列表
    """
    args = 'network ls --format "{{json .}}"'
    status, result = _run_docker_json(args)
    if status != 0:
        return []
    return result


def remove_network(network_id):
    """删除 Docker 网络

    Args:
        network_id: 网络 ID

    Returns:
        dict: {'code': 0/-1, 'msg': '...'}
    """
    status, output = _run_docker(f'network rm {network_id}')
    if status == 0:
        return {'code': 0, 'msg': f'网络 {network_id} 已删除'}
    else:
        return {'code': -1, 'msg': f'网络 {network_id} 删除失败：{output}'}


def web_handler(context):
    """Docker 模块的 Web 请求处理入口

    Args:
        context: RequestHandler 实例
    """
    action = context.get_argument('action', '')

    if action == 'overview':
        context.write({'code': 0, 'data': get_overview()})

    elif action == 'version':
        context.write({'code': 0, 'data': get_version_info()})

    elif action == 'status':
        context.write({'code': 0, 'data': {'running': get_status(), 'installed': is_installed()}})

    elif action == 'service':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许操作 Docker 服务！'})
            return
        op = context.get_argument('op', '')
        context.write(service_control(op))

    elif action == 'containers':
        all_containers = context.get_argument('all', 'false') == 'true'
        context.write({'code': 0, 'data': containers_with_stats(all_containers)})

    elif action == 'container_control':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许操作容器！'})
            return
        container_id = context.get_argument('id', '')
        op = context.get_argument('op', '')
        if not container_id or not op:
            context.write({'code': -1, 'msg': '参数不完整！'})
            return
        context.write(container_control(container_id, op))

    elif action == 'images':
        context.write({'code': 0, 'data': list_images()})

    elif action == 'remove_image':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许删除镜像！'})
            return
        image_id = context.get_argument('id', '')
        if not image_id:
            context.write({'code': -1, 'msg': '镜像 ID 不能为空！'})
            return
        context.write(remove_image(image_id))

    elif action == 'search_images':
        keyword = context.get_argument('keyword', '')
        context.write({'code': 0, 'data': search_images(keyword)})

    elif action == 'pull_image':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许拉取镜像！'})
            return
        image_name = context.get_argument('name', '')
        if not image_name:
            context.write({'code': -1, 'msg': '镜像名称不能为空！'})
            return
        context.write(pull_image(image_name))

    elif action == 'networks':
        context.write({'code': 0, 'data': list_networks()})

    elif action == 'remove_network':
        if context.config.get('runtime', 'mode') == 'demo':
            context.write({'code': -1, 'msg': '演示模式不允许删除网络！'})
            return
        network_id = context.get_argument('id', '')
        if not network_id:
            context.write({'code': -1, 'msg': '网络 ID 不能为空！'})
            return
        context.write(remove_network(network_id))

    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})
