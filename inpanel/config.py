#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from pathlib import Path


def _init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - config.py - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    logger = _init_logging()

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
    logger.info(f'Config action: {action}')

    if action == 'init':
        logger.info(f'Initializing config file at: {config_file}')
        Path(config_file).parent.mkdir(parents=True, exist_ok=True)
        config = load_config(config_file)
        logger.info(f'Config file created successfully')
        print(f'Config file created at: {config_file}')
        sys.exit(0)

    if action == 'list':
        logger.info('Listing all configurations')
        config = load_config(config_file)
        config_list = config.get_config_list()
        sections = [sec['section'] for sec in config_list]
        logger.info(f'Found {len(sections)} sections: {sections}')
        for sec in config_list:
            print(f'[{sec["section"]}]')
            for opt, val in sec['option'].items():
                display_val = '***HIDDEN***' if opt == 'password' else val
                print(f'  {opt} = {display_val}')
            print()
        sys.exit(0)

    if action == 'reset':
        logger.info('Resetting config to default')
        config = load_config(config_file)
        for sec in config.get_section_list():
            config.remove_section(sec)
        config.update()
        config = load_config(config_file)
        logger.info('Config reset completed')
        print('Config reset to default')
        sys.exit(0)

    if len(args) < 3:
        logger.error('Missing arguments for get/set action')
        print('Error: Missing arguments')
        sys.exit(1)

    section = args[1]
    option = args[2]

    logger.info(f'Processing {action} action for [{section}].{option}')

    config = load_config(config_file)

    if action == 'get':
        value = config.get(section, option)
        if value is not None:
            display_val = '***HIDDEN***' if option == 'password' else value
            logger.info(f'Got [{section}].{option} = {display_val}')
            print(value)
        else:
            logger.error(f'Option "{option}" not found in section "{section}"')
            print(f'Error: Option "{option}" not found in section "{section}"')
            sys.exit(1)

    elif action == 'set':
        if len(args) < 4:
            logger.error('Missing value for set action')
            print('Error: Missing value')
            sys.exit(1)
        value = args[3]
        
        if section == 'auth' and option == 'password':
            logger.info('Setting auth.password, generating hash')
            from hashlib import md5
            from hmac import new as hmac_new
            from .utils import randstr
            key = md5(randstr().encode('utf-8')).hexdigest()
            pwd = hmac_new(key.encode('utf-8'), value.encode('utf-8'), md5).hexdigest()
            value = '%s:%s' % (pwd, key)
            logger.info(f'Password hash generated, key length: {len(key)}, hash length: {len(pwd)}')
        
        result = config.set(section, option, value)
        if result:
            display_val = '***HIDDEN***' if option == 'password' else value
            logger.info(f'Successfully set [{section}].{option} = {display_val}')
            print(f'Successfully set {section}.{option}')
        else:
            logger.error(f'Failed to set [{section}].{option}')
            print(f'Error: Failed to set {section}.{option}')
            sys.exit(1)

    else:
        logger.error(f'Unknown action: {action}')
        print(f'Unknown action: {action}')
        sys.exit(1)


if __name__ == '__main__':
    main()