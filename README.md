# 🚀 LogMaster Pro

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](https://github.com/yourusername/LogMasterPro)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 项目介绍

**LogMaster Pro** 是一款专业级的Android日志分析工具，专为开发者和测试工程师打造。它提供了比Android Studio Logcat更强大的功能，包括智能过滤、正则表达式支持、彩色日志显示和一键保存等特性。

### ✨ 核心特性

- 🎯 **智能标签过滤** - 支持正则表达式和多标签匹配
- 🌈 **彩色日志显示** - 不同级别日志用不同颜色区分
- 🔍 **高级搜索功能** - 实时搜索，支持大小写敏感选项
- 💾 **一键保存日志** - 完整保存所有日志到文件
- 📱 **自动设备检测** - 实时监控设备连接状态
- ⚡ **高性能处理** - 支持大量日志的实时显示
- 🎨 **现代化界面** - 直观易用的图形界面

## 🚀 快速开始

### 📋 系统要求

- **操作系统**: macOS 10.12+ / Linux / Windows 10+
- **Python**: 3.6 或更高版本
- **Android SDK**: 需要ADB命令可用
- **依赖库**: PyQt5

### 📦 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/LogMasterPro.git
cd LogMasterPro
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **确保ADB可用**
```bash
adb version
```

### 🎯 使用方法

#### 方法1: 直接运行
```bash
python3 LogMasterPro.py
```

#### 方法2: 独立安装包（推荐）
对于非开发者用户，你可以使用打包脚本生成一个完全独立的 macOS 应用程序（`.dmg`格式），用户无需安装 Python 也能直接运行。
```bash
./scripts/build_app.sh
```
执行完毕后，将生成的 `dist/LogMasterPro.dmg` 发送给其他用户即可。

#### 方法3: 创建macOS外壳应用
```bash
./scripts/create_macos_app.sh
# 然后在Applications文件夹中找到LogMaster
```

#### 方法4: 使用启动脚本
```bash
./scripts/launch.sh
```

## 🎨 界面功能

### 📱 主界面布局
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 LogMaster Pro - Android日志大师                        │
├─────────────────────────────────────────────────────────────┤
│ ▶️ 开始记录 💾 保存 🗑️ 清空 🔍 查找 ⬇️ 自动滚动        │
├─────────────────────────────────────────────────────────────┤
│ 📱 设备: [设备选择] 🔄 刷新设备 🧹 清除缓冲区 统计信息    │
├─────────────────────────────────────────────────────────────┤
│ 🔍 级别: [下拉框] 标签: [正则支持] 关键字: [输入框] PID:  │
│ 🔍 搜索: [输入框] [区分大小写] ⬇️ 下一个 ⬆️ 上一个      │
│ 💡 标签过滤支持正则表达式和多标签匹配                      │
├─────────────────────────────────────────────────────────────┤
│                                                           │
│ 📝 日志显示区域 (彩色显示)                                │
│ 09-28 20:30:45.123 1234/5678 D TestTag: 调试信息 - 蓝色   │
│ 09-28 20:30:46.456 1234/5678 I MyApp: 信息日志 - 绿色     │
│ 09-28 20:30:47.789 1234/5678 E ErrorTag: 错误信息 - 红色  │
│                                                           │
└─────────────────────────────────────────────────────────────┘
```

### 🌈 日志级别颜色

- **Verbose (V)** - ⬜ 灰色 - 最详细的日志信息
- **Debug (D)** - 🔵 蓝色 - 调试信息  
- **Info (I)** - 🟢 绿色 - 一般信息
- **Warning (W)** - 🟠 橙色 - 警告信息
- **Error (E)** - 🔴 红色 - 错误信息
- **Fatal (F)** - 🟣 紫色 - 致命错误

### 🔍 高级过滤功能

#### 标签过滤（支持正则表达式）
- **多标签匹配**: `MyApp,Network,Database`
- **正则表达式**: `.*Test.*|.*Debug.*`
- **组合使用**: `MyApp,.*Error.*,^System`

#### 正则表达式示例
```
MyApp|Network|Database        # 匹配MyApp或Network或Database
.*Test.*                        # 匹配包含Test的标签
^System                         # 匹配以System开头的标签
(?!System).*                    # 负向前瞻，不匹配System开头的标签
[A-Z].*                         # 匹配大写字母开头的标签
```

## ⌨️ 快捷键

- `Ctrl+S` - 保存日志
- `Ctrl+L` - 清空日志  
- `Ctrl+Q` - 退出应用
- `Ctrl+F` - 聚焦搜索框

## 🛠️ 开发指南

### 项目结构
```
LogMasterPro/
├── src/                    # 源代码目录
│   ├── core.py            # 核心功能模块
│   └── gui.py             # 图形界面模块
├── scripts/               # 脚本文件
│   ├── create_macos_app.sh # macOS应用包创建脚本
│   └── launch.sh          # 通用启动脚本
├── docs/                  # 文档目录
├── tests/                 # 测试文件
├── assets/                # 资源文件（图标等）
├── LogMasterPro.py        # 主程序入口
├── requirements.txt       # Python依赖
├── README.md            # 项目文档
└── LICENSE              # 许可证
```

### 核心模块

#### DeviceManager
负责Android设备的检测和管理
- 自动检测设备连接/断开
- 获取设备详细信息
- 监控设备状态变化

#### LogcatReader  
负责ADB日志的读取和过滤
- 实时读取logcat输出
- 支持多级过滤（级别、标签、关键字、PID）
- 正则表达式标签匹配
- 大容量日志缓冲

#### GUI模块
基于PyQt5的现代化图形界面
- 彩色日志显示
- 实时搜索和高亮
- 直观的过滤控制
- 一键保存功能

## 🧪 测试

运行测试脚本验证功能：
```bash
# 生成测试日志
python3 tests/generate_test_logs.py

# 运行功能测试
python3 tests/test_functionality.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 强大的GUI框架
- [Android Debug Bridge](https://developer.android.com/studio/command-line/adb) - Android调试工具


<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个星！** 

Made with ❤️ by [BPP](https://github.com/jianjianDong)

</div>