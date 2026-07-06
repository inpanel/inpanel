# InPanel

English | [简体中文](README.md)

> InPanel is a lightweight, non-intrusive Linux system-level operation and maintenance management panel, dedicated to achieving efficient and secure server administration through a Web interface.
>
> Backend written in Python, based on the Tornado asynchronous framework, licensed under [BSD 3-Clause](https://github.com/inpanel/inpanel/blob/main/LICENSE). Project started on Jan 11, 2017, continuously maintained to this day.

Official Website: [inpanel.org](https://inpanel.org 'InPanel')

PyPI: [inpanel](https://pypi.org/project/inpanel/ 'PyPI')

Author: [Jackson Dou](https://github.com/jksdou 'Jackson Dou')

## Features

### Core Advantages

- **System-level Administration**: Directly operates system-native configuration files (`/etc/passwd`, Nginx vhost, firewall rules, etc.), no intermediate layer dependency
- **Ultra-low Intrusion**: Pure UI-level management, no modification to system core architecture, clean uninstall with no residual dependencies
- **Lightweight & Efficient**: Memory footprint only 30-40MB, minimal resource consumption, ideal for VPS/lightweight server environments
- **Full-featured & Free**: Open source BSD license, all features available without restrictions or paywalls

### System Management

- User and permission management (system users, SSH keys, sudo permissions)
- Process management and monitoring (process viewing, termination, resource statistics)
- Service management (systemd/init.d service start/stop, autostart configuration)
- Firewall management (iptables/firewalld rule configuration)

### Website Operations

- Nginx virtual host management (configuration, SSL, redirection)
- Apache HTTP Server management (virtual hosts, module configuration)
- PHP environment management (version switching, configuration adjustment)
- MySQL/MariaDB management (databases, users, permissions)
- FTP service management (vsftpd configuration, user management)

### File Management

- Powerful online file manager (upload, download, edit, compress)
- Recycle bin mechanism (recover accidentally deleted files)
- File permission management (chmod, chown)
- Remote file management (SSH connection to other servers)

### System Tools

- System resource monitoring (CPU, memory, disk, network)
- Package management (YUM/DNF/APT package management)
- Scheduled tasks (Crontab management)
- System updates (automatic update detection and installation)
- SSL certificate management (Let's Encrypt auto-issuance)

### Compatibility

- CentOS/RHEL 7+, Debian 10+, Ubuntu 18.04+
- Python 3.6+ (compatible up to Python 3.14)

## Version Compatibility

| Python Version | Status |
|----------------|--------|
| Python 3.6 | ✅ Compatible |
| Python 3.7+ | ✅ Compatible |
| Python 3.12-3.14 | ✅ Compatible (requires tornado>=6.5) |
| Python 3.5 and below | ❌ Not supported |

## Installation

### Method 1: Install via pip

```bash
pip install inpanel
```

### Method 2: Install via package manager

#### CentOS / RHEL

```bash
# CentOS 8+ / RHEL 8+
dnf install inpanel

# CentOS 7 / RHEL 7
yum install inpanel
```

#### Debian / Ubuntu

```bash
apt-get update
apt-get install inpanel
```

### Method 3: Install from source

```bash
git clone https://github.com/inpanel/inpanel.git
cd inpanel
pip install -e .
```

## Service Management

```bash
# Start service (background)
inpanel start

# Stop service
inpanel stop

# Check status
inpanel status

# Restart service
inpanel restart

# Run in foreground (for debugging)
inpanel run
```

## Configuration

### List all configurations

```bash
inpanel config list
```

### Change username and password

```bash
inpanel config set auth username 'your-username'
inpanel config set auth password 'your-password'
```

### Modify configuration

```bash
# Set config value
inpanel config set <section> <option> <value>

# Get config value
inpanel config get <section> <option>

# Reset to default
inpanel config reset
```

## Uninstall

### Method 1: Official uninstall command (Recommended)

```bash
# Default uninstall (keep config and logs)
inpanel uninstall

# Complete uninstall (remove config and logs)
inpanel uninstall --purge

# Remove config files only
inpanel uninstall --purge-config

# Remove log files only
inpanel uninstall --purge-logs
```

### Method 2: Uninstall via package manager

#### Installed via pip

```bash
inpanel stop
pip uninstall inpanel
rm -rf /etc/inpanel
rm -rf /var/log/inpanel
```

#### Installed via RPM (CentOS/RHEL)

```bash
yum remove inpanel
# or for complete removal:
# yum erase inpanel
```

#### Installed via DEB (Debian/Ubuntu)

```bash
apt-get remove inpanel
# or for complete removal:
# apt-get purge inpanel
```

### Method 3: Manual uninstall

```bash
inpanel stop
pip uninstall inpanel
rm -rf /etc/inpanel
rm -rf /var/log/inpanel
rm -f /usr/lib/systemd/system/inpanel.service
rm -f /etc/init.d/inpanel
```

### Uninstallation Notes

InPanel adopts a **non-intrusive architecture design**, with all operations based on system-native configuration files. After uninstallation, the following characteristics apply:

| Feature | Description |
|---------|-------------|
| **No Residual Dependencies** | Uninstallation only removes InPanel components, no impact on existing system packages |
| **Configuration Files Preserved** | Default uninstall keeps config files (`/etc/inpanel/`), facilitating configuration recovery after reinstallation |
| **System Services Unaffected** | Services configured via InPanel (Nginx, MySQL, PHP, etc.) continue to operate normally |
| **User Data Safe** | Website files, databases, and other user data remain unaffected |
| **Clean Process Exit** | Automatically stops InPanel service and cleans PID files before uninstallation |

**System State After Uninstallation**:

- System user configurations (`/etc/passwd`, `/etc/group`) remain unchanged
- Nginx vhost configurations, firewall rules remain unchanged
- Installed packages (Nginx, MySQL, PHP, etc.) remain unchanged
- Only InPanel service process, configuration directory, and log files are removed

> **Tip**: Use `inpanel uninstall --purge` for complete data cleanup if needed.

## Admin Username and Password

Default username: `admin`

Default password: `admin`

Change password after first login:

```bash
inpanel config set auth password 'new-password'
```

## Local Development

### Environment Requirements

- Python 3.6+
- pip 20.0+

### Development Steps

```bash
# 1. Clone repository
git clone https://github.com/inpanel/inpanel.git
cd inpanel

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies in development mode
pip install -e .

# 4. Start development server (foreground, with hot reload)
inpanel run
```

### Development Mode Features

- Config files located in `data/` folder of project directory
- Log files located in `data/` folder of project directory
- Code changes take effect immediately without reinstallation
- DEBUG mode enabled by default

### Build Packages

```bash
# Build pip package
pip install build
python -m build

# Build RPM package (requires rpmbuild)
rpmbuild -bb rpmbuild.spec

# Build DEB package (requires debuild)
debuild -us -uc
```

## License

This project is licensed under the BSD license. The full license text can be found in the [LICENSE](https://github.com/inpanel/inpanel/blob/main/LICENSE) file.
