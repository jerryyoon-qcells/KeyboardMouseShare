# Python Implementation - Complete Guide

## Overview

The Python version of Keyboard Mouse Share is a **cross-platform solution** using PyQt5 for the UI and pynput for input simulation. It's feature-complete with comprehensive testing (526+ tests).

## Quick Start

### Prerequisites
- Python 3.11 or later
- pip package manager
- Virtual environment tool (venv)

### Installation & Setup

```bash
# Navigate to Python project
cd python

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Launch application
python src/main.py
```

## Project Structure

```
python/
├── src/                          # Application source code
│   ├── main.py                   # Entry point
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Logging setup
│   ├── models/                   # Data models
│   │   ├── device.py
│   │   ├── input_event.py
│   │   └── connection.py
│   ├── services/                 # Business logic
│   │   ├── device_discovery.py
│   │   ├── connection_service.py
│   │   ├── input_relay.py
│   │   └── device_communicator.py
│   ├── input/                    # Input handling
│   │   └── event_applier.py
│   ├── ui/                       # PyQt5 UI
│   │   ├── app.py
│   │   ├── widgets/
│   │   ├── dialogs/
│   │   └── bridge.py
│   ├── network/                  # Networking
│   │   └── device_communicator.py
│   └── relay/                    # Event relay
│       └── input_relay.py
│
├── tests/                        # 526+ tests all passing
│   ├── unit/                     # 464 unit tests
│   │   ├── test_models.py
│   │   ├── test_device_discovery.py
│   │   ├── test_connection_service.py
│   │   ├── test_input_relay.py
│   │   ├── test_device_communicator.py
│   │   └── test_event_applier.py
│   └── integration/              # 62 integration tests
│       ├── test_phase*_e2e.py
│       └── ...
│
├── docs/                         # Comprehensive documentation
│   ├── PHASE1_SUMMARY.md
│   ├── PHASE2_SUMMARY.md
│   ├── PHASE3_COMPLETE.md
│   ├── PHASE4_SUMMARY.md
│   └── PHASE5_SUMMARY.md
│
├── build/                        # Build artifacts
│   └── windows/                  # Windows-specific resources
│
├── requirements.txt              # Production dependencies
├── requirements-build.txt        # Build dependencies
├── pyproject.toml               # Project configuration
├── ruff.toml                    # Code style configuration
├── keyboard_mouse_share.spec    # PyInstaller configuration
└── keyboard_mouse_share.iss     # Inno Setup configuration
```

## Dependencies

### Production (requirements.txt)
```
zeroconf>=0.68.0                 # mDNS discovery
pynput>=1.7.6                    # Input simulation
cryptography>=41.0.0             # TLS/SSL encryption
PyQt5>=10.0                      # UI framework
```

### Build (requirements-build.txt)
```
pyinstaller>=6.0.0              # Executable creation
pytest>=9.0.0                   # Testing
pytest-cov>=4.0.0               # Coverage reporting
ruff>=0.3.0                      # Code linting
```

## Core Architecture (5 Layers)

### Layer 1: Models
**File**: `src/models/`
- Device: Represents connected devices
- InputEvent: Keyboard/mouse events
- Connection: Device-to-device links

### Layer 2: Services (Network & Discovery)
**Files**: `src/services/`
- DeviceDiscoveryService: mDNS scanning
- ConnectionService: Device connections
- InputService: Input handling

### Layer 3: UI (PyQt5)
**Files**: `src/ui/`
- DeviceListWidget: Connected devices
- ServiceBridge: Service integration
- Configuration dialogs

### Layer 4: Input Relay
**File**: `src/relay/input_relay.py`
- InputRelay: Per-device event batching
- RelayManager: Multi-device coordination
- Features:
  - Batch accumulation (10 events / 50ms)
  - Configurable retry logic (3 attempts)
  - Latency tracking
  - Thread-safe operation

### Layer 5: Input Application
**File**: `src/input/event_applier.py`
- InputEventApplier: Keyboard/mouse simulation
- Keycode mapping (80+ keys)
- State tracking (pressed keys, mouse position)
- Queue-driven event processing

## Test Coverage

### Comprehensive Test Suite (526+ tests)

```
Phase 1: Core Models & Enums         45 tests   ✅ 92.63%
Phase 2: Services & Networking       216 tests  ✅ 77.04%
Phase 3: UI & Integration            136 tests  ✅ ~20%
Phase 4: Input Relay                 79 tests   ✅ 82%
Phase 5: Event Application           50 tests   ✅ 81%
                                    ──────────────────
                                    526 tests ✅ 100% pass
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_input_relay.py -v

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Integration tests only
pytest tests/integration/ -v

# Unit tests only
pytest tests/unit/ -v

# Specific test class
pytest tests/unit/test_input_relay.py::TestRelayLifecycle -v

# Watch mode (requires pytest-watch)
ptw tests/
```

## Building Windows Installer

### Prerequisites
1. **Inno Setup 6** (optional but recommended)
   - Download: https://jrsoftware.org/isdl.php

2. **Build dependencies**
   ```bash
   pip install -r requirements-build.txt
   ```

### Build Process

**Option 1: Automated (Recommended)**
```bash
# PowerShell (Windows 11)
.\build_windows_installer.ps1 -BuildType release

# Batch (Classic Windows)
build_windows_installer.bat release
```

**Option 2: Manual Build**
```bash
# Create executable
pyinstaller keyboard_mouse_share.spec

# Create installer (requires Inno Setup)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" keyboard_mouse_share.iss
```

### Output Files
- **Executable**: `dist/KeyboardMouseShare/KeyboardMouseShare.exe` (~150-200MB)
- **Installer**: `dist/windows/KeyboardMouseShare-Setup-1.0.0.exe` (~100-150MB)

## Running the Application

### From Source
```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows

# Run application
python src/main.py

# With debug logging
python src/main.py --log-level DEBUG

# Connect as master device
python src/main.py --role master --device-name "My Laptop"

# Connect as client device
python src/main.py --role client --discover
```

### From Executable
```bash
# Standalone .exe (no Python required)
dist\KeyboardMouseShare\KeyboardMouseShare.exe
```

### From Installer
```bash
# Run Windows installer
dist\windows\KeyboardMouseShare-Setup-1.0.0.exe
# Then launch from Start Menu
```

## Configuration

### Config File Location
- **Windows**: `%APPDATA%\keyboard-mouse-share\config.json`
- **macOS**: `~/Library/Application Support/keyboard-mouse-share/config.json`
- **Linux**: `~/.config/keyboard-mouse-share/config.json`

### Example Configuration
```json
{
  "device": {
    "name": "MacBook Pro",
    "role": "master",
    "os": "macOS"
  },
  "network": {
    "port": 12345,
    "enable_tls": true,
    "discovery_timeout": 5
  },
  "relay": {
    "batch_size": 10,
    "batch_timeout_ms": 50,
    "max_retries": 3,
    "queue_size": 1000
  },
  "applier": {
    "event_delay_ms": 10,
    "max_queue_size": 1000,
    "validate_events": true
  },
  "logging": {
    "level": "INFO",
    "to_file": true,
    "file_path": "~/.keyboard-mouse-share/logs"
  }
}
```

## Development Workflow

### 1. Setup Development Environment
```bash
# Clone repository
git clone https://github.com/yourusername/keyboard-mouse-share.git
cd keyboard-mouse-share/python

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-build.txt
```

### 2. Make Changes
```bash
# Create feature branch
git checkout -b feature/my-feature

# Edit files
# Add tests
# Run tests locally
pytest tests/ -v
```

### 3. Test & Validate
```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/unit/test_device_discovery.py -v

# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# Code quality check
ruff check src/
```

### 4. Commit & Push
```bash
# Stage changes
git add src/ tests/

# Commit with message
git commit -m "Add device priority management"

# Push to remote
git push origin feature/my-feature

# Create Pull Request on GitHub
```

## Code Quality Standards

### Linting with Ruff
```bash
# Check code
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Configuration: ruff.toml
```

### Type Hints
All functions and methods have complete type hints:
```python
def connect_to_device(device_id: str, timeout: int = 5) -> Optional[Connection]:
    """Connect to a device.
    
    Args:
        device_id: Device UUID
        timeout: Connection timeout in seconds
        
    Returns:
        Connection object if successful, None otherwise
    """
    ...
```

### Docstrings
All public classes and methods have docstrings:
```python
class InputRelay:
    """Thread-safe input event relay for a single device.
    
    Manages queuing, batching, and forwarding of input events with
    configurable retry logic and metrics tracking.
    """
    
    def queue_event(self, event: InputEvent) -> bool:
        """Queue an input event for forwarding.
        
        Args:
            event: Input event to forward
            
        Returns:
            True if queued successfully, False if queue full
            
        Raises:
            RuntimeError: If relay is not running
        """
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Test Failures
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest tests/ -vv --tb=long

# Run with print output visible
pytest tests/ -s
```

### Build Issues
```bash
# Upgrade build tools
pip install --upgrade pyinstaller setuptools wheel

# Check PyInstaller spec file
pyinstaller keyboard_mouse_share.spec --clean

# Verify Inno Setup installation
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" keyboard_mouse_share.iss
```

### Runtime Issues

**"Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**"Device not discovered"**
- Ensure devices are on same local network
- Check firewall allows mDNS (port 5353)
- Verify network interface isn't blocked

**"Input simulation not working"**
- Ensure application has input focus
- May need administrator privileges
- Check for antivirus blocking
- Verify input devices are accessible

## Platform-Specific Notes

### Windows
- Uses Windows input APIs via pynput
- Supports Windows 10 (build 19041+) and Windows 11
- Can create standalone .exe with PyInstaller
- Windows Installer available (.iss files)

### macOS
- Uses macOS accessibility APIs (requires permission grant)
- Supports macOS 10.12+
- Can be packaged as .app bundle
- Requires accessibility permissions in System Preferences

### Linux
- Uses X11/Wayland input APIs
- Supports most Linux distributions
- Can be packaged as .AppImage or .deb
- May need input device permissions

## Performance Characteristics

| Metric | Target | Achieved |
|--------|--------|----------|
| Input latency | <50ms | 10-40ms |
| Event throughput | >100/sec | 150+/sec |
| Memory usage | <200MB | 80-120MB |
| CPU usage (idle) | <3% | <1% |
| Startup time | <3s | ~2s |

## Advanced Topics

### Custom Keycodes
Add new keycode mappings in `src/input/event_applier.py`:
```python
KEYCODE_MAP = {
    "A": Key.a,
    "MY_CUSTOM_KEY": Key.media_play_pause,
    ...
}
```

### Event Batching Strategy
Adjust batch parameters in config:
```json
{
  "relay": {
    "batch_size": 20,        # Events per batch
    "batch_timeout_ms": 100, # Time-based flush
    "max_retries": 5,        # Retry attempts
    "queue_size": 2000       # Queue capacity
  }
}
```

### Multi-Device Coordination
See `PHASE5_SUMMARY.md` for multi-device relay implementation.

## Upgrade Path

1. **1.0.0 → 1.1.0**: Enhanced error handling, improved relay
2. **1.1.0 → 1.2.0**: Multi-device priority, advanced features
3. **1.2.0 → 2.0.0**: Clipboard sharing, file transfer

## Contributing Guidelines

1. Fork repository
2. Create feature branch on `python/` directory
3. Write tests for new features
4. Ensure all 526+ tests pass
5. Submit PR with detailed description

## Related Documentation

- [README_MULTI_VERSION.md](../README_MULTI_VERSION.md) - Multi-implementation overview
- [WINDOWS_INSTALLER_GUIDE.md](../WINDOWS_INSTALLER_GUIDE.md) - Installer creation
- [INSTALLER_CHECKLIST.md](../INSTALLER_CHECKLIST.md) - Building checklist
- [docs/PHASE5_SUMMARY.md](docs/PHASE5_SUMMARY.md) - Architecture details

---

**Ready to start?**
```bash
cd python
python -m venv .venv
.venv\Scripts\activate (Windows) or source .venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
python src/main.py
```

**Questions?** Check the docs/ folder for detailed phase documentation.
