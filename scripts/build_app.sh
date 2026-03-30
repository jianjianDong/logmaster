#!/bin/bash

# LogMaster Pro - PyInstaller独立应用打包脚本
# 此脚本将Python程序及所有依赖打包成独立的macOS应用

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 LogMaster Pro - 开始独立应用打包${NC}"
echo "=========================================="

cd "$PROJECT_DIR"

# 1. 检查并安装依赖
echo -e "${YELLOW}📦 检查并安装依赖...${NC}"
pip install -r requirements.txt
pip install pyinstaller

# 2. 清理旧的构建文件
echo -e "${YELLOW}🧹 清理旧的构建目录...${NC}"
rm -rf "$PROJECT_DIR/build"
rm -rf "$DIST_DIR/LogMasterPro.app"
rm -f "$DIST_DIR/LogMasterPro.dmg"

# 3. 确定图标路径
ICON_PATH="assets/icon.icns"
if [ ! -f "$ICON_PATH" ]; then
    if [ -f "assets/Logmaster.icns" ]; then
        ICON_PATH="assets/Logmaster.icns"
    else
        echo -e "${YELLOW}⚠️ 未找到图标文件，将使用默认图标${NC}"
        ICON_PATH=""
    fi
fi

# 4. 执行PyInstaller打包
echo -e "${YELLOW}🏗️ 正在使用PyInstaller打包应用...${NC}"
echo "这可能需要几分钟时间，请耐心等待..."

PYINSTALLER_CMD="pyinstaller --noconfirm --clean \
    --windowed \
    --name \"LogMasterPro\" \
    --add-data \"src:src\" \
    --hidden-import \"PyQt5\" \
    --hidden-import \"PyQt5.sip\" \
    --hidden-import \"PyQt5.QtCore\" \
    --hidden-import \"PyQt5.QtGui\" \
    --hidden-import \"PyQt5.QtWidgets\" \
    --hidden-import \"PyQt5.QtNetwork\" \
    --hidden-import \"PyQt5.QtPrintSupport\""

if [ -n "$ICON_PATH" ]; then
    PYINSTALLER_CMD="$PYINSTALLER_CMD --icon \"$ICON_PATH\""
fi

PYINSTALLER_CMD="$PYINSTALLER_CMD LogMasterPro.py"

eval $PYINSTALLER_CMD

# 5. 验证打包结果
if [ -d "$DIST_DIR/LogMasterPro.app" ]; then
    echo -e "${GREEN}✅ 应用打包成功！位置: $DIST_DIR/LogMasterPro.app${NC}"
else
    echo -e "${RED}❌ 应用打包失败！${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 独立应用打包完成！${NC}"

# 6. 创建 DMG 安装包
echo -e "${YELLOW}💿 正在创建 DMG 安装包...${NC}"
if command -v create-dmg &> /dev/null; then
    cd "$DIST_DIR"
    create-dmg \
        --volname "LogMaster Pro Installer" \
        --volicon "../$ICON_PATH" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "LogMasterPro.app" 150 190 \
        --hide-extension "LogMasterPro.app" \
        --app-drop-link 450 190 \
        "LogMasterPro.dmg" \
        "LogMasterPro.app"
    
    if [ -f "LogMasterPro.dmg" ]; then
        echo -e "${GREEN}✅ DMG 创建成功！位置: $DIST_DIR/LogMasterPro.dmg${NC}"
        echo -e "💡 你现在可以将这个 DMG 文件发送给其他人，他们双击即可安装使用，无需任何依赖！"
    else
        echo -e "${RED}❌ DMG 创建失败。${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ 未找到 create-dmg 工具。尝试使用 hdiutil 创建基本 DMG...${NC}"
    cd "$DIST_DIR"
    hdiutil create -volname "LogMaster Pro" -srcfolder "LogMasterPro.app" -ov -format UDZO "LogMasterPro.dmg"
    
    if [ -f "LogMasterPro.dmg" ]; then
        echo -e "${GREEN}✅ 基础 DMG 创建成功！位置: $DIST_DIR/LogMasterPro.dmg${NC}"
        echo -e "💡 你现在可以将这个 DMG 文件发送给其他人，他们双击即可安装使用，无需任何依赖！"
    else
        echo -e "${RED}❌ DMG 创建失败。${NC}"
    fi
fi
