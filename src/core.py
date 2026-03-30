#!/usr/bin/env python3
"""
LogMaster Pro - Android日志大师
一个专业级的Android日志分析工具
"""

import sys
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    VERBOSE = "V"
    DEBUG = "D"
    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    FATAL = "F"


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    pid: str
    tid: str
    level: LogLevel
    tag: str
    message: str
    raw_line: str
    device_serial: str = ""


class Device:
    """设备信息"""
    def __init__(self, serial: str, status: str, product: str = "", model: str = "", device: str = "", transport_id: str = ""):
        self.serial = serial
        self.status = status
        self.product = product
        self.model = model
        self.device = device
        self.transport_id = transport_id


class DeviceManager:
    """设备管理器"""
    def __init__(self):
        self.devices: List[Device] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: List[Callable] = []
        
    def add_device_callback(self, callback: Callable):
        """添加设备变化回调函数"""
        self._callbacks.append(callback)
        
    def _notify_callbacks(self):
        """通知所有回调函数设备列表已更新"""
        for callback in self._callbacks:
            try:
                callback(self.devices)
            except Exception as e:
                print(f"回调函数执行错误: {e}")
    
    def get_devices(self, notify=True) -> List[Device]:
        """获取当前连接的设备列表"""
        try:
            # First try adb devices
            result = subprocess.run(['adb', 'devices', '-l'], 
                                  capture_output=True, text=True, timeout=5)
            
            # If adb is not found or fails, try looking for it in common locations
            if result.returncode != 0:
                adb_path = ''
                if os.environ.get('ANDROID_HOME'):
                    adb_path = os.path.join(os.environ.get('ANDROID_HOME'), 'platform-tools', 'adb')
                elif os.environ.get('ANDROID_SDK_ROOT'):
                    adb_path = os.path.join(os.environ.get('ANDROID_SDK_ROOT'), 'platform-tools', 'adb')
                else:
                    home = os.path.expanduser('~')
                    common_paths = [
                        os.path.join(home, 'Library/Android/sdk/platform-tools/adb'),
                        '/usr/local/bin/adb',
                        '/opt/homebrew/bin/adb'
                    ]
                    for p in common_paths:
                        if os.path.exists(p):
                            adb_path = p
                            break
                            
                if adb_path and os.path.exists(adb_path):
                    result = subprocess.run([adb_path, 'devices', '-l'], 
                                          capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                self._parse_devices_output(result.stdout)
            else:
                print(f"ADB命令执行失败: {result.stderr}")
                self.devices = []
        except subprocess.TimeoutExpired:
            print("ADB命令超时")
            self.devices = []
        except FileNotFoundError:
            print("未找到ADB命令，请确保Android SDK已安装并配置环境变量")
            self.devices = []
        except Exception as e:
            print(f"获取设备列表时出错: {e}")
            self.devices = []
            
        if notify:
            self._notify_callbacks()
        return self.devices
    
    def _parse_devices_output(self, output: str):
        """解析adb devices -l的输出"""
        devices = []
        lines = output.strip().split('\n')
        
        for line in lines[1:]:  # 跳过第一行的"List of devices attached"
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]
                
                device = Device(serial=serial, status=status)
                
                # 解析额外的设备信息
                for part in parts[2:]:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        if key == 'product':
                            device.product = value
                        elif key == 'model':
                            device.model = value
                        elif key == 'device':
                            device.device = value
                        elif key == 'transport_id':
                            device.transport_id = value
                
                devices.append(device)
        
        self.devices = devices
    
    def start_monitoring(self, interval: float = 3.0):
        """开始监控设备连接状态 - 降低频率避免过于敏感"""
        if self._running:
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_devices, 
                                            args=(interval,), daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控设备连接状态 - 增强版"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            # 给线程一个机会自然结束
            self._monitor_thread.join(timeout=1)  # 减少等待时间
            if self._monitor_thread.is_alive():
                print("警告: 设备监控线程停止超时")
    
    def _monitor_devices(self, interval: float):
        """监控设备连接状态的线程函数"""
        previous_devices = self.get_devices(notify=False).copy()
        
        while self._running:
            time.sleep(interval)
            current_devices = self.get_devices(notify=False)
            
            # 检查设备变化
            if self._devices_changed(previous_devices, current_devices):
                self._handle_device_change(previous_devices, current_devices)
                previous_devices = current_devices.copy()
                self._notify_callbacks()
    
    def _devices_changed(self, old_devices: List[Device], 
                        new_devices: List[Device]) -> bool:
        """检查设备列表是否发生变化 - 增强版，忽略轻微状态波动"""
        if len(old_devices) != len(new_devices):
            return True
            
        old_serials = {d.serial for d in old_devices}
        new_serials = {d.serial for d in new_devices}
        
        # 检查是否有真正的设备增减，而不是状态变化
        if old_serials != new_serials:
            return True
            
        # 检查设备状态是否有重大变化，忽略轻微的状态波动
        old_status = {d.serial: d.status for d in old_devices}
        new_status = {d.serial: d.status for d in new_devices}
        
        for serial in old_serials:
            old_stat = old_status.get(serial)
            new_stat = new_status.get(serial)
            
            if old_stat != new_stat:
                # 只有当状态发生实质性变化时才认为有变化
                # 忽略: device <-> host, device <-> recovery 等轻微波动
                # 只关注: device <-> offline, device <-> unauthorized 等重大变化
                significant_changes = [
                    ('device', 'offline'), ('offline', 'device'),
                    ('device', 'unauthorized'), ('unauthorized', 'device'),
                    ('offline', 'unauthorized'), ('unauthorized', 'offline')
                ]
                
                if (old_stat, new_stat) in significant_changes:
                    return True
        
        return False
    
    def _handle_device_change(self, old_devices: List[Device], 
                             new_devices: List[Device]):
        """处理设备变化事件"""
        old_serials = {d.serial for d in old_devices}
        new_serials = {d.serial for d in new_devices}
        
        connected = new_serials - old_serials
        disconnected = old_serials - new_serials
        
        if connected:
            print(f"🔄 设备连接: {connected}")
        if disconnected:
            print(f"🔄 设备断开: {disconnected}")
        
        # 如果有设备变化，通知回调函数
        if connected or disconnected:
            print(f"📊 设备变化统计 - 连接: {len(connected)}, 断开: {len(disconnected)}")
            for callback in self._callbacks:
                try:
                    callback(new_devices)
                except Exception as e:
                    print(f"设备变化回调执行错误: {e}")
    
    def is_adb_available(self) -> bool:
        """检查ADB是否可用"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=3)
            return result.returncode == 0
        except:
            return False
    
    def get_adb_version(self) -> Optional[str]:
        """获取ADB版本"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                # 解析版本信息
                match = re.search(r'Android Debug Bridge version (\d+\.\d+\.\d+)', 
                                result.stdout)
                if match:
                    return match.group(1)
            return None
        except:
            return None


class LogcatReader:
    """日志读取器"""
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self._read_thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: List[Callable] = []
        self._filters = {
            'level': None,
            'tag': None,
            'tag_regex': False,
            'keyword': None,
            'pid': None
        }
        self._buffer_size = 10000  # 缓冲区大小
        self._log_buffer: List[LogEntry] = []
        self._buffer_lock = threading.Lock()
        self._last_log_time = time.time()
        self._log_count = 0
        self._health_check_thread: Optional[threading.Thread] = None  # 健康检查线程
        self._health_check_running = False
        
    def add_log_callback(self, callback: Callable):
        """添加日志回调函数"""
        self._callbacks.append(callback)
        
    def remove_log_callback(self, callback: Callable):
        """移除日志回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
        
    def _notify_callbacks(self, log_entry: LogEntry):
        """通知所有回调函数有新的日志条目"""
        for callback in self._callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                print(f"日志回调函数执行错误: {e}")
    
    def start_logcat(self, device_serial: str, clear_buffer: bool = True,
                    filters: Optional[dict] = None):
        """开始读取logcat - 修复过滤器更新逻辑，增强健壮性"""
        if self._running:
            self.stop_logcat()
        
        if clear_buffer:
            self._clear_logcat_buffer(device_serial)
        
        # 应用过滤器 - 正确处理None值
        if filters:
            for key, value in filters.items():
                self._filters[key] = value
        
        # 构建adb logcat命令 - 简化命令，避免复杂参数
        cmd = ['adb', '-s', device_serial, 'logcat', '-v', 'threadtime']
        
        # 应用级别过滤器
        if self._filters['level']:
            cmd.extend(['*:' + self._filters['level']])
        
        print(f"启动logcat命令: {' '.join(cmd)}")
        print(f"过滤器设置: {self._filters}")
        
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          universal_newlines=True,
                                          bufsize=1)
            
            self._running = True
            self._log_count = 0
            self._last_log_time = time.time()
            
            self._read_thread = threading.Thread(target=self._read_logcat_output,
                                               args=(device_serial,), 
                                               daemon=True)
            self._read_thread.start()
            
            # 启动健康检查线程
            self._start_health_check(device_serial)
            
            print("Logcat读取线程已启动")
            
        except Exception as e:
            print(f"启动logcat失败: {e}")
            self._running = False
            
    def stop_logcat(self):
        """停止读取logcat - 增强版，包含健康检查线程停止"""
        print("正在停止logcat...")
        self._running = False
        self._health_check_running = False
        
        # 停止健康检查线程
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=1)
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print("进程终止超时，强制杀死进程")
                self.process.kill()
            except Exception as e:
                print(f"停止进程时出错: {e}")
            finally:
                self.process = None
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2)
            
        print("Logcat已停止")
    
    def _clear_logcat_buffer(self, device_serial: str):
        """清除logcat缓冲区"""
        try:
            result = subprocess.run(['adb', '-s', device_serial, 'logcat', '-c'], 
                                   capture_output=True, timeout=5)
            print(f"清除缓冲区结果: {result.returncode}")
        except Exception as e:
            print(f"清除缓冲区失败: {e}")
    
    def _read_logcat_output(self, device_serial: str):
        """读取logcat输出的线程函数 - 增强异常处理和自动恢复"""
        print("开始读取logcat输出...")
        if not self.process:
            print("进程不存在")
            return
            
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while self._running and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if not line:
                        # 如果连续10次都读到空行，认为进程可能有问题
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"连续{max_consecutive_errors}次读取空行，可能进程异常")
                            break
                        time.sleep(0.01)  # 短暂等待，避免CPU占用过高
                        continue
                    
                    # 重置错误计数
                    consecutive_errors = 0
                    
                    # 调试输出
                    if self._log_count < 5:  # 只显示前5行的调试信息
                        print(f"原始日志行: {line.strip()}")
                    
                    log_entry = self._parse_log_line(line.strip(), device_serial)
                    if log_entry:
                        self._log_count += 1
                        
                        # 应用过滤器
                        if self._should_include_log(log_entry):
                            # 添加到缓冲区
                            with self._buffer_lock:
                                self._log_buffer.append(log_entry)
                                if len(self._log_buffer) > self._buffer_size:
                                    self._log_buffer.pop(0)
                            
                            # 通知回调
                            self._notify_callbacks(log_entry)
                            
                            # 更新最后日志时间
                            self._last_log_time = time.time()
                            
                            if self._log_count <= 5:
                                print(f"处理日志: {log_entry.tag} - {log_entry.message[:50]}")
                        else:
                            if self._log_count <= 5:
                                print(f"日志被过滤: {log_entry.tag} - {log_entry.message[:50]}")
                                
                except Exception as inner_e:
                    consecutive_errors += 1
                    print(f"处理单行日志时出错 ({consecutive_errors}/{max_consecutive_errors}): {inner_e}")
                    
                    # 如果连续错误太多，退出循环
                    if consecutive_errors >= max_consecutive_errors:
                        print("连续错误过多，停止日志读取")
                        break
                        
                    # 短暂延迟后重试
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"读取logcat输出时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._running = False
            process_status = self.process.poll() if self.process else 'None'
            print(f"日志读取线程结束，运行状态: {self._running}, 进程状态: {process_status}")
            print(f"总共处理了 {self._log_count} 条日志")
            
            # 如果是因为异常退出且仍在运行状态，通知外部需要重启
            if self._running and consecutive_errors >= max_consecutive_errors:
                print("日志读取异常终止，建议外部重启")
    
    def _parse_log_line(self, line: str, device_serial: str) -> Optional[LogEntry]:
        """解析logcat输出行"""
        if not line:
            return None
            
        # 解析格式: MM-DD HH:MM:SS.mmm PID TID L TAG: message
        pattern = r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+([^:\s]+):\s+(.*)'
        
        match = re.match(pattern, line)
        if match:
            timestamp, pid, tid, level, tag, message = match.groups()
            
            try:
                log_level = LogLevel(level)
            except ValueError:
                log_level = LogLevel.VERBOSE
            
            return LogEntry(
                timestamp=timestamp,
                pid=pid,
                tid=tid,
                level=log_level,
                tag=tag,
                message=message,
                raw_line=line,
                device_serial=device_serial
            )
        
        # 如果正则表达式匹配失败，尝试更宽松的匹配
        loose_pattern = r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+(.*)'
        loose_match = re.match(loose_pattern, line)
        if loose_match:
            timestamp, pid, tid, level, rest = loose_match.groups()
            
            # 尝试从剩余部分提取标签和消息
            if ':' in rest:
                tag, message = rest.split(':', 1)
                tag = tag.strip()
                message = message.strip()
            else:
                tag = "Unknown"
                message = rest
            
            try:
                log_level = LogLevel(level)
            except ValueError:
                log_level = LogLevel.VERBOSE
            
            return LogEntry(
                timestamp=timestamp,
                pid=pid,
                tid=tid,
                level=log_level,
                tag=tag,
                message=message,
                raw_line=line,
                device_serial=device_serial
            )
        
        return None
    
    def _should_include_log(self, log_entry: LogEntry) -> bool:
        """检查日志条目是否应该被包含（应用过滤器）"""
        # 级别过滤
        if self._filters['level']:
            level_priority = {
                'V': 0, 'D': 1, 'I': 2, 'W': 3, 'E': 4, 'F': 5
            }
            entry_priority = level_priority.get(log_entry.level.value, 0)
            filter_priority = level_priority.get(self._filters['level'], 0)
            if entry_priority < filter_priority:
                return False
        
        # 标签过滤 - 支持正则表达式和多标签匹配
        if self._filters['tag']:
            filter_tag = self._filters['tag'].strip()
            entry_tag = log_entry.tag.strip()
            
            # 检查是否启用正则表达式模式
            if self._filters.get('tag_regex', False):
                try:
                    # 使用正则表达式匹配
                    if not re.search(filter_tag, entry_tag, re.IGNORECASE):
                        return False
                except re.error:
                    # 如果正则表达式无效，降级为普通匹配
                    if filter_tag.lower() not in entry_tag.lower():
                        return False
            else:
                # 检查是否包含逗号分隔的多个标签
                if ',' in filter_tag:
                    # 多个标签，使用OR逻辑
                    tags = [tag.strip().lower() for tag in filter_tag.split(',')]
                    if not any(tag in entry_tag.lower() for tag in tags):
                        return False
                else:
                    # 单个标签，使用包含匹配
                    if filter_tag.lower() not in entry_tag.lower():
                        return False
        
        # 关键字过滤 - 在标签和消息中搜索，不区分大小写
        if self._filters['keyword']:
            keyword = self._filters['keyword'].lower().strip()
            entry_tag = log_entry.tag.lower().strip()
            entry_message = log_entry.message.lower().strip()
            
            # 关键字必须在标签或消息中找到
            if keyword not in entry_tag and keyword not in entry_message:
                return False
        
        # PID过滤
        if self._filters['pid']:
            if log_entry.pid != self._filters['pid']:
                return False
        
        return True
    
    def set_filter(self, filter_type: str, value: Optional[str]):
        """设置过滤器"""
        if filter_type in self._filters:
            old_value = self._filters[filter_type]
            self._filters[filter_type] = value
            
            if old_value != value:
                print(f"过滤器 {filter_type} 更新: {old_value} -> {value}")
    
    def get_buffered_logs(self) -> List[LogEntry]:
        """获取缓冲区中的日志"""
        with self._buffer_lock:
            return self._log_buffer.copy()
    
    def clear_buffer(self):
        """清空日志缓冲区"""
        with self._buffer_lock:
            self._log_buffer.clear()
            self._log_count = 0
    
    def save_logs_to_file(self, filename: str, logs: Optional[List[LogEntry]] = None):
        """保存日志到文件"""
        if logs is None:
            logs = self.get_buffered_logs()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"LogMaster Pro - Android日志\n")
                f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
                device_serial = getattr(logs[0], 'device_serial', 'Unknown') if logs else 'Unknown'
                f.write(f"设备: {device_serial}\n")
                f.write(f"日志数量: {len(logs)}\n")
                f.write("=" * 80 + "\n\n")
                
                for log_entry in logs:
                    if hasattr(log_entry, 'raw_line'):
                        f.write(f"{log_entry.raw_line}\n")
                    else:
                        f.write(f"{log_entry}\n")
                    
            print(f"日志保存成功: {filename} ({len(logs)} 条)")
            return True
        except Exception as e:
            print(f"保存日志文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_stats(self):
        """获取统计信息"""
        with self._buffer_lock:
            return {
                'total_logs': len(self._log_buffer),
                'processed_logs': self._log_count,
                'last_log_time': self._last_log_time,
                'is_running': self._running
            }
    
    def _start_health_check(self, device_serial: str):
        """启动健康检查线程"""
        if self._health_check_running:
            return
            
        self._health_check_running = True
        self._health_check_thread = threading.Thread(target=self._health_check_loop,
                                                   args=(device_serial,), 
                                                   daemon=True)
        self._health_check_thread.start()
        print("健康检查线程已启动")
    
    def _health_check_loop(self, device_serial: str):
        """健康检查循环"""
        check_interval = 5  # 每5秒检查一次
        max_idle_time = 30  # 最大空闲时间30秒
        
        while self._health_check_running and self._running:
            try:
                current_time = time.time()
                idle_time = current_time - self._last_log_time
                
                # 检查进程状态
                process_alive = (self.process and self.process.poll() is None)
                
                # 如果进程不在运行，退出循环
                if not process_alive:
                    print("健康检查: ADB进程已停止")
                    break
                
                # 如果空闲时间太长，认为可能有问题
                if idle_time > max_idle_time and self._log_count > 0:
                    print(f"健康检查警告: 日志空闲时间超过{max_idle_time}秒 (空闲: {idle_time:.1f}秒)")
                    # 这里可以添加重启逻辑，但暂时只警告
                
                # 检查线程状态
                thread_alive = (self._read_thread and self._read_thread.is_alive())
                if not thread_alive:
                    print("健康检查警告: 读取线程已停止")
                    break
                    
            except Exception as e:
                print(f"健康检查出错: {e}")
                
            # 等待下一次检查
            time.sleep(check_interval)
        
        print("健康检查线程结束")
        # 如果健康检查线程结束，但主线程还在运行，说明有问题
        if self._running:
            print("健康检查线程异常结束，建议重启日志记录")