# Build & Release Manual

This document covers building and releasing Keyboard Mouse Share installers.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Building Windows Installer](#building-windows-installer)
3. [Building macOS DMG](#building-macos-dmg)
4. [Signing & Notarization](#signing--notarization)
5. [Testing Installers](#testing-installers)
6. [Release Process](#release-process)
7. [Troubleshooting](#troubleshooting)

---

## Development Setup

### Prerequisites

- Git 2.20+
- Python 3.11+
- Node.js 18+ (for GitHub automation)
- Windows 10/11 for Windows builds
- macOS 10.15+ for macOS builds
- NSIS 3.0+ (Windows)
- Xcode 12+ (macOS)

### Clone & Setup Repository

```bash
# Clone repository
git clone https://github.com/yourusername/keyboard-mouse-share.git
cd keyboard-mouse-share

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -e python[dev,build]
pip install pyinstaller pywin32  # (Windows)
```

---

## Building Windows Installer

### Step 1: Prepare Binaries

```powershell
# From Windows machine with Python 3.11+

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run build script (handles everything)
.\build\windows\build.ps1 -Version "1.0.0"
```

### Step 2: Verify Output

```powershell
# Check dist directory
Get-ChildItem .\build\dist\

# Expected files:
# - KeyboardMouseShare-1.0.0-setup.exe
# - KeyboardMouseShare-1.0.0-setup.exe.sha256
# - RELEASE_NOTES.txt
```

### Manual Build (If Needed)

```powershell
# Step A: Run PyInstaller
pyinstaller `
  .\build\windows\pyinstaller.spec `
  --distpath .\build\dist `
  --buildpath .\build\windows\build `
  --specpath .\build\windows

# Step B: Build NSIS installer
$nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
& $nsisPath /V2 .\build\windows\keyboard-mouse-share.nsi

# Step C: Generate checksum
$installer = ".\build\dist\KeyboardMouseShare-1.0.0-setup.exe"
(Get-FileHash $installer -Algorithm SHA256).Hash | `
  Out-File -FilePath "$installer.sha256" -Encoding UTF8 -NoNewline
```

### Build Configuration

Edit `build/windows/pyinstaller.spec` to customize:

```python
# Include additional files:
datas=[
    ('python/src', 'src'),
    ('path/to/icons', 'icons'),
    ('path/to/docs', 'docs'),
]

# Add hidden imports:
hiddenimports=[
    'zeroconf',
    'pynput',
    'cryptography',
]
```

---

## Building macOS DMG

### Step 1: Prepare DMG Script

Create `build/macos/create-dmg.sh`:

```bash
#!/bin/bash

# Build DMG installer for macOS
VERSION="1.0.0"
APP_NAME="Keyboard Mouse Share"
DMG_FILE="build/dist/KeyboardMouseShare-${VERSION}-macos.dmg"

# Create PyInstaller build
pyinstaller build/macos/pyinstaller-macos.spec \
  --distpath build/dist \
  --buildpath build/macos/build \
  --specpath build/macos

# Create DMG
mkdir -p dmg_temp
cp -r build/dist/KeyboardMouseShare.app dmg_temp/
cp README.md dmg_temp/
cp LICENSE dmg_temp/

hdiutil create \
  -volname "${APP_NAME}" \
  -srcfolder dmg_temp \
  -ov -format UDZO \
  "${DMG_FILE}"

rm -rf dmg_temp

echo "✓ DMG created: ${DMG_FILE}"
```

### Step 2: Run Build

```bash
chmod +x build/macos/create-dmg.sh
./build/macos/create-dmg.sh
```

---

## Signing & Notarization

### Windows Code Signing (Optional but Recommended)

```powershell
# Requires code signing certificate from DigiCert, Sectigo, etc.
# Using SignTool (Windows SDK)

$certPath = "path/to/certificate.pfx"
$certPassword = "certificate-password"
$installerPath = "build\dist\KeyboardMouseShare-1.0.0-setup.exe"

# Sign the installer
signtool sign `
  /f "$certPath" `
  /p "$certPassword" `
  /a `
  "$installerPath"

# Verify signature
signtool verify /a "$installerPath"
```

### macOS Codesigning & Notarization

```bash
# Sign the app
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" \
  build/dist/KeyboardMouseShare.app

# Notarize with Apple
xcrun notarytool submit build/dist/KeyboardMouseShare-1.0.0-macos.dmg \
  --apple-id "your-apple-id@example.com" \
  --password "app-specific-password" \
  --team-id "YOURTEAMID"
```

---

## Testing Installers

### Windows Installer Testing

```powershell
# Test 1: Silent install
$InstallDirectory = "C:\Temp\KeyboardMouseShareTest"
New-Item -ItemType Directory -Path $InstallDirectory -Force

.\build\dist\KeyboardMouseShareSetup.exe /S /D=$InstallDirectory
Start-Sleep -Seconds 10

# Test 2: Verify installation
Test-Path "$InstallDirectory\KeyboardMouseShare.exe"

# Test 3: Run application
& "$InstallDirectory\KeyboardMouseShare.exe"

# Test 4: Uninstall
& "$InstallDirectory\Uninstall.exe" /S
```

### macOS Installer Testing

```bash
# Test 1: Mount DMG
hdiutil mount build/dist/KeyboardMouseShare-1.0.0-macos.dmg

# Test 2: Copy to Applications
cp -r /Volumes/KeyboardMouseShare/KeyboardMouseShare.app /Applications/

# Test 3: Run application
open /Applications/KeyboardMouseShare.app

# Test 4: Verify codesignature
codesign -v /Applications/KeyboardMouseShare.app
```

### Automated Testing

```powershell
# Test matrix across Windows versions
$versions = @("Windows 10 Enterprise", "Windows 11 Professional")
foreach ($version in $versions) {
    # Test in VM or container
    Write-Host "Testing on $version..."
    # Run installer and basic functionality tests
}
```

---

## Release Process

### Automated Release (GitHub Actions)

1. **Create Release Tag**:
   ```bash
   git tag -a v1.0.0 -m "Release Version 1.0.0"
   git push origin v1.0.0
   ```

2. **GitHub Actions Triggers**:
   - Workflow `.github/workflows/release.yml` automatically runs
   - Builds Windows installer
   - Creates checksum files
   - Generates release notes
   - Uploads to GitHub Releases

3. **Monitor Build**:
   - View logs at: github.com/yourusername/keyboard-mouse-share/actions
   - Typically completes in 10-15 minutes

### Manual Release Process

```bash
# Step 1: Prepare release branch
git checkout -b release/v1.0.0
sed -i 's/version = ".*"/version = "1.0.0"/' python/pyproject.toml

# Step 2: Commit version bump
git add python/pyproject.toml
git commit -m "Bump version to 1.0.0"

# Step 3: Create tag
git tag -s -a v1.0.0 -m "Release v1.0.0 - Production Release"

# Step 4: Push to remote
git push origin release/v1.0.0
git push origin v1.0.0

# Step 5: Create GitHub Release (manually or via API)
# - Draft release notes
# - Upload binaries (Windows .exe, macOS .dmg)
# - Include SHA256 checksums
# - Publish release
```

---

## Release Checklist

- [ ] All tests passing (coverage > 70%)
- [ ] Code review approved
- [ ] Version numbers updated
- [ ] CHANGELOG.md updated with release notes
- [ ] Build artifacts generated and verified
- [ ] Checksums computed and recorded
- [ ] Installers tested on target platforms
- [ ] Code signed (if applicable)
- [ ] README and docs match new version
- [ ] Installation instructions updated
- [ ] Release notes complete
- [ ] GitHub Release created with assets
- [ ] Announcement/changelog published
- [ ] Backup of source tagged in git

---

## Troubleshooting

### PyInstaller Issues

**Problem**: "ModuleNotFoundError: No module named 'zeroconf'"

**Solution**:
```powershell
# Add to hiddenimports in pyinstaller.spec
hiddenimports=['zeroconf', 'pynput', 'cryptography']

# Or install globally:
pip install zeroconf pynput cryptography
```

### NSIS Compilation Fails

**Problem**: "makensis.exe: Command not found"

**Solution**:
```powershell
# Install NSIS via Chocolatey
choco install nsis -y

# Or download from https://nsis.sourceforge.io/
```

**Problem**: "Script error: Invalid command 'File /r'"

**Solution**: Update NSIS installation or fix script path:
```nsi
; Use absolute paths:
File /r "C:\full\path\to\dist\*.*"
```

### Code Signing Certificate Issues

**Problem**: "SignTool Error: The specified timestamp server could not be reached"

**Solution**:
```powershell
# Retry with different timestamp server
signtool sign /f certificate.pfx `
  /t http://timestamp.sectigo.com `
  installer.exe
```

### Test Installation Rollback

```powershell
# Create system restore point before testing
Checkpoint-Computer -Description "Before Keyboard Mouse Share Test"

# Test installer
# If issues, restore:
Restore-Computer -RestorePoint (Get-ComputerRestorePoint)[0].SequenceNumber
```

---

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes or major features
- **MINOR** (1.1.0): New features, backward compatible
- **PATCH** (1.0.1): Bug fixes, backward compatible

**Example**:
- v1.0.0 - Production release
- v1.0.1 - Security patch
- v1.1.0 - New device discovery features
- v2.0.0 - Major refactor, protocol changes

---

## Distribution Channels

1. **GitHub Releases**: Primary source
   - https://github.com/yourusername/keyboard-mouse-share/releases

2. **Direct Download**: Host on website
   - https://keyboard-mouse-share.local/download.html

3. **Package Managers** (future):
   - Windows: Chocolatey, Winget
   - macOS: Homebrew
   - Linux: Snap, AppImage

---

**Last Updated**: February 2026  
**Version**: 1.0.0  
**Maintainer**: Cross-Device Input Team
