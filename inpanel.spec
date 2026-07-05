%define name inpanel
%define version 1.2.27
%define release 1
%define arch noarch
%define summary InPanel - A Web-based Linux Server Management Tool
%define desc InPanel is a web-based Linux server management tool

Name: %{name}
Version: %{version}
Release: %{release}
Summary: %{summary}
License: BSD
URL: https://inpanel.org/
Group: System/Administration
BuildArch: %{arch}
BuildRequires: python3-devel python3-setuptools python3-wheel
Requires: python3 >= 3.7 python3-tornado python3-psutil python3-pexpect python3-cryptography

%description
%{desc}

%prep
%autosetup -p1

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
mkdir -p %{buildroot}/usr/lib/systemd/system
mkdir -p %{buildroot}/etc/init.d
mkdir -p %{buildroot}/var/log/inpanel

cat > %{buildroot}/usr/lib/systemd/system/inpanel.service << 'EOF'
[Unit]
Description=InPanel Control Panel
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/inpanel run
ExecStop=/usr/bin/inpanel stop
ExecReload=/usr/bin/inpanel reload
PIDFile=/var/run/inpanel.pid
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > %{buildroot}/etc/init.d/inpanel << 'EOF'
#!/bin/bash
# chkconfig: 2345 99 01
# description: InPanel Control Panel

PROG="inpanel"
PROG_PATH="/usr/bin/inpanel"

case "$1" in
    start|stop|status|restart|reload)
        $PROG_PATH $1
        ;;
    config)
        shift
        $PROG_PATH config "$@"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|reload|config}"
        exit 1
        ;;
esac

exit 0
EOF

chmod 755 %{buildroot}/etc/init.d/inpanel

%pre
if [ $1 -eq 1 ]; then
    mkdir -p /var/log/inpanel
    mkdir -p /etc/inpanel
fi

%post
if [ $1 -eq 1 ]; then
    if [ -d /etc/systemd/system ]; then
        systemctl daemon-reload
        systemctl enable inpanel
    else
        chkconfig --add inpanel
        chkconfig inpanel on
    fi
fi

%preun
if [ $1 -eq 0 ]; then
    if [ -d /etc/systemd/system ]; then
        systemctl stop inpanel
        systemctl disable inpanel
    else
        /etc/init.d/inpanel stop
        chkconfig --del inpanel
    fi
fi

%files
%defattr(-,root,root)
/usr/bin/inpanel
%{python3_sitelib}/inpanel*
/usr/lib/systemd/system/inpanel.service
/etc/init.d/inpanel
%dir /var/log/inpanel

%changelog
* Wed Jul 05 2026 Jackson Dou <jksdou@qq.com> - 1.2.27-1
- Initial release