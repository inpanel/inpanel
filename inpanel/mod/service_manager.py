# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''统一服务管理器模块

架构设计：
    双层分离 —— 查询层（快速） + 操作层（通过包管理器）

    查询层（Fast Query Layer）：
        使用系统 API 快速获取服务运行状态，不依赖包管理器命令。
        - macOS: launchctl list + glob plist 文件（<50ms）
        - Linux: systemctl list-units 批量查询

    操作层（Package Manager Operations）：
        通过包管理器命令执行 start/stop/restart/enable/disable/install/uninstall。
        - macOS: brew services
        - Linux: systemctl / chkconfig / apt / yum / dnf

    服务定义：
        面板支持的服务列表统一在 templates/services/services.json 中定义。
        包含：服务分类、包管理器映射、配置文件路径、日志路径、数据目录等详情。

    服务分为三层：
        1. 固定服务 —— services.json 中定义的、面板原生支持的服务
        2. 用户自定义服务 —— 用户从"其他"服务中手动分类到某个类别的服务
        3. 其他服务 —— 系统上运行但不在固定服务列表中的服务

    核心接口：
        get_all_status()           → 批量获取固定服务状态（快速）
        get_other_services()       → 获取"其他"服务列表
        get_service_detail(id)     → 获取服务详情（配置文件、路径等）
        status(name)               → 单个服务状态
        start/stop/restart(name)   → 通过包管理器操作
        install/uninstall(name)    → 通过包管理器安装/卸载
'''

import glob as glob_mod
import json
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import getstatusoutput

from .system import get_os_family, is_darwin
from ..templates.services import load_services, save_user_custom_categories


# ==========================================================================
# 加载服务配置
# ==========================================================================

def _load_services_config():
    """加载 services.json 配置（含缓存）"""
    if not hasattr(_load_services_config, '_cache'):
        _load_services_config._cache = load_services()
    return _load_services_config._cache


def _get_package_manager_priority():
    """获取当前系统的包管理器优先级列表"""
    family = get_os_family()
    cfg = _load_services_config()
    return cfg.get('package_manager_priority', {}).get(family, [])


def _get_active_package_manager():
    """获取当前系统可用的首选包管理器"""
    for pm in _get_package_manager_priority():
        if pm == 'brew' and shutil.which('brew'):
            return 'brew'
        elif pm == 'yum' and shutil.which('yum'):
            return 'yum'
        elif pm == 'dnf' and shutil.which('dnf'):
            return 'dnf'
        elif pm == 'apt' and shutil.which('apt'):
            return 'apt'
    # fallback: 检测任意可用
    for pm in ['brew', 'yum', 'dnf', 'apt']:
        if shutil.which(pm):
            return pm
    return None


def get_all_service_names():
    """获取面板支持的全部固定服务 ID 列表"""
    cfg = _load_services_config()
    names = []
    for cat in cfg.get('categories', []):
        for svc in cat.get('services', []):
            names.append(svc['id'])
    return names


def get_service_config(service_id):
    """获取单个服务的完整配置"""
    cfg = _load_services_config()
    for cat in cfg.get('categories', []):
        for svc in cat.get('services', []):
            if svc['id'] == service_id:
                return svc
    return None


def get_custom_categories():
    """获取用户自定义分类：{service_id: category_id}"""
    cfg = _load_services_config()
    return cfg.get('custom_categories', {})


# ==========================================================================
# 抽象基类
# ==========================================================================

class ServiceManagerBase(ABC):
    """服务管理器抽象基类"""

    @abstractmethod
    def detect(self):
        """检测当前系统是否匹配此服务管理器"""
        pass

    @abstractmethod
    def status(self, service_name):
        """获取服务状态: 'running' | 'stopped' | None（未安装）"""
        pass

    @abstractmethod
    def start(self, service_name):
        """启动服务"""
        pass

    @abstractmethod
    def stop(self, service_name):
        """停止服务"""
        pass

    @abstractmethod
    def restart(self, service_name):
        """重启服务"""
        pass

    @abstractmethod
    def enable(self, service_name):
        """设置开机自启"""
        pass

    @abstractmethod
    def disable(self, service_name):
        """取消开机自启"""
        pass

    @abstractmethod
    def is_enabled(self, service_name):
        """检查是否已设置开机自启"""
        pass

    @abstractmethod
    def get_all_status(self):
        """批量获取面板固定服务的状态（快速查询层）"""
        pass

    @abstractmethod
    def get_other_services(self):
        """获取"其他"服务列表（系统上运行但不在固定服务中的服务）"""
        pass

    @abstractmethod
    def install(self, service_name):
        """安装服务"""
        pass

    @abstractmethod
    def uninstall(self, service_name):
        """卸载服务"""
        pass

    @abstractmethod
    def list_all_package_services(self):
        """列出包管理器管理的全部服务"""
        pass


# ==========================================================================
# macOS brew 服务管理器
# ==========================================================================

class BrewServiceManager(ServiceManagerBase):
    """macOS Homebrew 服务管理器

    快速查询层：
        launchctl list（~6ms）一次性获取所有 launchd 服务状态
        glob plist 文件确认已安装的 formula

    操作层：
        brew services start/stop/restart
        brew install/uninstall
    """

    def __init__(self):
        self._has_brew = shutil.which('brew') is not None
        self._loaded_services_cache = None

    def detect(self):
        return is_darwin() and self._has_brew

    def _run_brew(self, *args):
        cmd = f'brew {" ".join(args)} 2>&1'
        rc, output = getstatusoutput(cmd)
        # brew services 的输出信息可能包含在 stdout 或 stderr 中，
        # 以实际输出内容判断是否成功
        if rc == 0 and output:
            if 'Successfully' in output or 'already' in output.lower():
                return (True, output)
        return (False, output)

    # ---- 快速查询层 ----

    def _get_launchctl_state(self):
        """launchctl list 一次性获取所有 launchd 服务状态（~6ms）"""
        rc, output = getstatusoutput('launchctl list 2>/dev/null')
        if rc != 0:
            return {}
        state = {}
        for line in output.split('\n'):
            parts = line.split()
            if len(parts) >= 3 and 'homebrew' in parts[2]:
                pid = parts[0]
                label = parts[2]
                state[label] = 'running' if pid.isdigit() else 'stopped'
        return state

    def _get_installed_formulas(self):
        """通过 glob plist 确认已安装的 formula（~10ms）"""
        installed = {}
        patterns = [
            '/usr/local/opt/*/homebrew.mxcl.*.plist',
            '/opt/homebrew/opt/*/homebrew.mxcl.*.plist',
        ]
        for pattern in patterns:
            for f in glob_mod.glob(pattern):
                name = os.path.basename(f).replace('.plist', '')
                installed[name] = f
        return installed

    def _get_loaded_services(self):
        """获取已在 LaunchAgents 注册的服务（软链接）"""
        loaded = set()
        patterns = [
            os.path.expanduser('~/Library/LaunchAgents/homebrew.mxcl.*.plist'),
        ]
        for pattern in patterns:
            for f in glob_mod.glob(pattern):
                name = os.path.basename(f).replace('.plist', '')
                loaded.add(name)
        return loaded

    def _check_pgrep(self, pgrep_names):
        """用 pgrep 检查进程是否运行"""
        for name in pgrep_names:
            rc, _ = getstatusoutput(f'pgrep -l {name} 2>/dev/null')
            if rc == 0:
                return True
        return False

    def _get_all_launchctl_services(self):
        """获取所有 launchd 服务（包括非 homebrew 的）—— 用于"其他"服务"""
        rc, output = getstatusoutput('launchctl list 2>/dev/null')
        if rc != 0:
            return {}
        state = {}
        for line in output.split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                pid = parts[0]
                label = parts[2]
                if label.startswith('com.apple.'):
                    continue
                state[label] = 'running' if pid.isdigit() else 'stopped'
        return state

    def _get_launchctl_label(self, service_id):
        """获取服务的 launchctl label"""
        svc = get_service_config(service_id)
        if svc:
            return svc.get('launchctl_label')
        return None

    def _get_pgrep_names(self, service_id):
        """获取服务的 pgrep 进程名列表"""
        svc = get_service_config(service_id)
        if svc:
            return svc.get('pgrep_names', [service_id])
        return [service_id]

    def status(self, service_name):
        """获取单个服务状态"""
        label = self._get_launchctl_label(service_name)
        if label:
            launchctl_state = self._get_launchctl_state()
            installed = self._get_installed_formulas()
            if label in installed:
                return launchctl_state.get(label, 'stopped')
            if label in launchctl_state:
                return launchctl_state[label]
            return None

        # 非 launchctl 管理的服务，用 pgrep
        if self._check_pgrep(self._get_pgrep_names(service_name)):
            return 'running'
        return 'stopped'

    def get_all_status(self):
        """批量获取面板固定服务的状态（<50ms）"""
        launchctl_state = self._get_launchctl_state()
        installed = self._get_installed_formulas()
        self._loaded_services_cache = self._get_loaded_services()

        result = {}
        for service_id in get_all_service_names():
            svc = get_service_config(service_id)
            if not svc:
                continue

            label = svc.get('launchctl_label')
            if label:
                if label in installed or label in launchctl_state:
                    result[service_id] = launchctl_state.get(label, 'stopped')
                else:
                    result[service_id] = None
            else:
                pgrep_names = svc.get('pgrep_names', [service_id])
                if self._check_pgrep(pgrep_names):
                    result[service_id] = 'running'
                else:
                    result[service_id] = 'stopped'

        return result

    def get_other_services(self):
        """获取"其他"服务列表 —— 系统上运行但不在面板固定服务中的 launchd 服务"""
        all_labels = self._get_all_launchctl_services()
        installed = self._get_installed_formulas()
        known_labels = set()

        # 收集所有已知服务的 label
        for service_id in get_all_service_names():
            label = self._get_launchctl_label(service_id)
            if label:
                known_labels.add(label)

        # 收集已安装的 formula 但不在已知列表中的
        other_services = []
        for label, status in all_labels.items():
            if label in known_labels:
                continue
            # 过滤掉系统服务
            if label.startswith('com.apple.'):
                continue
            is_installed = label in installed
            other_services.append({
                'id': label,
                'name': label.replace('homebrew.mxcl.', ''),
                'status': status,
                'autostart': label in (self._loaded_services_cache or self._get_loaded_services()),
                'package_manager': 'brew' if is_installed else 'unknown',
                'category': 'other',
                'installed': is_installed,
            })

        # 按名称排序
        other_services.sort(key=lambda x: x['name'])
        return other_services

    def is_enabled(self, service_name):
        """检查是否已设置开机自启"""
        label = self._get_launchctl_label(service_name)
        if label:
            if self._loaded_services_cache is not None:
                return label in self._loaded_services_cache
            return label in self._get_loaded_services()
        return self._check_pgrep(self._get_pgrep_names(service_name))

    # ---- 操作层（brew 命令） ----

    def _get_brew_package_name(self, service_id):
        """获取 brew 包名"""
        pm = _get_active_package_manager()
        svc = get_service_config(service_id)
        if svc and pm:
            return svc.get('packages', {}).get(pm)
        return None

    def start(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('services', 'start', brew_name)
        if ok:
            return (True, f'{service_name} 已启动成功')
        return (False, f'{service_name} 启动失败：{output}')

    def stop(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('services', 'stop', brew_name)
        if ok:
            return (True, f'{service_name} 已成功停止运行')
        return (False, f'{service_name} 停止失败：{output}')

    def restart(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('services', 'restart', brew_name)
        if ok:
            return (True, f'{service_name} 已重新启动')
        return (False, f'{service_name} 重新启动失败：{output}')

    def enable(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('services', 'start', brew_name)
        if ok:
            return (True, f'成功启用 {service_name} 自动启动')
        return (False, f'启用 {service_name} 自动启动失败：{output}')

    def disable(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('services', 'stop', brew_name)
        if ok:
            return (True, f'成功禁用 {service_name} 自动启动')
        return (False, f'禁用 {service_name} 自动启动失败：{output}')

    def install(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('install', brew_name)
        if ok:
            return (True, f'{service_name} 安装成功')
        return (False, f'{service_name} 安装失败：{output}')

    def uninstall(self, service_name):
        brew_name = self._get_brew_package_name(service_name)
        if not brew_name:
            return (False, f'不支持的服务或未找到对应的 brew 包：{service_name}')
        ok, output = self._run_brew('uninstall', brew_name)
        if ok:
            return (True, f'{service_name} 卸载成功')
        return (False, f'{service_name} 卸载失败：{output}')

    def list_all_package_services(self):
        """列出 brew 管理的全部服务"""
        rc, output = self._run_brew('services', 'list')
        if rc != 0 or not output.strip():
            return []
        services = []
        lines = output.strip().split('\n')
        for line in lines[1:]:
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            if '/' in name:
                name = name.split('/')[-1]
            services.append(name)
        return sorted(services)


# ==========================================================================
# Linux systemd 服务管理器
# ==========================================================================

class SystemdManager(ServiceManagerBase):
    """Linux systemd 服务管理器

    快速查询层：
        systemctl list-units 批量查询活跃/非活跃单元

    操作层：
        systemctl start/stop/restart/enable/disable
        包管理器 install/uninstall（yum/dnf/apt）
    """

    def __init__(self):
        self._has_systemctl = shutil.which('systemctl') is not None
        self._active_pm = _get_active_package_manager()

    def detect(self):
        family = get_os_family()
        return family in ('rhel', 'debian')

    def _get_systemd_unit(self, service_id):
        """获取 systemd 服务单元名称"""
        svc = get_service_config(service_id)
        if svc:
            return svc.get('systemd_unit')
        return None

    def _get_pgrep_names(self, service_id):
        svc = get_service_config(service_id)
        if svc:
            return svc.get('pgrep_names', [service_id])
        return [service_id]

    def _check_pid_file(self, service_id):
        """检查 PID 文件"""
        svc = get_service_config(service_id)
        if not svc:
            return None
        pid_file = svc.get('pid_file', '')
        if pid_file and Path(pid_file).exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = f.readline().strip()
                if pid and Path(f'/proc/{pid}').exists():
                    return 'running'
            except (IOError, PermissionError):
                pass
        return None

    def _check_pgrep(self, pgrep_names):
        for name in pgrep_names:
            rc, _ = getstatusoutput(f'pidof -c -o %PPID -x {name} 2>/dev/null')
            if rc == 0:
                return True
        return False

    def _run_cmd(self, cmd):
        rc, output = getstatusoutput(cmd)
        return (rc == 0, output.strip())

    # ---- 状态查询 ----

    def status(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name)
            if unit:
                rc, output = getstatusoutput(f'systemctl is-active {unit} 2>/dev/null')
                if rc == 0 and 'active' in output:
                    return 'running'
                if 'inactive' in output or 'dead' in output:
                    return 'stopped'
                if 'unknown' in output or 'not-found' in output:
                    return self._fallback_status(service_name)
        return self._fallback_status(service_name)

    def _fallback_status(self, service_name):
        """回退：PID 文件 + pgrep"""
        pid_result = self._check_pid_file(service_name)
        if pid_result:
            return pid_result

        pgrep_names = self._get_pgrep_names(service_name)
        if self._check_pgrep(pgrep_names):
            return 'running'
        return 'stopped'

    def get_all_status(self):
        """批量获取面板固定服务的状态"""
        active_units = set()
        inactive_units = set()

        if self._has_systemctl:
            rc, output = getstatusoutput(
                'systemctl list-units --type=service --state=active --no-legend 2>/dev/null'
            )
            if rc == 0:
                for line in output.strip().split('\n'):
                    parts = line.split()
                    if parts:
                        active_units.add(parts[0].replace('.service', ''))

            rc, output = getstatusoutput(
                'systemctl list-units --type=service --state=inactive --no-legend 2>/dev/null'
            )
            if rc == 0:
                for line in output.strip().split('\n'):
                    parts = line.split()
                    if parts:
                        inactive_units.add(parts[0].replace('.service', ''))

        result = {}
        for service_id in get_all_service_names():
            unit = self._get_systemd_unit(service_id)
            if unit:
                unit_name = unit.replace('.service', '')
                if unit_name in active_units:
                    result[service_id] = 'running'
                elif unit_name in inactive_units:
                    result[service_id] = 'stopped'
                else:
                    result[service_id] = self._fallback_status(service_id)
            else:
                result[service_id] = self._fallback_status(service_id)

        return result

    def get_other_services(self):
        """获取"其他"服务列表"""
        known_units = set()
        for service_id in get_all_service_names():
            unit = self._get_systemd_unit(service_id)
            if unit:
                known_units.add(unit.replace('.service', ''))

        other_services = []
        if self._has_systemctl:
            # 获取所有活跃服务
            for state, status_str in [('active', 'running'), ('inactive', 'stopped')]:
                rc, output = getstatusoutput(
                    f'systemctl list-units --type=service --state={state} --no-legend 2>/dev/null'
                )
                if rc == 0:
                    for line in output.strip().split('\n'):
                        parts = line.split()
                        if not parts:
                            continue
                        unit_name = parts[0].replace('.service', '')
                        if unit_name in known_units:
                            continue
                        # 过滤系统内部服务
                        if unit_name.startswith('systemd-') or unit_name.endswith('.mount') or unit_name.endswith('.device'):
                            continue
                        # 检查是否已经添加
                        if any(s['id'] == unit_name for s in other_services):
                            continue

                        # 检查是否已启用
                        rc2, _ = getstatusoutput(f'systemctl is-enabled {unit_name}.service 2>/dev/null')
                        is_enabled = rc2 == 0

                        other_services.append({
                            'id': unit_name,
                            'name': unit_name,
                            'status': status_str,
                            'autostart': is_enabled,
                            'package_manager': self._active_pm or 'unknown',
                            'category': 'other',
                            'installed': True,
                        })

        other_services.sort(key=lambda x: x['name'])
        return other_services

    def is_enabled(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name)
            if unit:
                rc, _ = getstatusoutput(f'systemctl is-enabled {unit} 2>/dev/null')
                return rc == 0
        rc, output = getstatusoutput(f'chkconfig --list {service_name} 2>/dev/null')
        return ':on' in output or ':启用' in output

    # ---- 操作层 ----

    def _get_package_name(self, service_id):
        pm = self._active_pm
        svc = get_service_config(service_id)
        if svc and pm:
            return svc.get('packages', {}).get(pm)
        return None

    def start(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name) or f'{service_name}.service'
            ok, output = self._run_cmd(f'systemctl start {unit} 2>&1')
        else:
            ok, output = self._run_cmd(f'/etc/init.d/{service_name} start 2>&1')
        if ok:
            return (True, f'{service_name} 已启动成功')
        return (False, f'{service_name} 启动失败：{output}')

    def stop(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name) or f'{service_name}.service'
            ok, output = self._run_cmd(f'systemctl stop {unit} 2>&1')
        else:
            ok, output = self._run_cmd(f'/etc/init.d/{service_name} stop 2>&1')
        if ok:
            return (True, f'{service_name} 已停止运行')
        return (False, f'{service_name} 停止失败：{output}')

    def restart(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name) or f'{service_name}.service'
            ok, output = self._run_cmd(f'systemctl restart {unit} 2>&1')
        else:
            ok, output = self._run_cmd(f'/etc/init.d/{service_name} restart 2>&1')
        if ok:
            return (True, f'{service_name} 已重新启动')
        return (False, f'{service_name} 重新启动失败：{output}')

    def enable(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name) or f'{service_name}.service'
            ok, output = self._run_cmd(f'systemctl enable {unit} 2>&1')
        else:
            ok, output = self._run_cmd(f'chkconfig {service_name} on 2>&1')
        if ok:
            return (True, f'成功启用 {service_name} 自动启动')
        return (False, f'启用 {service_name} 自动启动失败：{output}')

    def disable(self, service_name):
        if self._has_systemctl:
            unit = self._get_systemd_unit(service_name) or f'{service_name}.service'
            ok, output = self._run_cmd(f'systemctl disable {unit} 2>&1')
        else:
            ok, output = self._run_cmd(f'chkconfig {service_name} off 2>&1')
        if ok:
            return (True, f'成功禁用 {service_name} 自动启动')
        return (False, f'禁用 {service_name} 自动启动失败：{output}')

    def install(self, service_name):
        pkg_name = self._get_package_name(service_name)
        if not pkg_name:
            return (False, f'不支持的服务或未找到对应包名：{service_name}')
        pm = self._active_pm
        if pm == 'yum':
            ok, output = self._run_cmd(f'yum install -y {pkg_name} 2>&1')
        elif pm == 'dnf':
            ok, output = self._run_cmd(f'dnf install -y {pkg_name} 2>&1')
        elif pm == 'apt':
            ok, output = self._run_cmd(f'apt-get install -y {pkg_name} 2>&1')
        else:
            return (False, f'当前系统没有可用的包管理器')
        if ok:
            return (True, f'{service_name} 安装成功')
        return (False, f'{service_name} 安装失败：{output}')

    def uninstall(self, service_name):
        pkg_name = self._get_package_name(service_name)
        if not pkg_name:
            return (False, f'不支持的服务或未找到对应包名：{service_name}')
        pm = self._active_pm
        if pm == 'yum':
            ok, output = self._run_cmd(f'yum remove -y {pkg_name} 2>&1')
        elif pm == 'dnf':
            ok, output = self._run_cmd(f'dnf remove -y {pkg_name} 2>&1')
        elif pm == 'apt':
            ok, output = self._run_cmd(f'apt-get remove -y {pkg_name} 2>&1')
        else:
            return (False, f'当前系统没有可用的包管理器')
        if ok:
            return (True, f'{service_name} 卸载成功')
        return (False, f'{service_name} 卸载失败：{output}')

    def list_all_package_services(self):
        """列出所有 systemd 服务"""
        services = []
        if self._has_systemctl:
            rc, output = getstatusoutput('systemctl list-unit-files --type=service --no-legend 2>/dev/null')
            if rc == 0:
                for line in output.strip().split('\n'):
                    parts = line.split()
                    if parts and parts[0].endswith('.service'):
                        svc = parts[0].replace('.service', '')
                        if svc not in services:
                            services.append(svc)
        return sorted(services)


# ==========================================================================
# 工厂函数
# ==========================================================================

_SERVICE_MANAGER = None


def get_service_manager():
    """工厂函数：根据当前系统返回对应的服务管理器实例（单例）"""
    global _SERVICE_MANAGER
    if _SERVICE_MANAGER is not None:
        return _SERVICE_MANAGER

    managers = [
        BrewServiceManager(),
        SystemdManager(),
    ]
    for mgr in managers:
        if mgr.detect():
            _SERVICE_MANAGER = mgr
            return mgr
    return None


# ==========================================================================
# 服务详情构建工具
# ==========================================================================

def build_service_detail(service_id, status, autostart):
    """构建服务详情数据

    从 services.json 配置中提取服务的完整信息，
    包括配置文件、日志文件、数据目录等。
    路径中如果以 '/' 开头则是绝对路径，否则是相对于配置/数据/日志目录的路径。

    Returns:
        {
            'id': 'nginx',
            'name': 'Nginx',
            'category': 'http',
            'description': '...',
            'status': 'running'|'stopped'|None,
            'autostart': bool,
            'config_files': [{'path': '/etc/nginx/nginx.conf', 'label': '主配置文件', 'exists': True}],
            'log_files': [{'path': '/var/log/nginx/error.log', 'label': '错误日志', 'exists': True}],
            'data_dirs': [{'path': '/var/www/html', 'label': '网站根目录', 'exists': True}],
            'default_port': 80,
            'package_manager': 'brew'|'yum'|...,
            'package_name': 'nginx',
            'installed': bool,
        }
    """
    svc = get_service_config(service_id)
    if not svc:
        return None

    from inpanel.base import config_path, data_path, logging_path

    pm = _get_active_package_manager()
    pkg_name = svc.get('packages', {}).get(pm) if pm else None
    installed = status is not None

    def resolve_path(path_info):
        """解析路径，支持相对路径标记"""
        p = path_info.get('path', '')
        if p.startswith('/'):
            return p
        if path_info.get('relative_to_config'):
            return os.path.join(str(config_path), p)
        if path_info.get('relative_to_logs'):
            return os.path.join(str(logging_path), p)
        if path_info.get('relative_to_data'):
            return os.path.join(str(data_path), p)
        return p

    config_files = []
    for cf in svc.get('config_files', []):
        path = resolve_path(cf)
        config_files.append({
            'path': path,
            'label': cf.get('label', ''),
            'exists': Path(path).exists(),
        })

    log_files = []
    for lf in svc.get('log_files', []):
        path = resolve_path(lf)
        log_files.append({
            'path': path,
            'label': lf.get('label', ''),
            'exists': Path(path).exists(),
        })

    data_dirs = []
    for dd in svc.get('data_dirs', []):
        path = resolve_path(dd)
        data_dirs.append({
            'path': path,
            'label': dd.get('label', ''),
            'exists': Path(path).is_dir(),
        })

    return {
        'id': service_id,
        'name': svc.get('name', service_id),
        'category': svc.get('category', 'other'),
        'description': svc.get('description', ''),
        'status': status,
        'autostart': autostart,
        'config_files': config_files,
        'log_files': log_files,
        'data_dirs': data_dirs,
        'default_port': svc.get('default_port'),
        'package_manager': pm,
        'package_name': pkg_name,
        'installed': installed,
    }


__all__ = [
    'ServiceManagerBase',
    'SystemdManager',
    'BrewServiceManager',
    'get_service_manager',
    'get_all_service_names',
    'get_service_config',
    'get_custom_categories',
    'build_service_detail',
    'save_user_custom_categories',
]
