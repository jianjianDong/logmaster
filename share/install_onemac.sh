#!/bin/bash

# LogMaster Pro macOS 一键安装脚本
# 下载后直接在终端运行: bash install_onemac.sh

echo "🚀 LogMaster Pro 一键安装"
echo "=========================="

# 检查是否已下载完整包
if [ ! -f "LogMaster.app/Contents/MacOS/LogMasterPro" ]; then
    echo "❌ 请先下载完整的LogMasterPro_macOS.tar.gz包并解压"
    echo "📥 下载地址: [你的分享链接]"
    echo "📦 解压: tar -xzf LogMasterPro_macOS.tar.gz"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
if command -v brew &> /dev/null; then
    echo "安装ADB..."
    brew install android-platform-tools
else
    echo "⚠️  未找到Homebrew，请手动安装ADB:"
    echo "   https://developer.android.com/studio/releases/platform-tools"
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install PyQt5>=5.15.0

# 安装应用到系统
echo "📱 安装应用..."
rm -rf "/Applications/LogMaster.app" 2>/dev/null || true
cp -R "LogMaster.app" "/Applications/"
xattr -cr "/Applications/LogMaster.app" 2>/dev/null || true

# 创建桌面快捷方式
echo "🎯 创建快捷方式..."
ln -sf "/Applications/LogMaster.app" "$HOME/Desktop/LogMaster.app" 2>/dev/null || true

echo ""
echo "🎉 安装完成！"
echo "=========================="
echo "📱 手机设置步骤："
echo "1. 设置 → 关于手机 → 连续点击版本号7次"
echo "2. 设置 → 系统 → 开发者选项 → 启用USB调试"
echo "3. 用USB线连接手机到Mac"
echo ""
echo "💻 启动应用："
echo "1. 双击桌面上的LogMaster图标"
echo "2. 或从Applications文件夹启动"
echo "3. 选择设备，点击'开始'记录日志"
echo ""
echo "🔧 验证安装："
echo "终端运行: adb devices"
echo "应该能看到你的设备序列号"