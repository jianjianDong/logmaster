#!/bin/bash

# LogMaster Pro macOS 安装脚本

echo "🚀 LogMaster Pro macOS 安装程序"
echo "=================================="

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 安装目录: $SCRIPT_DIR"

# 检查Python
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3"
    echo "💡 请先安装Python 3.6或更高版本:"
    echo "   brew install python3"
    echo "   或访问: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 检查ADB
echo "🔍 检查ADB..."
if ! command -v adb &> /dev/null; then
    echo "📦 安装ADB..."
    if command -v brew &> /dev/null; then
        brew install android-platform-tools
    else
        echo "❌ 未找到Homebrew，请手动安装ADB:"
        echo "💡 访问: https://developer.android.com/studio/releases/platform-tools"
        exit 1
    fi
fi
echo "✅ ADB已安装"

# 安装依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt
echo "✅ 依赖安装完成"

# 复制应用到Applications
echo "📱 安装应用到系统..."
if [ -d "LogMaster.app" ]; then
    rm -rf "/Applications/LogMaster.app" 2>/dev/null || true
    cp -R "LogMaster.app" "/Applications/LogMaster.app"
    xattr -cr "/Applications/LogMaster.app" 2>/dev/null || true
    echo "✅ 应用已安装到Applications"
else
    echo "⚠️  未找到LogMaster.app，将使用命令行启动"
fi

echo ""
echo "🎉 安装完成！"
echo "=================================="
echo "启动方式："
echo "1. 在Applications中找到LogMaster"
echo "2. 或运行: python3 LogMasterPro.py"
echo ""
echo "📱 使用步骤："
echo "1. 手机开启USB调试"
echo "2. 连接USB线"
echo "3. 启动应用，选择设备"
echo "4. 点击'开始'记录日志"