# InPanel

English | [简体中文](README-zh.md)

## Introduction

InPanel is an open source Linux server management tool, the goal of this project is to make server management easy and fast.

## Features

1. Free, concise, and open source
2. Fast in-line installation, small and resource-saving
3. Supports CentOS/Redhat 5.4+, 6.x, 7.x, 8.x
4. Software Management Mechanism Based on Distribution Software Source
5. Easily build Linux + Nginx + MySQL + PHP environments
6. Powerful online file management and recycle bin mechanism
7. Quickly create and install multiple sites
8. Useful System Tools

## Installation

```bash
# stable version
curl -O https://raw.githubusercontent.com/inpanel/inpanel/main/install.py
python install.py

# beta version
curl -O https://raw.githubusercontent.com/inpanel/inpanel/dev/install.py
python install.py --dev
```

## Uninstall

```bash
service inpanel stop
rm -rf /usr/local/inpanel
rm -f /etc/init.d/inpanel
```

## Admin Username and Password

```bash
/usr/local/inpanel/config.py username 'your-username'
/usr/local/inpanel/config.py password 'your-password'
```

## Issues

Please file an issue at [Issues](https://github.com/inpanel/inpanel/issues).

## License

InPanel is released under the [BSD 3-Clause License](./LICENSE).

## Author

[Jackson Dou](https://github.com/jksdou 'Jackson Dou')

## Information

Official Website: [inpanel.org](https://inpanel.org 'InPanel')
