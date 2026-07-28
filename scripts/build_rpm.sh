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

    # 确保 build 包可用
    if ! python3 -c 'import build.env' 2>/dev/null; then
        info "安装 python-build 包..."
        python3 -m pip install build -q || fail "无法安装 build 包，请手动执行: pip3 install build"
    fi

    # 确保 setuptools 和 wheel 可用（--no-isolation 需要）
    if ! python3 -c 'import setuptools' 2>/dev/null; then
        info "安装 setuptools..."
        python3 -m pip install 'setuptools>=42' -q || fail "无法安装 setuptools"
    else
        # 检查版本是否满足要求
        local st_ver=$(python3 -c 'import setuptools; print(setuptools.__version__)')
        if ! python3 -c "from pkg_resources import parse_version; exit(0 if parse_version('$st_ver') >= parse_version('42') else 1)" 2>/dev/null; then
            info "升级 setuptools ($st_ver -> latest)..."
            python3 -m pip install 'setuptools>=42' -q || fail "无法升级 setuptools"
        fi
    fi
    if ! python3 -c 'import wheel' 2>/dev/null; then
        info "安装 wheel..."
        python3 -m pip install wheel -q || fail "无法安装 wheel"
    fi

    success "依赖检查通过"
}

build_sdist() {
    info "构建源码分发包..."
    cd "$SOURCE_DIR"

    mkdir -p "$BUILD_DIR"
    python3 -m build --sdist --no-isolation --outdir "$BUILD_DIR" || fail "源码分发包构建失败"

    SDIST_FILE=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$SDIST_FILE" ] || fail "未找到源码分发包文件"
    success "源码分发包构建完成: $(basename "$SDIST_FILE")"
}

extract_version() {
    local version=$(python3 -c "import tomllib; print(tomllib.load(open('$SOURCE_DIR/pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null)
    if [ -z "$version" ]; then
        # 兼容 Python 3.6-3.10 无 tomllib，使用 grep 提取
        version=$(grep -E '^version\s*=' "$SOURCE_DIR/pyproject.toml" | head -1 | sed 's/.*=\s*"\([^"]*\)".*/\1/')
    fi
    [ -n "$version" ] || fail "无法从 pyproject.toml 提取版本号"
    echo "$version"
}

build_rpm() {
    info "构建 RPM 包..."

    local version=$(extract_version)
    info "版本号: $version"

    local sdist_file=$(find "$BUILD_DIR" -name '*.tar.gz' | head -1)
    [ -f "$sdist_file" ] || fail "未找到源码分发包文件"

    local rpmbuild_dir="$BUILD_DIR/rpmbuild"
    mkdir -p "$rpmbuild_dir/SOURCES" "$rpmbuild_dir/SPECS" "$rpmbuild_dir/RPMS" "$rpmbuild_dir/SRPMS"

    cp "$sdist_file" "$rpmbuild_dir/SOURCES/"

    if [ -f "$SOURCE_DIR/rpmbuild.spec" ]; then
        cp "$SOURCE_DIR/rpmbuild.spec" "$rpmbuild_dir/SPECS/"
        rpmbuild --define "_topdir $rpmbuild_dir" --define "version $version" -ba "$rpmbuild_dir/SPECS/rpmbuild.spec" || fail "RPM 构建失败"
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
