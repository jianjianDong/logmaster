#!/bin/bash

# LogMaster Pro macOS 分享包构建脚本

set -e

echo "🚀 构建LogMaster Pro macOS分享包"
echo "=================================="

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 创建分享目录
SHARE_DIR="LogMasterPro_macOS"
rm -rf "$SHARE_DIR"
mkdir -p "$SHARE_DIR"

echo "📦 创建分享包结构..."

# 复制应用包
echo "📱 复制应用包..."
if [ -d "../LogMaster.app" ]; then
    cp -R "../LogMaster.app" "$SHARE_DIR/"
elif [ -d "LogMaster.app" ]; then
    cp -R "LogMaster.app" "$SHARE_DIR/"
else
    echo "❌ 未找到LogMaster.app，请先运行create_macos_app.sh"
    exit 1
fi

# 复制安装脚本
echo "🔧 复制安装脚本..."
cp "install.sh" "$SHARE_DIR/install.sh"

# 复制说明文档
echo "📖 复制说明文档..."
cp "README_SHARE.md" "$SHARE_DIR/README.md"
cp "../requirements.txt" "$SHARE_DIR/"
cp "../LICENSE" "$SHARE_DIR/"

# 复制主程序（作为备用）
echo "📝 复制主程序（备用）..."
cp "../LogMasterPro.py" "$SHARE_DIR/"
cp -R "../src" "$SHARE_DIR/"

# 创建快速启动脚本
echo "⚡ 创建快速启动脚本..."
cat > "$SHARE_DIR/start.sh" << 'EOF'
#!/bin/bash
# LogMaster Pro 快速启动

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 优先使用安装版本，否则使用本地版本
if [ -d "/Applications/LogMaster.app" ]; then
    echo "启动已安装的应用..."
    open "/Applications/LogMaster.app"
else
    echo "启动本地应用..."
    python3 LogMasterPro.py
fi
EOF

chmod +x "$SHARE_DIR/start.sh"

# 创建版本信息
echo "🔍 创建版本信息..."
cat > "$SHARE_DIR/VERSION.txt" << EOF
LogMaster Pro macOS版本
构建时间: $(date '+%Y-%m-%d %H:%M:%S')
Git提交: $(git rev-parse --short HEAD 2>/dev/null || echo "未知")
Python版本: 3.6+
系统要求: macOS 10.12+
应用大小: $(du -sh "$SHARE_DIR/LogMaster.app" | cut -f1)
EOF

# 创建压缩包
echo "📦 创建压缩包..."
PACKAGE_NAME="LogMasterPro_macOS_$(date '+%Y%m%d').tar.gz"
tar -czf "$PACKAGE_NAME" "$SHARE_DIR"

# 显示信息
echo ""
echo "🎉 分享包构建完成！"
echo "=================================="
echo "📦 文件名: $PACKAGE_NAME"
echo "📏 大小: $(ls -lh "$PACKAGE_NAME" | awk '{print $5}')"
echo "📁 内容:"
echo "   ├── LogMaster.app (macOS应用)"
echo "   ├── install.sh (安装脚本)"
echo "   ├── start.sh (快速启动)"
echo "   ├── README.md (使用说明)"
echo "   ├── requirements.txt (依赖列表)"
echo "   ├── VERSION.txt (版本信息)"
echo "   └── LICENSE (许可证)"
echo ""
echo "📤 分享方式:"
echo "1. 直接发送: $PACKAGE_NAME"
echo "2. 上传到云盘，分享下载链接"
echo "3. 通过邮件发送（注意文件大小限制）"
echo ""
echo "📋 接收方使用步骤:"
echo "1. 解压: tar -xzf $PACKAGE_NAME"
echo "2. 进入目录: cd LogMasterPro_macOS"
echo "3. 运行安装: ./install.sh"
echo "4. 启动应用: open -a LogMaster"