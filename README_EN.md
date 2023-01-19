# InPanel

> The goal of this project is to make the easiest, fastest, and most painless way of Linux VPS management. This project has been forked from VPSMate since 11 Jan 2017 but changed a lot.

Official Website: [inpanel.org](https://inpanel.org 'InPanel')

Author: [Jackson Dou](https://github.com/jksdou 'Jackson Dou')

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
rm -rf /usr/local/inpanel/inpaneld
rm -rf /usr/local/bin/inpanel
rm -rf /usr/local/bin/inpanel-config
rm -rf /usr/local/bin/inpanel-uninstall
rm -f /etc/init.d/inpanel
```

## Admin Username and Password

```bash
inpanel config username 'your-username'
inpanel config password 'your-password'
```
