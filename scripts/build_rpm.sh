#!/bin/bash
#
# RPM 包构建脚本
# 用法：./build_rpm.sh [SOURCE_DIR] [BUILD_DIR] [PACKAGE_DIR]
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
RPM_FILES=""

check_dependencies() {
    info "检查构建依赖..."
    local missing=()

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi
    if ! command -v rpmbuild &>/dev/null; then
        missing+=("rpmbuild")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        fail "缺少依赖: ${missing[*]}"
    fi
    success "依赖检查通过"
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

build_rpm() {
    info "构建 RPM 包..."

    local sdist_file=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$sdist_file" ] || fail "未找到源码分发包文件"

    local rpmbuild_dir="$BUILD_DIR/rpmbuild"
    mkdir -p "$rpmbuild_dir/SOURCES" "$rpmbuild_dir/SPECS" "$rpmbuild_dir/RPMS" "$rpmbuild_dir/SRPMS"

    cp "$sdist_file" "$rpmbuild_dir/SOURCES/"

    if [ -f "$SOURCE_DIR/rpmbuild.spec" ]; then
        cp "$SOURCE_DIR/rpmbuild.spec" "$rpmbuild_dir/SPECS/"
        rpmbuild --define "_topdir $rpmbuild_dir" -ba "$rpmbuild_dir/SPECS/rpmbuild.spec" || fail "RPM 构建失败"
    else
        fail "未找到 RPM spec 文件"
    fi

    mkdir -p "$PACKAGE_DIR/rpm"
    cp "$rpmbuild_dir/RPMS"/*/*.rpm "$PACKAGE_DIR/rpm/" 2>/dev/null || true
    cp "$rpmbuild_dir/SRPMS"/*.rpm "$PACKAGE_DIR/rpm/" 2>/dev/null || true

    RPM_FILES=$(ls "$PACKAGE_DIR/rpm/" 2>/dev/null)
    success "RPM 包构建完成"
}

main() {
    echo ""
    echo "============================================="
    echo "           RPM 包构建"
    echo "============================================="
    echo ""

    check_dependencies
    build_sdist
    build_rpm

    RESULT=0
    RESULT_MSG="RPM 包构建成功"

    echo ""
    echo "---------------------------------------------"
    echo "  RPM 构建结果: 成功"
    echo "  输出目录: $PACKAGE_DIR/rpm/"
    echo "  生成文件:"
    if [ -n "$RPM_FILES" ]; then
        ls -1 "$PACKAGE_DIR/rpm/" 2>/dev/null | sed 's/^/    /'
    else
        echo "    (无)"
    fi
    echo "---------------------------------------------"
}

main "$@"
