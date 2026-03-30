# LogMaster Pro for macOS 🚀

专业级Android日志分析工具，支持实时日志监控、高级过滤和彩色显示。

## 📦 分享包内容

```
LogMasterPro_macOS/
├── LogMaster.app          # macOS应用程序
├── install.sh             # 一键安装脚本
├── README.md              # 使用说明
├── requirements.txt       # Python依赖
└── LICENSE               # 许可证
```

## 🚀 快速安装

### 方法一：一键安装（推荐）

```bash
# 1. 解压下载的文件
tar -xzf LogMasterPro_macOS.tar.gz
cd LogMasterPro_macOS

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 启动应用
open -a LogMaster
```

### 方法二：手动安装

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 复制到Applications
cp -R LogMaster.app /Applications/

# 3. 清除安全限制
xattr -cr /Applications/LogMaster.app

# 4. 启动
open /Applications/LogMaster.app
```

## 📋 系统要求

- **macOS**: 10.12 (Sierra) 或更高版本
- **Python**: 3.6 或更高版本
- **ADB**: Android SDK Platform Tools

## 🔧 环境准备

### 1. 安装Python（如果未安装）
```bash
# 使用Homebrew安装
brew install python3

# 验证安装
python3 --version
```

### 2. 安装ADB
```bash
# 使用Homebrew安装
brew install android-platform-tools

# 验证安装
adb version
```

### 3. 手机设置
1. **开启开发者选项**:
   - 设置 → 关于手机 → 连续点击"版本号"7次
2. **启用USB调试**:
   - 设置 → 系统 → 开发者选项 → 启用"USB调试"
3. **连接手机**:
   - 使用USB线连接手机和Mac
   - 手机上选择"文件传输"模式

## 🎯 使用步骤

### 1. 启动应用
- 在Applications文件夹中找到LogMaster
- 或从Launchpad启动

### 2. 连接设备
- 应用会自动检测连接的Android设备
- 从下拉框中选择你的设备

### 3. 开始记录
- 点击"开始"按钮
- 实时查看设备日志

### 4. 高级功能
- **过滤日志**: 选择日志级别（V/D/I/W/E/F）
- **标签过滤**: 输入应用标签，支持正则表达式
- **关键字搜索**: 在日志内容中搜索
- **PID过滤**: 过滤特定进程
- **保存日志**: 点击"保存"按钮导出日志文件

## 🔍 高级过滤示例

### 正则表达式标签过滤
```
MyApp.*          # 匹配以MyApp开头的标签
.*Network.*      # 匹配包含Network的标签
MyApp|System     # 匹配MyApp或System
```

### 多标签匹配
```
MyApp,Network,Database    # 匹配任意一个标签
```

## ⌨️ 快捷键

- `⌘+S` - 保存日志
- `⌘+L` - 清空日志
- `⌘+F` - 聚焦搜索框
- `⌘+R` - 开始/停止记录

## 🛠️ 故障排除

### 应用无法启动
```bash
# 检查Python
python3 --version

# 检查ADB
adb version

# 查看日志
tail -f /tmp/logmaster_debug.log
```

### 设备无法识别
```bash
# 重启ADB服务
adb kill-server
adb start-server

# 检查设备
adb devices
```

### macOS安全提示
如果系统提示"无法验证开发者"：
1. 打开"系统偏好设置" → "安全性与隐私"
2. 点击"仍要打开"
3. 或使用命令: `xattr -cr /Applications/LogMaster.app`

## 📊 性能优化

- **日志缓冲区**: 自动限制10000行，防止内存溢出
- **自动清理**: 定期清理早期日志
- **高效过滤**: 实时过滤不影响性能

## 🎨 界面特色

- **彩色日志**: 不同级别用不同颜色显示
- **现代界面**: 简洁直观的UI设计
- **深色模式**: 适配macOS深色主题
- **响应式**: 支持窗口大小调整

## 📞 技术支持

如遇到问题，请提供：
1. macOS版本（关于本机）
2. Python版本（`python3 --version`）
3. ADB版本（`adb version`）
4. 设备型号和Android版本
5. 错误截图或日志

## 📄 许可证

MIT许可证 - 详见LICENSE文件

---

**享受使用LogMaster Pro！** 🎉