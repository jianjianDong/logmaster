import sys
import os
import signal
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QComboBox, 
                           QLabel, QLineEdit, QFileDialog, QMessageBox,
                           QGroupBox, QCheckBox, QMenuBar, QStatusBar, 
                           QAction, QToolBar, QPlainTextEdit, QScrollBar, QProgressBar,
                           QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QTextCursor, QTextDocument

# 将当前目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '..'))

from src.core import DeviceManager, Device, LogcatReader, LogEntry, LogLevel


class LogUpdateThread(QThread):
    """日志更新线程"""
    log_received = pyqtSignal(object)  # LogEntry对象
    
    def __init__(self, logcat_reader: LogcatReader):
        super().__init__()
        self.logcat_reader = logcat_reader
        self.running = True
        
    def run(self):
        """线程运行函数"""
        def on_log_received(log_entry: LogEntry):
            if self.running:
                self.log_received.emit(log_entry)
        
        self.logcat_reader.add_log_callback(on_log_received)
        
        # 保持线程运行
        while self.running:
            self.msleep(10)  # 减少CPU占用
    
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
        self.auto_scroll_checkbox = None  # 自动滚动复选框引用，稍后设置
        self._scroll_timer = QTimer()  # 添加滚动定时器
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._perform_delayed_scroll)
        self._pending_scroll = False  # 标记是否有待执行的滚动
        
    def setup_colors(self):
        """设置日志级别颜色"""
        self.level_colors = {
            'V': QColor(128, 128, 128),  # 灰色
            'D': QColor(0, 100, 200),    # 蓝色
            'I': QColor(0, 128, 0),      # 绿色
            'W': QColor(255, 140, 0),    # 橙色
            'E': QColor(220, 0, 0),       # 红色
            'F': QColor(128, 0, 128)      # 紫色
        }
    
    def set_auto_scroll_checkbox(self, checkbox):
        """设置自动滚动复选框引用"""
        self.auto_scroll_checkbox = checkbox
        
    def append_colored_log(self, log_entry: LogEntry):
        """添加带颜色的日志条目"""
        # 格式化日志行
        log_line = f"{log_entry.timestamp} {log_entry.pid}/{log_entry.tid} {log_entry.level.value} {log_entry.tag}: {log_entry.message}"
        
        # 获取日志级别的颜色
        color = self.level_colors.get(log_entry.level.value, QColor(0, 0, 0))
        
        # 创建文本格式
        format = QTextCharFormat()
        format.setForeground(color)
        
        # 如果行数过多，删除最早的行
        if self.blockCount() >= self.max_lines:
            # 删除前1000行
            start_cursor = QTextCursor(self.document())
            start_cursor.movePosition(QTextCursor.Start)
            start_cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, 1000)
            start_cursor.select(QTextCursor.Document)
            start_cursor.removeSelectedText()
        
        # 保存当前焦点控件
        focus_widget = QApplication.focusWidget()
        was_focused = (focus_widget is not None)
        
        # 移动到文档末尾并插入文本
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(log_line + "\n", format)
        
        # 简化的自动滚动逻辑：只要复选框选中就滚动到底部
        if self.auto_scroll_checkbox and self.auto_scroll_checkbox.isChecked():
            # 使用延迟滚动，避免频繁操作影响性能
            if not self._pending_scroll:
                self._pending_scroll = True
                self._scroll_timer.start(10)  # 10ms延迟，确保UI更新完成
                
    def _perform_delayed_scroll(self):
        """执行延迟滚动"""
        self._pending_scroll = False
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            # 直接设置到最大值，确保看到最新日志
            scrollbar.setValue(scrollbar.maximum())
                
    def scroll_to_bottom(self):
        """强制滚动到底部 - 用于手动触发"""
        scrollbar = self.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())


class LogMasterPro(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            print("正在初始化LogMasterPro...")
            self.device_manager = DeviceManager()
            self.logcat_reader = LogcatReader()
            self.current_device: Device = None
            self.is_logging = False
            self.log_count = 0
            self.log_update_thread = None
            self.search_text = ""
            
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
        
        # 设置简洁的应用程序样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QToolBar {
                background-color: #2c3e50;
                spacing: 2px;
                padding: 5px;
                border: none;
            }
            QToolButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 12px;
                margin: 1px;
            }
            QToolButton:hover {
                background-color: #2980b9;
            }
            QToolButton:pressed {
                background-color: #21618c;
            }
            QMenuBar {
                background-color: #34495e;
                color: white;
                font-size: 13px;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
            QPushButton {
                background-color: #f8f9fa;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="%23666" d="M2 4L6 8L10 4Z"/></svg>');
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                selection-background-color: #3498db;
                selection-color: white;
                background-color: white;
                color: #333;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                color: #333;
                padding: 6px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #3498db;
                color: white;
            }
            QComboBox::item:selected {
                background-color: #3498db;
                color: white;
            }
            QCheckBox {
                font-size: 12px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVCiRY/z//z8DJYCJgUKAqoKKgD6QjYGBgYGBjY0NRx0VA1UHFQNVB1UDVQ9VExMDVQtVC1ULVQ9Vj4mBqoeJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJgYmBqYuJg==);
            }
            QStatusBar {
                background-color: #34495e;
                color: white;
                font-size: 12px;
            }
            QTextEdit, QPlainTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-family: 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
        """)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 创建设备控制区域
        device_group = self.create_device_control_group()
        main_layout.addWidget(device_group)
        
        # 创建过滤器和搜索区域
        filter_search_group = self.create_filter_search_group()
        main_layout.addWidget(filter_search_group)
        
        # 创建日志显示区域
        log_group = self.create_log_display_group()
        main_layout.addWidget(log_group)
        
        # 设置定时器更新状态栏
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(1000)  # 每秒更新一次
        
        # 添加logcat监控定时器
        self.logcat_monitor_timer = QTimer()
        self.logcat_monitor_timer.timeout.connect(self.monitor_logcat_status)
        self.logcat_monitor_timer.start(2000)  # 每2秒检查一次
        
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
        """创建现代化工具栏"""
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # 图标旁边显示文字，更稳定
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(toolbar)
        
        # 创建主控制按钮组 - 使用纯文字避免字符编码问题
        # 开始/停止按钮
        self.start_stop_action = QAction('▶ 开始', self)
        self.start_stop_action.setToolTip("开始或停止日志记录 (Ctrl+R)")
        self.start_stop_action.setShortcut('Ctrl+R')
        self.start_stop_action.triggered.connect(self.toggle_logging)
        toolbar.addAction(self.start_stop_action)
        
        toolbar.addSeparator()
        
        # 保存和清空按钮组
        save_action = QAction('保存', self)
        save_action.setToolTip("将当前日志保存到文件 (Ctrl+S)")
        save_action.triggered.connect(self.save_logs)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        clear_action = QAction('清空', self)
        clear_action.setToolTip("清空当前显示的日志 (Ctrl+L)")
        clear_action.triggered.connect(self.clear_logs)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        # 查找按钮
        find_action = QAction('搜索', self)
        find_action.setToolTip("在日志中搜索内容 (Ctrl+F)")
        find_action.triggered.connect(self.show_search_dialog)
        toolbar.addAction(find_action)
        
        # 添加弹性空间，让自动滚动复选框靠右对齐
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # 自动滚动复选框 - 放在工具栏右侧，设置合适的样式
        self.auto_scroll_checkbox = QCheckBox("自动滚动")
        self.auto_scroll_checkbox.setToolTip("自动滚动到最新的日志条目")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                font-size: 11px;
                background-color: transparent;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #cccccc;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="white" d="M9.5 3.5L8 2L4.5 5.5L3 4L1.5 5.5L4.5 8.5L8 5L9.5 3.5Z"/></svg>');
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
                border-color: #cccccc;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #3498db;
            }
        """)
        toolbar.addWidget(self.auto_scroll_checkbox)
        
        # 添加滚动到底部按钮 - 重新设计，更直观
        scroll_bottom_btn = QPushButton("🔽 最新日志")
        scroll_bottom_btn.setToolTip("滚动到最新的日志条目")
        scroll_bottom_btn.setFixedSize(80, 28)
        scroll_bottom_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        scroll_bottom_btn.clicked.connect(lambda: self.log_text.scroll_to_bottom())
        toolbar.addWidget(scroll_bottom_btn)
        
    def create_device_control_group(self) -> QGroupBox:
        """创建设备控制组"""
        group = QGroupBox("设备控制")
        layout = QHBoxLayout()
        
        # 设备选择下拉框
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        self.device_combo.setMinimumWidth(300)
        layout.addWidget(QLabel("设备:"))
        layout.addWidget(self.device_combo, 2)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新设备")
        refresh_btn.setToolTip("重新扫描连接的Android设备")
        refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_btn)
        
        # 清除缓冲区按钮
        clear_buffer_btn = QPushButton("清除缓冲区")
        clear_buffer_btn.setToolTip("清除Android设备的日志缓冲区")
        clear_buffer_btn.clicked.connect(self.clear_logcat_buffer)
        layout.addWidget(clear_buffer_btn)
        
        # 日志统计
        self.log_stats_label = QLabel("就绪")
        layout.addWidget(self.log_stats_label)
        
        layout.addStretch()
        group.setLayout(layout)
        return group
        
    def create_filter_search_group(self) -> QGroupBox:
        """创建过滤器和搜索组"""
        group = QGroupBox("高级过滤器和搜索")
        layout = QVBoxLayout()
        
        # 过滤器行
        filter_layout = QHBoxLayout()
        
        # 日志级别过滤
        filter_layout.addWidget(QLabel("级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["全部", "Verbose", "Debug", "Info", "Warning", "Error", "Fatal"])
        self.level_combo.currentTextChanged.connect(self.on_filter_changed_delayed)
        self.level_combo.setMinimumWidth(100)
        filter_layout.addWidget(self.level_combo)
        
        # 标签过滤（支持正则表达式）
        filter_layout.addWidget(QLabel("标签:"))
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("例: MyApp,Network,.*Test.* 或正则表达式")
        self.tag_edit.setToolTip("输入要过滤的标签，支持逗号分隔多个标签或正则表达式")
        self.tag_edit.textChanged.connect(self.on_filter_changed_delayed)
        self.tag_edit.setMinimumWidth(200)
        filter_layout.addWidget(self.tag_edit)
        
        # 标签过滤模式
        self.tag_regex_checkbox = QCheckBox("启用正则表达式")
        self.tag_regex_checkbox.setToolTip("启用正则表达式匹配标签（支持复杂匹配模式）")
        self.tag_regex_checkbox.stateChanged.connect(self.on_filter_changed_delayed)
        self.tag_regex_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="white" d="M9.5 3.5L8 2L4.5 5.5L3 4L1.5 5.5L4.5 8.5L8 5L9.5 3.5Z"/></svg>');
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
                border-color: #cccccc;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #3498db;
            }
        """)
        filter_layout.addWidget(self.tag_regex_checkbox)
        
        # 关键字过滤
        filter_layout.addWidget(QLabel("关键字:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("在日志消息内容中搜索...")
        self.keyword_edit.setToolTip("输入要在日志消息内容中搜索的关键字")
        self.keyword_edit.textChanged.connect(self.on_filter_changed_delayed)
        self.keyword_edit.setMinimumWidth(150)
        filter_layout.addWidget(self.keyword_edit)
        
        # PID过滤
        filter_layout.addWidget(QLabel("PID:"))
        self.pid_edit = QLineEdit()
        self.pid_edit.setPlaceholderText("进程ID号...")
        self.pid_edit.setToolTip("输入要过滤的进程ID号")
        self.pid_edit.textChanged.connect(self.on_filter_changed_delayed)
        self.pid_edit.setMinimumWidth(80)
        filter_layout.addWidget(self.pid_edit)
        
        # 应用过滤器按钮
        apply_filter_btn = QPushButton("应用过滤器")
        apply_filter_btn.setToolTip("立即应用当前设置的过滤条件到日志流")
        apply_filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 搜索行
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("在当前显示的日志中搜索内容...")
        self.search_edit.setToolTip("在当前显示的日志内容中搜索，不影响实时日志流")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_edit.setMinimumWidth(200)
        search_layout.addWidget(self.search_edit)
        
        # 搜索选项
        self.case_sensitive_check = QCheckBox("区分大小写")
        self.case_sensitive_check.stateChanged.connect(self.on_search_text_changed)
        self.case_sensitive_check.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="white" d="M9.5 3.5L8 2L4.5 5.5L3 4L1.5 5.5L4.5 8.5L8 5L9.5 3.5Z"/></svg>');
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
                border-color: #cccccc;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #3498db;
            }
        """)
        search_layout.addWidget(self.case_sensitive_check)
        
        # 搜索统计
        self.search_stats_label = QLabel("")
        search_layout.addWidget(self.search_stats_label)
        
        # 查找下一个/上一个
        self.find_next_btn = QPushButton("下一个")
        self.find_next_btn.clicked.connect(self.find_next)
        search_layout.addWidget(self.find_next_btn)
        
        self.find_prev_btn = QPushButton("上一个")
        self.find_prev_btn.clicked.connect(self.find_previous)
        search_layout.addWidget(self.find_prev_btn)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # 添加正则表达式提示
        regex_hint = QLabel("提示: 标签过滤支持正则表达式，如: MyApp|Network|.*Test.*, 或使用逗号分隔多个标签: MyApp,Network,Database")
        regex_hint.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(regex_hint)
        
        group.setLayout(layout)
        return group
        
    def create_log_display_group(self) -> QGroupBox:
        """创建日志显示组"""
        group = QGroupBox("日志输出")
        layout = QVBoxLayout()
        
        # 使用自定义的彩色日志编辑器
        self.log_text = LogTextEdit()
        
        layout.addWidget(self.log_text)
        
        # 进度条（用于大量日志时的显示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group
        
    def init_device_monitoring(self):
        """初始化设备监控"""
        self.device_manager.add_device_callback(self.on_devices_updated)
        self.device_manager.start_monitoring()
        self.refresh_devices()
        
        # 设置过滤器延迟应用定时器
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.apply_filters)
        
    def refresh_devices(self):
        """刷新设备列表"""
        devices = self.device_manager.get_devices()
        self.update_device_combo(devices)
        
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
        index = self.device_combo.currentIndex()
        if index >= 0:
            device = self.device_combo.itemData(index)
            if isinstance(device, Device):
                self.current_device = device
                self.statusBar().showMessage(f"已选择设备: {device.serial}")
                # 更新窗口标题显示当前设备
                if not self.is_logging:
                    self.setWindowTitle(f'Logmaster - {device.serial}')
            else:
                self.current_device = None
                # 重置窗口标题
                if not self.is_logging:
                    self.setWindowTitle('Logmaster - Android日志分析工具')
        else:
            self.current_device = None
            # 重置窗口标题
            if not self.is_logging:
                self.setWindowTitle('Logmaster - Android日志分析工具')
            
    def on_devices_updated(self, devices: list):
        """设备列表更新处理"""
        self.update_device_combo(devices)
        
    def toggle_logging(self):
        """切换日志记录状态"""
        if self.is_logging:
            self.stop_logging()
        else:
            self.start_logging()
            
    def start_logging(self):
        """开始日志记录 - 增强版"""
        print("开始日志记录函数被调用")
        
        # 添加状态保护
        if self.is_logging:
            print("已经在记录中，跳过启动")
            return
            
        if not self.current_device:
            QMessageBox.warning(self, "警告", "请先选择设备")
            return
            
        if self.current_device.status != "device":
            QMessageBox.warning(self, "警告", "设备未连接或状态异常")
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
            self.start_stop_action.setText("⏸ 停止")
            self.start_stop_action.setToolTip("停止当前日志记录")
            self.statusBar().showMessage("正在记录日志...")
            # 更新窗口标题显示记录状态
            if self.current_device:
                self.setWindowTitle(f'Logmaster - {self.current_device.serial} [正在记录]')
            else:
                self.setWindowTitle('Logmaster - Android日志分析工具 [正在记录]')
        else:
            self.start_stop_action.setText("▶ 开始")
            self.start_stop_action.setToolTip("开始记录新的日志")
            self.statusBar().showMessage("日志记录已停止")
            # 恢复窗口标题
            self.setWindowTitle('Logmaster - Android日志分析工具')
    
    def stop_logging(self):
        """停止日志记录"""
        print("停止日志记录函数被调用")
        
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
        
    def get_filter_settings(self) -> dict:
        """获取过滤器设置"""
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
        
        # 标签（支持正则表达式）
        tag_text = self.tag_edit.text().strip()
        if tag_text:
            filters['tag'] = tag_text
            filters['tag_regex'] = self.tag_regex_checkbox.isChecked()
            
        # 关键字
        keyword_text = self.keyword_edit.text().strip()
        if keyword_text:
            filters['keyword'] = keyword_text
            
        # PID
        pid_text = self.pid_edit.text().strip()
        if pid_text:
            filters['pid'] = pid_text
            
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
            
    def on_log_received(self, log_entry: LogEntry):
        """接收到新日志"""
        try:
            # 直接显示日志，保持实时性
            self.log_text.append_colored_log(log_entry)
            self.log_count += 1
            self.update_log_stats()
        except Exception as e:
            print(f"处理日志时出错: {e}")
            import traceback
            traceback.print_exc()
        
    def update_log_stats(self):
        """更新日志统计"""
        stats = self.logcat_reader.get_stats()
        total_logs = stats['total_logs']
        processed_logs = stats['processed_logs']
        
        self.log_stats_label.setText(f"总日志: {total_logs} | 已处理: {processed_logs}")
        
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
            self.statusBar().showMessage("已清除logcat缓冲区")
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
            if not stats['is_running']:
                print("检测到logcat已停止，自动恢复界面状态")
                self.is_logging = False
                self.start_stop_action.setText("▶ 开始")
                self.start_stop_action.setToolTip("开始记录新的日志")
                self.statusBar().showMessage("日志记录已停止")
    
    def update_status_bar(self):
        """更新状态栏"""
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
            
        self.statusBar().showMessage(status_text)
    
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
        
        # 获取当前目录
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