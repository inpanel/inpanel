#!/bin/bash
#
# DEB 包构建脚本
# 用法：./build_deb.sh [SOURCE_DIR] [BUILD_DIR] [PACKAGE_DIR]
#

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SOURCE_DIR="$(readlink -f "${1:-$SCRIPT_DIR/..}")"
BUILD_DIR="$(readlink -f "${2:-$SOURCE_DIR/build}")"
PACKAGE_DIR="$(readlink -f "${3:-$SOURCE_DIR/packages}")"

OK='\033[1;32mOK\033[0m'
FAILED='\033[1;31mFAILED\033[0m'
INFO='\033[1;34mINFO\033[0m'

info()    { echo -e "[$INFO] $1"; }
success() { echo -e "[$OK] $1"; }
fail()    { echo -e "[$FAILED] $1"; exit 1; }

RESULT=0
RESULT_MSG=""
DEB_FILES=""

check_dependencies() {
    info "检查构建依赖..."
    local missing=()

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi
    if ! command -v dpkg-buildpackage &>/dev/null; then
        missing+=("dpkg-buildpackage")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        fail "缺少依赖: ${missing[*]}"
    fi
    success "依赖检查通过"
}

clean_build_dirs() {
    info "清理旧的构建产物..."
    rm -rf "$BUILD_DIR/deb"
    rm -rf "$PACKAGE_DIR/deb"
    success "已清理 build/deb 和 packages/deb"
}

build_sdist() {
    info "构建源码分发包..."
    cd "$SOURCE_DIR"

    if python3 -c 'import build.env' 2>/dev/null; then
        python3 -m build --sdist --outdir "$BUILD_DIR" || fail "源码分发包构建失败"
    elif [ -f setup.py ]; then
        python3 setup.py sdist --dist-dir "$BUILD_DIR" || fail "源码分发包构建失败"
    else
        fail "未找到 python-build 包且无 setup.py，无法构建源码分发包"
    fi

    SDIST_FILE=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$SDIST_FILE" ] || fail "未找到源码分发包文件"
    success "源码分发包构建完成: $(basename "$SDIST_FILE")"
}

build_deb() {
    info "构建 DEB 包..."

    local sdist_file=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$sdist_file" ] || fail "未找到源码分发包文件"

    local deb_build_dir="$BUILD_DIR/deb"
    mkdir -p "$deb_build_dir"

    cd "$deb_build_dir"
    tar xzf "$sdist_file" || fail "解压源码失败"

    local pkg_dir=$(find . -maxdepth 1 -type d -name 'inpanel-*' | head -1)
    [ -d "$pkg_dir" ] || fail "未找到解压后的包目录"

    cd "$pkg_dir"

    if [ -d "$SOURCE_DIR/debian" ]; then
        cp -r "$SOURCE_DIR/debian" .
    else
        fail "未找到 debian 目录"
    fi

    mkdir -p scripts/systemd scripts/init.d/ubuntu
    cp "$SOURCE_DIR/scripts/systemd/inpanel.service" scripts/systemd/
    cp "$SOURCE_DIR/scripts/init.d/ubuntu/inpanel" scripts/init.d/ubuntu/

    # 清理 sdist 中可能残留的 __pycache__
    find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

    local version=$(grep '^version =' "$SOURCE_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')

    cat > debian/changelog << EOF
inpanel (${version}-1) unstable; urgency=medium

  * Build from pyproject.toml version ${version}

 -- Jackson Dou <jksdou@qq.com>  $(date -R)
EOF

    dpkg-buildpackage -b -us -uc -d || fail "DEB 构建失败"

    cd "$deb_build_dir"
    mkdir -p "$PACKAGE_DIR/deb"
    cp *.deb "$PACKAGE_DIR/deb/" 2>/dev/null || true

    DEB_FILES=$(ls "$PACKAGE_DIR/deb/" 2>/dev/null)
    success "DEB 包构建完成"
}

main() {
    echo ""
    echo "============================================="
    echo "           DEB 包构建"
    echo "============================================="
    echo ""

    check_dependencies
    clean_build_dirs
    build_sdist
    build_deb

    RESULT=0
    RESULT_MSG="DEB 包构建成功"

    echo ""
    echo "---------------------------------------------"
    echo "  DEB 构建结果: 成功"
    echo "  输出目录: $PACKAGE_DIR/deb/"
    echo "  生成文件:"
    if [ -n "$DEB_FILES" ]; then
        ls -1 "$PACKAGE_DIR/deb/" 2>/dev/null | sed 's/^/    /'
    else
        echo "    (无)"
    fi
    echo "---------------------------------------------"
}

main "$@"
