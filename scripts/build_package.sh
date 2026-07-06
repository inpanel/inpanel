#!/bin/bash

set -e

SOURCE_DIR="${SOURCE_DIR:-$(dirname "$(readlink -f "$0")")/..}"
BUILD_DIR="${BUILD_DIR:-./build}"
PACKAGE_DIR="${PACKAGE_DIR:-./packages}"

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
    info "Checking build dependencies..."
    
    local missing=()
    
    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi
    
    if ! command -v pip3 &>/dev/null; then
        missing+=("pip3")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        fail "Missing dependencies: ${missing[*]}"
    fi
    
    success "Dependencies check passed"
}

create_build_structure() {
    info "Creating build structure..."
    
    mkdir -p "$BUILD_DIR"
    mkdir -p "$PACKAGE_DIR/rpm"
    mkdir -p "$PACKAGE_DIR/deb"
    
    success "Build structure created"
}

build_sdist() {
    info "Building source distribution..."
    
    cd "$SOURCE_DIR"
    
    if [ -f pyproject.toml ]; then
        python3 -m build --sdist --outdir "$BUILD_DIR" || fail "Failed to build source distribution"
    else
        python3 setup.py sdist --dist-dir "$BUILD_DIR" || fail "Failed to build source distribution"
    fi
    
    SDIST_FILE=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$SDIST_FILE" ] || fail "Source distribution file not found"
    
    success "Source distribution built: $(basename "$SDIST_FILE")"
}

build_rpm() {
    info "Building RPM package..."
    
    local sdist_file=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$sdist_file" ] || fail "Source distribution file not found"
    
    local rpmbuild_dir="$BUILD_DIR/rpmbuild"
    mkdir -p "$rpmbuild_dir/SOURCES" "$rpmbuild_dir/SPECS" "$rpmbuild_dir/RPMS" "$rpmbuild_dir/SRPMS"
    
    cp "$sdist_file" "$rpmbuild_dir/SOURCES/"
    
    if [ -f "$SOURCE_DIR/inpanel.spec" ]; then
        cp "$SOURCE_DIR/inpanel.spec" "$rpmbuild_dir/SPECS/"
        rpmbuild --define "_topdir $rpmbuild_dir" -ba "$rpmbuild_dir/SPECS/inpanel.spec" || fail "Failed to build RPM"
    else
        fail "RPM spec file not found"
    fi
    
    cp "$rpmbuild_dir/RPMS"/*/*.rpm "$PACKAGE_DIR/rpm/" 2>/dev/null || true
    cp "$rpmbuild_dir/SRPMS"/*.rpm "$PACKAGE_DIR/rpm/" 2>/dev/null || true
    
    success "RPM package built"
}

build_deb() {
    info "Building DEB package..."
    
    local sdist_file=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$sdist_file" ] || fail "Source distribution file not found"
    
    local deb_build_dir="$BUILD_DIR/deb"
    mkdir -p "$deb_build_dir"
    
    cd "$deb_build_dir"
    tar xzf "$sdist_file" || fail "Failed to extract source"
    
    local pkg_dir=$(find . -maxdepth 1 -type d -name 'inpanel-*' | head -1)
    [ -d "$pkg_dir" ] || fail "Package directory not found after extraction"
    
    cd "$pkg_dir"
    
    if [ -d "$SOURCE_DIR/debian" ]; then
        cp -r "$SOURCE_DIR/debian" .
    else
        fail "Debian directory not found"
    fi
    
    local version=$(grep '^version =' "$SOURCE_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
    
    cat > debian/changelog << EOF
inpanel (${version}-1) unstable; urgency=medium

  * Build from pyproject.toml version ${version}

 -- Jackson Dou <jksdou@qq.com>  $(date -R)
EOF
    
    dpkg-buildpackage -b -us -uc || fail "Failed to build DEB"
    
    cd "$deb_build_dir"
    cp *.deb "$PACKAGE_DIR/deb/" 2>/dev/null || true
    
    success "DEB package built"
}

main() {
    check_dependencies
    create_build_structure
    build_sdist
    
    if command -v rpmbuild &>/dev/null; then
        build_rpm
    else
        info "rpmbuild not found, skipping RPM build"
    fi
    
    if command -v dpkg-buildpackage &>/dev/null; then
        build_deb
    else
        info "dpkg-buildpackage not found, skipping DEB build"
    fi
    
    echo ""
    echo "============================================="
    echo "          Package Build Complete"
    echo "============================================="
    echo ""
    echo "Packages location: $PACKAGE_DIR"
    echo ""
    echo "RPM packages:"
    ls -la "$PACKAGE_DIR/rpm/" 2>/dev/null || echo "  (none)"
    echo ""
    echo "DEB packages:"
    ls -la "$PACKAGE_DIR/deb/" 2>/dev/null || echo "  (none)"
    echo ""
}

main "$@"