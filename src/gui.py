import sys
import os
import time
import signal
import threading
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QComboBox, 
                           QLabel, QLineEdit, QFileDialog, QMessageBox,
                           QGroupBox, QCheckBox, QMenuBar, QStatusBar, 
                           QAction, QToolBar, QPlainTextEdit, QScrollBar, QProgressBar,
                           QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QTextCursor, QTextDocument, QPainter, QPen

# 将当前目录添加到Python路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的应用
    current_dir = sys._MEIPASS
else:
    # 如果是源码运行
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)

from src.core import DeviceManager, Device, LogcatReader, LogEntry, LogLevel


class LogUpdateThread(QThread):
    """日志更新线程"""
    log_received = pyqtSignal(list)  # 重新改回 list，以实现真正的性能优化
    
    def __init__(self, logcat_reader: LogcatReader):
        super().__init__()
        self.logcat_reader = logcat_reader
        self.running = True
        self._batch_queue = []
        self._batch_lock = threading.Lock()
        
    def run(self):
        """线程运行函数"""
        def on_log_received(log_entry: LogEntry):
            if self.running:
                with self._batch_lock:
                    self._batch_queue.append(log_entry)
        
        self.logcat_reader.add_log_callback(on_log_received)
        
        # 保持线程运行
        while self.running:
            # 批量处理日志，减少主线程压力
            batch_to_emit = None
            with self._batch_lock:
                if self._batch_queue:
                    batch_to_emit = self._batch_queue[:]
                    self._batch_queue.clear()
            
            if batch_to_emit:
                self.log_received.emit(batch_to_emit)
                
            self.msleep(50)  # 50ms 攒一批日志一起发送
    
    def stop(self):
        """停止线程"""
        self.running = False
        # 等待一小段时间让线程自然结束
        self.msleep(50)


class LogTextEdit(QPlainTextEdit):
    """自定义日志文本编辑器，支持彩色显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        # 禁用自动换行，这对日志显示的性能提升至关重要（避免庞大的布局重新计算）
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        # 使用系统默认等宽字体，避免字体缺失问题
        font = QFont()
        font.setFamily("Monaco")
        font.setPointSize(12)
        if not font.exactMatch():
            font.setFamily("Menlo")  # macOS默认等宽字体
        if not font.exactMatch():
            font.setFamily("Consolas")  # Windows等宽字体
        if not font.exactMatch():
            font.setFamily("Courier New")  # 通用等宽字体
        self.setFont(font)
        self.setup_colors()
        self.max_lines = 100000  # 限制最大行数
        self.setMaximumBlockCount(self.max_lines)  # 让 Qt C++ 底层自动处理超长截断，极大地提升性能
        self.auto_scroll_checkbox = None  # 自动滚动复选框引用，稍后设置
        self._scroll_timer = QTimer()  # 添加滚动定时器
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._perform_delayed_scroll)
        self._pending_scroll = False  # 标记是否有待执行的滚动
        
    def setup_colors(self):
        """设置日志级别颜色"""
        self.level_colors = {
            'V': QColor(128, 128, 128),  # 灰色 (Verbose)
            'D': QColor(86, 156, 214),   # 浅蓝 (Debug)
            'I': QColor(78, 201, 176),   # 浅绿 (Info)
            'W': QColor(220, 163, 16),   # 橙黄 (Warn)
            'E': QColor(244, 71, 71),    # 亮红 (Error)
            'F': QColor(197, 134, 192)   # 粉紫 (Fatal)
        }
        
        # 预先创建并缓存 QTextCharFormat，避免在每次循环中创建对象，极大地提升批量插入性能
        self.level_formats = {}
        for level, color in self.level_colors.items():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self.level_formats[level] = fmt
            
        self.default_format = QTextCharFormat()
        self.default_format.setForeground(QColor(212, 212, 212))
    
    def set_auto_scroll_checkbox(self, checkbox):
        """设置自动滚动复选框引用"""
        self.auto_scroll_checkbox = checkbox
        
    def append_colored_log_batch(self, log_entries: list):
        """真正的极速批量添加，兼顾颜色与性能"""
        if not log_entries:
            return
            
        try:
            doc = self.document()
            
            # 移动到文档末尾并准备插入文本
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.End)
            
            # 核心优化：
            # 即使不使用 HTML，在循环中不断调用 cursor.insertText() 并切换 format 依然有巨大的内部开销。
            # 这里我们将具有相同颜色的连续日志拼接成一个大长串，然后再统一调用 insertText()。
            cursor.beginEditBlock()
            
            current_level = None
            current_text_buffer = []
            
            for log_entry in log_entries:
                level_val = log_entry.level.value
                log_line = f"{log_entry.timestamp} {log_entry.pid}/{log_entry.tid} {level_val} {log_entry.tag}: {log_entry.message}\n"
                
                # 如果日志级别变了，或者第一次处理
                if current_level is None or current_level != level_val:
                    # 先把上一个级别的文本刷进去
                    if current_text_buffer:
                        fmt = self.level_formats.get(current_level, self.default_format)
                        cursor.insertText("".join(current_text_buffer), fmt)
                        current_text_buffer.clear()
                    current_level = level_val
                
                current_text_buffer.append(log_line)
                
            # 把最后一点刷进去
            if current_text_buffer:
                fmt = self.level_formats.get(current_level, self.default_format)
                cursor.insertText("".join(current_text_buffer), fmt)
                
            cursor.endEditBlock()
            
            # 简化的自动滚动逻辑
            if self.auto_scroll_checkbox and self.auto_scroll_checkbox.isChecked():
                if not self._pending_scroll:
                    self._pending_scroll = True
                    self._scroll_timer.start(50)
                    
        except Exception as e:
            print(f"批量添加日志失败: {e}")
            import traceback
            traceback.print_exc()

    def append_colored_log(self, log_entry: LogEntry):
        """添加带颜色的日志条目"""
        try:
            # 格式化日志行
            level_val = log_entry.level.value
            log_line = f"{log_entry.timestamp} {log_entry.pid}/{log_entry.tid} {level_val} {log_entry.tag}: {log_entry.message}"
            
            # 检查文档是否有效
            doc = self.document()
            if not doc:
                print("文档无效，跳过日志添加")
                return
            
            # 保存当前焦点控件
            focus_widget = QApplication.focusWidget()
            was_focused = (focus_widget is not None)
            
            # 移动到文档末尾并插入文本
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.End)
            fmt = self.level_formats.get(level_val, self.default_format)
            cursor.insertText(log_line + "\n", fmt)
            
            # 简化的自动滚动逻辑：只要复选框选中就滚动到底部
            if self.auto_scroll_checkbox and self.auto_scroll_checkbox.isChecked():
                # 使用延迟滚动，避免频繁操作影响性能
                if not self._pending_scroll:
                    self._pending_scroll = True
                    self._scroll_timer.start(10)  # 10ms延迟，确保UI更新完成
                    
        except Exception as e:
            print(f"添加日志失败: {e}")
            import traceback
            traceback.print_exc()
                
    def _perform_delayed_scroll(self):
        """执行延迟滚动"""
        self._pending_scroll = False
        try:
            scrollbar = self.verticalScrollBar()
            if scrollbar:
                # 直接设置到最大值，确保看到最新日志
                max_value = scrollbar.maximum()
                if max_value >= 0:
                    scrollbar.setValue(max_value)
        except Exception as e:
            print(f"滚动失败: {e}")
                
    def scroll_to_bottom(self):
        """强制滚动到底部 - 用于手动触发"""
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())


class LogMasterPro(QMainWindow):
    # 定义信号 - 用于线程安全的UI更新
    devices_updated_signal = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        try:
            print("正在初始化LogMasterPro...")
            self.device_manager = DeviceManager()
            self.logcat_reader = LogcatReader(device_manager=self.device_manager)
            self.current_device: Device = None
            self.is_logging = False
            self.log_count = 0
            self.log_update_thread = None
            self.search_text = ""
            
            # 连接信号到槽函数
            self.devices_updated_signal.connect(self._on_devices_updated_safe)
            
            # 设置应用程序终止处理
            self.setup_termination_handling()
            
            # 设置macOS特定的dock处理
            self.setup_macos_dock_handling()
            
            print("正在初始化UI...")
            self.init_ui()
            print("正在初始化设备监控...")
            self.init_device_monitoring()
            print("初始化完成")
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('Logmaster - Android日志分析工具')
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置现代化的暗色主题样式
        self.setStyleSheet("""
            /* 全局暗色背景 */
            QMainWindow {
                background-color: #1e1e1e;
            }
            
            /* 顶部工具栏 - 深色渐变 */
            QToolBar {
                background-color: #2d2d2d;
                spacing: 6px;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
            }
            QToolButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                margin: 2px 4px;
            }
            QToolButton:hover {
                background-color: #4a4a4a;
                border-color: #5a5a5a;
                color: #ffffff;
            }
            QToolButton:pressed {
                background-color: #2d2d2d;
                border-color: #3a3a3a;
            }
            
            /* 菜单栏 */
            QMenuBar {
                background-color: #2d2d2d;
                color: #cccccc;
                font-size: 13px;
                padding: 4px;
                border-bottom: 1px solid #3d3d3d;
            }
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 30px 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3d3d3d;
                margin: 4px 10px;
            }
            
            /* 按钮 - 现代扁平风格 */
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666666;
            }
            
            /* 输入框和下拉框 */
            QLineEdit, QComboBox {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: #3c3c3c;
                color: #d4d4d4;
                selection-background-color: #094771;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #0e639c;
                background-color: #2d2d2d;
            }
            QLineEdit:hover, QComboBox:hover {
                border-color: #5a5a5a;
            }
            QLineEdit::placeholder {
                color: #808080;
            }
            
            /* 下拉框展开 */
            QComboBox::drop-down {
                border: none;
                width: 24px;
                padding-right: 6px;
            }
            QComboBox::down-arrow {
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="%23cccccc" d="M2 4L6 8L10 4Z"/></svg>');
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                selection-background-color: #094771;
                selection-color: #ffffff;
                background-color: #252526;
                color: #cccccc;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                color: #cccccc;
                padding: 6px 10px;
                min-height: 24px;
                border-radius: 3px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #094771;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            
            /* 复选框 - 使用简洁的填充样式 */
            QCheckBox {
                font-size: 13px;
                color: #cccccc;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #5a5a5a;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border-color: #0e639c;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border-color: #0e639c;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border-color: #5a5a5a;
            }
            QCheckBox::indicator:disabled {
                background-color: #1e1e1e;
                border-color: #3c3c3c;
            }
            
            /* 状态栏 */
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
                font-size: 13px;
                padding: 4px 10px;
            }
            
            /* 文本编辑区 - 日志显示 */
            QTextEdit, QPlainTextEdit {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                selection-background-color: #264f78;
                selection-color: #ffffff;
                padding: 4px;
            }
            QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #0e639c;
            }
            
            /* 标签 */
            QLabel {
                color: #cccccc;
                font-size: 13px;
                background-color: transparent;
            }
            
            /* 进度条 */
            QProgressBar {
                border: none;
                border-radius: 2px;
                background-color: #3c3c3c;
                text-align: center;
                color: #ffffff;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 2px;
            }
            
            /* 滚动条 */
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: transparent;
            }
            
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #424242;
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background-color: transparent;
            }
            
            /* 消息框 */
            QMessageBox {
                background-color: #252526;
                color: #cccccc;
            }
            QMessageBox QLabel {
                color: #cccccc;
            }
            
            /* 文件对话框 */
            QFileDialog {
                background-color: #252526;
                color: #cccccc;
            }
        """)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # 初始化时不执行耗时的状态栏更新，给个默认值
        self.status_bar.showMessage("就绪 - 正在初始化...")
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局 (减小边距以最大化日志显示空间)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 为了让界面更紧凑，我们将控制区和搜索区合并或简化
        # 创建顶部控制面板 (水平布局，包含设备选择和搜索)
        top_panel = self.create_top_control_panel()
        main_layout.addWidget(top_panel)
        
        # 创建过滤器面板
        filter_panel = self.create_filter_panel()
        main_layout.addWidget(filter_panel)
        
        # 创建日志显示区域 (占用所有剩余空间)
        log_group = self.create_log_display_group()
        main_layout.addWidget(log_group, 1) # stretch=1，使其占据主要空间
        
        # 设置定时器更新状态栏
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        # 将状态栏更新频率从 1000ms 降低到 5000ms，因为查询 ADB 版本可能非常耗时
        self.status_timer.start(5000)
        
        # 添加logcat监控定时器
        self.logcat_monitor_timer = QTimer()
        self.logcat_monitor_timer.timeout.connect(self.monitor_logcat_status)
        # 延长监控间隔，减少系统开销
        self.logcat_monitor_timer.start(3000)  # 每3秒检查一次
        
        # 连接日志文本编辑器和自动滚动复选框（所有UI组件已创建）
        self.log_text.set_auto_scroll_checkbox(self.auto_scroll_checkbox)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        save_action = QAction('保存日志...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip("将当前显示的日志保存到本地文件")
        save_action.triggered.connect(self.save_logs)
        file_menu.addAction(save_action)
        
        clear_action = QAction('清空日志', self)
        clear_action.setShortcut('Ctrl+L')
        clear_action.setStatusTip("清空日志显示区域的内容")
        clear_action.triggered.connect(self.clear_logs)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        find_action = QAction('搜索...', self)
        find_action.setShortcut('Ctrl+F')
        find_action.setStatusTip("在日志中搜索指定内容")
        find_action.triggered.connect(self.show_search_dialog)
        edit_menu.addAction(find_action)
        
        # 高级菜单
        advanced_menu = menubar.addMenu('高级')
        
        regex_action = QAction('正则表达式指南', self)
        regex_action.setStatusTip("查看正则表达式语法和使用示例")
        regex_action.triggered.connect(self.show_regex_help)
        advanced_menu.addAction(regex_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.setStatusTip("查看应用程序信息和版本")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """创建现代化工具栏 - 使用精美的图标按钮"""
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(toolbar)
        
        # === 开始/停止按钮 - 使用精美的播放/暂停图标 ===
        self.start_stop_action = QAction('开始', self)
        self.start_stop_action.setToolTip("开始记录日志 (Ctrl+R)")
        self.start_stop_action.setShortcut('Ctrl+R')
        self.start_stop_action.triggered.connect(self.toggle_logging)
        # 使用绿色背景的播放按钮样式
        toolbar.addAction(self.start_stop_action)
        
        toolbar.addSeparator()
        
        # === 保存按钮 - 带磁盘图标 ===
        save_action = QAction('保存', self)
        save_action.setToolTip("将当前日志保存到文件 (Ctrl+S)")
        save_action.triggered.connect(self.save_logs)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # === 清空按钮 - 带垃圾桶图标 ===
        clear_action = QAction('清空', self)
        clear_action.setToolTip("清空当前显示的日志 (Ctrl+L)")
        clear_action.triggered.connect(self.clear_logs)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        # === 搜索按钮 - 带放大镜图标 ===
        find_action = QAction('搜索', self)
        find_action.setToolTip("在日志中搜索内容 (Ctrl+F)")
        find_action.triggered.connect(self.show_search_dialog)
        toolbar.addAction(find_action)
        
        # 添加弹性空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # === 自动滚动复选框 ===
        self.auto_scroll_checkbox = QCheckBox("自动滚动")
        self.auto_scroll_checkbox.setToolTip("自动滚动到最新的日志条目")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                font-size: 13px;
                background-color: transparent;
                spacing: 6px;
                padding: 4px 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #5a5a5a;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border-color: #0e639c;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border-color: #0e639c;
            }
        """)
        toolbar.addWidget(self.auto_scroll_checkbox)
        
        # === 滚动到底部按钮 - 精美的绿色按钮 ===
        scroll_bottom_btn = QPushButton("最新")
        scroll_bottom_btn.setToolTip("滚动到最新的日志条目")
        scroll_bottom_btn.setFixedSize(60, 28)
        scroll_bottom_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d8a2d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3da33d;
            }
            QPushButton:pressed {
                background-color: #1d6a1d;
            }
        """)
        scroll_bottom_btn.clicked.connect(lambda: self.log_text.scroll_to_bottom())
        toolbar.addWidget(scroll_bottom_btn)
        
    def create_top_control_panel(self) -> QWidget:
        """创建顶部控制面板（包含设备选择和内联搜索，更加紧凑）"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 设备控制部分 ---
        device_label = QLabel("设备")
        device_label.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(device_label)
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        self.device_combo.setMinimumWidth(250)
        layout.addWidget(self.device_combo)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setToolTip("重新扫描连接的Android设备")
        refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_btn)
        
        clear_buffer_btn = QPushButton("清缓存")
        clear_buffer_btn.setToolTip("清除Android设备的日志缓冲区 (adb logcat -c)")
        clear_buffer_btn.clicked.connect(self.clear_logcat_buffer)
        layout.addWidget(clear_buffer_btn)
        
        # 弹簧分隔设备控制和搜索
        layout.addSpacing(20)
        
        # --- 搜索部分 ---
        search_label = QLabel("搜索")
        search_label.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("在日志中搜索...")
        self.search_edit.setToolTip("在当前显示的日志内容中搜索，支持区分大小写")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_edit.setMinimumWidth(200)
        layout.addWidget(self.search_edit)
        
        # 区分大小写复选框 - 使用清晰的文字
        self.case_sensitive_check = QCheckBox("区分大小写")
        self.case_sensitive_check.setToolTip("勾选后搜索时区分大小写")
        self.case_sensitive_check.setStyleSheet("""
            QCheckBox {
                color: #aaaaaa;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #5a5a5a;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border-color: #0e639c;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border-color: #0e639c;
            }
        """)
        self.case_sensitive_check.stateChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.case_sensitive_check)
        
        # 搜索统计标签
        self.search_stats_label = QLabel("")
        self.search_stats_label.setMinimumWidth(80)
        self.search_stats_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.search_stats_label)
        
        # 上一个/下一个按钮 - 使用清晰的文字
        self.find_prev_btn = QPushButton("上一个")
        self.find_prev_btn.setToolTip("跳转到上一个匹配结果 (Shift+Enter)")
        self.find_prev_btn.setFixedHeight(28)
        self.find_prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                color: #ffffff;
            }
        """)
        self.find_prev_btn.clicked.connect(self.find_previous)
        layout.addWidget(self.find_prev_btn)
        
        self.find_next_btn = QPushButton("下一个")
        self.find_next_btn.setToolTip("跳转到下一个匹配结果 (Enter)")
        self.find_next_btn.setFixedHeight(28)
        self.find_next_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                color: #ffffff;
            }
        """)
        self.find_next_btn.clicked.connect(self.find_next)
        layout.addWidget(self.find_next_btn)
        
        return panel
        
    def create_filter_panel(self) -> QWidget:
        """创建过滤器面板（一行展示所有过滤器）"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志级别
        level_label = QLabel("级别")
        level_label.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(level_label)
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "Verbose", "Debug", "Info", "Warning", "Error", "Fatal"])
        self.level_combo.currentTextChanged.connect(self.on_filter_changed_delayed)
        self.level_combo.setFixedWidth(100)
        layout.addWidget(self.level_combo)
        
        # 标签过滤
        tag_label = QLabel("标签")
        tag_label.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(tag_label)
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("例: MyApp,Network")
        self.tag_edit.setToolTip("输入要过滤的标签，支持逗号分隔或正则表达式")
        self.tag_edit.textChanged.connect(self.on_filter_changed_delayed)
        self.tag_edit.setMinimumWidth(180)
        layout.addWidget(self.tag_edit)
        
        self.tag_regex_checkbox = QCheckBox("正则")
        self.tag_regex_checkbox.setToolTip("启用正则表达式匹配标签")
        self.tag_regex_checkbox.setStyleSheet("""
            QCheckBox {
                color: #888888;
                font-size: 12px;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #4a4a4a;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:hover {
                border-color: #0e639c;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border-color: #0e639c;
            }
        """)
        self.tag_regex_checkbox.stateChanged.connect(self.on_filter_changed_delayed)
        layout.addWidget(self.tag_regex_checkbox)
        
        # 关键字过滤
        keyword_label = QLabel("关键字")
        keyword_label.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(keyword_label)
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("包含的内容...")
        self.keyword_edit.textChanged.connect(self.on_filter_changed_delayed)
        self.keyword_edit.setMinimumWidth(120)
        layout.addWidget(self.keyword_edit)
        
        # PID过滤
        pid_label = QLabel("PID")
        pid_label.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(pid_label)
        self.pid_edit = QLineEdit()
        self.pid_edit.setPlaceholderText("进程ID")
        self.pid_edit.textChanged.connect(self.on_filter_changed_delayed)
        self.pid_edit.setFixedWidth(80)
        layout.addWidget(self.pid_edit)
        
        # 占位
        layout.addStretch()
        
        # 日志统计显示在这一行的最右侧
        self.log_stats_label = QLabel("就绪")
        self.log_stats_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.log_stats_label)
        
        return panel
        
    def create_log_display_group(self) -> QWidget:
        """创建日志显示组 (移除臃肿的GroupBox边框，只保留编辑器本身)"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用自定义的彩色日志编辑器
        self.log_text = LogTextEdit()
        
        layout.addWidget(self.log_text)
        
        # 进度条（用于大量日志时的显示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4) # 让进度条更细更现代
        layout.addWidget(self.progress_bar)
        
        return container
        
    def init_device_monitoring(self):
        """初始化设备监控"""
        self.device_manager.add_device_callback(self.on_devices_updated)
        
        # 不要在这里同步刷新设备，这样会阻塞启动
        self.device_combo.addItem("正在加载设备...")
        self.device_combo.setEnabled(False)
        
        # 将耗时的设备刷新放到后台线程
        threading.Thread(target=self._async_initial_refresh, daemon=True).start()
        
        # 设置过滤器延迟应用定时器
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.apply_filters)
        
    def _async_initial_refresh(self):
        """在后台线程进行初始的设备扫描，不卡主界面"""
        print("后台线程开始初始扫描设备...")
        devices = self.device_manager.get_devices()
        print(f"后台扫描完成，找到 {len(devices)} 台设备")
        
        # 发送信号通知主线程更新UI
        self.devices_updated_signal.emit(devices)
        
        # 扫描完成后，再开始定期监控
        self.device_manager.start_monitoring()
        
    def refresh_devices(self):
        """刷新设备列表（异步）"""
        self.device_combo.setEnabled(False)
        self.device_combo.setItemText(self.device_combo.currentIndex(), "正在刷新设备...")
        # 将耗时的刷新操作放入后台线程
        threading.Thread(target=self._async_refresh_devices, daemon=True).start()
        
    def _async_refresh_devices(self):
        """后台刷新设备列表"""
        devices = self.device_manager.get_devices()
        self.devices_updated_signal.emit(devices)
        
    def update_device_combo(self, devices: list):
        """更新设备下拉框"""
        current_device = self.device_combo.currentData()
        self.device_combo.clear()
        
        if not devices:
            self.device_combo.addItem("未找到设备")
            self.device_combo.setEnabled(False)
            self.current_device = None
        else:
            self.device_combo.setEnabled(True)
            for device in devices:
                display_text = f"{device.serial} - {device.model} ({device.status})"
                self.device_combo.addItem(display_text, device)
            
            # 如果之前有选中的设备，尝试保持选中状态
            if current_device:
                for i in range(self.device_combo.count()):
                    device = self.device_combo.itemData(i)
                    if isinstance(device, Device) and device.serial == current_device.serial:
                        self.device_combo.setCurrentIndex(i)
                        break
            else:
                # 如果没有之前选中的设备，自动选择第一个设备
                self.device_combo.setCurrentIndex(0)
                # 立即更新设备选择
                self._update_device_selection()
                        
    def on_device_changed(self):
        """设备选择变化处理 - 增强防抖版"""
        print(f"设备变化事件触发，当前记录状态: {self.is_logging}")
        
        # 添加防抖机制，避免频繁重启
        if hasattr(self, '_device_change_timer'):
            self._device_change_timer.stop()
        else:
            self._device_change_timer = QTimer()
            self._device_change_timer.setSingleShot(True)
            self._device_change_timer.timeout.connect(self._handle_device_change_delayed)
        
        # 延迟处理设备变化（1500ms防抖，避免过于频繁）
        self._device_change_timer.start(1500)
    
    def _handle_device_change_delayed(self):
        """延迟处理设备变化 - 同一设备不停止记录"""
        print("执行延迟设备变化处理")
        
        # 获取当前选中的设备
        current_selected_device = None
        index = self.device_combo.currentIndex()
        if index >= 0:
            current_selected_device = self.device_combo.itemData(index)
        
        # 如果正在记录，检查是否是同一个设备
        if self.is_logging and self.current_device and current_selected_device:
            # 如果是同一个设备（序列号相同），不停止记录
            if self.current_device.serial == current_selected_device.serial:
                print(f"同一设备状态变化，继续记录: {self.current_device.serial}")
                self._update_device_selection()  # 只更新选择，不停止记录
                return
            else:
                print(f"设备切换: {self.current_device.serial} -> {current_selected_device.serial}")
                print("设备变化时正在记录，先停止当前记录")
                self.stop_logging()
                # 延迟重新启动（3秒后，给设备充分时间稳定）
                QTimer.singleShot(3000, self._restart_logging_with_new_device)
        else:
            self._update_device_selection()
    
    def _restart_logging_with_new_device(self):
        """使用新设备重新启动记录"""
        print("尝试自动重新启动日志记录")
        self._update_device_selection()
        if self.current_device and self.current_device.status == "device":
            print("条件满足，自动重新启动日志记录")
            self.start_logging()
        else:
            print("条件不满足，不自动重新启动")
    
    def _update_device_selection(self):
        """更新设备选择（不处理记录状态）"""
        print(f"_update_device_selection 被调用")
        index = self.device_combo.currentIndex()
        print(f"当前选中索引: {index}")
        if index >= 0:
            device = self.device_combo.itemData(index)
            print(f"设备数据: {device}")
            if isinstance(device, Device):
                self.current_device = device
                print(f"更新 current_device: {device.serial}")
                # 使用QTimer延迟UI更新，确保在主线程执行
                QTimer.singleShot(0, lambda: self._update_ui_for_device(device))
            else:
                self.current_device = None
                print("current_device 设置为 None (数据类型错误)")
                # 使用QTimer延迟UI更新，确保在主线程执行
                QTimer.singleShot(0, lambda: self._clear_ui_device())
        else:
            self.current_device = None
            print("current_device 设置为 None (索引<0)")
            # 使用QTimer延迟UI更新，确保在主线程执行
            QTimer.singleShot(0, lambda: self._clear_ui_device())
    
    def _update_ui_for_device(self, device):
        """在主线程更新设备UI"""
        self.statusBar().showMessage(f"已选择设备: {device.serial}")
        # 更新窗口标题显示当前设备
        if not self.is_logging:
            self.setWindowTitle(f'Logmaster - {device.serial}')
    
    def _clear_ui_device(self):
        """清除设备UI显示"""
        self.statusBar().showMessage("就绪")
        # 重置窗口标题
        if not self.is_logging:
            self.setWindowTitle('Logmaster - Android日志分析工具')
            
    def on_devices_updated(self, devices: list):
        """设备列表更新处理 - 线程安全版本"""
        # 使用信号机制确保在主线程更新UI
        self.devices_updated_signal.emit(devices)
    
    def _on_devices_updated_safe(self, devices: list):
        """在主线程安全地更新设备列表"""
        try:
            self.update_device_combo(devices)
        except Exception as e:
            print(f"设备列表更新错误: {e}")
            import traceback
            traceback.print_exc()
        
    def toggle_logging(self):
        """切换日志记录状态"""
        if self.is_logging:
            self.stop_logging()
        else:
            self.start_logging()
            
    def start_logging(self):
        """开始日志记录 - 增强版，包含自动重启机制"""
        print("开始日志记录函数被调用")
        
        # 添加状态保护
        if self.is_logging:
            print("已经在记录中，跳过启动")
            return
            
        print(f"current_device: {self.current_device}")
        if not self.current_device:
            QMessageBox.warning(self, "警告", "请先选择设备")
            return
            
        print(f"当前设备状态: '{self.current_device.status}'")
        if self.current_device.status != "device":
            QMessageBox.warning(self, "警告", f"设备未连接或状态异常 (状态: {self.current_device.status})")
            return
        
        # 获取过滤器设置
        filters = self.get_filter_settings()
        print(f"过滤器设置: {filters}")
        
        try:
            print(f"启动设备 {self.current_device.serial} 的logcat")
            
            # 确保之前的线程已完全停止
            if self.log_update_thread and self.log_update_thread.isRunning():
                print("等待之前的日志线程停止...")
                self.log_update_thread.stop()
                self.log_update_thread.wait(2000)  # 最多等待2秒
            
            # 开始logcat
            self.logcat_reader.start_logcat(self.current_device.serial, 
                                           clear_buffer=True, filters=filters)
            
            # 启动日志更新线程
            self.log_update_thread = LogUpdateThread(self.logcat_reader)
            self.log_update_thread.log_received.connect(self.on_log_received)
            self.log_update_thread.start()
            
            self.is_logging = True
            self.update_ui_for_logging_state(True)
            
            # 清空显示并重置计数
            self.log_text.clear()
            self.log_count = 0
            
            self.update_log_stats()
            
            # 启动后台监控线程
            self._start_logging_monitor()
            
            print("日志记录启动成功")
            
        except Exception as e:
            print(f"启动日志记录失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"启动日志记录失败: {e}")
            self.is_logging = False
        
    def update_ui_for_logging_state(self, is_logging: bool):
        """更新UI状态"""
        if is_logging:
            self.start_stop_action.setText("停止")
            self.start_stop_action.setToolTip("停止当前日志记录 (Ctrl+R)")
            # 使用QTimer延迟UI更新，确保在主线程执行
            QTimer.singleShot(0, lambda: self._update_logging_ui(True))
        else:
            self.start_stop_action.setText("开始")
            self.start_stop_action.setToolTip("开始记录日志 (Ctrl+R)")
            # 使用QTimer延迟UI更新，确保在主线程执行
            QTimer.singleShot(0, lambda: self._update_logging_ui(False))
    
    def _update_logging_ui(self, is_logging: bool):
        """在主线程更新日志记录UI"""
        if is_logging:
            self.statusBar().showMessage("正在记录日志...")
            # 更新窗口标题显示记录状态
            if self.current_device:
                self.setWindowTitle(f'Logmaster - {self.current_device.serial} [正在记录]')
            else:
                self.setWindowTitle('Logmaster - Android日志分析工具 [正在记录]')
        else:
            self.statusBar().showMessage("日志记录已停止")
            # 恢复窗口标题
            self.setWindowTitle('Logmaster - Android日志分析工具')
    
    def stop_logging(self):
        """停止日志记录 - 增强版"""
        import traceback
        print("======== 停止日志记录函数被调用 ========")
        # 强行打印详细的堆栈，看看是谁在“幽灵调用”它
        traceback.print_stack()
        print("=========================================")
        
        # 停止监控线程
        self._stop_logging_monitor()
        
        if self.log_update_thread:
            print("停止日志更新线程...")
            self.log_update_thread.stop()
            self.log_update_thread.wait()
            self.log_update_thread = None
            
        print("停止logcat读取...")
        self.logcat_reader.stop_logcat()
        
        self.is_logging = False
        self.update_ui_for_logging_state(False)
        
        print("日志记录已停止")
    
    def _start_logging_monitor(self):
        """启动日志记录监控线程"""
        if hasattr(self, '_logging_monitor_thread') and self._logging_monitor_thread and self._logging_monitor_thread.is_alive():
            print("监控线程已在运行")
            return
            
        self._logging_monitor_running = True
        self._logging_monitor_thread = threading.Thread(target=self._logging_monitor_loop, daemon=True)
        self._logging_monitor_thread.start()
        print("日志监控线程已启动")
    
    def _stop_logging_monitor(self):
        """停止日志记录监控线程"""
        if hasattr(self, '_logging_monitor_running'):
            self._logging_monitor_running = False
            if hasattr(self, '_logging_monitor_thread') and self._logging_monitor_thread and self._logging_monitor_thread.is_alive():
                self._logging_monitor_thread.join(timeout=2)
                print("日志监控线程已停止")
    
    def _logging_monitor_loop(self):
        """日志记录监控循环 - 检测异常停止并自动重启"""
        check_interval = 3  # 每3秒检查一次
        max_silent_time = 15  # 最大静默时间15秒
        restart_attempts = 0
        max_restart_attempts = 3  # 最多连续重启3次
        
        while getattr(self, '_logging_monitor_running', False) and self.is_logging:
            try:
                current_time = time.time()
                stats = self.logcat_reader.get_stats()
                
                # 检查logcat读取器状态
                reader_running = stats.get('is_running', False)
                last_log_time = stats.get('last_log_time', 0)
                processed_logs = stats.get('processed_logs', 0)
                
                silent_time = current_time - last_log_time
                
                # 如果读取器停止运行，或者静默时间太长，尝试重启
                if not reader_running or (silent_time > max_silent_time and processed_logs > 0):
                    print(f"健康检查：检测到日志记录异常! 运行状态={reader_running}, 静默时间={silent_time:.1f}秒, processed={processed_logs}")
                    
                    if restart_attempts < max_restart_attempts:
                        restart_attempts += 1
                        print(f"尝试自动重启日志记录 (第{restart_attempts}次)")
                        self._restarting_logcat = True
                        
                        # 停止当前记录
                        try:
                            self.logcat_reader.stop_logcat()
                        except:
                            pass
                        
                        # 延迟后重启
                        time.sleep(2)
                        
                        # 检查设备状态
                        if self.current_device and self.current_device.status == "device":
                            try:
                                # 重新获取过滤器设置
                                filters = self.get_filter_settings()
                                self.logcat_reader.start_logcat(self.current_device.serial, 
                                                              clear_buffer=False,  # 不清除缓冲区，避免数据丢失
                                                              filters=filters)
                                print("自动重启成功")
                                restart_attempts = 0  # 重置重启计数
                            except Exception as restart_e:
                                print(f"自动重启失败: {restart_e}")
                        else:
                            print("设备状态异常，无法自动重启")
                            
                        self._restarting_logcat = False
                    else:
                        print(f"已达到最大重启次数({max_restart_attempts})，停止自动重启")
                        # 可以选择停止整个记录或继续监控
                        # 在UI线程恢复状态
                        QTimer.singleShot(0, self._recover_ui_after_fatal_stop)
                        break
                else:
                    # 如果一切正常，重置重启计数
                    if restart_attempts > 0:
                        print("日志记录恢复正常，重置重启计数")
                        restart_attempts = 0
                
            except Exception as e:
                print(f"日志监控线程出错: {e}")
                
            # 等待下一次检查
            time.sleep(check_interval)
        
        print("日志监控线程结束")
        # 如果是因为异常退出，可以在这里添加额外的处理逻辑
        
    def _recover_ui_after_fatal_stop(self):
        """当日志监控多次重启失败后，在UI线程恢复停止状态"""
        if self.is_logging:
            print("自动恢复界面状态为停止记录")
            self.is_logging = False
            self.start_stop_action.setText("开始")
            self.start_stop_action.setToolTip("开始记录日志 (Ctrl+R)")
            self.statusBar().showMessage("日志记录异常停止，已达到最大重启次数")
        
    def get_filter_settings(self) -> dict:
        """获取过滤器设置 - 修复空值处理"""
        filters = {}
        
        # 日志级别
        level_text = self.level_combo.currentText()
        if level_text != "全部":
            level_map = {
                "Verbose": "V",
                "Debug": "D", 
                "Info": "I",
                "Warning": "W",
                "Error": "E",
                "Fatal": "F"
            }
            filters['level'] = level_map.get(level_text)
        else:
            filters['level'] = None
        
        # 标签（支持正则表达式）
        tag_text = self.tag_edit.text().strip()
        if tag_text:
            filters['tag'] = tag_text
            filters['tag_regex'] = self.tag_regex_checkbox.isChecked()
        else:
            filters['tag'] = None
            filters['tag_regex'] = False
            
        # 关键字
        keyword_text = self.keyword_edit.text().strip()
        if keyword_text:
            filters['keyword'] = keyword_text
        else:
            filters['keyword'] = None
            
        # PID
        pid_text = self.pid_edit.text().strip()
        if pid_text:
            filters['pid'] = pid_text
        else:
            filters['pid'] = None
            
        return filters
        
    def on_filter_changed_delayed(self):
        """过滤器变化延迟处理（避免频繁重启）"""
        if self.is_logging:
            self.filter_timer.start(1000)  # 1秒后应用过滤器
            
    def apply_filters(self):
        """应用过滤器"""
        if self.is_logging:
            # 重新启动logcat以应用新过滤器
            # start_logging函数现在会处理滚动位置保持
            self.stop_logging()
            self.start_logging()
            
    def on_log_received(self, log_entries):
        """接收到新日志"""
        try:
            # 直接显示日志，保持实时性
            if isinstance(log_entries, list):
                self.log_text.append_colored_log_batch(log_entries)
                self.log_count += len(log_entries)
            else:
                self.log_text.append_colored_log(log_entries)
                self.log_count += 1
                
            self.update_log_stats()
        except Exception as e:
            print(f"处理日志时出错: {e}")
            import traceback
            traceback.print_exc()
        
    def update_log_stats(self):
        """更新日志统计"""
        # 不要每收到一条日志就更新 UI
        # 限制更新频率，例如每 500 条或用 QTimer
        stats = self.logcat_reader.get_stats()
        total_logs = stats['total_logs']
        processed_logs = stats['processed_logs']
        
        # 只有在数量有显著变化时才更新文本，减少 UI 刷新压力
        if getattr(self, '_last_update_count', 0) == processed_logs:
            return
            
        if processed_logs - getattr(self, '_last_update_count', 0) > 100 or processed_logs < 100:
            self.log_stats_label.setText(f"总日志: {total_logs} | 已处理: {processed_logs}")
            self._last_update_count = processed_logs
        
    def on_search_text_changed(self):
        """搜索文本变化"""
        self.search_text = self.search_edit.text().strip()
        
        # 更新搜索统计
        self.update_search_stats()
        
    def update_search_stats(self):
        """更新搜索统计"""
        if not self.search_text:
            self.search_stats_label.setText("")
            return
            
        # 统计匹配的日志数量
        text = self.log_text.toPlainText()
        if not text:
            self.search_stats_label.setText("未找到")
            return
            
        # 计算匹配次数
        if self.case_sensitive_check.isChecked():
            matches = text.count(self.search_text)
        else:
            matches = text.lower().count(self.search_text.lower())
            
        self.search_stats_label.setText(f"找到 {matches} 个匹配")
        
    def find_next(self):
        """查找下一个"""
        if not self.search_text:
            return
            
        cursor = self.log_text.textCursor()
        
        # 设置查找选项
        options = QTextDocument.FindFlags()
        if self.case_sensitive_check.isChecked():
            options |= QTextDocument.FindCaseSensitively
        
        # 查找下一个
        found_cursor = self.log_text.document().find(self.search_text, cursor, options)
        
        if not found_cursor.isNull():
            self.log_text.setTextCursor(found_cursor)
        else:
            # 从头开始查找
            cursor.movePosition(QTextCursor.Start)
            found_cursor = self.log_text.document().find(self.search_text, cursor, options)
            if not found_cursor.isNull():
                self.log_text.setTextCursor(found_cursor)
            else:
                QMessageBox.information(self, "查找", "未找到更多匹配项")
                
    def find_previous(self):
        """查找上一个"""
        if not self.search_text:
            return
            
        cursor = self.log_text.textCursor()
        
        # 设置查找选项
        options = QTextDocument.FindFlags()
        if self.case_sensitive_check.isChecked():
            options |= QTextDocument.FindCaseSensitively
        options |= QTextDocument.FindBackward
        
        # 查找上一个
        found_cursor = self.log_text.document().find(self.search_text, cursor, options)
        
        if not found_cursor.isNull():
            self.log_text.setTextCursor(found_cursor)
        else:
            # 从末尾开始查找
            cursor.movePosition(QTextCursor.End)
            found_cursor = self.log_text.document().find(self.search_text, cursor, options)
            if not found_cursor.isNull():
                self.log_text.setTextCursor(found_cursor)
            else:
                QMessageBox.information(self, "查找", "未找到更多匹配项")
                
    def show_search_dialog(self):
        """显示搜索对话框"""
        # 将焦点设置到搜索框
        self.search_edit.setFocus()
        self.search_edit.selectAll()
        
    def show_regex_help(self):
        """显示正则表达式帮助"""
        help_text = r"""
🚀 LogMaster Pro - 正则表达式使用指南

📋 基本语法：
• .       - 匹配任意字符
• *       - 匹配0次或多次
• +       - 匹配1次或多次  
• ?       - 匹配0次或1次
• |       - 或操作符
• []      - 字符集，如 [a-z] 匹配小写字母
• ^       - 行首
• $       - 行尾

🎯 常用示例：
• MyApp|Network|Database        - 匹配MyApp或Network或Database
• .*Test.*                        - 匹配包含Test的标签
• ^System                         - 匹配以System开头的标签
• (MyApp|Network).*               - 匹配MyApp或Network开头的标签
• [A-Z].*                         - 匹配大写字母开头的标签

🔥 高级技巧：
• MyApp.*Error$                   - 匹配MyApp开头且Error结尾的标签
• (?!System).*                    - 负向前瞻，不匹配System开头的标签
• \d+                             - 匹配一个或多个数字
• [A-Za-z]+                       - 匹配一个或多个字母

📊 多标签（逗号分隔）：
• MyApp,Network,Database          - 匹配任意一个标签
• MyApp,.*Test.*,^System          - 混合使用普通文本和正则

💡 提示：
• 勾选"正则模式"启用正则表达式
• 不勾选时使用简单的包含匹配
• 逗号分隔的标签会自动使用OR逻辑
• 正则表达式错误时会自动降级为普通匹配
        """
        
        QMessageBox.information(self, "🔧 正则表达式帮助", help_text.strip())
        
    def clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        self.log_count = 0
        self.logcat_reader.clear_buffer()
        self.update_log_stats()
        
    def clear_logcat_buffer(self):
        """清除logcat缓冲区"""
        if self.current_device:
            self.logcat_reader._clear_logcat_buffer(self.current_device.serial)
            # 使用QTimer延迟UI更新，确保在主线程执行
            QTimer.singleShot(0, lambda: self.statusBar().showMessage("已清除logcat缓冲区"))
        else:
            QMessageBox.warning(self, "警告", "请先选择设备")
            
    def save_logs(self):
        """保存日志"""
        if self.log_count == 0:
            QMessageBox.information(self, "信息", "没有日志可保存")
            return
            
        # 选择保存文件
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志", 
            f"logmaster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if filename:
            logs = self.logcat_reader.get_buffered_logs()
            if self.logcat_reader.save_logs_to_file(filename, logs):
                QMessageBox.information(self, "成功", f"日志已保存到:\n{filename}\n共 {len(logs)} 条日志")
            else:
                QMessageBox.critical(self, "错误", "保存日志失败")
                
    def monitor_logcat_status(self):
        """监控logcat状态"""
        if self.is_logging and self.logcat_reader:
            stats = self.logcat_reader.get_stats()
            # 这里原本的逻辑会和 _logging_monitor_loop 中的自动重启冲突。
            # 当监控线程尝试重启时，可能会出现短暂的 is_running 为 False 的状态，
            # 此时如果这里强制恢复UI，就会把 is_logging 置为 False，导致自动重启中断或者后续再也无法记录。
            # 为了让自动重启生效，我们只关注监控线程是否已经彻底放弃重启：
            if not stats['is_running'] and not getattr(self, '_restarting_logcat', False):
                # 如果健康检查线程没有在跑，或者也认为它死透了，我们才修改 UI
                print("monitor_logcat_status 发现 logcat 停止，检查是否可以恢复 UI...")
                pass # The automatic UI recovery should be handled properly, wait for health check.
    
    def update_status_bar(self):
        """更新状态栏 (异步，避免卡主线程)"""
        # 不要在这里直接调用 subprocess 去拿 ADB 状态，否则会卡爆主界面！
        threading.Thread(target=self._async_update_status_bar, daemon=True).start()

    def _async_update_status_bar(self):
        """在后台线程获取 ADB 状态并更新 UI"""
        adb_available = self.device_manager.is_adb_available()
        adb_version = self.device_manager.get_adb_version()
        
        if adb_available:
            status_text = f"ADB可用"
            if adb_version:
                status_text += f" (版本: {adb_version})"
        else:
            status_text = "ADB不可用"
            
        device_count = len(self.device_manager.devices)
        status_text += f" | 设备数量: {device_count}"
        
        if self.is_logging:
            status_text += " | 正在记录日志..."
            
        # 使用QTimer延迟UI更新，确保在主线程执行
        QTimer.singleShot(0, lambda: self.statusBar().showMessage(status_text))
    
    def setup_termination_handling(self):
        """设置应用程序终止处理"""
        # 处理macOS的SIGTERM信号（当从dock退出时）
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        
        # 处理SIGINT信号（Ctrl+C）
        signal.signal(signal.SIGINT, self.handle_sigint)
        
        # 设置应用程序的aboutToQuit信号处理
        QApplication.instance().aboutToQuit.connect(self.cleanup_before_exit)
    
    def setup_macos_dock_handling(self):
        """设置macOS特定的dock处理"""
        try:
            # 设置应用程序名称，帮助dock识别
            QApplication.instance().setApplicationName("LogMaster Pro")
            QApplication.instance().setApplicationDisplayName("LogMaster Pro")
            
            # 设置应用程序属性，改善dock集成
            if hasattr(QApplication.instance(), 'setQuitOnLastWindowClosed'):
                QApplication.instance().setQuitOnLastWindowClosed(True)
            
            # 设置窗口标题，帮助dock显示
            self.setWindowTitle("LogMaster Pro - Android日志大师")
            
            print("✅ macOS dock处理设置完成")
            
        except Exception as e:
            print(f"⚠️ macOS dock处理设置失败: {e}")
    
    def handle_sigterm(self, signum, frame):
        """处理SIGTERM信号 - macOS dock退出"""
        print(f"收到SIGTERM信号 ({signum})，正在优雅退出...")
        try:
            self.cleanup_before_exit()
            # 使用quit而不是exit，避免异常退出
            QApplication.instance().quit()
        except Exception as e:
            print(f"SIGTERM处理出错: {e}")
            # 即使出错也要强制退出
            QApplication.instance().quit()
    
    def handle_sigint(self, signum, frame):
        """处理SIGINT信号 - Ctrl+C"""
        print(f"收到SIGINT信号 ({signum})，正在优雅退出...")
        try:
            self.cleanup_before_exit()
            QApplication.instance().quit()
        except Exception as e:
            print(f"SIGINT处理出错: {e}")
            QApplication.instance().quit()
    
    def cleanup_before_exit(self):
        """退出前的清理工作 - 增强版"""
        print("执行清理工作...")
        try:
            # 停止日志记录
            if self.is_logging:
                print("停止日志记录...")
                self.stop_logging()
            
            # 停止设备监控
            if self.device_manager:
                print("停止设备监控...")
                self.device_manager.stop_monitoring()
            
            # 停止日志更新线程
            if self.log_update_thread and self.log_update_thread.isRunning():
                print("停止日志更新线程...")
                self.log_update_thread.stop()
                # 给线程一点时间来完成当前操作
                if not self.log_update_thread.wait(1000):  # 最多等待1秒
                    print("警告: 日志更新线程停止超时")
                
            # 停止过滤器定时器
            if hasattr(self, 'filter_timer') and self.filter_timer.isActive():
                print("停止过滤器定时器...")
                self.filter_timer.stop()
                
            # 停止设备变化定时器
            if hasattr(self, '_device_change_timer') and self._device_change_timer.isActive():
                print("停止设备变化定时器...")
                self._device_change_timer.stop()
                
            print("清理完成")
        except Exception as e:
            print(f"清理过程中出错: {e}")
            # 即使有错误也要继续退出，不要阻塞
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于 Logmaster", 
                         "Logmaster - Android日志大师\n\n"
                         "一个专业级的Android日志分析工具\n\n"
                         "核心功能:\n"
                         "• 实时日志捕获和显示\n"
                         "• 智能设备自动检测\n"
                         "• 高级正则表达式标签过滤\n"
                         "• 多标签匹配支持\n"
                         "• 强大的搜索和高亮功能\n"
                         "• 一键保存完整日志\n"
                         "• 彩色日志级别显示\n"
                         "• 语法高亮和搜索高亮\n\n"
                         "专为Android开发者打造的专业工具\n\n"
                         "版本: 1.0 Edition")
        
    def closeEvent(self, event):
        """关闭事件处理"""
        print("收到关闭事件，正在优雅退出...")
        self.cleanup_before_exit()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置应用图标
    try:
        from PyQt5.QtGui import QIcon
        import os
        
        # 获取基础目录
        if getattr(sys, 'frozen', False):
            project_root = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
        
        # 尝试多个图标路径（相对路径，更可靠）
        icon_paths = [
            os.path.join(project_root, 'assets', 'icon.icns'),
            os.path.join(project_root, 'assets', 'Logmaster.icns'),
            os.path.join(project_root, 'assets', 'icon.png'),
            # macOS app bundle 中的图标
            os.path.join(project_root, 'LogMaster Pro.app', 'Contents', 'Resources', 'AppIcon.icns'),
            os.path.join(project_root, 'LogMaster.app', 'Contents', 'Resources', 'AppIcon.icns'),
            os.path.join(project_root, 'LogMaster.app', 'Contents', 'Resources', 'LogMaster.icns'),
        ]
        
        icon_set = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    icon = QIcon(icon_path)
                    app.setWindowIcon(icon)
                    print(f'✅ 应用图标设置成功: {icon_path}')
                    icon_set = True
                    break
                except Exception as icon_error:
                    print(f'⚠️ 图标加载失败 {icon_path}: {icon_error}')
        
        if not icon_set:
            print('⚠️ 未找到应用图标，使用默认图标')
            # 尝试设置一个默认的窗口标题，帮助识别应用
            app.setApplicationDisplayName("LogMaster Pro")
            
    except Exception as e:
        print(f'⚠️ 图标设置失败: {e}')
    
    window = LogMasterPro()
    window.show()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        print(f"收到信号 {signum}，正在退出...")
        try:
            window.cleanup_before_exit()
            app.quit()
        except Exception as e:
            print(f"信号处理出错: {e}")
            app.quit()  # 强制退出
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        exit_code = app.exec_()
        print(f"应用程序正常退出，退出码: {exit_code}")
        return exit_code
    except Exception as e:
        print(f"应用程序异常退出: {e}")
        return 0  # 返回0而不是1，避免macOS认为是异常退出


if __name__ == '__main__':
    main()