# LogMaster Pro - Architecture Overview

## Project Overview

LogMaster Pro is a professional Android log analysis tool built with Python and PyQt5. It provides advanced filtering, real-time log monitoring, and comprehensive search capabilities that surpass Android Studio Logcat.

**Architecture Pattern**: Modular architecture with clear separation between core logic and GUI  
**Technology Stack**: Python 3.6+, PyQt5, ADB (Android Debug Bridge)  
**Platform Support**: macOS 10.12+, Linux, Windows 10+

## Core Architecture

### Module Structure

```
LogMasterPro.py          # Main entry point, handles initialization and error handling
src/
├── core.py              # Core functionality: DeviceManager, LogcatReader, data models
└── gui.py               # PyQt5-based GUI: MainWindow, custom widgets, event handling
```

### Key Components

#### DeviceManager (src/core.py:53-206)
- **Purpose**: Android device detection and management
- **Key Methods**: `get_devices()`, `start_monitoring()`, `is_adb_available()`
- **Threading**: Uses background thread for device monitoring
- **Callbacks**: Supports device change notifications

#### LogcatReader (src/core.py:208-538)
- **Purpose**: ADB logcat reading and filtering
- **Key Methods**: `start_logcat()`, `stop_logcat()`, `set_filter()`
- **Filtering**: Supports level, tag (regex), keyword, and PID filters
- **Buffering**: Maintains circular buffer (10k entries) for performance
- **Threading**: Separate thread for log reading to prevent UI blocking

#### LogMasterPro GUI (src/gui.py:122-1073)
- **Purpose**: Main application window and user interface
- **Key Features**: Real-time log display, advanced filtering, search functionality
- **Custom Widgets**: `LogTextEdit` for colored log display, `LogUpdateThread` for async updates
- **Styling**: Modern dark theme with custom CSS-like styling

### Data Models

#### LogEntry (src/core.py:29-40)
```python
@dataclass
class LogEntry:
    timestamp: str
    pid: str
    tid: str
    level: LogLevel
    tag: str
    message: str
    raw_line: str
    device_serial: str
```

#### Device (src/core.py:42-51)
```python
class Device:
    serial: str
    status: str
    product: str
    model: str
    device: str
    transport_id: str
```

## Build & Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python3 LogMasterPro.py

# Using launch script (recommended)
./scripts/launch.sh

# Environment check
./scripts/launch.sh --check
```

### Testing
```bash
# Generate test logs
python3 tests/generate_test_logs.py --count 1000 --output test_logs.txt

# Run functionality tests
python3 tests/test_functionality.py
```

### macOS App Creation
```bash
# Create macOS application bundle
./scripts/create_macos_app.sh
```

### Deployment
```bash
# Package for distribution (manual process)
# 1. Ensure all dependencies are installed
# 2. Test on target platforms
# 3. Create platform-specific packages
```

## Code Style & Conventions

### Python Code Style
- **Language**: Python 3.6+ with type hints where applicable
- **Naming**: Snake_case for functions/variables, PascalCase for classes
- **Documentation**: Chinese comments for business logic, English for technical details
- **Error Handling**: Try-except blocks with specific exception types
- **Threading**: Daemon threads for background operations

### GUI Conventions
- **Widget Naming**: Descriptive names (e.g., `log_text`, `device_combo`)
- **Styling**: CSS-like styling embedded in Python code
- **Layout**: QVBoxLayout/QHBoxLayout for consistent spacing
- **Icons**: Unicode symbols for buttons (▶, ⏸, 💾)

### File Organization
- **Core Logic**: Separate from GUI in `src/core.py`
- **GUI Code**: Consolidated in `src/gui.py`
- **Entry Point**: Minimal logic in `LogMasterPro.py`
- **Resources**: Icons and assets in `assets/` directory

## Testing Strategy

### Test Structure
- **Unit Tests**: `tests/test_functionality.py` - Core functionality testing
- **Integration Tests**: Manual testing with real Android devices
- **Performance Tests**: Buffer management and large log handling

### Test Execution
```bash
# Run all tests
python3 tests/test_functionality.py

# Test with specific scenarios
python3 test_autoscroll_fix.py
python3 test_pid_filter_autoscroll.py
```

### Key Test Areas
- Device detection and connection handling
- Log filtering accuracy (regex, multi-tag)
- UI responsiveness during high log volume
- Search functionality performance
- File save operations

## Security Considerations

### Data Protection
- **Log Data**: Stored locally only, no external transmission
- **File Access**: User-controlled save operations with file dialogs
- **Device Access**: Requires ADB authorization on device

### Input Validation
- **Regex Patterns**: Error handling for invalid regex expressions
- **File Paths**: Validation through QFileDialog
- **Device Input**: ADB command validation and timeout handling

### Process Security
- **ADB Commands**: Limited to read-only logcat operations
- **Subprocess Management**: Proper process termination and cleanup
- **Thread Safety**: Mutex locks for shared data structures

## Configuration Management

### Environment Requirements
- **Python**: 3.6+ with PyQt5 5.15+
- **ADB**: Android SDK platform-tools
- **System**: macOS 10.12+, Linux, or Windows 10+

### Runtime Configuration
- **Filters**: Runtime-configurable through GUI
- **Display**: Color schemes and auto-scroll preferences
- **Buffer**: Fixed 10k entry circular buffer
- **Monitoring**: 1-second device polling interval

### Dependencies (requirements.txt)
```
PyQt5>=5.15.0
adb-shell>=0.4.0
```

## Performance Considerations

### Memory Management
- **Circular Buffer**: 10k entry limit prevents memory exhaustion
- **Line Limiting**: 100k line limit in log display
- **Thread Cleanup**: Proper thread termination on exit

### UI Responsiveness
- **Async Updates**: Separate thread for log processing
- **Delayed Filtering**: 1-second delay before applying filters
- **Progressive Search**: Real-time search with debouncing

### ADB Optimization
- **Simple Commands**: Minimal ADB command complexity
- **Timeout Handling**: 5-second timeouts for ADB operations
- **Error Recovery**: Graceful handling of ADB disconnections

## Development Workflow

### Adding New Features
1. **Core Logic**: Implement in `src/core.py` with proper error handling
2. **GUI Integration**: Add UI elements in `src/gui.py`
3. **Testing**: Add corresponding tests in `tests/`
4. **Documentation**: Update development.md and inline comments

### Debugging Guidelines
- **ADB Issues**: Check `adb devices` and device authorization
- **GUI Issues**: Enable PyQt5 debug mode or add print statements
- **Threading Issues**: Monitor thread lifecycle and callbacks
- **Performance**: Use buffer statistics and timing logs

### Common Issues
- **Device Not Found**: ADB not in PATH or device not authorized
- **PyQt5 Import**: Virtual environment or system package issues
- **Performance**: Large log volumes may require buffer tuning
- **macOS Permissions**: May require accessibility permissions for GUI