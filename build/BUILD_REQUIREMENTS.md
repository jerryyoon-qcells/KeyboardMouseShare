# Build System Requirements

This file lists dependencies required for building production installers.

## Python Build Dependencies

Install these in the `build` group:

```bash
pip install -e .[build]
```

Or manually:

```bash
pip install \
  pyinstaller>=6.1.0 \
  pywin32>=306 \
  wheel>=0.40.0 \
  build>=1.0.0
```

## Windows-Specific Requirements

### NSIS (Nullsoft Scriptable Install System)

**Version**: 3.0 or later

**Installation Options**:

1. **Chocolatey** (Recommended):
   ```powershell
   choco install nsis -y
   ```

2. **Manual Download**:
   - Download from: https://nsis.sourceforge.io/
   - Run installer
   - Default install path: `C:\Program Files (x86)\NSIS\`

3. **Verify Installation**:
   ```powershell
   "C:\Program Files (x86)\NSIS\makensis.exe" /VERSION
   ```

### Code Signing (Optional)

For code-signed executables (Windows SmartScreen bypass):

```powershell
# Requires Windows SDK with SignTool
# Usually located at:
# C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe

# Verify SignTool availability:
where signtool
```

Requires certificate:
- Sectigo/DigiCert EV Code Signing Certificate
- Or self-signed cert for testing

## macOS-Specific Requirements

### Xcode Command Line Tools

```bash
xcode-select --install
```

### create-dmg

```bash
brew install create-dmg
```

### Code Signing and Notarization

```bash
# Apple Developer Account (free)
# Download provisioning profiles from developer.apple.com
# Get App-specific password from appleid.apple.com

# Install notarization tools:
xcode-select --install  # Includes xcrun/notarytool
```

## Development Requirements

For contributing to build scripts:

```bash
pip install \
  pytest>=7.4.0 \
  pylint>=2.17.0 \
  black>=23.9.0 \
  mypy>=1.5.0
```

## CI/CD Requirements

GitHub Actions is configured with:

- Python 3.11 (auto-provisioned)
- pip/setuptools (latest)
- Windows-latest runner (includes NSIS)
- macOS-latest runner (includes Xcode)

No additional setup needed for CI.

## Version Compatibility Matrix

| Component | Min Version | Tested Version | Notes |
|-----------|------------|----------------|-------|
| Python | 3.11 | 3.11.8+ | Required for app and build tools |
| PyInstaller | 6.0 | 6.1.0+ | App bundling |
| NSIS | 3.0 | 3.09 | Windows installer creation |
| pywin32 | 300 | 306+ | Windows-specific modules |
| Xcode | 12.0 | 15.0+ | macOS builds (deprecated) |
| create-dmg | 1.1.0 | 1.1.1+ | macOS DMG creation |

## Troubleshooting

### "pyinstaller command not found"

```bash
pip install pyinstaller --upgrade
# Or add to PATH:
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
# Windows: $env:PATH += ";$HOME\AppData\Local\Programs\Python\Python311\Scripts"
```

### "makensis.exe not found" (Windows)

```powershell
# Check installation
Test-Path "C:\Program Files (x86)\NSIS\makensis.exe"

# Install if missing:
choco install nsis -y

# Or add to PATH manually in Environment Variables
```

### "xcode-select: command not found" (macOS)

```bash
xcode-select --install
# Then restart terminal
```

---

**Last Updated**: February 2026
