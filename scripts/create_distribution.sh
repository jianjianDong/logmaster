#!/bin/bash

# LogMaster Pro 修复版打包脚本
# 创建包含稳定性修复的分发包

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_NAME="LogMasterPro_修复版_$(date +%Y%m%d_%H%M%S)"
DIST_DIR="$PROJECT_DIR/dist/$DIST_NAME"

echo "🚀 LogMaster Pro 修复版打包开始"
echo "=================================="

# 创建分发目录
echo "📁 创建分发目录..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# 复制应用包
echo "📦 复制应用包..."
if [ -d "$PROJECT_DIR/LogMaster.app" ]; then
    cp -R "$PROJECT_DIR/LogMaster.app" "$DIST_DIR/"
    echo "✅ 应用包已复制"
else
    echo "❌ 未找到应用包，请先运行打包脚本"
    exit 1
fi

# 复制源代码（包含修复）
echo "📄 复制源代码..."
mkdir -p "$DIST_DIR/source"
cp -R "$PROJECT_DIR/src" "$DIST_DIR/source/"
cp "$PROJECT_DIR/LogMasterPro.py" "$DIST_DIR/source/"
cp "$PROJECT_DIR/requirements.txt" "$DIST_DIR/source/"

# 复制测试脚本
echo "🧪 复制测试脚本..."
cp "$PROJECT_DIR/test_log_stability.py" "$DIST_DIR/"
cp "$PROJECT_DIR/test_quick_stability.py" "$DIST_DIR/"

# 复制文档
echo "📖 复制文档..."
cp "$PROJECT_DIR/README.md" "$DIST_DIR/"
cp "$PROJECT_DIR/LICENSE" "$DIST_DIR/"

# 创建修复说明
cat > "$DIST_DIR/修复说明.md" << 'EOF'
# LogMaster Pro 稳定性修复说明

## 🛠️ 修复内容

本次修复主要解决了**日志记录功能自动停止**的问题，包含以下改进：

### 1. 增强异常处理机制
- **逐行异常捕获**: 防止单条日志处理失败导致整个线程崩溃
- **连续错误计数**: 超过10次连续错误才触发重启机制
- **详细错误日志**: 提供丰富的诊断信息

### 2. 健康检查系统
- **独立监控线程**: 每5秒检查一次系统健康状态
- **进程状态监控**: 实时检测ADB进程运行状态
- **空闲时间检测**: 超过30秒无日志会触发警告

### 3. 自动重启机制
- **后台监控**: GUI层每3秒检查日志记录状态
- **智能重启**: 检测到异常停止时自动重启（最多3次）
- **状态保持**: 重启时不清除缓冲区，避免数据丢失

### 4. 设备状态优化
- **防抖处理**: 避免设备状态轻微波动导致记录中断
- **智能切换**: 同一设备状态变化时保持记录连续性
- **平滑过渡**: 设备切换时自动重启记录

## 📊 监控指标

修复后的系统会持续监控：
- ✅ ADB进程运行状态
- ✅ 日志读取线程健康度  
- ✅ 日志空闲时间（>15秒触发警告）
- ✅ 连续异常计数（>10次触发重启）
- ✅ 自动重启次数（最多3次）

## 🧪 测试验证

包含两个测试脚本：
- `test_quick_stability.py`: 30秒快速稳定性测试
- `test_log_stability.py`: 5分钟长时间稳定性测试

## 🚀 使用方法

1. **直接运行应用**:
   ```bash
   open LogMaster.app
   ```

2. **运行稳定性测试**:
   ```bash
   python3 test_quick_stability.py
   ```

3. **查看详细日志**:
   应用会在控制台输出详细的运行状态，便于问题诊断

## 📈 性能改进

- **异常容错**: 从单点崩溃 → 逐行恢复
- **状态监控**: 从无监控 → 多层健康检查
- **自动恢复**: 从手动重启 → 自动检测重启
- **进程管理**: 从简单终止 → 完善资源清理

---

修复版本提供了更稳定、更可靠的日志记录体验！
EOF

# 创建安装脚本
cat > "$DIST_DIR/安装说明.md" << 'EOF'
# 安装说明

## macOS 安装

1. **复制到应用程序文件夹**:
   ```bash
   cp -R LogMaster.app /Applications/
   ```

2. **首次运行**:
   - 双击 `LogMaster.app` 或在Launchpad中找到应用
   - 如果提示"无法打开应用"，请执行：
     ```bash
     sudo spctl --master-disable
     sudo xattr -dr com.apple.quarantine /Applications/LogMaster.app
     ```

3. **创建桌面快捷方式**（可选）:
   ```bash
   ln -s /Applications/LogMaster.app ~/Desktop/LogMaster.app
   ```

## 源码运行

如果需要从源码运行：

```bash
# 安装依赖
pip3 install -r source/requirements.txt

# 运行应用
python3 source/LogMasterPro.py
```

## 测试稳定性

运行稳定性测试：
```bash
python3 test_quick_stability.py  # 30秒快速测试
python3 test_log_stability.py    # 5分钟完整测试
```

EOF

# 创建启动脚本
cat > "$DIST_DIR/启动应用.command" << 'EOF'
#!/bin/bash
# LogMaster 启动脚本

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "正在启动 LogMaster Pro..."
open LogMaster.app
EOF

chmod +x "$DIST_DIR/启动应用.command"

# 创建压缩包
echo "📦 创建分发压缩包..."
cd "$PROJECT_DIR/dist"
zip -r "$DIST_NAME.zip" "$DIST_NAME"

# 计算文件大小
PACKAGE_SIZE=$(du -h "$DIST_NAME.zip" | cut -f1)

echo ""
echo "🎉 打包完成！"
echo "=================================="
echo "📦 分发包: $PROJECT_DIR/dist/$DIST_NAME.zip"
echo "📏 大小: $PACKAGE_SIZE"
echo "📁 内容:"
echo "  - LogMaster.app (修复后的应用)"
echo "  - source/ (完整源代码)"
echo "  - test_*.py (稳定性测试脚本)"
echo "  - 修复说明.md (详细修复文档)"
echo "  - 安装说明.md"
echo ""
echo "✅ 所有修复内容已打包完成！"
echo "应用现在具有更强的稳定性和自动恢复能力。"