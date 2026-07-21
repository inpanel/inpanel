# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""后台异步任务管理模块

提供异步任务的生命周期管理：创建、执行、状态查询、取消、清理。

设计原则：
- TaskManager 管理任务状态（running → finish/cancel）
- 业务逻辑由各 async 方法实现，通过 run_job() 提交到事件循环
- 前端通过 Task service 的 "POST 创建 → GET 轮询" 模式获取任务结果
- 任务日志记录到 /var/log/inpanel/task.log（可通过配置文件设置路径）
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from . import shell
from ..base import logging_path as _base_logging_path

logger = logging.getLogger(__name__)


def _get_task_log_path(settings=None):
    """获取任务日志路径。"""
    if settings and settings.get('task_log_path'):
        return settings['task_log_path']
    return str(Path(_base_logging_path) / 'task.log')


def _ensure_log_dir(log_path):
    """确保日志目录存在。"""
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)


def _write_task_log(settings, log_entry):
    """写入任务日志。

    日志格式：
    时间 | 任务名称 | 任务状态 | 执行结果 | 任务描述 | 开始时间 | 结束时间 | 耗时(秒)
    """
    log_path = _get_task_log_path(settings)
    try:
        _ensure_log_dir(log_path)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        logger.warning(f"Failed to write task log: {e}")

logger = logging.getLogger(__name__)


class TaskManager:
    """后台异步任务管理器。

    管理所有后台任务的创建、执行、状态追踪。

    任务状态流转:
        running → finish (成功/失败)
        running → cancel (用户取消)
    """

    # 类变量：所有实例共享同一份任务数据
    _jobs = {}    # {jobname: {status, code, msg, started_at, finished_at, data?}}
    _locks = {}   # {lockname: True}  互斥锁

    def __init__(self, settings, config):
        self.settings = settings
        self.config = config

    # ------------------------------------------------------------------
    # 任务生命周期管理（公共接口）
    # ------------------------------------------------------------------

    def run_job(self, coro):
        """将协程提交到事件循环异步执行。

        Args:
            coro: 协程对象 或 返回协程的 callable（如 partial, lambda）
        """
        async def _wrapper():
            try:
                if callable(coro) and not asyncio.iscoroutine(coro):
                    await coro()
                else:
                    await coro
            except Exception as e:
                logger.error(f"TaskManager async task error: {e}", exc_info=True)
        asyncio.ensure_future(_wrapper())

    def get_job(self, jobname):
        """获取指定任务的状态。

        Returns:
            dict: 任务状态，不存在的任务返回 {'status': 'none', 'code': -1, 'msg': ''}
        """
        if jobname not in self._jobs:
            return {'status': 'none', 'code': -1, 'msg': ''}
        return self._jobs[jobname]

    def list_jobs(self):
        """获取所有任务列表。

        Returns:
            list[dict]: 任务列表，每个任务包含 name, status, code, msg, started_at, finished_at
        """
        result = []
        for name, info in self._jobs.items():
            result.append({
                'name': name,
                'status': info.get('status', 'unknown'),
                'code': info.get('code', -1),
                'msg': info.get('msg', ''),
                'started_at': info.get('started_at', 0),
                'finished_at': info.get('finished_at', 0),
            })
        return result

    def cancel_job(self, jobname):
        """取消指定任务（仅标记状态，不强制终止进程）。

        Returns:
            bool: 是否成功取消
        """
        if jobname not in self._jobs:
            return False
        if self._jobs[jobname]['status'] == 'running':
            self._jobs[jobname]['status'] = 'cancel'
            self._jobs[jobname]['msg'] = '任务已被用户取消'
            self._jobs[jobname]['finished_at'] = time.time()
            self._log_job(jobname, 'cancel')
            return True
        return False

    def clear_finished(self):
        """清除所有已完成/已取消/无效的任务记录。

        Returns:
            int: 清除的任务数量
        """
        to_remove = [name for name, info in self._jobs.items()
                     if info.get('status') in ('finish', 'cancel', 'none')]
        for name in to_remove:
            del self._jobs[name]
        return len(to_remove)

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _log_job(self, jobname, event):
        """记录任务日志。

        格式：时间 | 任务名称 | 任务状态 | 执行结果 | 任务描述 | 开始时间 | 结束时间 | 耗时(秒)
        """
        if jobname not in self._jobs:
            return
        job = self._jobs[jobname]
        now = time.time()
        now_str = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
        started_str = datetime.fromtimestamp(
            job.get('started_at', now)).strftime('%Y-%m-%d %H:%M:%S')
        finished_at = job.get('finished_at', now)
        finished_str = datetime.fromtimestamp(finished_at).strftime('%Y-%m-%d %H:%M:%S')
        elapsed = f"{finished_at - job.get('started_at', now):.1f}" if event != 'start' else '-'

        status_map = {'running': '正在执行', 'finish': '已完成', 'cancel': '已取消'}
        result_map = {0: '成功', -1: '失败'}
        status_cn = status_map.get(job.get('status', event), event)
        # 任务刚启动（event='start'）时还没有执行结果，显示 '-'；否则取 code 映射
        if event == 'start':
            result_cn = '-'
        else:
            result_cn = result_map.get(job.get('code', -1), '-')

        log_entry = ' | '.join([
            now_str,
            jobname,
            status_cn,
            result_cn,
            job.get('msg', ''),
            started_str,
            finished_str,
            elapsed,
        ])
        _write_task_log(self.settings, log_entry)

    def _lock_job(self, lockname):
        """尝试获取互斥锁，防止同一类任务并发执行。"""
        if lockname in self._locks:
            return False
        self._locks[lockname] = True
        return True

    def _unlock_job(self, lockname):
        """释放互斥锁。"""
        if lockname not in self._locks:
            return False
        del self._locks[lockname]
        return True

    def _start_job(self, jobname):
        """标记任务为 running 状态。如果同名任务已在运行则返回 False。"""
        if jobname in self._jobs and self._jobs[jobname]['status'] == 'running':
            return False
        self._jobs[jobname] = {'status': 'running', 'msg': '', 'started_at': time.time()}
        self._log_job(jobname, 'start')
        return True

    def _update_job(self, jobname, code, msg):
        """更新任务的进度消息（任务仍在运行中）。"""
        self._jobs[jobname]['code'] = code
        self._jobs[jobname]['msg'] = msg

    def _finish_job(self, jobname, code, msg, data=None):
        """标记任务为 finish 状态。

        Args:
            code: 0=成功, -1=失败
            msg: 结果描述
            data: 可选的附加数据
        """
        self._jobs[jobname]['status'] = 'finish'
        self._jobs[jobname]['code'] = code
        self._jobs[jobname]['msg'] = msg
        self._jobs[jobname]['finished_at'] = time.time()
        if data is not None:
            self._jobs[jobname]['data'] = data
        self._log_job(jobname, 'finish')


def dispatch_task(jobname, task_manager, post_body=None, arguments=None):
    """按 模块.函数.action_参数 约定解析 jobname 并分发到对应模块。

    规则：
    1. jobname 格式为 {module}.{func}[.{action}]_[{param1}[_{param2}...]]
    2. 模块和函数和action之间用 . 分割，参数之间用 _ 分割
    3. 第一个 _ 左侧为 {module}.{func}[.action]，右侧为参数
    4. action 可以为空，参数可以为空
    5. 参数从 POST body 获取，jobname 中参数段按函数签名补位

    例如：
    - file.remove_/etc/passwd → mod.file.file_remove(tm, paths='/etc/passwd')
    - service.install_tomcat → mod.service.service_install(tm, service='tomcat')
    - file.compress_/tmp/a.gz_/tmp/a → mod.file.file_compress(tm, zippath='/tmp/a.gz', paths='/tmp/a')
    - service.restart_inpanel → mod.service.service_restart(tm, service='inpanel')

    Args:
        jobname: 任务名称（路由路径）
        task_manager: TaskManager 实例
        post_body: POST 请求的原始 body（bytes）
        arguments: URL/表单参数字典 {key: [values]}

    Returns:
        (ok: bool, msg: str)
    """
    import importlib
    import inspect
    import json as json_mod
    from functools import partial

    # ---- 解析 JSON body ----
    json_args = {}
    if post_body:
        try:
            json_args = json_mod.loads(post_body)
        except Exception:
            pass

    def _get_arg(name, default=''):
        if isinstance(json_args, dict) and name in json_args:
            return json_args[name]
        if arguments and name in arguments:
            vals = arguments[name]
            return vals[0].decode('utf-8') if isinstance(vals[0], bytes) else vals[0]
        return default

    # ---- 解析 jobname：找到分隔参数和函数名的 _ ----
    underscore_positions = [i for i, ch in enumerate(jobname) if ch == '_']
    mod = None
    func = None
    extra_parts = []
    mod_name = None
    func_name = None

    for split_pos in underscore_positions:
        method_path = jobname[:split_pos]
        param_str = jobname[split_pos + 1:]
        dot_parts = method_path.split('.')
        if len(dot_parts) < 2:
            continue
        candidate_mod = dot_parts[0]
        candidate_func = dot_parts[1]
        candidate_full = f'{candidate_mod}_{candidate_func}'

        try:
            mod = importlib.import_module(f'inpanel.mod.{candidate_mod}')
        except ImportError:
            continue

        func = getattr(mod, candidate_full, None)
        if func is not None:
            mod_name = candidate_mod
            func_name = candidate_func
            extra_parts = param_str.split('_') if param_str else []
            break

    # 如果没有 _ 分隔符，整个 jobname 就是方法路径
    if mod is None and '_' not in jobname:
        dot_parts = jobname.split('.')
        if len(dot_parts) >= 2:
            candidate_mod = dot_parts[0]
            candidate_func = dot_parts[1]
            candidate_full = f'{candidate_mod}_{candidate_func}'
            try:
                mod = importlib.import_module(f'inpanel.mod.{candidate_mod}')
                func = getattr(mod, candidate_full, None)
                if func is not None:
                    mod_name = candidate_mod
                    func_name = candidate_func
                    extra_parts = []
            except ImportError:
                pass

    if mod is None or func is None:
        return False, '未定义的操作！'

    # ---- 收集参数：POST body + jobname 参数段 ----
    kwargs = {}
    sig = inspect.signature(func)
    sig_params = set(sig.parameters.keys()) - {'tm'}

    if arguments:
        for key in arguments:
            if key in sig_params:
                kwargs[key] = _get_arg(key, '')

    for param_name, param in sig.parameters.items():
        if param_name == 'tm':
            continue
        if param_name not in kwargs and extra_parts:
            while extra_parts and extra_parts[0] in kwargs.values():
                extra_parts.pop(0)
            if extra_parts:
                kwargs[param_name] = extra_parts.pop(0)

    kwargs['tm'] = task_manager

    coro = partial(func, **kwargs)
    task_manager.run_job(coro)
    return True, '任务已创建，正在处理中...'