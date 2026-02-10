# Keyboard Mouse Share - Multi-Language Implementation

This repository contains **two separate implementations** of the Keyboard Mouse Share application:
- **Python version** (PyQt5 + pynput for cross-platform support)
- **C# .NET version** (WPF for Windows-only optimized performance)

## Project Structure

```
keyboard-mouse-share/
├── python/                    # Python implementation (PyQt5)
│   ├── src/                   # Python application source
│   ├── tests/                 # Python unit and integration tests
│   ├── docs/                  # Python documentation
│   ├── build/                 # Python build artifacts
│   ├── requirements.txt        # Python dependencies
│   └── pyproject.toml         # Python project config
│
├── csharp/                    # C# .NET implementation
│   └── KeyboardMouseShare/    # Main C# project
│       ├── src/               # C# application source
│       │   ├── Models.cs
│       │   ├── Program.cs
│       │   ├── MainWindow.xaml[.cs]
│       │   ├── DeviceDiscoveryService.cs
│       │   ├── ConnectionService.cs
│       │   └── InputEventApplier.cs
│       ├── tests/             # C# unit tests
│       │   └── UnitTests.cs
│       └── KeyboardMouseShare.csproj  # C# project file
│
└── README.md                  # This file
```

## Two Implementations

### Python Version (`./python/`)

**Technology Stack:**
- **Language**: Python 3.11+
- **UI Framework**: PyQt5
- **Input Simulation**: pynput
- **Networking**: zeroconf
- **Platform Support**: Windows, macOS, Linux

**Advantages:**
- Cross-platform support
- Lighter weight
- Excellent testing coverage (526+ tests)
- Production-ready

**Getting Started:**
```bash
cd python
python -m venv .venv
.venv\Scripts\activate        # Windows
# or: source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python -m pytest tests/         # Run tests
python src/main.py            # Launch app
```

### C# .NET Version (`./csharp/`)

**Technology Stack:**
- **Language**: C# 12
- **Framework**: .NET 8.0
- **UI Framework**: WPF (Windows Forms compatible)
- **Input Simulation**: InputSimulator2
- **Networking**: SharpZeroConf
- **Platform Support**: Windows only

**Advantages:**
- High performance on Windows
- Native Windows integration
- Strong typing with C#
- Better resource utilization

**Getting Started:**
```bash
cd csharp/KeyboardMouseShare
dotnet restore              # Restore NuGet packages
dotnet build               # Build solution
dotnet test               # Run tests
dotnet run                # Launch app
```

## Feature Comparison

| Feature | Python | C# .NET |
|---------|--------|---------|
| Cross-Platform | ✅ Windows, macOS, Linux | ❌ Windows only |
| Keyboard Control | ✅ | ✅ |
| Mouse Control | ✅ | ✅ |
| Device Discovery | ✅ (zeroconf) | ✅ (SharpZeroConf) |
| Network Communication | ✅ (TLS 1.3) | ✅ (TLS 1.3) |
| GUI | ✅ PyQt5 | ✅ WPF |
| Input Relay System | ✅ | 🔄 In Development |
| Event Application | ✅ | 🔄 In Development |
| Test Coverage | ✅ 526+ tests | 🔄 In Development |
| Windows Installer | ✅ | 🔄 Planned |
| Code Signing | Prepared | Planned |

## Quick Comparison Table

```
PYTHON VERSION                    C# .NET VERSION
└──────────────────────────────────────────────────
✅ Production Ready                🔄 Actively Developing
✅ 526+ Tests (100% pass)          🔄 Unit tests added
✅ Cross-platform support          ❌ Windows 11 only
✅ PyQt5 UI                        ✅ WPF UI
✅ Lightweight (~300MB)            ✅ Native performance
✅ Easy deployment                 ✅ Enterprise-grade
✅ installerAvailable              🔄 Planned
```

## Development Paths

### Python Development
```bash
cd python
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-build.txt  # For creating installers

# Run tests
pytest tests/ -v

# Build Windows installer (requires Inno Setup)
.\build_windows_installer.ps1

# Launch development
python src/main.py
```

### C# Development
```bash
cd csharp/KeyboardMouseShare
dotnet restore
dotnet build

# Run tests
dotnet test

# Debug run
dotnet run

# Build release
dotnet publish -c Release
```

## Architecture Overview

Both implementations share the same **5-layer architecture**:

### Layer 1: Models
- Device (identification and properties)
- InputEvent (keyboard/mouse events)
- Connection (device-to-device links)

### Layer 2: Services
- Device Discovery (mDNS)
- Connection Management
- Input Relay

### Layer 3: UI
- Python: PyQt5 widgets
- C#: WPF/XAML

### Layer 4: Event Relay
- Batching and queuing
- Retry logic
- Multi-device support

### Layer 5: Event Application
- Keyboard simulation
- Mouse simulation
- State tracking

## System Requirements

### Python Version
- **OS**: Windows 10+, macOS 10.12+, Linux
- **Python**: 3.11 or later
- **Memory**: 4GB RAM
- **Storage**: 500MB

### C# .NET Version
- **OS**: Windows 11 / Windows 10 (build 19041+)
- **Runtime**: .NET 8.0 Runtime
- **Memory**: 4GB RAM
- **Storage**: 500MB
- **Developer**: Visual Studio 2022 / VS Code

## Installation

### Using Python Version
```bash
# Windows Installer
1. Download: KeyboardMouseShare-Setup-1.0.0.exe
2. Run installer
3. Application ready

# Or from source
cd python
pip install -r requirements.txt
python src/main.py
```

### Using C# .NET Version
```bash
# From source
cd csharp/KeyboardMouseShare
dotnet run

# Or from published build
dotnet publish -c Release
# Executable at: bin\Release\net8.0-windows\publish\KeyboardMouseShare.exe
```

## Testing

### Python
```bash
cd python

# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_input_relay.py -v
pytest tests/integration/test_phase4_e2e.py -v
```

### C#
```bash
cd csharp/KeyboardMouseShare

# All tests
dotnet test

# Verbose
dotnet test -v d

# Specific test
dotnet test --filter "InputEventApplierTests"
```

## Configuration

### Python
Configuration file location:
- Windows: `%APPDATA%\keyboard-mouse-share\config.json`
- macOS: `~/Library/Application Support/keyboard-mouse-share/config.json`
- Linux: `~/.config/keyboard-mouse-share/config.json`

### C#
Configuration file location:
- Windows: `%APPDATA%\KeyboardMouseShare\config.json`

Example configuration:
```json
{
  "Device": {
    "Name": "My Computer",
    "Role": "master"
  },
  "Network": {
    "Port": 12345,
    "EnableTLS": true
  },
  "Logging": {
    "LogLevel": "Information"
  }
}
```

## Networking

Both versions use the same network protocols:

- **Service Discovery**: mDNS (Multicast DNS) on port 5353
- **Device Communication**: Custom protocol on port 12345
- **Security**: TLS 1.3 encryption
- **Network Requirement**: Local network (LAN) only

## Contributing

### Python Development
1. Fork repository
2. Create feature branch
3. Make changes in `/python` directory
4. Add tests in `/python/tests`
5. Run: `pytest tests/ -v`
6. Submit pull request

### C# Development
1. Fork repository
2. Create feature branch
3. Make changes in `/csharp` directory
4. Add tests in `/csharp/KeyboardMouseShare/tests`
5. Run: `dotnet test`
6. Submit pull request

## Build & Distribution

### Python Distribution
```bash
cd python
.\build_windows_installer.ps1 -BuildType release

# Output: dist\windows\KeyboardMouseShare-Setup-1.0.0.exe
```

### C# Distribution
```bash
cd csharp/KeyboardMouseShare
dotnet publish -c Release -p:PublishProfile=WindowsDesktop

# Output: bin\Release\net8.0-windows\publish\
```

## License

MIT License - See LICENSE.txt

## Support

### Python Version
- Issues: GitHub Issues (tag with `[Python]`)
- Documentation: `/python/docs/...`
- Tests: `/python/tests/...`

### C# .NET Version
- Issues: GitHub Issues (tag with `[C#]`)
- Documentation: `/csharp/...`
- Tests: `/csharp/KeyboardMouseShare/tests/...`

## Roadmap

### Phase 6: Multi-Device Coordination (Both)
- Device priority management
- Simultaneous 3+ device connections
- Automatic failover
- Session persistence

### Phase 7: Performance Optimization (Both)
- Latency measurement
- Event batching optimization
- Memory optimization
- Network bandwidth

### Phase 8: Advanced Features (Python First, then C#)
- Clipboard sharing
- File transfer
- Multi-display support
- Application launching

## Development Notes

### Synchronization
Both implementations aim for feature parity where platform differences allow. Core architectural patterns are identical.

### Testing Philosophy
- Unit tests verify component behavior
- Integration tests verify end-to-end flows
- E2E tests simulate real user scenarios

### Code Quality
- Python: ruff for linting, 526+ tests
- C#: Code analysis enabled, xunit tests

## FAQ

**Q: Which version should I use?**
A: Use Python for cross-platform support. Use C# for Windows-only high performance.

**Q: Can I run both simultaneously?**
A: Yes, on different ports or machines.

**Q: Is network communication encrypted?**
A: Yes, both use TLS 1.3.

**Q: What's the latency?**
A: ~10-50ms per event depending on network conditions.

**Q: Can I contribute to both?**
A: Yes! Both codebases welcome contributions.

---

**Start with Python version** if you want immediate cross-platform support.

**Start with C# version** if you want native Windows performance and enterprise-grade development.

Ready to get started? Pick your language and dive in! 🚀
