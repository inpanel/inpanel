# -*- coding: utf-8 -*-
#
# Copyright (c) 2020-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of The New BSD License.
# The full license can be found in 'LICENSE'.
"""Sources configuration data loader.

All configuration data for package/repository management is stored as JSON files
in this directory. This module provides helpers to load them.

Loading failures will raise exceptions – there is no hardcoded fallback.
"""

import json
import os

_cache = {}


def _load_json(filename):
    """Load a JSON config file with caching.

    Raises FileNotFoundError if the JSON file is missing,
    or json.JSONDecodeError if the file content is invalid.
    """
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _cache[filename] = data
    return data


def load_apt():
    """Load APT configuration data from apt.json."""
    return _load_json('apt.json')


def load_dnf():
    """Load DNF configuration data from dnf.json."""
    return _load_json('dnf.json')


def load_yum():
    """Load YUM configuration data from yum.json."""
    return _load_json('yum.json')


def load_brew():
    """Load Homebrew configuration data from brew.json."""
    return _load_json('brew.json')


def load_pip():
    """Load pip configuration data from pip.json."""
    return _load_json('pip.json')


def load_package_map():
    """Load package name mapping configuration from package_map.json."""
    return _load_json('package_map.json')


def load_docker():
    """Load Docker registry mirror configuration from docker.json."""
    return _load_json('docker.json')


def load_third_party():
    """Load third-party sources configuration from third_party.json."""
    return _load_json('third_party.json')
