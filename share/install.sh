#!/bin/bash

# LogMaster Pro 安装脚本 (macOS)

set -e

echo "🚀 LogMaster Pro 安装程序"
echo "=========================="

# 检查系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此安装脚本仅支持macOS"
    exit 1
fi

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 安装目录: $SCRIPT_DIR"

# 检查Python
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.6或更高版本"
    echo "💡 建议访问: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python版本: $PYTHON_VERSION"

# 检查ADB
echo "🔍 检查ADB环境..."
if command -v adb &> /dev/null; then
    ADB_VERSION=$(adb version | head -1)
    echo "✅ ADB已安装: $ADB_VERSION"
else
    echo "⚠️  未找到ADB，将尝试安装..."
    if command -v brew &> /dev/null; then
        echo "📦 使用Homebrew安装ADB..."
        brew install android-platform-tools
    else
        echo "❌ 未找到Homebrew，请手动安装ADB"
        echo "💡 访问: https://developer.android.com/studio/releases/platform-tools"
        exit 1
    fi
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    echo "🔧 尝试安装Python依赖..."
    # 首先尝试使用 --break-system-packages 标志
    if pip3 install --break-system-packages -r requirements.txt 2>/dev/null; then
        echo "✅ Python依赖安装完成"
    else
        echo "⚠️  系统包管理限制，尝试用户模式安装..."
        # 如果失败，尝试用户模式安装
        if pip3 install --user -r requirements.txt; then
            echo "✅ Python依赖安装完成（用户模式）"
        else
            echo "❌ Python依赖安装失败"
            echo "💡 建议手动安装依赖："
            echo "   1. 创建虚拟环境: python3 -m venv venv"
            echo "   2. 激活环境: source venv/bin/activate"
            echo "   3. 安装依赖: pip install -r requirements.txt"
            echo "   4. 运行应用: python3 LogMasterPro.py"
            exit 1
        fi
    fi
else
    echo "⚠️  未找到requirements.txt文件，跳过依赖安装"
fi

# 复制应用到Applications文件夹
echo "📱 安装应用到系统..."
APP_NAME="LogMaster"
APP_PATH="/Applications/$APP_NAME.app"

if [ -d "LogMaster.app" ]; then
    # 如果存在应用包，复制到Applications
    if [ -d "$APP_PATH" ]; then
        echo "🔄 移除旧版本..."
        rm -rf "$APP_PATH"
    fi
    
    echo "📋 复制应用到Applications..."
    cp -R "LogMaster.app" "$APP_PATH"
    
    # 修复权限
    chmod -R 755 "$APP_PATH"
    
    echo "✅ 应用安装完成: $APP_PATH"
else
    echo "⚠️  未找到LogMaster.app，创建桌面快捷方式..."
    
    # 创建桌面快捷方式
    DESKTOP_PATH="$HOME/Desktop/LogMaster.command"
    cat > "$DESKTOP_PATH" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
python3 LogMasterPro.py
EOF
    chmod +x "$DESKTOP_PATH"
    echo "✅ 桌面快捷方式已创建: $DESKTOP_PATH"
fi

# 清除macOS安全限制
echo "🔓 清除macOS安全限制..."
if [ -d "$APP_PATH" ]; then
    xattr -cr "$APP_PATH" 2>/dev/null || true
fi

# 创建启动脚本
echo "📝 创建启动脚本..."
cat > "start_logmaster.sh" << 'EOF'
#!/bin/bash
# LogMaster 启动脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查应用是否已安装到Applications
if [ -d "/Applications/LogMaster.app" ]; then
    echo "启动已安装的应用..."
    open "/Applications/LogMaster.app"
else
    echo "启动本地应用..."
    python3 LogMasterPro.py
fi
EOF

chmod +x start_logmaster.sh

echo ""
echo "🎉 安装完成！"
echo "=========================="
echo "启动方式："
echo "1. 双击桌面上的LogMaster图标"
echo "2. 在Applications文件夹中找到LogMaster"
echo "3. 运行: ./start_logmaster.sh"
echo ""
echo "📖 使用说明："
echo "1. 连接Android设备并启用USB调试"
echo "2. 启动应用并选择设备"
echo "3. 点击'开始'按钮记录日志"
echo ""
echo "🔧 故障排除："
echo "- 如果应用无法启动，请检查Python和ADB是否正确安装"
echo "- 查看日志: tail -f /tmp/logmaster_debug.log"
echo "- 重新安装: 删除/Applications/LogMaster.app后重新运行此脚本"