#!/bin/bash

set -e

REPO_DIR="${REPO_DIR:-./repo}"
PACKAGE_DIR="${PACKAGE_DIR:-./packages}"
GPG_KEY_ID="${GPG_KEY_ID:-}"

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

check_dependencies() {
    info "Checking dependencies..."
    
    local missing=()
    
    if ! command -v createrepo_c &>/dev/null && ! command -v createrepo &>/dev/null; then
        missing+=("createrepo_c")
    fi
    
    if ! command -v reprepro &>/dev/null; then
        missing+=("reprepro")
    fi
    
    if ! command -v gpg &>/dev/null; then
        missing+=("gnupg")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        fail "Missing dependencies: ${missing[*]}"
    fi
    
    success "Dependencies check passed"
}

create_repo_structure() {
    info "Creating repository structure..."
    
    mkdir -p "$REPO_DIR/rpm"
    mkdir -p "$REPO_DIR/deb"
    mkdir -p "$REPO_DIR/gpg"
    mkdir -p "$PACKAGE_DIR/rpm"
    mkdir -p "$PACKAGE_DIR/deb"
    
    success "Repository structure created"
}

generate_gpg_key() {
    if [ -n "$GPG_KEY_ID" ] && ! gpg --list-secret-keys "$GPG_KEY_ID" &>/dev/null; then
        info "Generating GPG key..."
        
        cat > /tmp/gpg_keygen_batch << EOF
%echo Generating InPanel GPG key
Key-Type: RSA
Key-Length: 4096
Name-Real: InPanel Repository
Name-Email: repo@inpanel.org
Expire-Date: 0
%no-protection
%commit
%echo Done
EOF
        
        gpg --batch --gen-key /tmp/gpg_keygen_batch || fail "Failed to generate GPG key"
        rm -f /tmp/gpg_keygen_batch
        
        success "GPG key generated"
    elif [ -z "$GPG_KEY_ID" ]; then
        info "No GPG key ID specified, using existing key or skip signing"
    else
        success "GPG key already exists"
    fi
}

export_gpg_key() {
    info "Exporting GPG key..."
    
    if [ -n "$GPG_KEY_ID" ]; then
        gpg --armor --export "$GPG_KEY_ID" > "$REPO_DIR/gpg/inpanel.gpg.key" || fail "Failed to export GPG key"
        success "GPG key exported"
    else
        info "Skipping GPG key export (no key ID specified)"
    fi
}

build_rpm_repo() {
    info "Building RPM repository..."
    
    local rpm_dirs=$(find "$PACKAGE_DIR/rpm" -mindepth 1 -maxdepth 1 -type d)
    
    for dist_dir in $rpm_dirs; do
        local dist_name=$(basename "$dist_dir")
        local repo_path="$REPO_DIR/rpm/$dist_name"
        
        mkdir -p "$repo_path"
        
        cp "$dist_dir"/*.rpm "$repo_path/" 2>/dev/null || true
        
        local createrepo_cmd=$(command -v createrepo_c || command -v createrepo)
        
        if [ -n "$GPG_KEY_ID" ]; then
            "$createrepo_cmd" --gpg-key "$GPG_KEY_ID" "$repo_path" || fail "Failed to create RPM repo for $dist_name"
        else
            "$createrepo_cmd" "$repo_path" || fail "Failed to create RPM repo for $dist_name"
        fi
        
        success "Built RPM repo for $dist_name"
    done
    
    success "RPM repository built"
}

build_deb_repo() {
    info "Building DEB repository..."
    
    mkdir -p "$REPO_DIR/deb/conf"
    
    cat > "$REPO_DIR/deb/conf/distributions" << EOF
Origin: InPanel
Label: InPanel
Suite: stable
Codename: buster
Version: 1.0
Architectures: all source
Components: main
Description: InPanel Debian/Ubuntu Repository
SignWith: $GPG_KEY_ID
EOF
    
    cat > "$REPO_DIR/deb/conf/options" << EOF
verbose
basedir .
EOF
    
    local deb_dirs=$(find "$PACKAGE_DIR/deb" -mindepth 1 -maxdepth 1 -type d)
    
    for dist_dir in $deb_dirs; do
        local dist_name=$(basename "$dist_dir")
        
        for deb_file in "$dist_dir"/*.deb; do
            [ -f "$deb_file" ] || continue
            
            if [ -n "$GPG_KEY_ID" ]; then
                reprepro -b "$REPO_DIR/deb" -C main includedeb "$dist_name" "$deb_file" || fail "Failed to add DEB: $deb_file"
            else
                reprepro -b "$REPO_DIR/deb" --noskipold -C main includedeb "$dist_name" "$deb_file" || fail "Failed to add DEB: $deb_file"
            fi
        done
        
        success "Added DEBs for $dist_name"
    done
    
    success "DEB repository built"
}

main() {
    check_dependencies
    create_repo_structure
    generate_gpg_key
    export_gpg_key
    build_rpm_repo
    build_deb_repo
    
    echo ""
    echo "============================================="
    echo "          Repository Build Complete"
    echo "============================================="
    echo ""
    echo "Repository location: $REPO_DIR"
    echo ""
    echo "To serve the repository, use:"
    echo "  python3 -m http.server 8000 --directory $REPO_DIR"
    echo ""
    echo "Or upload to your web server and set REPO_URL in install_repo.sh"
    echo ""
}

main "$@"