#!/bin/bash
#
# 统一构建入口脚本 - 依次构建 RPM 和 DEB 包，汇总两个结果
# 用法：./build_package.sh [SOURCE_DIR] [BUILD_DIR] [PACKAGE_DIR]
#

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SOURCE_DIR="$(readlink -f "${1:-$SCRIPT_DIR/..}")"
BUILD_DIR="$(readlink -f "${2:-$SOURCE_DIR/build}")"
PACKAGE_DIR="$(readlink -f "${3:-$SOURCE_DIR/packages}")"

OK='\033[1;32mOK\033[0m'
FAILED='\033[1;31mFAILED\033[0m'
INFO='\033[1;34mINFO\033[0m'
WARN='\033[1;33mWARN\033[0m'

info()    { echo -e "[$INFO] $1"; }
success() { echo -e "[$OK] $1"; }
fail()    { echo -e "[$FAILED] $1"; }
warn()    { echo -e "[$WARN] $1"; }

RPM_RESULT="SKIP"
RPM_MSG=""
DEB_RESULT="SKIP"
DEB_MSG=""

run_rpm() {
    if command -v rpmbuild &>/dev/null; then
        info "开始构建 RPM 包..."
        if bash "$SCRIPT_DIR/build_rpm.sh" "$SOURCE_DIR" "$BUILD_DIR" "$PACKAGE_DIR"; then
            RPM_RESULT="成功"
            RPM_MSG="RPM 包构建成功"
        else
            RPM_RESULT="失败"
            RPM_MSG="RPM 包构建失败，请查看上方日志"
        fi
    else
        warn "未检测到 rpmbuild，跳过 RPM 构建"
        RPM_RESULT="跳过"
        RPM_MSG="未安装 rpmbuild"
    fi
}

run_deb() {
    if command -v dpkg-buildpackage &>/dev/null; then
        info "开始构建 DEB 包..."
        if bash "$SCRIPT_DIR/build_deb.sh" "$SOURCE_DIR" "$BUILD_DIR" "$PACKAGE_DIR"; then
            DEB_RESULT="成功"
            DEB_MSG="DEB 包构建成功"
        else
            DEB_RESULT="失败"
            DEB_MSG="DEB 包构建失败，请查看上方日志"
        fi
    else
        warn "未检测到 dpkg-buildpackage，跳过 DEB 构建"
        DEB_RESULT="跳过"
        DEB_MSG="未安装 dpkg-buildpackage"
    fi
}

print_summary() {
    echo ""
    echo "============================================="
    echo "          构建结果汇总"
    echo "============================================="
    echo ""
    printf "  %-12s %s\n" "RPM:" "$RPM_RESULT"
    printf "  %-12s %s\n" "DEB:" "$DEB_RESULT"
    echo ""
    echo "  输出目录: $PACKAGE_DIR"
    echo ""

    if [ -d "$PACKAGE_DIR/rpm" ] && ls "$PACKAGE_DIR/rpm/"*.rpm &>/dev/null 2>&1; then
        echo "  RPM 文件:"
        ls -1 "$PACKAGE_DIR/rpm/" 2>/dev/null | sed 's/^/    /'
        echo ""
    fi

    if [ -d "$PACKAGE_DIR/deb" ] && ls "$PACKAGE_DIR/deb/"*.deb &>/dev/null 2>&1; then
        echo "  DEB 文件:"
        ls -1 "$PACKAGE_DIR/deb/" 2>/dev/null | sed 's/^/    /'
        echo ""
    fi

    echo "============================================="

    # 如果两个都跳过了，说明没有构建环境
    if [ "$RPM_RESULT" = "跳过" ] && [ "$DEB_RESULT" = "跳过" ]; then
        echo ""
        warn "当前环境不支持 RPM 和 DEB 构建，请安装 rpmbuild 或 dpkg-buildpackage"
        exit 1
    fi
}

main() {
    echo ""
    echo "============================================="
    echo "         InPanel 安装包构建"
    echo "============================================="
    echo ""
    echo "  源码目录: $SOURCE_DIR"
    echo "  构建目录: $BUILD_DIR"
    echo "  输出目录: $PACKAGE_DIR"
    echo ""

    # 创建目录结构
    mkdir -p "$BUILD_DIR"
    mkdir -p "$PACKAGE_DIR"

    run_rpm
    run_deb
    print_summary
}

main "$@"
