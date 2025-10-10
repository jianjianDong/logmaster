# LogMaster Pro - 开发文档

## 项目概述

LogMaster Pro 是一个专业级的Android日志分析工具，提供比Android Studio Logcat更强大的功能，包括智能过滤、正则表达式支持、彩色日志显示和一键保存等特性。

## 技术架构

### 核心模块

#### 1. DeviceManager (src/core.py)
负责Android设备的检测和管理：
- 自动检测设备连接/断开
- 获取设备详细信息
- 监控设备状态变化
- 提供ADB版本检查

#### 2. LogcatReader (src/core.py)
负责ADB日志的读取和过滤：
- 实时读取logcat输出
- 支持多级过滤（级别、标签、关键字、PID）
- 正则表达式标签匹配
- 大容量日志缓冲
- 日志文件保存

#### 3. GUI模块 (src/gui.py)
基于PyQt5的现代化图形界面：
- 彩色日志显示
- 实时搜索和高亮
- 直观的过滤控制
- 一键保存功能
- 响应式设计

## 安装和运行

### 系统要求
- Python 3.6+
- PyQt5 5.15+
- Android SDK (ADB命令可用)
- macOS 10.12+ / Linux / Windows 10+

### 快速开始

```bash
# 克隆项目
git clone https://github.com/yourusername/LogMasterPro.git
cd LogMasterPro

# 安装依赖
pip install -r requirements.txt

# 运行应用
python3 LogMasterPro.py
```

### 使用启动脚本

```bash
# 通用启动脚本
./scripts/launch.sh

# 环境检查
./scripts/launch.sh --check

# 跳过依赖安装
./scripts/launch.sh --no-deps
```

### macOS应用打包

```bash
# 创建macOS应用包
./scripts/create_macos_app.sh

# 应用将出现在Applications文件夹和桌面
```

## 功能特性

### 智能过滤
- **级别过滤**: Verbose, Debug, Info, Warning, Error, Fatal
- **标签过滤**: 支持正则表达式和多标签匹配
- **关键字过滤**: 在日志消息中搜索
- **PID过滤**: 按进程ID过滤

### 高级搜索
- 实时搜索功能
- 区分大小写选项
- 搜索统计信息
- 查找下一个/上一个

### 彩色显示
- 不同级别使用不同颜色
- 自定义颜色方案
- 高对比度显示

### 数据管理
- 一键保存完整日志
- 自动滚动选项
- 缓冲区管理
- 统计信息显示

## 开发指南

### 项目结构
```
LogMasterPro/
├── src/                    # 源代码目录
│   ├── core.py            # 核心功能模块
│   └── gui.py             # 图形界面模块
├── scripts/               # 脚本文件
│   ├── create_macos_app.sh # macOS应用包创建脚本
│   └── launch.sh          # 通用启动脚本
├── tests/                 # 测试文件
│   ├── generate_test_logs.py  # 测试数据生成器
│   └── test_functionality.py  # 功能测试脚本
├── docs/                  # 文档目录
├── LogMasterPro.py        # 主程序入口
├── requirements.txt       # Python依赖
└── README.md            # 项目文档
```

### 核心类说明

#### LogEntry
日志条目数据结构：
```python
@dataclass
class LogEntry:
    timestamp: str        # 时间戳
    pid: str              # 进程ID
    tid: str              # 线程ID
    level: LogLevel       # 日志级别
    tag: str              # 标签
    message: str          # 消息内容
    raw_line: str         # 原始行
    device_serial: str    # 设备序列号
```

#### Device
设备信息：
```python
class Device:
    serial: str           # 设备序列号
    status: str           # 设备状态
    product: str          # 产品型号
    model: str            # 设备型号
    device: str           # 设备名称
    transport_id: str     # 传输ID
```

### 过滤器系统

支持多种过滤方式：

1. **级别过滤**: 基于日志级别的优先级过滤
2. **标签过滤**: 支持正则表达式和逗号分隔的多标签
3. **关键字过滤**: 在标签和消息中搜索
4. **PID过滤**: 精确匹配进程ID

### 正则表达式支持

标签过滤支持完整的正则表达式语法：

```
MyApp|Network|Database        # 匹配MyApp或Network或Database
.*Test.*                        # 匹配包含Test的标签
^System                         # 匹配以System开头的标签
(MyApp|Network).*               # 匹配MyApp或Network开头的标签
[A-Z].*                         # 匹配大写字母开头的标签
```

## 测试

### 生成测试数据
```bash
# 生成1000条测试日志
python3 tests/generate_test_logs.py --count 1000 --output test_logs.txt

# 实时生成模式
python3 tests/generate_test_logs.py --realtime --interval 0.5
```

### 运行功能测试
```bash
# 运行完整的功能测试
python3 tests/test_functionality.py
```

## 故障排除

### 常见问题

1. **ADB未找到**
   - 确保Android SDK已安装
   - 配置ADB环境变量
   - 安装android-platform-tools

2. **PyQt5安装失败**
   - 使用虚拟环境
   - 安装系统依赖：
     ```bash
     # Ubuntu/Debian
     sudo apt-get install python3-pyqt5
     
     # macOS
     brew install pyqt5
     ```

3. **设备未检测到**
   - 启用USB调试
   - 检查USB连接
   - 重启ADB服务：
     ```bash
     adb kill-server
     adb start-server
     ```

### 调试模式

启动应用时添加调试输出：
```bash
python3 LogMasterPro.py --debug
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 更新日志

### v5.0.0 (2024-10)
- ✨ 全新现代化UI设计
- 🎯 改进的正则表达式支持
- 🔍 增强的搜索功能
- 📱 更好的设备管理
- 🚀 性能优化

### v4.0.0 (2024-09)
- 🎨 彩色日志显示
- 🔧 高级过滤器
- 💾 日志保存功能
- 📊 统计信息显示