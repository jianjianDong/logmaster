#!/bin/bash

# LogMaster - macOS启动器
# 这个脚本创建macOS应用包，支持点击图标启动

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

echo -e "${GREEN}🚀 LogMaster - macOS应用包创建器${NC}"
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

# 创建Info.plist
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
    <string>5.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>5.0</string>
    <key>CFBundleExecutable</key>
    <string>LogMasterPro</string>
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
</dict>
</plist>
EOF

# 创建启动脚本
cat > "$APP_BUNDLE/Contents/MacOS/LogMasterPro" << 'EOF'
#!/bin/bash

# LogMaster 启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 设置Python路径
export PYTHONPATH="$DIR/../Resources:$PYTHONPATH"

# 设置环境变量，确保ADB能被找到
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# 启动应用（ADB检测将在应用内部处理）
python3 "$DIR/../Resources/LogMasterPro.py" "$@"
EOF

chmod +x "$APP_BUNDLE/Contents/MacOS/LogMasterPro"

# 复制项目文件
echo -e "${YELLOW}📁 复制项目文件...${NC}"
cp -r "$PROJECT_DIR/src" "$APP_BUNDLE/Contents/Resources/"
cp "$PROJECT_DIR/LogMasterPro.py" "$APP_BUNDLE/Contents/Resources/"

# 创建图标（如果没有实际的图标文件）
if [ ! -f "$PROJECT_DIR/assets/icon.icns" ] && [ ! -f "$PROJECT_DIR/assets/Logmaster.icns" ]; then
    echo -e "${YELLOW}🎨 创建默认图标...${NC}"
    mkdir -p "$PROJECT_DIR/assets"
    
    # 检查是否有Python图标生成器
    if [ -f "$PROJECT_DIR/create_icons.py" ]; then
        echo -e "${YELLOW}🖼️  使用Python图标生成器...${NC}"
        cd "$PROJECT_DIR"
        python3 create_icons.py || echo "图标生成器执行失败"
    fi
fi

# 复制图标文件到应用包
if [ -f "$PROJECT_DIR/assets/icon.icns" ]; then
    cp "$PROJECT_DIR/assets/icon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
    echo -e "${GREEN}✅ 使用 icon.icns 作为应用图标${NC}"
elif [ -f "$PROJECT_DIR/assets/Logmaster.icns" ]; then
    cp "$PROJECT_DIR/assets/Logmaster.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
    echo -e "${GREEN}✅ 使用 Logmaster.icns 作为应用图标${NC}"
else
    # 创建一个简单的图标（使用系统图标作为替代）
    echo -e "${YELLOW}⚠️  未找到图标文件，尝试使用系统图标...${NC}"
    cp "/System/Applications/Utilities/Console.app/Contents/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns" 2>/dev/null || \
    cp "/Applications/Utilities/Console.app/Contents/Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns" 2>/dev/null || \
    echo "noicon" > "$APP_BUNDLE/Contents/Resources/icon.txt"
fi

# 更新Info.plist中的图标引用
if [ -f "$APP_BUNDLE/Contents/Resources/AppIcon.icns" ]; then
    /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon.icns" "$APP_BUNDLE/Contents/Info.plist" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon.icns" "$APP_BUNDLE/Contents/Info.plist" 2>/dev/null || true
    echo -e "${GREEN}✅ Info.plist图标引用已更新${NC}"
fi

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

# 测试运行 - 使用更轻量的测试方式
echo -e "${GREEN}✅ 应用包创建完成！${NC}"
echo -e "${YELLOW}🧪 验证应用包完整性...${NC}"

# 检查关键文件是否存在
if [ -f "$APP_BUNDLE/Contents/MacOS/LogMasterPro" ] && [ -f "$APP_BUNDLE/Contents/Resources/LogMasterPro.py" ]; then
    echo -e "${GREEN}✅ 应用包结构验证通过！${NC}"
    # 只做语法检查，不实际运行应用
    if python3 -m py_compile "$APP_BUNDLE/Contents/Resources/LogMasterPro.py" 2>/dev/null; then
        echo -e "${GREEN}✅ Python语法检查通过！${NC}"
    else
        echo -e "${YELLOW}⚠️  Python语法检查失败${NC}"
    fi
else
    echo -e "${RED}❌ 应用包结构不完整${NC}"
fi

echo ""
echo -e "${GREEN}🎉 LogMaster 应用包创建完成！${NC}"
echo "=========================================="
echo -e "📍 应用位置: ${APP_BUNDLE}"
echo -e "💻 桌面快捷方式: ${DESKTOP_LINK}"
echo -e "📱 Applications快捷方式: ${APP_LINK}"
echo ""
echo -e "${YELLOW}🚀 现在你可以：${NC}"
echo "1. 双击桌面上的 'LogMaster' 图标启动应用"
echo "2. 或者在Applications文件夹中找到LogMaster"
echo "3. 或者从终端运行: open \"$APP_BUNDLE\""
echo ""
echo -e "${GREEN}享受使用LogMaster！${NC}"