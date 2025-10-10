#!/bin/bash

# LogMaster Pro - macOS Dock图标修复脚本
# 解决macOS dock栏图标显示异常问题

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 LogMaster Pro - macOS Dock图标修复器${NC}"
echo "=========================================="

# 1. 检查现有图标文件
echo -e "${YELLOW}🔍 检查现有图标文件...${NC}"
ICON_FILES=(
    "$PROJECT_DIR/assets/icon.icns"
    "$PROJECT_DIR/assets/Logmaster.icns"
    "$PROJECT_DIR/assets/icon.png"
)

found_icon=""
for icon_file in "${ICON_FILES[@]}"; do
    if [ -f "$icon_file" ]; then
        echo -e "${GREEN}✅ 找到图标文件: $icon_file${NC}"
        found_icon="$icon_file"
        break
    fi
done

if [ -z "$found_icon" ]; then
    echo -e "${YELLOW}⚠️  未找到图标文件，生成新图标...${NC}"
    if [ -f "$PROJECT_DIR/create_icons.py" ]; then
        cd "$PROJECT_DIR"
        python3 create_icons.py
        found_icon="$PROJECT_DIR/assets/icon.icns"
    else
        echo -e "${RED}❌ 无法生成图标，缺少create_icons.py${NC}"
        exit 1
    fi
fi

# 2. 创建或更新应用包
echo -e "${YELLOW}🏗️  创建/更新应用包...${NC}"

# 检查现有的应用包
APP_BUNDLES=(
    "$PROJECT_DIR/LogMaster Pro.app"
    "$PROJECT_DIR/LogMaster.app"
)

app_bundle=""
for bundle in "${APP_BUNDLES[@]}"; do
    if [ -d "$bundle" ]; then
        app_bundle="$bundle"
        echo -e "${GREEN}✅ 找到现有应用包: $bundle${NC}"
        break
    fi
done

if [ -z "$app_bundle" ]; then
    echo -e "${YELLOW}📦 创建新的应用包...${NC}"
    app_bundle="$PROJECT_DIR/LogMaster Pro.app"
    
    # 创建应用包结构
    mkdir -p "$app_bundle/Contents/MacOS"
    mkdir -p "$app_bundle/Contents/Resources"
    mkdir -p "$app_bundle/Contents/Frameworks"
    
    # 创建Info.plist
    cat > "$app_bundle/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>LogMaster Pro</string>
    <key>CFBundleDisplayName</key>
    <string>LogMaster Pro</string>
    <key>CFBundleIdentifier</key>
    <string>com.logmasterpro.app</string>
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
    <string>Copyright © 2024 LogMaster Pro. All rights reserved.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>LogMaster Pro需要访问系统事件来正常运行</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIconName</key>
    <string>AppIcon</string>
</dict>
</plist>
EOF
    
    # 创建启动脚本
    cat > "$app_bundle/Contents/MacOS/LogMasterPro" << 'EOF'
#!/bin/bash

# LogMaster Pro 启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 设置Python路径
export PYTHONPATH="$DIR/../Resources:$PYTHONPATH"

# 检查ADB
if ! command -v adb &> /dev/null; then
    osascript -e 'display alert "ADB未找到" message "请确保Android SDK已安装并配置环境变量" buttons {"OK"} default button "OK"'
    exit 1
fi

# 启动应用
python3 "$DIR/../Resources/LogMasterPro.py" "$@"
EOF
    
    chmod +x "$app_bundle/Contents/MacOS/LogMasterPro"
fi

# 3. 复制图标文件到应用包
echo -e "${YELLOW}🎨 设置应用图标...${NC}"

# 复制图标文件
if [[ "$found_icon" == *.icns ]]; then
    cp "$found_icon" "$app_bundle/Contents/Resources/AppIcon.icns"
elif [[ "$found_icon" == *.png ]]; then
    # 如果是PNG，尝试转换为icns
    if command -v sips &> /dev/null; then
        sips -s format icns "$found_icon" --out "$app_bundle/Contents/Resources/AppIcon.icns" 2>/dev/null || \
        cp "$found_icon" "$app_bundle/Contents/Resources/AppIcon.png"
    else
        cp "$found_icon" "$app_bundle/Contents/Resources/AppIcon.png"
    fi
fi

# 4. 复制项目文件
echo -e "${YELLOW}📁 复制项目文件...${NC}"
cp -r "$PROJECT_DIR/src" "$app_bundle/Contents/Resources/"
cp "$PROJECT_DIR/LogMasterPro.py" "$app_bundle/Contents/Resources/"
cp "$PROJECT_DIR/requirements.txt" "$app_bundle/Contents/Resources/" 2>/dev/null || true

# 5. 清除系统图标缓存
echo -e "${YELLOW}🔄 清除系统图标缓存...${NC}"
echo "正在清除图标缓存..."
rm -rf ~/Library/Caches/com.apple.dock.iconcache
rm -rf ~/Library/Caches/com.apple.iconservices.store
rm -rf ~/Library/Caches/com.apple.finder
rm -rf ~/Library/Caches/Icon*
rm -rf ~/Library/Saved\ Application\ State/com.logmasterpro.app.savedState 2>/dev/null || true

# 6. 重新注册应用
echo -e "${YELLOW}📝 重新注册应用...${NC}"
if [ -d "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/" ]; then
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -seed -r -f -v "$app_bundle" 2>/dev/null || true
fi

# 7. 重启相关服务
echo -e "${YELLOW}🔄 重启相关服务...${NC}"
echo "正在重启Dock和Finder..."
killall Dock 2>/dev/null || true
killall Finder 2>/dev/null || true
killall SystemUIServer 2>/dev/null || true

# 等待系统刷新
echo "等待系统刷新..."
sleep 3

# 8. 创建桌面快捷方式
echo -e "${YELLOW}🔗 创建桌面快捷方式...${NC}"
DESKTOP_LINK="$HOME/Desktop/LogMaster Pro.app"
rm -f "$DESKTOP_LINK"
ln -s "$app_bundle" "$DESKTOP_LINK" 2>/dev/null || true

# 9. 创建Applications快捷方式
echo -e "${YELLOW}📱 创建Applications快捷方式...${NC}"
APP_LINK="/Applications/LogMaster Pro.app"
if [ -w "/Applications" ]; then
    rm -f "$APP_LINK"
    ln -s "$app_bundle" "$APP_LINK" 2>/dev/null || true
fi

# 10. 验证图标设置
echo -e "${YELLOW}🔍 验证图标设置...${NC}"
if [ -f "$app_bundle/Contents/Resources/AppIcon.icns" ]; then
    echo -e "${GREEN}✅ 应用图标已设置: AppIcon.icns${NC}"
elif [ -f "$app_bundle/Contents/Resources/AppIcon.png" ]; then
    echo -e "${GREEN}✅ 应用图标已设置: AppIcon.png${NC}"
else
    echo -e "${RED}⚠️  应用图标设置失败${NC}"
fi

# 检查Info.plist
if grep -q "CFBundleIconFile" "$app_bundle/Contents/Info.plist"; then
    echo -e "${GREEN}✅ Info.plist图标配置正确${NC}"
else
    echo -e "${RED}⚠️  Info.plist缺少图标配置${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Dock图标修复完成！${NC}"
echo "=========================================="
echo -e "📍 应用位置: ${app_bundle}"
echo -e "💻 桌面快捷方式: ${DESKTOP_LINK}"
echo -e "📱 Applications快捷方式: ${APP_LINK}"
echo ""
echo -e "${YELLOW}💡 使用说明:${NC}"
echo "1. 双击桌面上的 'LogMaster Pro' 图标启动应用"
echo "2. 或者在Applications文件夹中找到LogMaster Pro"
echo "3. 如果图标仍然异常，请重启Mac"
echo "4. 启动台图标可能需要几分钟才能完全刷新"
echo ""
echo -e "${BLUE}🔧 故障排除:${NC}"
echo "• 如果图标仍然显示异常，运行: ./scripts/fix_icon_cache.sh"
echo "• 检查应用是否正常运行: python3 LogMasterPro.py --version"
echo "• 查看控制台日志获取详细信息"
echo ""
echo -e "${GREEN}享受使用LogMaster Pro！${NC}"