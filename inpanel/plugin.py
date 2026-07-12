# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.

'''Plugin Framework for InPanel.'''

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Callable


_hooks: Dict[str, List[Callable]] = {}


def hook(name: str) -> Callable:
    '''Decorator to register an event hook.
    
    Example:
        @hook('service.start')
        def on_service_start(service_name):
            pass
    '''
    def decorator(func: Callable) -> Callable:
        if name not in _hooks:
            _hooks[name] = []
        _hooks[name].append(func)
        return func
    return decorator


def trigger_hook(name: str, **kwargs) -> None:
    '''Trigger all hooks registered for the given event name.
    
    Args:
        name: The hook name to trigger
        **kwargs: Arguments to pass to hook functions
    '''
    if name in _hooks:
        for func in _hooks[name]:
            try:
                func(**kwargs)
            except Exception as e:
                import logging
                logging.error(f'Hook {name} failed: {e}')


class PluginBase:
    '''Base class for all InPanel plugins.
    
    All plugins must inherit from this class and implement required methods.
    
    Attributes:
        app: The InPanel application instance
        name: The plugin ID (should match directory name)
        info: Parsed info.json data
        config: Plugin configuration
    '''
    
    def __init__(self, app: Any, plugin_dir: str) -> None:
        '''Initialize plugin.
        
        Args:
            app: The InPanel application instance
            plugin_dir: Path to the plugin directory
        '''
        self.app = app
        self.plugin_dir = plugin_dir
        self.name = Path(plugin_dir).name
        self.info = self._load_info()
        self.config = self._load_config()
        self.enabled = False
    
    def _load_info(self) -> Dict[str, Any]:
        '''Load plugin metadata from info.json.'''
        info_path = Path(self.plugin_dir) / 'info.json'
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_config(self) -> Dict[str, Any]:
        '''Load plugin configuration.
        
        Configuration is loaded with priority:
        1. Plugin directory default_config.json (default)
        2. Plugin directory config.json (user config)
        3. Environment variables
        '''
        config = {}
        
        default_config = Path(self.plugin_dir) / 'default_config.json'
        if default_config.exists():
            with open(default_config, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        
        user_config = Path(self.plugin_dir) / 'config.json'
        if user_config.exists():
            with open(user_config, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        
        env_prefix = f'INPANEL_PLUGIN_{self.name.upper()}_'
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                config[config_key] = value
        
        return config
    
    def install(self) -> bool:
        '''Install the plugin.
        
        Called when the plugin is first installed.
        Should handle:
        - Installing dependencies
        - Creating necessary directories
        - Initializing database tables
        
        Returns:
            True if installation succeeded, False otherwise.
        '''
        return True
    
    def uninstall(self) -> bool:
        '''Uninstall the plugin.
        
        Called when the plugin is uninstalled.
        Should handle:
        - Removing created files/directories
        - Cleaning up database tables
        
        Returns:
            True if uninstallation succeeded, False otherwise.
        '''
        return True
    
    def enable(self) -> bool:
        '''Enable the plugin.
        
        Called when the plugin is enabled.
        Should handle:
        - Registering routes
        - Registering event hooks
        - Starting background tasks
        
        Returns:
            True if enabling succeeded, False otherwise.
        '''
        self.enabled = True
        return True
    
    def disable(self) -> bool:
        '''Disable the plugin.
        
        Called when the plugin is disabled.
        Should handle:
        - Stopping background tasks
        - Cleaning up resources
        
        Returns:
            True if disabling succeeded, False otherwise.
        '''
        self.enabled = False
        return True
    
    def get_routes(self) -> List[tuple]:
        '''Return custom API routes (Tornado Handler list).
        
        Returns:
            List of (pattern, handler_class, kwargs) tuples.
        '''
        return []
    
    def get_menu(self) -> Optional[Dict[str, str]]:
        '''Return menu item configuration.
        
        Returns:
            Dictionary with name, icon, path, parent keys, or None.
        '''
        return None
    
    def save_config(self, config: Dict[str, Any]) -> None:
        '''Save plugin configuration.
        
        Args:
            config: Configuration dictionary to save.
        '''
        self.config.update(config)
        
        user_config_path = Path(self.plugin_dir) / 'config.json'
        with open(user_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_config_schema(self) -> Dict[str, Any]:
        '''Return configuration schema for form generation.
        
        Returns:
            config_schema from info.json or empty dict.
        '''
        return self.info.get('config_schema', {})
