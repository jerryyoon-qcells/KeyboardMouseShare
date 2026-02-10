# Windows 11 Installer Setup - Complete

I've created a complete Windows 11 installer package for the Keyboard Mouse Share application. Here's what has been set up:

## Files Created

### 1. **Build Configuration**
- `keyboard_mouse_share.spec` - PyInstaller configuration to create standalone executable
- `keyboard_mouse_share.iss` - Inno Setup script for professional Windows installer
- `build_windows_installer.ps1` - PowerShell build automation script
- `build_windows_installer.bat` - Batch build automation script

### 2. **Documentation**
- `WINDOWS_INSTALLER_GUIDE.md` - Complete guide for building and distributing installer
- `build/windows/BEFORE_INSTALL.txt` - Pre-installation information for users
- `build/windows/SYSTEM_REQUIREMENTS.txt` - System requirements and compatibility info

### 3. **Support Files**
- `build/windows/` - Directory for build resources (icon placeholder, etc.)

## Quick Start

### Option 1: PowerShell (Recommended for Windows 11)
```powershell
.\build_windows_installer.ps1 -BuildType release
```

### Option 2: Command Prompt (Classic Windows)
```cmd
build_windows_installer.bat release
```

## What Happens During Build

1. ✓ Runs all tests to ensure application works
2. ✓ Creates standalone executable with PyInstaller (~150-200 MB)
3. ✓ Bundles Python runtime and all dependencies
4. ✓ Creates professional Windows installer with Inno Setup (~100-150 MB compressed)

## Output

The installer will be created at:
```
dist/windows/KeyboardMouseShare-Setup-1.0.0.exe
```

## Prerequisites to Install First

Before building, ensure you have:

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - Install with "Add Python to PATH" checked

2. **Virtual Environment with Dependencies**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. **Inno Setup 6** (Optional but recommended)
   - Download: https://jrsoftware.org/isdl.php
   - Without it, you still get a portable executable
   - With it, you get a proper Windows installer

## Features of the Installer

✓ Windows 11 and Windows 10 (build 19041+) support
✓ 64-bit only (modern and secure)
✓ Automatic system requirement validation
✓ Desktop shortcut creation option
✓ Startup launch option
✓ Installation location selection
✓ Registry integration for uninstall
✓ Windows Firewall warning if needed
✓ Professional uninstaller
✓ Automatic firewall rules suggestion

## Distribute

Once built, users receive one file:
- **KeyboardMouseShare-Setup-1.0.0.exe** (~100-150 MB)

Users run it and the application is installed and ready to use.

## Customization

To customize the installer:
1. Edit `keyboard_mouse_share.iss` for installer appearance
2. Create custom icon: `build/windows/kms.ico` (256×256 PNG converted to ICO)
3. Update version in `pyproject.toml` and `.iss` file
4. Rebuild

## Troubleshooting

**If PyInstaller fails:**
- Ensure virtual environment is activated
- Check Python 3.11+ is installed
- Run tests first to verify application works

**If Inno Setup not found:**
- Script will create portable executable anyway
- Optional: Download Inno Setup 6 for professional installer
- Can also manually run: `iscc keyboard_mouse_share.iss`

**If SmartScreen blocks installer:**
- This is normal for unsigned installers
- Users click "More info" → "Run anyway"
- To fix: Code sign the installer (requires certificate)

## Next Steps

1. **Install Prerequisites** (if not already done):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Install Inno Setup** (optional):
   - Download from https://jrsoftware.org/isdl.php

3. **Build the Installer**:
   ```powershell
   .\build_windows_installer.ps1
   ```

4. **Test the Installer**:
   - Run `dist\windows\KeyboardMouseShare-Setup-1.0.0.exe`
   - Verify installation works
   - Test all features

5. **Distribute**:
   - Upload to GitHub releases
   - Host on your website
   - Share with users

## File Sizes (Typical)

- Executable alone: 150-200 MB
- Installer (compressed): 100-150 MB
- After installation on disk: 250-300 MB

## System Requirements (Built In)

The installer automatically checks:
- Windows 11 or Windows 10 (build 19041+)
- 64-bit processor
- Internet connection NOT required (LAN only)
- Administrator access for installation

## Version Management

Update version in 3 places:
1. `pyproject.toml` - version = "1.0.1"
2. `keyboard_mouse_share.iss` - #define MyAppVersion "1.0.1"  
3. `src/main.py` - version="%(prog)s 1.0.1-dev"

Then rebuild.

## Support

All configuration is in these files:
- `keyboard_mouse_share.spec` - PyInstaller options
- `keyboard_mouse_share.iss` - Installer appearance and behavior
- `build_windows_installer.ps1` - Build automation

Edit these to customize for your needs.

---

**You're now ready to create professional Windows installers for your application!**
