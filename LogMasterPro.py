#!/usr/bin/env python3
"""
LogMaster Pro - Android日志大师
主程序入口
"""

import sys
import os
import signal
import time

# Always redirect stdout and stderr when frozen to avoid any console-related crashes
if getattr(sys, 'frozen', False):
    try:
        sys.stdout = open('/tmp/logmaster_stdout.log', 'w', buffering=1)
        sys.stderr = open('/tmp/logmaster_stderr.log', 'w', buffering=1)
    except Exception as e:
        pass

# 增加调试信息收集
with open('/tmp/logmaster_debug.log', 'w') as f:
    f.write(f"sys.frozen: {getattr(sys, 'frozen', False)}\n")
    f.write(f"sys.executable: {sys.executable}\n")
    f.write(f"sys.argv: {sys.argv}\n")
    f.write(f"sys.path: {sys.path}\n")
    f.write(f"os.getcwd(): {os.getcwd()}\n")
    f.write(f"sys.stdout: {repr(getattr(sys, 'stdout', None))}\n")
    if getattr(sys, 'frozen', False):
        f.write(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}\n")

# 将src目录添加到Python路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的应用
    current_dir = sys._MEIPASS
else:
    # 如果是源码运行
    current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def signal_handler(signum, frame):
    """处理系统信号"""
    print(f"\n收到信号 {signum}，正在优雅退出...")
    sys.exit(0)

# 设置信号处理
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try:
    from gui import main
    
    print("🚀 启动 LogMaster Pro - Android日志大师")
    print("=" * 60)
    print("✨ 专业级Android日志分析工具")
    print("📱 支持正则表达式标签过滤")
    print("🎯 多标签匹配和高级搜索")
    print("💾 一键保存完整日志")
    print("🌈 彩色日志级别显示")
    print("=" * 60)
    
    # 运行主程序
    exit_code = main()
    sys.exit(exit_code)
    
except ImportError as e:
    import traceback
    with open('/tmp/logmaster_crash.log', 'w', encoding='utf-8') as f:
        f.write(f"ImportError: {e}\n")
        traceback.print_exc(file=f)
    print(f"❌ 导入模块失败: {e}")
    print("请确保已安装PyQt5: pip install PyQt5")
    sys.exit(1)
    
except KeyboardInterrupt:
    print("\n🛑 用户中断程序")
    sys.exit(0)
    
except Exception as e:
    import traceback
    with open('/tmp/logmaster_crash.log', 'w', encoding='utf-8') as f:
        f.write(f"Exception: {e}\n")
        traceback.print_exc(file=f)
    print(f"❌ 程序运行出错: {e}")
    traceback.print_exc()
    sys.exit(1)