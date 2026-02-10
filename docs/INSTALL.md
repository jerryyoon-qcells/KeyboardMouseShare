# Installation Guide - Keyboard Mouse Share

## Windows Installation

### System Requirements

- **OS**: Windows 10 or Windows 11 (64-bit recommended)
- **RAM**: Minimum 2 GB (4 GB recommended)
- **Disk Space**: 150 MB for application
- **Network**: Local Area Network (LAN) connectivity
- **Privileges**: Administrator rights required for installation and first run
- **Port Access**: Network access to ports 5353 (mDNS), 20000-20005 (TLS connections)

### Pre-Installation Checklist

- [ ] Windows 10 or later is installed
- [ ] User account has administrator privileges
- [ ] System has access to local network without proxy/firewall blocking LAN
- [ ] .NET Framework 4.7.2+ is installed (or Windows Update to latest)
- [ ] At least 150 MB free disk space available

### Installation Steps

#### Option 1: Graphical Installer (Recommended)

1. **Download** the installer:
   - Visit [https://github.com/yourusername/keyboard-mouse-share/releases](https://github.com/yourusername/keyboard-mouse-share/releases)
   - Download `KeyboardMouseShare-1.0.0-setup.exe`

2. **Run as Administrator**:
   - Right-click the `.exe` file
   - Select "Run as administrator"

3. **Follow the Wizard**:
   - Accept the license agreement
   - Choose installation directory (default: `C:\Program Files\Keyboard Mouse Share`)
   - Wait for installation to complete
   - Click "Finish"

4. **First Launch**:
   - Windows may show a security warning (SmartScreen)
   - Click "More info" → "Run anyway"
   - Grant the application necessary network and system permissions

#### Option 2: Silent Installation (Script/Admin)

```powershell
# Run from PowerShell as Administrator
$installerPath = "C:\Downloads\KeyboardMouseShare-1.0.0-setup.exe"
& $installerPath /S /D="C:\Program Files\Keyboard Mouse Share"

# Wait for installation
Start-Sleep -Seconds 10

# Verify installation
Test-Path "C:\Program Files\Keyboard Mouse Share\KeyboardMouseShare.exe"
```

### Verification

After installation, verify success by:

```powershell
# Check installation directory
Get-ChildItem "C:\Program Files\Keyboard Mouse Share"

# Expected files:
# - KeyboardMouseShare.exe (main application)
# - src/ (Python modules)
# - docs/ (documentation)
```

### Start Menu & Shortcuts

After installation:
- **Start Menu**: Search for "Keyboard Mouse Share" and click
- **Desktop Shortcut**: Shortcut created on desktop
- **Command Line**: Add to PATH for `keyboard-mouse-share` command

### Post-Installation

1. **Network Permissions**:
   - Allow application through Windows Firewall if prompted
   - Grant access to local network only (not internet)

2. **First Run Wizard**:
   - Select Master or Client role
   - Configure device name
   - Set passphrase for device pairing
   - Test device discovery

3. **System Tray Icon**:
   - Application runs in system tray (bottom right)
   - Right-click for menu options
   - Status shows connection information

---

## macOS Installation (Future)

macOS support coming in v1.1.0

### Requirements
- macOS 10.15 or later
- Intel or Apple Silicon (M1/M2/M3+)
- Accessibility permissions
- Approximately 100 MB disk space

---

## Uninstallation

### Windows

#### Using Control Panel

1. Open **Settings** → **Apps** → **Apps & Features**
2. Find "Keyboard Mouse Share"
3. Click **Uninstall**
4. Follow the uninstaller wizard

#### Using Command Line

```powershell
# Run as Administrator
"C:\Program Files\Keyboard Mouse Share\Uninstall.exe"
```

#### Manual Removal

```powershell
# Remove application directory
Remove-Item -Path "C:\Program Files\Keyboard Mouse Share" -Recurse -Force

# Remove shortcuts
Get-ChildItem "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Keyboard Mouse Share" -Recurse | Remove-Item
```

---

## Troubleshooting

### Installation Fails with "Access Denied"

**Problem**: Windows blocks execution of installer

**Solution**:
1. Right-click installer → Properties
2. Check "Unblock" checkbox at bottom
3. Click Apply → OK
4. Run as Administrator again

### Application Won't Start After Install

**Problem**: KeyboardMouseShare.exe won't launch

**Solutions**:
1. Check Windows Event Viewer for errors:
   ```powershell
   Get-WinEvent -LogName Application | Where-Object {$_.Source -like "*Keyboard*"}
   ```

2. Verify installation integrity:
   ```powershell
   Get-FileHash "C:\Program Files\Keyboard Mouse Share\KeyboardMouseShare.exe"
   ```

3. Repair installation:
   - Uninstall completely (see Uninstallation section)
   - Reboot system
   - Reinstall fresh

4. Check .NET Framework:
   ```powershell
   # Verify .NET 4.7.2 or later
   Get-ChildItem "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP" -Recurse | `
     Where-Object {$_.Name -like "*Full*" -or $_.Name -like "*Core*"}
   ```

### Network Discovery Not Working

**Problem**: Cannot find other devices on network

**Checklist**:
- [ ] Both devices on same LAN (not WiFi-isolated from each other)
- [ ] Firewall allows UDP port 5353 (mDNS)
- [ ] No network proxy blocking multicast
- [ ] Both applications running and set to same role (one Master, one Client)
- [ ] Both devices have matching passphrases configured

### Connection Timeout Errors

**Problem**: "Connection timeout" during device linking

**Solutions**:
1. Check firewall allows TCP ports 20000-20005:
   ```powershell
   Get-NetFirewallRule -DisplayName "Keyboard*" | Format-List Name, Enabled
   ```

2. Verify network connectivity:
   ```powershell
   # Ping target device
   ping <other_device_ip>
   
   # Test port accessibility
   Test-NetConnection -ComputerName <other_device_ip> -Port 20000
   ```

3. Restart both applications

### High Latency/Input Lag

**Problem**: Keyboard/mouse actions are delayed

**Optimization**:
1. **Wired Connection**: Use Ethernet if possible (WiFi can add 50-100ms latency)
2. **Network Quality**: Check for interference:
   ```powershell
   # Run network diagnostics
   netsh diag show netdiag
   ```
3. **Resource Usage**: Check CPU/Memory:
   ```powershell
   Get-Process KeyboardMouseShare | Select-Object CPU, WorkingSet
   ```
4. **Local Network**: Ensure no background uploads/downloads on LAN

---

## Upgrading

### From v0.x to v1.0.0

1. **Backup Configuration**:
   ```powershell
   Copy-Item -Path "$env:APPDATA\KeyboardMouseShare" -Destination "$env:APPDATA\KeyboardMouseShare.backup" -Recurse
   ```

2. **Uninstall Old Version**: See Uninstallation

3. **Install New Version**: Follow Installation steps

4. **Restore Settings** (if compatible):
   ```powershell
   Copy-Item -Path "$env:APPDATA\KeyboardMouseShare.backup\*" -Destination "$env:APPDATA\KeyboardMouseShare" -Recurse -Force
   ```

---

## Verification & Checksums

### Verify Installer Integrity

```powershell
# Download both the installer and SHA256 file
# Verify the checksum matches

$expected = (Get-Content "KeyboardMouseShare-1.0.0-setup.exe.sha256").Split()[0]
$actual = (Get-FileHash "KeyboardMouseShare-1.0.0-setup.exe" -Algorithm SHA256).Hash

if ($expected -eq $actual) {
    Write-Host "✓ Installer verified successfully"
} else {
    Write-Host "✗ Checksum mismatch - installer may be corrupted"
}
```

### Official SHA256 Checksums

```
v1.0.0:
a1b2c3d4e5f6... KeyboardMouseShare-1.0.0-setup.exe
```

---

## Support & Contact

For installation issues:

- **GitHub Issues**: [github.com/yourusername/keyboard-mouse-share/issues](https://github.com/yourusername/keyboard-mouse-share/issues)
- **Documentation**: [github.com/yourusername/keyboard-mouse-share/docs](https://github.com/yourusername/keyboard-mouse-share/docs)
- **Email**: team@keyboard-mouse-share.local

---

**Last Updated**: February 2026  
**Version**: 1.0.0  
**Status**: Production Release
