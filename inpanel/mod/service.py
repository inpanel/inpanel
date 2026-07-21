# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''服务管理模块

提供跨平台的服务管理功能，架构为：
- 双层分离：查询层（快速系统 API） + 操作层（通过包管理器）
- 服务定义：统一在 templates/services/services.json 中配置
- 服务分类：固定服务 + 用户自定义服务 + 其他服务

核心接口：
    web_handler          → 处理 /api/operation/service 请求
    get_service_list()   → 获取分类服务列表（固定 + 自定义 + 其他）
    get_service_detail() → 获取服务详情（配置文件、路径、日志等）
    get_autostart_list() → 获取已设置开机自启的服务列表
'''


from .service_manager import (
    get_service_manager,
    get_all_service_names,
    get_service_config,
    get_custom_categories,
    build_service_detail,
    save_user_custom_categories,
)


# ==========================================================================
# 模块级函数（供 web_handler 和外部调用）
# ==========================================================================

def web_handler(context):
    '''处理服务管理的 Web 请求（/api/operation/service）

    支持的操作：
        - start, stop, restart: 服务启停控制
        - chkconfig: 开机自启管理
        - get_autostart_list: 获取自启列表
        - get_service_list: 获取分类服务列表（新接口）
        - get_service_detail: 获取服务详情（新接口）
        - set_custom_category: 设置用户自定义分类（新接口）
        - install, uninstall: 安装/卸载服务（新接口）
    '''
    action = context.get_argument('action', '')

    manager = get_service_manager()
    if not manager:
        context.write({'code': -1, 'msg': '当前系统不支持服务管理'})
        return

    if action in ('start', 'stop', 'restart'):
        name = context.get_argument('name', '')
        service_label = context.get_argument('service', '')
        if not name:
            name = service_label
        if action == 'start':
            ok, msg = manager.start(service_label)
        elif action == 'stop':
            ok, msg = manager.stop(service_label)
        else:
            ok, msg = manager.restart(service_label)
        context.write({'code': 0 if ok else -1, 'msg': msg})

    elif action == 'chkconfig':
        service_label = context.get_argument('service', '')
        autostart = context.get_argument('autostart', '')
        name = context.get_argument('name', '')
        if not name:
            name = service_label

        autostart_str = {'on': '启用', 'off': '禁用'}
        if autostart == 'on':
            ok, msg = manager.enable(service_label)
        else:
            ok, msg = manager.disable(service_label)

        if ok:
            context.write({'code': 0, 'msg': f'成功{autostart_str.get(autostart, autostart)} {name} 自动启动！'})
        else:
            context.write({'code': -1, 'msg': msg})

    elif action == 'get_autostart_list':
        context.write({'code': 0, 'data': get_autostart_list()})

    elif action == 'get_service_list':
        # 新接口：获取分类服务列表
        context.write({'code': 0, 'data': get_service_list()})

    elif action == 'get_service_detail':
        # 新接口：获取服务详情
        service_id = context.get_argument('service', '')
        if not service_id:
            context.write({'code': -1, 'msg': '服务名称不能为空'})
            return
        detail = get_service_detail(service_id)
        if detail:
            context.write({'code': 0, 'data': detail})
        else:
            context.write({'code': -1, 'msg': f'服务 {service_id} 不存在'})

    elif action == 'set_custom_category':
        # 新接口：用户自定义服务分类
        service_id = context.get_argument('service', '')
        category_id = context.get_argument('category', '')
        if not service_id:
            context.write({'code': -1, 'msg': '服务名称不能为空'})
            return
        ok = set_custom_category(service_id, category_id)
        if ok:
            context.write({'code': 0, 'msg': f'服务 {service_id} 分类已更新为 {category_id}'})
        else:
            context.write({'code': -1, 'msg': f'设置分类失败'})

    elif action == 'install':
        service_label = context.get_argument('service', '')
        name = context.get_argument('name', '') or service_label
        ok, msg = manager.install(service_label)
        context.write({'code': 0 if ok else -1, 'msg': msg})

    elif action == 'uninstall':
        service_label = context.get_argument('service', '')
        name = context.get_argument('name', '') or service_label
        ok, msg = manager.uninstall(service_label)
        context.write({'code': 0 if ok else -1, 'msg': msg})

    else:
        context.write({'code': -1, 'msg': '未定义的操作！'})


def do_start(service_name=None):
    '''启动服务'''
    if not service_name:
        return False
    manager = get_service_manager()
    if manager:
        ok, _ = manager.start(service_name)
        return ok
    return False


def do_stop(service_name=None):
    '''停止服务'''
    if not service_name:
        return False
    manager = get_service_manager()
    if manager:
        ok, _ = manager.stop(service_name)
        return ok
    return False


def do_restart(service_name=None):
    '''重启服务'''
    if not service_name:
        return False
    manager = get_service_manager()
    if manager:
        ok, _ = manager.restart(service_name)
        return ok
    return False


def get_status(name=None):
    '''获取服务状态'''
    if name is None:
        return False
    manager = get_service_manager()
    if manager:
        return manager.status(name)
    return None


def get_list():
    '''获取所有服务列表（包管理器管理的全部服务）'''
    manager = get_service_manager()
    if manager:
        return manager.list_all_package_services()
    return []


def get_autostart_list():
    """获取已设置开机自启的服务列表"""
    manager = get_service_manager()
    if not manager:
        return []
    all_status = manager.get_all_status()
    return [s for s, st in all_status.items() if st is not None and manager.is_enabled(s)]


def set_autostart(service_name=None, autostart=True):
    """设置或取消服务开机自启"""
    if not service_name:
        return False
    manager = get_service_manager()
    if not manager:
        return False
    if autostart:
        ok, _ = manager.enable(service_name)
    else:
        ok, _ = manager.disable(service_name)
    return ok


# ==========================================================================
# 新接口：服务列表和服务详情
# ==========================================================================

def get_service_list():
    """获取分类服务列表

    返回结构：
    {
        'categories': [
            {
                'id': 'http',
                'name': 'HTTP',
                'services': [
                    {
                        'id': 'nginx',
                        'name': 'Nginx',
                        'status': 'running',
                        'autostart': True,
                        'installed': True,
                        'category': 'http',
                    },
                    ...
                ]
            },
            ...
        ],
        'other': [
            {
                'id': 'homebrew.mxcl.someapp',
                'name': 'someapp',
                'status': 'running',
                'autostart': False,
                'installed': True,
                'category': 'other',
            },
            ...
        ]
    }
    """
    from ..templates.services import load_categories

    manager = get_service_manager()
    if not manager:
        return {'categories': [], 'other': []}

    # 获取所有固定服务的状态
    all_status = manager.get_all_status()

    # 获取用户自定义分类
    custom_categories = get_custom_categories()

    # 构建分类结构
    categories_config = load_categories()
    category_order = {c['id']: c.get('order', 99) for c in categories_config}
    category_names = {c['id']: c['name'] for c in categories_config}

    # 按分类组织固定服务
    categorized = {}  # {category_id: [service_items]}

    for service_id in get_all_service_names():
        svc = get_service_config(service_id)
        if not svc:
            continue

        # 检查用户自定义分类
        cat_id = custom_categories.get(service_id, svc.get('category', 'other'))

        if cat_id not in categorized:
            categorized[cat_id] = []

        status = all_status.get(service_id)
        categorized[cat_id].append({
            'id': service_id,
            'name': svc.get('name', service_id),
            'status': status,
            'autostart': manager.is_enabled(service_id) if status is not None else False,
            'installed': status is not None,
            'category': cat_id,
            'description': svc.get('description', ''),
            'default_port': svc.get('default_port'),
        })

    # 构建 categories 数组（按 order 排序）
    categories_result = []
    for cat in sorted(categories_config, key=lambda x: x.get('order', 99)):
        cat_id = cat['id']
        if cat_id == 'other':
            continue  # "其他" 单独处理
        if cat_id not in categorized:
            continue
        categories_result.append({
            'id': cat_id,
            'name': cat['name'],
            'icon': cat.get('icon', ''),
            'order': cat.get('order', 99),
            'services': categorized[cat_id],
        })

    # 获取"其他"服务
    other_services = manager.get_other_services()

    return {
        'categories': categories_result,
        'other': other_services,
    }


def get_service_detail(service_id):
    """获取服务详情

    包含配置文件、日志文件、数据目录等完整信息。
    """
    manager = get_service_manager()
    if not manager:
        return None

    status = manager.status(service_id)
    autostart = manager.is_enabled(service_id) if status is not None else False

    # 先检查是否是固定服务
    detail = build_service_detail(service_id, status, autostart)
    if detail:
        return detail

    # 如果不在固定服务中，尝试从"其他"服务查找
    other_services = manager.get_other_services()
    for s in other_services:
        if s['id'] == service_id:
            return {
                'id': service_id,
                'name': s['name'],
                'category': 'other',
                'description': f'通过系统发现的 {s["package_manager"]} 服务',
                'status': s['status'],
                'autostart': s['autostart'],
                'config_files': [],
                'log_files': [],
                'data_dirs': [],
                'default_port': None,
                'package_manager': s['package_manager'],
                'package_name': service_id,
                'installed': s['installed'],
            }

    return None


def set_custom_category(service_id, category_id):
    """将"其他"服务归类到指定分类"""
    from ..templates.services import load_categories

    # 验证 category_id 是否存在
    categories_config = load_categories()
    valid_ids = {c['id'] for c in categories_config}
    if category_id not in valid_ids:
        return False

    custom_categories = dict(get_custom_categories())
    custom_categories[service_id] = category_id
    save_user_custom_categories(custom_categories)
    return True


# ==========================================================================
# Service 类（兼容旧接口）
# ==========================================================================

class Service(object):
    '''服务管理类

    兼容旧接口。服务列表现在从 services.json 动态加载。
    '''

    @staticmethod
    def _get_manager():
        return get_service_manager()

    # 兼容旧代码：保持 _page_service_items 字典格式
    _page_service_items = {}

    @classmethod
    def _ensure_items(cls):
        """延迟初始化 _page_service_items（从配置加载）"""
        if not cls._page_service_items:
            for name in get_all_service_names():
                cls._page_service_items[name] = False

    @classmethod
    def get_service_items(cls):
        """返回面板支持的全部服务列表（从配置加载）"""
        cls._ensure_items()
        return dict(cls._page_service_items)

    # 兼容旧代码：Service.service_items 作为属性访问
    @property
    def service_items(self):
        self._ensure_items()
        return self._page_service_items

    @service_items.setter
    def service_items(self, value):
        pass  # 忽略赋值，从配置加载

    # 类级别的 service_items 属性
    _class_service_items = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def status(cls, service=None):
        """获取单个服务状态"""
        if not service:
            return None
        manager = cls._get_manager()
        if manager:
            return manager.status(service)
        return None


# 初始化 Service 类属性
Service._ensure_items()

# 兼容旧代码的类属性访问
setattr(Service, 'service_items', Service._page_service_items)


__all__ = [
    'do_start', 'do_stop', 'do_restart', 'get_status', 'get_list',
    'get_autostart_list', 'set_autostart', 'web_handler',
    'get_service_list', 'get_service_detail', 'set_custom_category',
    'Service',
    'service_start', 'service_stop', 'service_restart',
    'service_install', 'service_uninstall', 'service_info',
]


# ==========================================================================
# 异步任务函数（供 web.py _dispatch_task 调用，第一个参数 tm 为 TaskManager）
# ==========================================================================

import asyncio


async def _service_action(tm, action, service, name):
    """服务启停控制（start/stop/restart）"""
    jobname = f'service.{action}_{service}'
    if not tm._start_job(jobname):
        return

    action_str = {'start': '启动', 'stop': '停止', 'restart': '重启'}
    tm._update_job(jobname, 2, f'正在{action_str[action]} {name} 服务...')

    from .service_manager import get_service_manager
    manager = get_service_manager()

    if manager is None:
        tm._finish_job(jobname, -1, '当前系统不支持服务管理')
        return

    loop = asyncio.get_event_loop()
    if action == 'start':
        ok, output = await loop.run_in_executor(None, manager.start, service)
    elif action == 'stop':
        ok, output = await loop.run_in_executor(None, manager.stop, service)
    elif action == 'restart':
        ok, output = await loop.run_in_executor(None, manager.restart, service)
    else:
        tm._finish_job(jobname, -1, f'未定义的操作：{action}')
        return

    if ok:
        code = 0
        msg = f'{name} 服务{action_str[action]}成功！'
        data = None
    else:
        code = -1
        msg = f'{name} 服务{action_str[action]}失败！'
        data = output.replace('\n', '<br>')

    tm._finish_job(jobname, code, msg, data=data)


async def service_start(tm, service, name=None):
    """服务启停控制（异步任务）- 对应 jobname: service.start_{service}"""
    if not name:
        name = service
    await _service_action(tm, "start", service, name)

async def service_stop(tm, service, name=None):
    """停止服务（异步任务）- 对应 jobname: service.stop_{service}"""
    if not name:
        name = service
    await _service_action(tm, "stop", service, name)


async def service_restart(tm, service, name=None):
    """重启服务（异步任务）- 对应 jobname: service.restart_{service}"""
    if not name:
        name = service
    await _service_action(tm, "restart", service, name)


async def service_install(tm, service, name=''):
    """安装服务（异步任务）- 对应 jobname: service.install_{service}"""
    if not name:
        name = service
    jobname = f'service.install_{service}'
    if not tm._start_job(jobname):
        return

    if not name:
        name = service

    tm._update_job(jobname, 2, f'正在安装 {name} 服务...')

    from .service_manager import get_service_manager
    manager = get_service_manager()

    if manager is None:
        tm._finish_job(jobname, -1, '当前系统不支持服务管理')
        return

    loop = asyncio.get_event_loop()
    ok, output = await loop.run_in_executor(None, manager.install, service)

    if ok:
        code = 0
        msg = f'{name} 安装成功！'
        data = None
    else:
        code = -1
        msg = f'{name} 安装失败！'
        data = output.replace('\n', '<br>')

    tm._finish_job(jobname, code, msg, data=data)


async def service_uninstall(tm, service, name=''):
    """卸载服务（异步任务）- 对应 jobname: service.uninstall_{service}"""
    jobname = f'service.uninstall_{service}'
    if not tm._start_job(jobname):
        return

    if not name:
        name = service

    tm._update_job(jobname, 2, f'正在卸载 {name} 服务...')

    from .service_manager import get_service_manager
    manager = get_service_manager()

    if manager is None:
        tm._finish_job(jobname, -1, '当前系统不支持服务管理')
        return

    loop = asyncio.get_event_loop()
    ok, output = await loop.run_in_executor(None, manager.uninstall, service)

    if ok:
        code = 0
        msg = f'{name} 卸载成功！'
        data = None
    else:
        code = -1
        msg = f'{name} 卸载失败！'
        data = output.replace('\n', '<br>')

    tm._finish_job(jobname, code, msg, data=data)


async def service_info(tm, service_id):
    """获取服务详情（异步任务）- 对应 jobname: service.info_{service_id}"""
    jobname = f'service.info_{service_id}'
    if not tm._start_job(jobname):
        return

    tm._update_job(jobname, 2, '正在获取服务详情...')

    detail = get_service_detail(service_id)
    if detail:
        code = 0
        msg = '获取服务详情成功！'
        data = detail
    else:
        code = -1
        msg = '获取服务详情失败：服务 %s 不存在' % service_id
        data = None

    tm._finish_job(jobname, code, msg, data)


if __name__ == '__main__':
    manager = get_service_manager()
    if manager:
        print(f'Service Manager: {manager.__class__.__name__}')
        all_status = manager.get_all_status()
        for name in get_all_service_names():
            status = all_status.get(name)
            enabled = manager.is_enabled(name) if status is not None else False
            print(f'* Status of {name}: {status} (autostart: {enabled})')

        print('\n--- Other Services ---')
        for s in manager.get_other_services():
            print(f'  {s["id"]}: {s["status"]} (installed: {s["installed"]})')
    else:
        print('No service manager available on this system.')
