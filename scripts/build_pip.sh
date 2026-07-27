#!/bin/bash
#
# pip 包构建和上传脚本
# 用法：./build_pip.sh [build|upload] [SOURCE_DIR] [BUILD_DIR]
#

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SOURCE_DIR="$(readlink -f "${2:-$SCRIPT_DIR/..}")"
BUILD_DIR="$(readlink -f "${3:-$SOURCE_DIR/build}")"

OK='\033[1;32mOK\033[0m'
FAILED='\033[1;31mFAILED\033[0m'
INFO='\033[1;34mINFO\033[0m'
WARN='\033[1;33mWARN\033[0m'

info()    { echo -e "[$INFO] $1"; }
success() { echo -e "[$OK] $1"; }
fail()    { echo -e "[$FAILED] $1"; exit 1; }
warn()    { echo -e "[$WARN] $1"; }

ACTION="${1:-build}"

check_dependencies() {
    info "检查构建依赖..."
    local missing=()

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi
    if ! python3 -c 'import build.env' 2>/dev/null; then
        missing+=("python3-build (pip install build)")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        fail "缺少依赖: ${missing[*]}"
    fi
    success "依赖检查通过"
}

build_pip() {
    info "构建 pip 包..."
    cd "$SOURCE_DIR"

    python3 -m build --outdir "$BUILD_DIR" || fail "pip 包构建失败"

    local wheel_file=$(find "$BUILD_DIR" -name '*.whl' | head -1)
    local sdist_file=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)

    echo ""
    success "pip 包构建完成"
    echo ""
    echo "  输出目录: $BUILD_DIR"
    if [ -f "$wheel_file" ]; then
        echo "  Wheel: $(basename "$wheel_file")"
    fi
    if [ -f "$sdist_file" ]; then
        echo "  sdist: $(basename "$sdist_file")"
    fi
    echo ""
}

upload_pip() {
    info "上传 pip 包到 PyPI..."

    if ! python3 -c 'import twine' 2>/dev/null; then
        fail "缺少 twine，请先安装: pip install twine"
    fi

    # 先构建
    build_pip

    info "正在上传..."
    cd "$SOURCE_DIR"
    python3 -m twine upload "$BUILD_DIR"/* || fail "上传失败"

    success "上传成功"
}

usage() {
    echo ""
    echo "用法: $(basename "$0") [build|upload] [SOURCE_DIR] [BUILD_DIR]"
    echo ""
    echo "子命令:"
    echo "  build    构建 pip 包（默认）"
    echo "  upload   构建并上传到 PyPI"
    echo ""
    echo "参数:"
    echo "  SOURCE_DIR  源码目录（默认: 脚本所在目录的上级目录）"
    echo "  BUILD_DIR   构建输出目录（默认: SOURCE_DIR/build）"
    echo ""
    echo "示例:"
    echo "  $(basename "$0")                       # 构建 pip 包"
    echo "  $(basename "$0") build                 # 构建 pip 包"
    echo "  $(basename "$0") upload                # 构建并上传到 PyPI"
    echo "  $(basename "$0") build /path/to/src    # 指定源码目录构建"
    echo ""
}

main() {
    case "$ACTION" in
        build)
            echo ""
            echo "============================================="
            echo "           pip 包构建"
            echo "============================================="
            echo ""
            echo "  源码目录: $SOURCE_DIR"
            echo "  输出目录: $BUILD_DIR"
            echo ""

            mkdir -p "$BUILD_DIR"
            check_dependencies
            build_pip
            ;;
        upload)
            echo ""
            echo "============================================="
            echo "         pip 包构建并上传"
            echo "============================================="
            echo ""
            echo "  源码目录: $SOURCE_DIR"
            echo "  输出目录: $BUILD_DIR"
            echo ""

            mkdir -p "$BUILD_DIR"
            check_dependencies
            upload_pip
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            fail "未知操作: $ACTION，支持 build / upload"
            ;;
    esac
}

main
