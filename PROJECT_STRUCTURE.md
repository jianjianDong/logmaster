# LogMaster Pro 项目目录结构

## 📁 主要目录

```
LogMasterPro/
├── src/                    # 源代码目录
│   ├── core.py            # 核心功能模块（设备管理、日志读取）
│   └── gui.py             # 图形界面模块（PyQt5界面）
├── scripts/               # 脚本文件
│   ├── create_macos_app.sh    # macOS应用包创建脚本
│   ├── create_clean_app.sh     # 清理应用包脚本
│   ├── fix_dock_icon.sh       # Dock图标修复脚本
│   ├── fix_icon_cache.sh      # 图标缓存修复脚本
│   └── launch.sh              # 通用启动脚本
├── dist/                  # 分发包目录
│   └── LogMasterPro_macOS_20251010.tar.gz  # macOS分享包
├── share/                 # 分享相关文件
│   ├── LogMasterPro_macOS/     # 分享包解压目录
│   │   ├── LogMaster.app       # macOS应用包
│   │   ├── install.sh          # 标准安装脚本
│   │   ├── install_onemac.sh   # 一键安装脚本
│   │   ├── start.sh            # 快速启动脚本
│   │   ├── README.md           # 详细使用说明
│   │   ├── requirements.txt    # Python依赖
│   │   └── VERSION.txt         # 版本信息
│   ├── build_share_package.sh  # 分享包构建脚本
│   └── README_SHARE.md         # 分享说明文档
├── tools/                 # 开发工具
│   ├── convert_icon.py    # 图标转换工具
│   ├── create_icons.py     # 图标创建工具
│   └── replace_icon.sh     # 图标替换工具
├── tests/                 # 测试文件
│   ├── generate_test_logs.py   # 测试日志生成器
│   └── legacy/                 # 历史测试文件
├── assets/                # 资源文件
│   └── Logmaster.icns     # 应用图标
├── docs/                  # 文档目录
│   └── development.md     # 开发文档
├── venv/                  # Python虚拟环境（开发用）
├── LogMaster.app/         # 当前构建的macOS应用
├── LogMasterPro.py        # 主程序入口
├── requirements.txt       # Python依赖列表
├── LICENSE               # MIT许可证
├── README.md             # 项目主文档
└── AGENTS.md             # 项目架构文档
```

## 🎯 关键文件说明

### 核心文件
- `src/core.py` - 设备管理、日志读取、过滤逻辑
- `src/gui.py` - PyQt5图形界面、事件处理
- `LogMasterPro.py` - 主程序入口

### 构建脚本
- `scripts/create_macos_app.sh` - 构建macOS应用包
- `share/build_share_package.sh` - 构建分享包

### 分享包
- `dist/LogMasterPro_macOS_*.tar.gz` - 完整的macOS分享包
- `share/install_onemac.sh` - 一键安装脚本

### 文档
- `README.md` - 项目主文档（中文）
- `share/README_SHARE.md` - 分享包使用说明
- `docs/development.md` - 开发文档

## 📤 分享时只需要

分享给朋友时，只需要发送：
```
dist/LogMasterPro_macOS_20251010.tar.gz
```

或者整个 `share/LogMasterPro_macOS/` 目录。

## 🛠️ 开发时使用

开发时主要使用：
- `scripts/create_macos_app.sh` - 构建应用
- `scripts/launch.sh` - 快速启动
- `src/` 目录下的源代码文件