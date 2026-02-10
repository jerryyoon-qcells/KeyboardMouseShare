# Windows 11 Installer Guide

This guide will help you create a professional Windows installer for the Keyboard Mouse Share application.

## Quick Start (Automated)

The easiest way is to use the automated build script:

```powershell
.\build_windows_installer.ps1 -BuildType release
```

This will:
1. ✓ Run all tests
2. ✓ Build standalone executable with PyInstaller
3. ✓ Create Windows installer with Inno Setup
4. ✓ Output to `dist\windows\`

## Prerequisites

### Required Software

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - Ensure "Add Python to PATH" is checked during installation

2. **Inno Setup 6** (for creating installer)
   - Download: https://jrsoftware.org/isdl.php
   - Installation is optional - executable will still be created without it

3. **Virtual Environment with Dependencies**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install pyinstaller
   ```

### System Requirements

- Windows 10 (build 19041+) or Windows 11
- 64-bit processor
- Administrator access for installation
- 500+ MB free disk space

## Build Process

### Option 1: Automated Build (Recommended)

```powershell
cd C:\path\to\keyboard-mouse-share
.\build_windows_installer.ps1
```

**Parameters:**
- `-BuildType release` - Optimized build (default)
- `-BuildType debug` - Debug build with verbose output
- `-SkipTests` - Skip test execution
- `-SkipClean` - Don't clean previous builds

### Option 2: Manual Build with Inno Setup

#### Step 1: Build Executable
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Build with PyInstaller
pyinstaller keyboard_mouse_share.spec
```

Output: `dist\KeyboardMouseShare\KeyboardMouseShare.exe`

#### Step 2: Create Installer
- Install Inno Setup
- Right-click `keyboard_mouse_share.iss`
- Select "Compile with Inno Setup"

Or command line:
```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" keyboard_mouse_share.iss
```

Output: `dist\windows\KeyboardMouseShare-Setup-1.0.0.exe`

### Option 3: Just Portable Executable

If you don't need an installer, just the executable:

```powershell
pyinstaller keyboard_mouse_share.spec
# Executable: dist\KeyboardMouseShare\KeyboardMouseShare.exe
```

Distribute the entire `dist\KeyboardMouseShare\` folder.

## Output Files

### From PyInstaller
```
dist/
└── KeyboardMouseShare/
    ├── KeyboardMouseShare.exe (main executable)
    ├── _internal/ (dependencies and libraries)
    ├── Python runtime (bundled)
    └── All required libraries
```

### From Inno Setup
```
dist/windows/
└── KeyboardMouseShare-Setup-1.0.0.exe (Windows installer)
```

## File Sizes

Typical sizes:
- **Portable Executable**: 150-200 MB
- **Windows Installer**: 100-150 MB (compressed)

## Distribution

### For Users (Choose One)

**Option A: Use Installer** (Recommended)
- Distribute: `KeyboardMouseShare-Setup-1.0.0.exe`
- Users run installer, select location, application is ready
- Uninstall available through Control Panel
- File size: ~100-150 MB

**Option B: Portable Version**
- Distribute: Entire `KeyboardMouseShare/` folder (zip it)
- Users extract and run `KeyboardMouseShare.exe`
- No installation needed, portable
- File size: ~150-200 MB

## Customization

### Change Application Icon
1. Create 256×256 PNG image
2. Convert to ICO format (use online converter)
3. Save as `build/windows/kms.ico`
4. Rebuild

### Update Application Name/Version
Edit `keyboard_mouse_share.iss`:
```
#define MyAppVersion "1.0.1"
#define MyAppName "Keyboard Mouse Share"
```

Then rebuild.

### Modify Installer Appearance
Edit `keyboard_mouse_share.iss` to customize:
- Welcome text
- Installation options (desktop icon, startup, etc.)
- License file
- Publisher information
- Support URLs

## Troubleshooting

### PyInstaller Issues

**Error: "No module named 'src'"**
- Ensure you're in the project root directory
- Check `.venv\Scripts\Activate.ps1` was run

**Large executable (400+ MB)**
- Normal - includes Python runtime
- Can be reduced by excluding unused modules in `.spec` file

### Inno Setup Issues

**"ISCC.exe not found"**
- Install Inno Setup 6 from https://jrsoftware.org/isdl.php
- Or build script will just create portable executable

**SmartScreen warning**
- This appears for unsigned installers
- Warn users to click "Run anyway"
- To fix: Code sign the executable (requires certificate)

### Windows SmartScreen Blocked

If users see "Windows protected your PC":
1. Click "More info"
2. Click "Run anyway"

To prevent this, you need to:
- Code sign the executable with a certificate
- Build reputation (many downloads)

## Code Signing (Optional)

For professional distribution, code sign the executable:

```powershell
# Sign executable
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com dist\KeyboardMouseShare\KeyboardMouseShare.exe

# Sign installer
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com dist\windows\KeyboardMouseShare-Setup-1.0.0.exe
```

Requires:
- Code signing certificate (from GoDaddy, DigiCert, etc.)
- Microsoft SignTool (part of Windows SDK)

## Testing the Installer

1. **Uninstall any existing version**
2. **Test on clean Windows installation** (use VM)
3. **Verify all features work:**
   - Application launches
   - Configuration loads
   - Device discovery works
   - Input relay functions
   - Uninstall works cleanly

## Hosting and Distribution

### On GitHub
1. Create Release
2. Upload `KeyboardMouseShare-Setup-1.0.0.exe`
3. Users download directly

### On Website
```html
<a href="/downloads/KeyboardMouseShare-Setup-1.0.0.exe">
  Download for Windows (100 MB)
</a>
```

### Updates
- Each version gets new executable
- Users must uninstall old version
- Or implement auto-update (advanced)

## Legal

Ensure you have:
- [ ] LICENSE.txt in installer
- [ ] README.md with system requirements
- [ ] Privacy policy referencing network access
- [ ] Third-party licenses for PyQt5, pynput, etc.

## Next Steps

1. **First run:** `.\build_windows_installer.ps1`
2. **Test installer:** Run in virtual machine or test system
3. **Distribute:** Upload to GitHub releases or website
4. **Document:** Add installation instructions to README.md

## Support

For issues with the build process:
1. Check system requirements above
2. Ensure Python 3.11+ is installed
3. Run in PowerShell as Administrator
4. Check build output for specific errors

For installer issues:
1. Reinstall Inno Setup
2. Check `keyboard_mouse_share.iss` syntax
3. Run `pyinstaller keyboard_mouse_share.spec` separately

## Environment Variables (Build Script)

The build script uses:
- `PYINSTALLER_OPTIONS` (if set) - additional PyInstaller arguments
- Current Python environment from `.venv`

## Version Management

Update version in:
1. `pyproject.toml` - `version = "1.0.1"`
2. `keyboard_mouse_share.spec` - `--version="1.0.1"`
3. `keyboard_mouse_share.iss` - `#define MyAppVersion "1.0.1"`
4. `src/main.py` - `version="%(prog)s 1.0.1-dev"`

Then rebuild the installer.
