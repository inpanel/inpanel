# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
"""Services configuration data loader.

面板支持的服务分类、服务详情（配置文件、路径、日志、包管理等）
均通过此目录下的 JSON 配置文件定义。

目录结构：
    templates/services/
        __init__.py          # 加载器
        _common.json         # 公共配置（custom_categories, package_manager_priority）
        categories.json      # 服务分类定义
        http.json            # HTTP 分类服务列表
        ftp.json             # FTP 分类服务列表
        database.json        # 数据库分类服务列表
        ...                  # 每个分类一个独立 JSON 文件

用户自定义服务配置保存在：
    <data_path>/services.json
"""

import json
import os

from inpanel.base import config_path

_cache = {}


def _load_json(filename):
    """Load a JSON config file with caching."""
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.isfile(path):
        _cache[filename] = None
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _cache[filename] = data
    return data


def load_services():
    """加载全部服务配置（内置分类文件 + 公共配置 + 用户自定义合并）

    从 categories.json 获取分类列表，逐一加载 {category_id}.json，
    与 _common.json 合并后返回完整配置。
    """
    if 'services' in _cache:
        return _cache['services']

    categories_config = _load_json('categories.json')
    common = _load_json('_common.json') or {}

    # 从分类文件加载各分类的服务列表
    categories = []
    for cat_def in categories_config or []:
        cat_id = cat_def['id']
        services = _load_json(f'{cat_id}.json') or []
        categories.append({
            'id': cat_id,
            'name': cat_def['name'],
            'services': services,
        })

    result = {
        'categories': categories,
        'custom_categories': common.get('custom_categories', {}),
        'package_manager_priority': common.get('package_manager_priority', {}),
    }

    # 加载用户自定义服务分类
    user_config = os.path.join(str(config_path), 'services.json')
    if os.path.isfile(user_config):
        try:
            with open(user_config, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            if isinstance(user_data, dict) and 'custom_categories' in user_data:
                result['custom_categories'] = user_data['custom_categories']
        except (json.JSONDecodeError, IOError):
            pass

    _cache['services'] = result
    return result


def load_categories():
    """加载服务分类定义"""
    return _load_json('categories.json')


def save_user_custom_categories(custom_categories):
    """保存用户自定义服务分类到 data_path/services.json"""
    user_config = os.path.join(str(config_path), 'services.json')
    conf_dir = os.path.dirname(user_config)
    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir, exist_ok=True)

    # 读取已有内容
    existing = {}
    if os.path.isfile(user_config):
        try:
            with open(user_config, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    existing['custom_categories'] = custom_categories
    with open(user_config, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


__all__ = [
    'load_services',
    'load_categories',
    'save_user_custom_categories',
]
