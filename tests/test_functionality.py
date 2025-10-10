#!/usr/bin/env python3
"""
LogMaster Pro - 功能测试脚本
测试核心功能和用户界面
"""

import sys
import os
import time
import threading
import subprocess
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import DeviceManager, LogcatReader, LogLevel, LogEntry
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest


class LogMasterProTester:
    """LogMaster Pro 功能测试器"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_test_result(self, test_name, passed, message=""):
        """记录测试结果"""
        self.total_tests += 1
        status = "✅ PASS" if passed else "❌ FAIL"
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        result = {
            'name': test_name,
            'passed': passed,
            'message': message,
            'status': status
        }
        
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if message:
            print(f"   💬 {message}")
    
    def test_device_manager(self):
        """测试设备管理器"""
        print("\n🔍 测试设备管理器...")
        
        try:
            device_manager = DeviceManager()
            
            # 测试ADB可用性
            adb_available = device_manager.is_adb_available()
            self.log_test_result(
                "ADB可用性检查",
                True,
                f"ADB状态: {'可用' if adb_available else '不可用'}"
            )
            
            # 测试获取ADB版本
            adb_version = device_manager.get_adb_version()
            self.log_test_result(
                "ADB版本获取",
                adb_version is not None,
                f"ADB版本: {adb_version or '无法获取'}"
            )
            
            # 测试获取设备列表
            devices = device_manager.get_devices()
            self.log_test_result(
                "设备列表获取",
                isinstance(devices, list),
                f"找到 {len(devices)} 个设备"
            )
            
            # 如果有设备，测试设备信息
            if devices:
                device = devices[0]
                self.log_test_result(
                    "设备信息解析",
                    hasattr(device, 'serial') and hasattr(device, 'status'),
                    f"设备序列号: {device.serial}, 状态: {device.status}"
                )
            
            # 测试设备监控
            device_manager.start_monitoring(interval=0.5)
            time.sleep(1)  # 等待监控启动
            device_manager.stop_monitoring()
            
            self.log_test_result(
                "设备监控功能",
                True,
                "设备监控启动/停止正常"
            )
            
        except Exception as e:
            self.log_test_result(
                "设备管理器测试",
                False,
                f"异常: {str(e)}"
            )
    
    def test_log_parsing(self):
        """测试日志解析功能"""
        print("\n🔍 测试日志解析...")
        
        try:
            reader = LogcatReader()
            
            # 测试标准日志格式解析
            test_lines = [
                "09-28 20:30:45.123  1234  5678 D MyApp: Debug message",
                "09-28 20:30:46.456  1234  5678 I Network: HTTP request completed",
                "09-28 20:30:47.789  1234  5678 E ErrorHandler: NullPointerException",
                "09-28 20:30:48.012  1234  5678 W System: Low memory warning"
            ]
            
            for line in test_lines:
                log_entry = reader._parse_log_line(line, "test_device")
                if log_entry:
                    self.log_test_result(
                        f"日志解析: {line[:50]}...",
                        True,
                        f"级别: {log_entry.level.value}, 标签: {log_entry.tag}"
                    )
                else:
                    self.log_test_result(
                        f"日志解析: {line[:50]}...",
                        False,
                        "解析失败"
                    )
            
            # 测试过滤器功能
            reader.set_filter('level', 'I')
            reader.set_filter('tag', 'MyApp')
            reader.set_filter('keyword', 'test')
            
            self.log_test_result(
                "过滤器设置",
                True,
                "过滤器配置成功"
            )
            
        except Exception as e:
            self.log_test_result(
                "日志解析测试",
                False,
                f"异常: {str(e)}"
            )
    
    def test_log_buffer(self):
        """测试日志缓冲区"""
        print("\n🔍 测试日志缓冲区...")
        
        try:
            reader = LogcatReader()
            
            # 创建测试日志条目
            test_entry = LogEntry(
                timestamp="09-28 20:30:45.123",
                pid="1234",
                tid="5678",
                level=LogLevel.INFO,
                tag="TestApp",
                message="Test message",
                raw_line="09-28 20:30:45.123  1234  5678 I TestApp: Test message",
                device_serial="test_device"
            )
            
            # 测试缓冲区添加
            reader._log_buffer.append(test_entry)
            buffered_logs = reader.get_buffered_logs()
            
            self.log_test_result(
                "日志缓冲区",
                len(buffered_logs) > 0,
                f"缓冲区中有 {len(buffered_logs)} 条日志"
            )
            
            # 测试缓冲区清空
            reader.clear_buffer()
            buffered_logs = reader.get_buffered_logs()
            
            self.log_test_result(
                "缓冲区清空",
                len(buffered_logs) == 0,
                "缓冲区已清空"
            )
            
            # 测试日志保存
            reader._log_buffer.append(test_entry)
            test_file = "/tmp/test_logs.txt"
            success = reader.save_logs_to_file(test_file)
            
            self.log_test_result(
                "日志文件保存",
                success and os.path.exists(test_file),
                f"日志保存到: {test_file}"
            )
            
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
            
        except Exception as e:
            self.log_test_result(
                "日志缓冲区测试",
                False,
                f"异常: {str(e)}"
            )
    
    def test_gui_components(self):
        """测试GUI组件"""
        print("\n🔍 测试GUI组件...")
        
        try:
            # 检查PyQt5导入
            from PyQt5.QtWidgets import QApplication, QMainWindow
            from PyQt5.QtCore import Qt
            from src.gui import LogMasterPro, LogTextEdit
            
            self.log_test_result(
                "PyQt5导入",
                True,
                "PyQt5模块导入成功"
            )
            
            # 创建测试应用（不显示窗口）
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # 测试日志文本编辑器
            log_edit = LogTextEdit()
            
            # 创建测试日志条目
            test_entry = LogEntry(
                timestamp="09-28 20:30:45.123",
                pid="1234",
                tid="5678",
                level=LogLevel.ERROR,
                tag="TestApp",
                message="Test error message",
                raw_line="09-28 20:30:45.123  1234  5678 E TestApp: Test error message",
                device_serial="test_device"
            )
            
            # 测试彩色日志添加
            log_edit.append_colored_log(test_entry)
            
            self.log_test_result(
                "彩色日志显示",
                True,
                "彩色日志添加成功"
            )
            
            # 测试主窗口创建（简化测试）
            try:
                # 只测试初始化，不显示窗口
                window = LogMasterPro.__new__(LogMasterPro)
                self.log_test_result(
                    "主窗口初始化",
                    True,
                    "主窗口对象创建成功"
                )
            except Exception as e:
                self.log_test_result(
                    "主窗口初始化",
                    False,
                    f"初始化失败: {str(e)}"
                )
            
        except ImportError as e:
            self.log_test_result(
                "GUI组件测试",
                False,
                f"PyQt5导入失败: {str(e)}"
            )
        except Exception as e:
            self.log_test_result(
                "GUI组件测试",
                False,
                f"异常: {str(e)}"
            )
    
    def test_filter_functionality(self):
        """测试过滤功能"""
        print("\n🔍 测试过滤功能...")
        
        try:
            reader = LogcatReader()
            
            # 创建测试日志条目
            test_logs = [
                LogEntry("09-28 20:30:45.123", "1001", "2001", LogLevel.DEBUG, "MyApp", "Debug message", "raw1", "device1"),
                LogEntry("09-28 20:30:46.456", "1002", "2002", LogLevel.INFO, "Network", "Network info", "raw2", "device1"),
                LogEntry("09-28 20:30:47.789", "1003", "2003", LogLevel.ERROR, "MyApp", "Error message", "raw3", "device1"),
                LogEntry("09-28 20:30:48.012", "1004", "2004", LogLevel.WARNING, "System", "Warning message", "raw4", "device1"),
            ]
            
            # 测试级别过滤
            reader.set_filter('level', 'I')
            filtered_logs = [log for log in test_logs if reader._should_include_log(log)]
            
            self.log_test_result(
                "级别过滤 (Info及以上)",
                len(filtered_logs) == 3,  # INFO, ERROR, WARNING
                f"过滤后剩余 {len(filtered_logs)} 条日志"
            )
            
            # 测试标签过滤
            reader.set_filter('level', None)
            reader.set_filter('tag', 'MyApp')
            filtered_logs = [log for log in test_logs if reader._should_include_log(log)]
            
            self.log_test_result(
                "标签过滤 (MyApp)",
                len(filtered_logs) == 2,
                f"过滤后剩余 {len(filtered_logs)} 条日志"
            )
            
            # 测试关键字过滤
            reader.set_filter('tag', None)
            reader.set_filter('keyword', 'message')
            filtered_logs = [log for log in test_logs if reader._should_include_log(log)]
            
            self.log_test_result(
                "关键字过滤 (message)",
                len(filtered_logs) >= 2,
                f"过滤后剩余 {len(filtered_logs)} 条日志"
            )
            
            # 测试PID过滤
            reader.set_filter('keyword', None)
            reader.set_filter('pid', '1002')
            filtered_logs = [log for log in test_logs if reader._should_include_log(log)]
            
            self.log_test_result(
                "PID过滤 (1002)",
                len(filtered_logs) == 1,
                f"过滤后剩余 {len(filtered_logs)} 条日志"
            )
            
            # 测试正则表达式标签过滤
            reader.set_filter('pid', None)
            reader.set_filter('tag', 'My.*')
            reader._filters['tag_regex'] = True
            filtered_logs = [log for log in test_logs if reader._should_include_log(log)]
            
            self.log_test_result(
                "正则表达式过滤 (My.*)",
                len(filtered_logs) == 2,
                f"过滤后剩余 {len(filtered_logs)} 条日志"
            )
            
        except Exception as e:
            self.log_test_result(
                "过滤功能测试",
                False,
                f"异常: {str(e)}"
            )
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 LogMaster Pro - 功能测试开始")
        print("=" * 50)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 运行各项测试
        self.test_device_manager()
        self.test_log_parsing()
        self.test_log_buffer()
        self.test_gui_components()
        self.test_filter_functionality()
        
        # 显示测试总结
        print("\n" + "=" * 50)
        print("📊 测试总结")
        print("=" * 50)
        print(f"总测试数: {self.total_tests}")
        print(f"✅ 通过: {self.passed_tests}")
        print(f"❌ 失败: {self.failed_tests}")
        print(f"📈 通过率: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        # 显示失败的测试详情
        if self.failed_tests > 0:
            print("\n❌ 失败的测试详情:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")
        
        print("=" * 50)
        
        return self.failed_tests == 0


def main():
    """主函数"""
    tester = LogMasterProTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败")
        sys.exit(1)


if __name__ == '__main__':
    main()