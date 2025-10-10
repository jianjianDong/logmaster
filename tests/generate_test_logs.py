#!/usr/bin/env python3
"""
LogMaster Pro - 测试数据生成器
生成模拟的Android日志数据用于测试
"""

import random
import time
import datetime
import threading
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import LogLevel


class LogGenerator:
    """日志生成器"""
    
    def __init__(self):
        self.tags = [
            "ActivityManager", "WindowManager", "SystemServer", "PackageManager",
            "MyApp", "NetworkLib", "DatabaseHelper", "CrashHandler",
            "LocationService", "PushService", "Analytics", "Logger",
            "HttpClient", "ImageLoader", "CacheManager", "ConfigManager",
            "UserService", "AuthManager", "FileUtils", "StringUtils",
            "MainActivity", "LoginActivity", "HomeFragment", "SettingsFragment",
            "NetworkReceiver", "BootReceiver", "AlarmReceiver", "GcmReceiver"
        ]
        
        self.messages = {
            LogLevel.VERBOSE: [
                "Detailed trace information",
                "Method entry: onCreate()",
                "Variable state: user_id=12345",
                "Loop iteration: i=0",
                "Function parameters: name=John, age=25",
                "Memory usage: 45MB",
                "Cache hit for key: user_profile_123",
                "Network request queued",
                "Database query prepared",
                "File read operation started"
            ],
            LogLevel.DEBUG: [
                "Debug: User authenticated successfully",
                "Loading configuration from assets",
                "Network request: GET /api/users/123",
                "Database connection established",
                "Cache initialized with 256MB capacity",
                "Image loaded from: https://example.com/image.jpg",
                "Activity lifecycle: onResume()",
                "Service started: LocationService",
                "Broadcast received: android.net.conn.CONNECTIVITY_CHANGE",
                "SharedPreferences loaded: app_settings.xml"
            ],
            LogLevel.INFO: [
                "Application started successfully",
                "User logged in: john@example.com",
                "Data synchronized with server",
                "New version available: 2.1.0",
                "Configuration updated",
                "Background service started",
                "Network connectivity restored",
                "Cache cleared successfully",
                "Database migration completed",
                "Push notification registered"
            ],
            LogLevel.WARNING: [
                "Low memory warning: 85% usage",
                "Network timeout, retrying...",
                "Deprecated API usage detected",
                "Battery level low: 15%",
                "Cache size exceeded limit",
                "SSL certificate validation skipped",
                "Location permission not granted",
                "Image loading failed, using placeholder",
                "Database query slow: 2.5s execution time",
                "Network request rate limited"
            ],
            LogLevel.ERROR: [
                "Network request failed: Connection timeout",
                "Database error: UNIQUE constraint failed",
                "File not found: /data/app/config.json",
                "NullPointerException in MainActivity.onCreate()",
                "SSL handshake failed",
                "Out of memory error",
                "Invalid API response format",
                "Permission denied: android.permission.CAMERA",
                "Service binding failed",
                "Crash report: java.lang.IllegalStateException"
            ],
            LogLevel.FATAL: [
                "FATAL EXCEPTION: main",
                "Application crash: Unhandled exception",
                "Critical error: Database corruption detected",
                "System error: Unable to allocate memory",
                "Fatal: Core service initialization failed",
                "Critical: Security breach detected",
                "Fatal error: Configuration file corrupted",
                "System crash: Kernel panic",
                "Critical failure: Unable to recover",
                "Fatal: Application state inconsistent"
            ]
        }
    
    def generate_log_entry(self):
        """生成单个日志条目"""
        # 随机选择日志级别
        level = random.choice(list(LogLevel))
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime("%m-%d %H:%M:%S.%f")[:-3]  # 毫秒精度
        
        # 随机PID和TID
        pid = random.randint(1000, 9999)
        tid = random.randint(1000, 9999)
        
        # 随机标签
        tag = random.choice(self.tags)
        
        # 随机消息
        message = random.choice(self.messages[level])
        
        # 偶尔添加额外信息
        if random.random() < 0.3:
            if level in [LogLevel.ERROR, LogLevel.FATAL]:
                message += f" (Error code: {random.randint(1000, 9999)})"
            elif level == LogLevel.WARNING:
                message += f" (Warning ID: {random.randint(100, 999)})"
        
        # 构建完整的日志行
        log_line = f"{timestamp} {pid:4d} {tid:4d} {level.value} {tag}: {message}"
        
        return {
            'timestamp': timestamp,
            'pid': str(pid),
            'tid': str(tid),
            'level': level,
            'tag': tag,
            'message': message,
            'raw_line': log_line
        }
    
    def generate_logs(self, count=100, delay=0.1):
        """生成多个日志条目"""
        logs = []
        for i in range(count):
            log_entry = self.generate_log_entry()
            logs.append(log_entry)
            
            if delay > 0:
                time.sleep(delay)
            
            # 显示进度
            if (i + 1) % 10 == 0:
                print(f"已生成 {i + 1}/{count} 条日志")
        
        return logs
    
    def save_logs_to_file(self, filename, count=1000):
        """保存日志到文件"""
        print(f"正在生成 {count} 条测试日志...")
        logs = self.generate_logs(count, delay=0)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"LogMaster Pro - 测试日志数据\n")
            f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"日志数量: {count}\n")
            f.write("=" * 80 + "\n\n")
            
            for log_entry in logs:
                f.write(log_entry['raw_line'] + "\n")
        
        print(f"✅ 测试日志已保存到: {filename}")
        return len(logs)


class RealTimeLogGenerator:
    """实时日志生成器"""
    
    def __init__(self, callback=None):
        self.generator = LogGenerator()
        self.callback = callback
        self.running = False
        self.thread = None
    
    def start(self, interval=0.5):
        """开始实时生成日志"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._generate_loop, args=(interval,))
        self.thread.daemon = True
        self.thread.start()
        print("🚀 实时日志生成器已启动")
    
    def stop(self):
        """停止实时生成日志"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("⏹️  实时日志生成器已停止")
    
    def _generate_loop(self, interval):
        """生成循环"""
        count = 0
        while self.running:
            log_entry = self.generator.generate_log_entry()
            
            if self.callback:
                self.callback(log_entry)
            else:
                print(log_entry['raw_line'])
            
            count += 1
            time.sleep(interval)
            
            # 偶尔显示统计信息
            if count % 20 == 0:
                print(f"📊 已生成 {count} 条日志")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LogMaster Pro - 测试日志生成器')
    parser.add_argument('--count', '-c', type=int, default=1000,
                       help='生成的日志数量 (默认: 1000)')
    parser.add_argument('--output', '-o', default='test_logs.txt',
                       help='输出文件名 (默认: test_logs.txt)')
    parser.add_argument('--realtime', '-r', action='store_true',
                       help='实时生成模式')
    parser.add_argument('--interval', '-i', type=float, default=0.5,
                       help='实时生成间隔 (秒, 默认: 0.5)')
    parser.add_argument('--pipe', '-p', action='store_true',
                       help='管道模式，直接输出到stdout')
    
    args = parser.parse_args()
    
    print("🚀 LogMaster Pro - 测试日志生成器")
    print("=" * 40)
    
    generator = LogGenerator()
    
    if args.realtime:
        # 实时生成模式
        def log_callback(log_entry):
            if args.pipe:
                print(log_entry['raw_line'])
            else:
                print(f"📋 {log_entry['raw_line']}")
        
        realtime_gen = RealTimeLogGenerator(callback=log_callback)
        
        try:
            realtime_gen.start(args.interval)
            print(f"🔄 实时生成中，间隔: {args.interval}s (按Ctrl+C停止)")
            
            # 保持运行
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n🛑 用户中断")
            realtime_gen.stop()
    
    else:
        # 批量生成模式
        print(f"📊 生成 {args.count} 条测试日志...")
        count = generator.save_logs_to_file(args.output, args.count)
        print(f"✅ 完成！共生成 {count} 条日志")
        
        # 显示统计信息
        print("\n📈 日志级别分布:")
        level_counts = {}
        with open(args.output, 'r') as f:
            for line in f:
                if ' V ' in line:
                    level_counts['V'] = level_counts.get('V', 0) + 1
                elif ' D ' in line:
                    level_counts['D'] = level_counts.get('D', 0) + 1
                elif ' I ' in line:
                    level_counts['I'] = level_counts.get('I', 0) + 1
                elif ' W ' in line:
                    level_counts['W'] = level_counts.get('W', 0) + 1
                elif ' E ' in line:
                    level_counts['E'] = level_counts.get('E', 0) + 1
                elif ' F ' in line:
                    level_counts['F'] = level_counts.get('F', 0) + 1
        
        for level, count in sorted(level_counts.items()):
            print(f"  {level}: {count}")


if __name__ == '__main__':
    main()