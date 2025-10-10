#!/bin/bash

# LogMaster - 创建干净的macOS应用包
# 解决启动台图标显示问题

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="LogMaster"
APP_BUNDLE="$PROJECT_DIR/${APP_NAME}.app"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 LogMaster - 创建干净的macOS应用包${NC}"
echo "=========================================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

# 检查ADB
if ! command -v adb &> /dev/null; then
    echo -e "${RED}❌ ADB 未找到，请确保Android SDK已安装${NC}"
    exit 1
fi

# 检查PyQt5
echo -e "${YELLOW}📦 检查PyQt5...${NC}"
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo -e "${YELLOW}📥 正在安装PyQt5...${NC}"
    pip3 install PyQt5
fi

# 创建应用包结构
echo -e "${YELLOW}🏗️  创建应用包结构...${NC}"
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
mkdir -p "$APP_BUNDLE/Contents/Frameworks"

# 创建Info.plist - 使用正确的图标配置
cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>LogMaster</string>
    <key>CFBundleDisplayName</key>
    <string>LogMaster</string>
    <key>CFBundleIdentifier</key>
    <string>com.logmaster.app</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>LogMaster</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 LogMaster. All rights reserved.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>LogMaster需要访问系统事件来正常运行</string>
    <key>CFBundleIconFile</key>
    <string>LogMaster</string>
    <key>CFBundleIconName</key>
    <string>LogMaster</string>
</dict>
</plist>
EOF

# 创建启动脚本
cat > "$APP_BUNDLE/Contents/MacOS/LogMaster" << 'EOF'
#!/bin/bash

# LogMaster 启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 设置Python路径
export PYTHONPATH="$DIR/../Resources:$PYTHONPATH"

# 设置ADB路径 - 从常见位置查找
ADB_PATH=""
if command -v /usr/local/bin/adb &> /dev/null; then
    ADB_PATH="/usr/local/bin/adb"
elif command -v adb &> /dev/null; then
    ADB_PATH="adb"
elif [ -f "$HOME/Android/sdk/platform-tools/adb" ]; then
    ADB_PATH="$HOME/Android/sdk/platform-tools/adb"
elif [ -f "/Applications/Android Studio.app/sdk/platform-tools/adb" ]; then
    ADB_PATH="/Applications/Android Studio.app/sdk/platform-tools/adb"
fi

if [ -n "$ADB_PATH" ]; then
    export PATH="$(dirname "$ADB_PATH"):$PATH"
else
    osascript -e 'display alert "ADB未找到" message "请确保Android SDK已安装并配置环境变量" buttons {"OK"} default button "OK"'
    exit 1
fi

# 启动应用
cd "$DIR/../Resources"
python3 "LogMasterPro.py" "$@"
EOF

chmod +x "$APP_BUNDLE/Contents/MacOS/LogMaster"

# 复制项目文件
echo -e "${YELLOW}📁 复制项目文件...${NC}"
cp -r "$PROJECT_DIR/src" "$APP_BUNDLE/Contents/Resources/"
cp "$PROJECT_DIR/LogMasterPro.py" "$APP_BUNDLE/Contents/Resources/"

# 复制图标文件
echo -e "${YELLOW}🎨 复制图标文件...${NC}"
if [ -f "$PROJECT_DIR/assets/Logmaster.icns" ]; then
    cp "$PROJECT_DIR/assets/Logmaster.icns" "$APP_BUNDLE/Contents/Resources/LogMaster.icns"
    echo -e "${GREEN}✅ 使用项目图标文件${NC}"
elif [ -f "$PROJECT_DIR/assets/icon.icns" ]; then
    cp "$PROJECT_DIR/assets/icon.icns" "$APP_BUNDLE/Contents/Resources/LogMaster.icns"
    echo -e "${GREEN}✅ 使用备用图标文件${NC}"
else
    echo -e "${YELLOW}⚠️  未找到图标文件，创建占位符${NC}"
    # 创建一个简单的图标描述文件
    echo "LogMaster Icon" > "$APP_BUNDLE/Contents/Resources/LogMaster.txt"
fi

# 清除macOS图标缓存
echo -e "${YELLOW}🧹 清除图标缓存...${NC}"
rm -rf "$HOME/Library/Caches/com.apple.dock.iconcache" 2>/dev/null || true
rm -rf "$HOME/Library/Caches/com.apple.iconservices.store" 2>/dev/null || true
rm -rf "$HOME/Library/Caches/com.apple.finder" 2>/dev/null || true

# 重启Dock（可选）
echo -e "${YELLOW}🔄 重启Dock服务...${NC}"
killall Dock 2>/dev/null || true
killall Finder 2>/dev/null || true

# 创建桌面快捷方式
echo -e "${YELLOW}🔗 创建桌面快捷方式...${NC}"
DESKTOP_LINK="$HOME/Desktop/LogMaster.app"
rm -f "$DESKTOP_LINK"
ln -s "$APP_BUNDLE" "$DESKTOP_LINK" 2>/dev/null || true

# 创建Applications快捷方式
APP_LINK="/Applications/LogMaster.app"
if [ -w "/Applications" ]; then
    rm -f "$APP_LINK"
    ln -s "$APP_BUNDLE" "$APP_LINK" 2>/dev/null || true
fi

# 测试运行
echo -e "${GREEN}✅ 应用包创建完成！${NC}"
echo -e "${YELLOW}🧪 测试运行...${NC}"

# 尝试运行应用
if "$APP_BUNDLE/Contents/MacOS/LogMaster" --version 2>/dev/null; then
    echo -e "${GREEN}✅ 应用测试运行成功！${NC}"
else
    echo -e "${YELLOW}⚠️  应用测试运行失败，但包已创建完成${NC}"
fi

echo ""
echo -e "${GREEN}🎉 LogMaster 应用包创建完成！${NC}"
echo "=========================================="
echo -e "📍 应用位置: ${APP_BUNDLE}"
echo -e "💻 桌面快捷方式: ${DESKTOP_LINK}"
echo -e "📱 Applications快捷方式: ${APP_LINK}"
echo ""
echo -e "${YELLOW}🚀 现在你可以：${NC}"
echo "1. 从启动台搜索'LogMaster'启动应用"
echo "2. 双击桌面上的'LogMaster'图标"
echo "3. 在Applications文件夹中找到LogMaster"
echo ""
echo -e "${GREEN}享受使用LogMaster！${NC}"
echo -e "${YELLOW}💡 提示：如果图标仍然显示异常，请重启Mac或等待几分钟让系统刷新图标缓存${NC}"