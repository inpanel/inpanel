#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) < 1:
        print('''Usage: inpanel config <action> [section] [option] [value]

Actions:
  get   section option         Get config value
  set   section option value   Set config value
  list                         List all configs
  reset                        Reset to default config
  init                         Initialize config file

Examples:
  inpanel config get server port
  inpanel config set server port 14433
  inpanel config list
  inpanel config init''')
        sys.exit(1)

    from .base import config_file
    from .mod.config import load_config

    action = args[0]

    if action == 'init':
        Path(config_file).parent.mkdir(parents=True, exist_ok=True)
        config = load_config(config_file)
        print(f'Config file created at: {config_file}')
        sys.exit(0)

    if action == 'list':
        config = load_config(config_file)
        config_list = config.get_config_list()
        for sec in config_list:
            print(f'[{sec["section"]}]')
            for opt, val in sec['option'].items():
                print(f'  {opt} = {val}')
            print()
        sys.exit(0)

    if action == 'reset':
        config = load_config(config_file)
        for sec in config.get_section_list():
            config.remove_section(sec)
        config.update()
        config = load_config(config_file)
        print('Config reset to default')
        sys.exit(0)

    if len(args) < 3:
        print('Error: Missing arguments')
        sys.exit(1)

    section = args[1]
    option = args[2]

    config = load_config(config_file)

    if action == 'get':
        value = config.get(section, option)
        if value is not None:
            print(value)
        else:
            print(f'Error: Option "{option}" not found in section "{section}"')
            sys.exit(1)

    elif action == 'set':
        if len(args) < 4:
            print('Error: Missing value')
            sys.exit(1)
        value = args[3]
        result = config.set(section, option, value)
        if result:
            print(f'Successfully set {section}.{option} = {value}')
        else:
            print(f'Error: Failed to set {section}.{option}')
            sys.exit(1)

    else:
        print(f'Unknown action: {action}')
        sys.exit(1)


if __name__ == '__main__':
    main()