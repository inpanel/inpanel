# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Plugin Management Module for InPanel.'''

import os
import sys
import json
import zipfile
import shutil
import tempfile
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.request import urlopen


class PluginManager:
    '''Manager for InPanel plugins.
    
    Handles plugin installation, uninstallation, enabling, disabling,
    and configuration management.
    '''
    
    def __init__(self, app: Any) -> None:
        '''Initialize plugin manager.
        
        Args:
            app: The InPanel application instance
        '''
        self.app = app
        self.plugins: Dict[str, Any] = {}
        self.loaded = False
        
        from ..base import config_path, run_type, root_path, data_path, logging_path
        self.config_path = config_path
        self.run_type = run_type
        self.root_path = root_path
        self.data_path = data_path
        self.logging_path = logging_path
        
        self.plugins_base_path = Path(data_path) / 'plugins'
        
        self.status_file = Path(config_path) / 'plugins.json'
        self.plugin_status: Dict[str, Dict[str, Any]] = self._load_status()
        
        self._init_plugin_logger()
    
    def _init_plugin_logger(self) -> None:
        '''Initialize plugin logger.'''
        plugin_log_file = Path(self.logging_path) / 'plugins.log'
        
        self.plugin_logger = logging.getLogger('plugin_manager')
        self.plugin_logger.setLevel(logging.INFO)
        
        if not self.plugin_logger.handlers:
            handler = logging.FileHandler(str(plugin_log_file), encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.plugin_logger.addHandler(handler)
    
    def _log(self, level: str, message: str) -> None:
        '''Log a message.
        
        Args:
            level: Log level (info, error, warning)
            message: The message to log
        '''
        if level == 'error':
            self.plugin_logger.error(message)
        elif level == 'warning':
            self.plugin_logger.warning(message)
        else:
            self.plugin_logger.info(message)
    
    def _load_status(self) -> Dict[str, Dict[str, Any]]:
        '''Load plugin status from status file.'''
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_status(self) -> None:
        '''Save plugin status to status file.'''
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.plugin_status, f, ensure_ascii=False, indent=2)
    
    def load_plugins(self) -> None:
        '''Load all installed plugins.'''
        if not self.plugins_base_path.exists():
            self.plugins_base_path.mkdir(parents=True, exist_ok=True)
            return
        
        for item in self.plugins_base_path.iterdir():
            if not item.is_dir():
                continue
            
            info_path = item / 'info.json'
            if not info_path.exists():
                continue
            
            try:
                self._load_plugin(str(item))
            except Exception as e:
                self._log('error', f'Failed to load plugin {item.name}: {e}')
        
        self.loaded = True
    
    def _load_plugin(self, plugin_dir: str) -> None:
        '''Load a single plugin.
        
        Args:
            plugin_dir: Path to the plugin directory
        '''
        plugin_id = Path(plugin_dir).name
        
        info_path = Path(plugin_dir) / 'info.json'
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        entry = info.get('entry', 'main:Plugin')
        module_name, class_name = entry.split(':')
        
        sys.path.insert(0, plugin_dir)
        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            plugin_instance = plugin_class(self.app, plugin_dir)
            self.plugins[plugin_id] = plugin_instance
        finally:
            sys.path.remove(plugin_dir)
        
        status = self.plugin_status.get(plugin_id, {})
        if status.get('enabled', False):
            try:
                plugin_instance.enable()
                self._register_plugin_routes(plugin_instance)
                self._log('info', f'Plugin {plugin_id} loaded and enabled')
            except Exception as e:
                self._log('error', f'Failed to enable plugin {plugin_id}: {e}')
        else:
            self._log('info', f'Plugin {plugin_id} loaded (disabled)')
    
    def _register_plugin_routes(self, plugin) -> None:
        '''Register routes for an enabled plugin.
        
        Args:
            plugin: The plugin instance
        '''
        routes = plugin.get_routes()
        for route in routes:
            if len(route) == 2:
                pattern, handler = route
                kwargs = {}
            else:
                pattern, handler, kwargs = route
            self.app.add_handlers(r'.*$', [(pattern, handler, kwargs or {})])
    
    def get_plugin(self, plugin_id: str) -> Optional[Any]:
        '''Get a plugin instance by ID.
        
        Args:
            plugin_id: The plugin ID
        
        Returns:
            Plugin instance or None if not found.
        '''
        return self.plugins.get(plugin_id)
    
    def get_plugins_list(self) -> List[Dict[str, Any]]:
        '''Get list of all plugins with their metadata.
        
        Returns:
            List of plugin dictionaries.
        '''
        result = []
        for plugin_id, plugin in self.plugins.items():
            status = self.plugin_status.get(plugin_id, {})
            result.append({
                'id': plugin_id,
                'name': plugin.info.get('name', plugin_id),
                'version': plugin.info.get('version', '1.0.0'),
                'description': plugin.info.get('description', ''),
                'author': plugin.info.get('author', ''),
                'email': plugin.info.get('email', ''),
                'category': plugin.info.get('category', 'other'),
                'icon': plugin.info.get('icon', ''),
                'status': 'installed',
                'enabled': status.get('enabled', False),
                'install_time': status.get('install_time', '')
            })
        return result
    
    def install_plugin(self, url: str, version: Optional[str] = None) -> Dict[str, Any]:
        '''Install a plugin from URL.
        
        Args:
            url: Git repository URL or zip file URL
            version: Optional version tag/commit
        
        Returns:
            Dictionary with code, message, and data.
        '''
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                if url.endswith('.zip'):
                    zip_path = tmp_path / 'plugin.zip'
                    with urlopen(url) as response, open(zip_path, 'wb') as f:
                        f.write(response.read())
                    
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(tmp_dir)
                    
                    plugin_dir = os.listdir(tmp_dir)[0]
                    plugin_path = tmp_path / plugin_dir
                else:
                    import subprocess
                    plugin_dir = Path(url).name.replace('.git', '')
                    plugin_path = tmp_path / plugin_dir
                    subprocess.run(
                        ['git', 'clone', url, str(plugin_path)],
                        check=True,
                        capture_output=True
                    )
                
                info_path = plugin_path / 'info.json'
                if not info_path.exists():
                    self._log('error', f'Plugin missing info.json: {plugin_dir}')
                    return {
                        'code': -1,
                        'message': '插件缺少 info.json 文件'
                    }
                
                with open(info_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                
                plugin_id = info.get('id', plugin_dir)
                target_path = self.plugins_base_path / plugin_id
                
                if target_path.exists():
                    self._log('warning', f'Plugin already exists: {plugin_id}')
                    return {
                        'code': -1,
                        'message': f'插件 {plugin_id} 已存在'
                    }
                
                shutil.move(str(plugin_path), str(target_path))
                
                sys.path.insert(0, str(target_path))
                try:
                    entry = info.get('entry', 'main:Plugin')
                    module_name, class_name = entry.split(':')
                    module = importlib.import_module(module_name)
                    plugin_class = getattr(module, class_name)
                    plugin_instance = plugin_class(self.app, target_path)
                    
                    if plugin_instance.install():
                        self.plugins[plugin_id] = plugin_instance
                        self.plugin_status[plugin_id] = {
                            'version': info.get('version', '1.0.0'),
                            'enabled': False,
                            'install_time': self._get_current_time()
                        }
                        self._save_status()
                        
                        self._log('info', f'Plugin installed: {plugin_id} v{info.get("version", "1.0.0")}')
                        
                        return {
                            'code': 0,
                            'message': '安装成功',
                            'data': {
                                'id': plugin_id,
                                'name': info.get('name', plugin_id),
                                'version': info.get('version', '1.0.0')
                            }
                        }
                    else:
                        shutil.rmtree(target_path)
                        self._log('error', f'Plugin installation failed: {plugin_id}')
                        return {
                            'code': -1,
                            'message': '插件安装失败'
                        }
                finally:
                    sys.path.remove(target_path)
        
        except Exception as e:
            self._log('error', f'Plugin installation error: {e}')
            return {
                'code': -1,
                'message': f'安装失败: {str(e)}'
            }
    
    def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        '''Uninstall a plugin.
        
        Args:
            plugin_id: The plugin ID
        
        Returns:
            Dictionary with code and message.
        '''
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            self._log('warning', f'Plugin not found for uninstall: {plugin_id}')
            return {
                'code': -1,
                'message': f'插件 {plugin_id} 不存在'
            }
        
        try:
            plugin.disable()
            plugin.uninstall()
            
            plugin_dir = self.plugins_base_path / plugin_id
            shutil.rmtree(str(plugin_dir), ignore_errors=True)
            
            del self.plugins[plugin_id]
            if plugin_id in self.plugin_status:
                del self.plugin_status[plugin_id]
            self._save_status()
            
            self._log('info', f'Plugin uninstalled: {plugin_id}')
            
            return {
                'code': 0,
                'message': '卸载成功'
            }
        except Exception as e:
            self._log('error', f'Plugin uninstall error: {plugin_id} - {e}')
            return {
                'code': -1,
                'message': f'卸载失败: {str(e)}'
            }
    
    def toggle_plugin(self, plugin_id: str, enable: bool) -> Dict[str, Any]:
        '''Enable or disable a plugin.
        
        Args:
            plugin_id: The plugin ID
            enable: True to enable, False to disable
        
        Returns:
            Dictionary with code, message, and data.
        '''
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            self._log('warning', f'Plugin not found for toggle: {plugin_id}')
            return {
                'code': -1,
                'message': f'插件 {plugin_id} 不存在'
            }
        
        try:
            if enable:
                success = plugin.enable()
                if success:
                    plugin.enabled = True
                    if plugin_id not in self.plugin_status:
                        self.plugin_status[plugin_id] = {}
                    self.plugin_status[plugin_id]['enabled'] = True
                    self._register_plugin_routes(plugin)
                    self._save_status()
                    
                    self._log('info', f'Plugin enabled: {plugin_id}')
                    
                    return {
                        'code': 0,
                        'message': '启用成功',
                        'data': {'enabled': True}
                    }
                else:
                    self._log('error', f'Plugin enable failed: {plugin_id}')
                    return {
                        'code': -1,
                        'message': '启用失败'
                    }
            else:
                success = plugin.disable()
                if success:
                    plugin.enabled = False
                    if plugin_id not in self.plugin_status:
                        self.plugin_status[plugin_id] = {}
                    self.plugin_status[plugin_id]['enabled'] = False
                    self._save_status()
                    
                    self._log('info', f'Plugin disabled: {plugin_id}')
                    
                    return {
                        'code': 0,
                        'message': '禁用成功',
                        'data': {'enabled': False}
                    }
                else:
                    self._log('error', f'Plugin disable failed: {plugin_id}')
                    return {
                        'code': -1,
                        'message': '禁用失败'
                    }
        except Exception as e:
            self._log('error', f'Plugin toggle error: {plugin_id} - {e}')
            return {
                'code': -1,
                'message': f'操作失败: {str(e)}'
            }
    
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        '''Get plugin configuration.
        
        Args:
            plugin_id: The plugin ID
        
        Returns:
            Dictionary with code and data.
        '''
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return {
                'code': -1,
                'message': f'插件 {plugin_id} 不存在'
            }
        
        return {
            'code': 0,
            'data': plugin.config
        }
    
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        '''Save plugin configuration.
        
        Args:
            plugin_id: The plugin ID
            config: Configuration dictionary
        
        Returns:
            Dictionary with code and message.
        '''
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return {
                'code': -1,
                'message': f'插件 {plugin_id} 不存在'
            }
        
        try:
            plugin.save_config(config)
            self._log('info', f'Plugin config saved: {plugin_id}')
            return {
                'code': 0,
                'message': '配置保存成功'
            }
        except Exception as e:
            self._log('error', f'Plugin config save error: {plugin_id} - {e}')
            return {
                'code': -1,
                'message': f'保存失败: {str(e)}'
            }
    
    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        '''Get plugin metadata (info.json).
        
        Args:
            plugin_id: The plugin ID
        
        Returns:
            Dictionary with code and data.
        '''
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return {
                'code': -1,
                'message': f'插件 {plugin_id} 不存在'
            }
        
        return {
            'code': 0,
            'data': plugin.info
        }
    
    def _get_current_time(self) -> str:
        '''Get current time in ISO format.'''
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_plugin_routes(self) -> List[tuple]:
        '''Get all routes from enabled plugins.
        
        Returns:
            List of (pattern, handler_class, kwargs) tuples.
        '''
        routes = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                routes.extend(plugin.get_routes())
        return routes
    
    def get_plugin_logs(self, limit: int = 50) -> List[str]:
        '''Get recent plugin logs.
        
        Args:
            limit: Maximum number of log entries to return
        
        Returns:
            List of log entries.
        '''
        log_file = Path(self.logging_path) / 'plugins.log'
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return lines[-limit:]
        except:
            return []