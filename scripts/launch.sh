#!/bin/bash

# LogMaster Pro 启动脚本
# Android日志分析工具

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动 LogMaster Pro - Android日志大师"
echo "=================================="

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 未找到Python，请安装Python 3.6+"
        exit 1
    fi
    
    # 检查Python版本
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.6"
    
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)"; then
        echo "❌ Python版本过低，需要 $REQUIRED_VERSION+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    
    echo "✅ Python版本: $PYTHON_VERSION"
}

# 检查ADB
check_adb() {
    if command -v adb &> /dev/null; then
        ADB_VERSION=$(adb version | head -n1)
        echo "✅ ADB可用: $ADB_VERSION"
    else
        echo "⚠️  未找到ADB命令"
        echo "   请确保Android SDK已安装并配置环境变量"
        echo "   或者安装: brew install android-platform-tools (macOS)"
        echo "            sudo apt-get install android-tools-adb (Ubuntu)"
    fi
}

# 安装依赖
install_dependencies() {
    echo "📦 检查依赖..."
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        echo "❌ 未找到requirements.txt文件"
        exit 1
    fi
    
    # 创建虚拟环境（可选）
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo "🐍 创建虚拟环境..."
        $PYTHON_CMD -m venv "$PROJECT_DIR/venv"
        echo "✅ 虚拟环境已创建"
    fi
    
    # 激活虚拟环境
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        echo "🔄 激活虚拟环境..."
        source "$PROJECT_DIR/venv/bin/activate"
    fi
    
    # 安装依赖
    echo "📥 安装Python依赖..."
    pip install -r "$PROJECT_DIR/requirements.txt"
    echo "✅ 依赖安装完成"
}

# 检查项目文件
check_project_files() {
    echo "📁 检查项目文件..."
    
    required_files=(
        "$PROJECT_DIR/LogMasterPro.py"
        "$PROJECT_DIR/src/core.py"
        "$PROJECT_DIR/src/gui.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ 缺失必要文件: $file"
            exit 1
        fi
    done
    
    echo "✅ 项目文件检查通过"
}

# 主函数
main() {
    cd "$PROJECT_DIR"
    
    check_python
    check_adb
    check_project_files
    install_dependencies
    
    echo ""
    echo "🎯 启动LogMaster Pro..."
    echo "=================================="
    
    # 运行主程序
    $PYTHON_CMD LogMasterPro.py "$@"
}

# 处理命令行参数
case "${1:-}" in
    --help|-h)
        echo "LogMaster Pro 启动脚本"
        echo ""
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --check        检查环境但不启动程序"
        echo "  --no-deps      跳过依赖安装"
        echo ""
        echo "示例:"
        echo "  $0                    # 正常启动"
        echo "  $0 --check            # 只检查环境"
        echo "  $0 --no-deps          # 跳过依赖安装"
        exit 0
        ;;
    --check)
        echo "🔍 环境检查模式"
        check_python
        check_adb
        check_project_files
        echo "✅ 环境检查通过"
        exit 0
        ;;
    --no-deps)
        echo "🚀 跳过依赖安装"
        cd "$PROJECT_DIR"
        check_python
        check_adb
        check_project_files
        $PYTHON_CMD LogMasterPro.py "${@:2}"
        ;;
    *)
        main "$@"
        ;;
esac