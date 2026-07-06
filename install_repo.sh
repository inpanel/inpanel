#!/bin/bash

set -e

REPO_URL="https://inpanel.github.io/repo.inpanel.org"
GPG_KEY_URL="$REPO_URL/gpg/inpanel.gpg.key"
GPG_KEY_ID="InPanel Repository"

OK='\033[1;32mOK\033[0m'
FAILED='\033[1;31mFAILED\033[0m'
INFO='\033[1;34mINFO\033[0m'

info() {
    echo -e "[$INFO] $1"
}

success() {
    echo -e "[$OK] $1"
}

fail() {
    echo -e "[$FAILED] $1"
    exit 1
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        CODENAME=${VERSION_CODENAME:-$(echo $VERSION | tr '.' '-')}
    elif [ -f /etc/redhat-release ]; then
        OS=$(cat /etc/redhat-release | grep -oE '(CentOS|Red Hat|Fedora)' | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
        VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
        CODENAME=""
    else
        fail "Cannot detect operating system"
    fi
}

install_dependencies() {
    info "Installing dependencies..."
    if [ "$OS" = "centos" ] || [ "$OS" = "redhat" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        if command -v dnf &>/dev/null; then
            dnf install -y curl wget
        else
            yum install -y curl wget
        fi
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt-get update
        apt-get install -y curl wget apt-transport-https ca-certificates
    else
        fail "Unsupported operating system: $OS"
    fi
}

import_gpg_key() {
    info "Importing GPG key..."
    mkdir -p /etc/pki/rpm-gpg /etc/apt/trusted.gpg.d

    if [ -f /etc/pki/rpm-gpg/RPM-GPG-KEY-inpanel ]; then
        rm -f /etc/pki/rpm-gpg/RPM-GPG-KEY-inpanel
    fi

    curl -fsSL "$GPG_KEY_URL" -o /etc/pki/rpm-gpg/RPM-GPG-KEY-inpanel || fail "Failed to download GPG key"

    if [ "$OS" = "centos" ] || [ "$OS" = "redhat" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-inpanel || fail "Failed to import GPG key"
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        gpg --dearmor -o /etc/apt/trusted.gpg.d/inpanel.gpg /etc/pki/rpm-gpg/RPM-GPG-KEY-inpanel || fail "Failed to import GPG key"
    fi

    success "GPG key imported"
}

configure_yum_repo() {
    info "Configuring YUM repository..."
    
    REPO_FILE="/etc/yum.repos.d/inpanel.repo"
    
    cat > "$REPO_FILE" << EOF
[inpanel]
name=InPanel Repository
baseurl=$REPO_URL/rpm/\$releasever/\$basearch/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-inpanel
EOF

    if command -v dnf &>/dev/null; then
        dnf makecache || fail "Failed to update yum cache"
    else
        yum makecache || fail "Failed to update yum cache"
    fi

    success "YUM repository configured"
}

configure_apt_repo() {
    info "Configuring APT repository..."
    
    APT_SOURCES_DIR="/etc/apt/sources.list.d"
    REPO_FILE="$APT_SOURCES_DIR/inpanel.sources"
    
    mkdir -p "$APT_SOURCES_DIR"
    
    cat > "$REPO_FILE" << EOF
Types: deb
URIs: $REPO_URL/deb
Suites: $CODENAME
Components: main
Signed-By: /etc/apt/trusted.gpg.d/inpanel.gpg
EOF

    apt-get update || fail "Failed to update apt cache"

    success "APT repository configured"
}

install_inpanel() {
    info "Installing InPanel..."
    
    if [ "$OS" = "centos" ] || [ "$OS" = "redhat" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        if command -v dnf &>/dev/null; then
            dnf install -y inpanel || fail "Failed to install inpanel"
        else
            yum install -y inpanel || fail "Failed to install inpanel"
        fi
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt-get install -y inpanel || fail "Failed to install inpanel"
    fi

    success "InPanel installed successfully"
}

start_service() {
    info "Starting InPanel service..."
    
    if [ -d /etc/systemd/system ]; then
        systemctl daemon-reload
        systemctl start inpanel || fail "Failed to start inpanel service"
        systemctl enable inpanel || info "Failed to enable inpanel service"
    else
        /etc/init.d/inpanel start || fail "Failed to start inpanel service"
    fi

    success "InPanel service started"
}

show_info() {
    echo ""
    echo "============================================="
    echo "          InPanel Installation Complete"
    echo "============================================="
    echo ""
    echo "URL: http://$(curl -s ifconfig.me):14433"
    echo "Username: admin"
    echo "Password: admin"
    echo ""
    echo "You can change the password using:"
    echo "  inpanel config set auth password <new_password>"
    echo "  inpanel config set auth username <new_username>"
    echo ""
}

main() {
    if [ "$(id -u)" != "0" ]; then
        fail "This script must be run as root"
    fi

    info "Detecting operating system..."
    detect_os
    success "Detected: $OS $VERSION"

    install_dependencies
    import_gpg_key

    if [ "$OS" = "centos" ] || [ "$OS" = "redhat" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        configure_yum_repo
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        configure_apt_repo
    else
        fail "Unsupported operating system: $OS"
    fi

    install_inpanel
    start_service
    show_info
}

main "$@"