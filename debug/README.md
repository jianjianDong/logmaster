# LogMaster Pro - 清理文件说明

这个文件夹包含了从主项目中移除的调试和测试文件，以及未使用的资源文件。

## 📁 文件组织结构

### debug/ - 调试和测试文件
- `test_dock_exit.py` - macOS dock退出功能测试
- `test_dock_icon.py` - macOS dock图标功能测试  
- `create_icons.py` - 图标生成工具
- `convert_icon.py` - 图标转换工具（如果有）
- `replace_icon.sh` - 图标替换脚本（如果有）

### debug/unused_assets/ - 未使用的资源文件
- `icon_new.png` - 早期版本的图标文件
- `icon_new_512.png` - 早期版本的512px图标文件
- `icon.iconset_new/` - 早期版本的图标集
- `Logmaster.iconset/` - 早期版本的Logmaster图标集
- `.DS_Store` - macOS系统文件

## 🧹 清理说明

### 保留的核心文件
```
assets/
├── icon.icns          # ✅ 当前使用的macOS图标
├── Logmaster.icns     # ✅ 当前使用的图标
├── icon.png           # ✅ 当前使用的PNG图标
└── icons/              # ✅ 图标生成源文件
    ├── icon.png
    ├── icon_16x16.png
    ├── icon_32x32.png
    └── ...
```

### 移除的文件类型
1. **测试文件** - 移动到debug/文件夹
2. **工具脚本** - 移动到debug/文件夹  
3. **未使用的图标变体** - 移动到debug/unused_assets/
4. **系统缓存文件** - 删除(.DS_Store, __pycache__等)

## 🚀 使用建议

### 如果需要使用调试工具
```bash
cd debug/
python3 test_dock_icon.py    # 测试dock图标
python3 create_icons.py      # 重新生成图标
```

### 如果需要恢复早期图标
```bash
# 从unused_assets中复制需要的文件
cp debug/unused_assets/icon_new.png assets/
```

## 📋 清理结果

- ✅ 项目根目录更整洁
- ✅ 核心文件更容易识别
- ✅ 调试工具仍然可用
- ✅ 未使用资源已归档
- ✅ Python缓存文件已清理

## 🔧 维护建议

1. **定期清理** - 定期检查并清理新的未使用文件
2. **版本控制** - 重要文件变更前做好备份
3. **文档更新** - 及时更新此说明文件
4. **测试分离** - 新的测试文件直接放入debug/文件夹