#!/bin/bash

# LogMaster - 修复macOS图标缓存问题
# 增强版本，包含更多缓存清理选项

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔄 修复LogMaster图标缓存问题..."
echo "=========================================="

# 1. 清除系统图标缓存
echo "清除系统图标缓存..."
rm -rf ~/Library/Caches/com.apple.dock.iconcache
rm -rf ~/Library/Caches/com.apple.iconservices.store
rm -rf ~/Library/Caches/com.apple.finder
rm -rf ~/Library/Caches/Icon*
rm -rf ~/Library/Caches/com.apple.IconServices
rm -rf ~/Library/Caches/com.apple.iconservices
rm -rf ~/Library/Caches/com.apple.dock.extra
rm -rf ~/Library/Caches/com.apple.dock.extra.*

# 2. 清除LaunchServices缓存
echo "清除LaunchServices缓存..."
if [ -f "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister" ]; then
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -seed -r -f -v -dump 2>/dev/null || true
fi

# 3. 清除应用特定缓存
echo "清除应用特定缓存..."
rm -rf ~/Library/Saved\ Application\ State/com.logmasterpro.app.savedState 2>/dev/null || true
rm -rf ~/Library/Saved\ Application\ State/com.logmaster.app.savedState 2>/dev/null || true
rm -rf ~/Library/Preferences/com.logmasterpro.app.plist 2>/dev/null || true
rm -rf ~/Library/Preferences/com.logmaster.app.plist 2>/dev/null || true

# 4. 重启相关服务
echo "重启相关服务..."
echo "正在重启Dock..."
killall Dock 2>/dev/null || true
sleep 2

echo "正在重启Finder..."
killall Finder 2>/dev/null || true
sleep 1

echo "正在重启SystemUIServer..."
killall SystemUIServer 2>/dev/null || true
sleep 1

# 5. 重新注册LogMaster应用
echo "重新注册LogMaster应用..."
APP_BUNDLES=(
    "$PROJECT_DIR/LogMaster Pro.app"
    "$PROJECT_DIR/LogMaster.app"
)

for bundle in "${APP_BUNDLES[@]}"; do
    if [ -d "$bundle" ]; then
        echo "注册应用: $bundle"
        if [ -f "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister" ]; then
            /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$bundle" 2>/dev/null || true
        fi
    fi
done

# 6. 等待系统刷新
echo "等待系统刷新..."
sleep 5

echo "=========================================="
echo "✅ 图标缓存修复完成！"
echo "=========================================="
echo ""
echo "💡 提示："
echo "• 如果图标仍然异常，请重启Mac"
echo "• 启动台图标可能需要几分钟才能完全刷新"
echo "• 应用启动时的图标切换是正常现象"
echo "• 可以使用 ./scripts/fix_dock_icon.sh 进行更全面的修复"
echo ""
echo "🔧 额外故障排除："
echo "• 检查控制台是否有错误信息"
echo "• 确认应用包结构完整"
echo "• 验证图标文件是否存在且有效"