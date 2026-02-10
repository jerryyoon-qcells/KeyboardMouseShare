# Quick Start Guide: Cross-Device Input Sharing

**Feature**: Cross-Device Input Sharing (001-cross-device-input)  
**Created**: 2026-02-09  
**Target**: Users setting up the app for the first time

---

## Installation

### Windows

1. Download the installer: `keyboard-mouse-share-1.0.0-windows.exe`
2. Run the installer; follow prompts to select installation directory
3. The app will be available in Start Menu → Keyboard Mouse Share
4. First run: Grant permission for input hook (may require UAC prompt)
5. Done! The app will start automatically and show in system tray

### macOS

1. Download the app: `keyboard-mouse-share-1.0.0-macos.dmg`
2. Open DMG; drag `Keyboard Mouse Share.app` to Applications folder
3. First run: 
   - Open Applications folder
   - Double-click `Keyboard Mouse Share.app`
   - You may see "Cannot verify developer" warning → Click "Open" anyway
4. Grant Accessibility permissions:
   - System Preferences → Security & Privacy → Accessibility
   - Find "Keyboard Mouse Share" in the list
   - Check the checkbox to allow input control
   - Close preferences
5. Done! The app is now running

---

## Basic Setup (2 Devices)

### Step 1: Start the App on Both Devices

**On Device 1 (e.g., Windows PC)**:
- Open "Keyboard Mouse Share" from Start Menu
- Main window shows: "Available Devices" (empty at first)
- Wait 3-5 seconds → Device 2 will appear in the list

**On Device 2 (e.g., MacBook)**:
- Open "Keyboard Mouse Share" from Applications
- Main window shows: "Available Devices" (empty at first)
- Wait 3-5 seconds → Device 1 will appear in the list

### Step 2: Register Devices

**On Device 1 (Windows)**:
- See "MacBook" in "Available Devices" list
- Click "Register Device" → Confirmation dialog: "Connect to MacBook?"
- Click "Yes"
- Device 1 now shows: "Registered Devices" → "MacBook" (status: waiting for approval)

**On Device 2 (MacBook)**:
- Notification popup: "Device Windows PC wants to connect. Confirm?"
- Click "Allow"
- Passphrase dialog pops up on both devices

### Step 3: Confirm Passphrase

**On Device 1 (Windows)**:
- UI shows: "Passphrase: ABC123"
- A passphrase is displayed (you don't type it)

**On Device 2 (MacBook)**:
- Input dialog: "Enter passphrase to confirm connection"
- Type the passphrase shown on Windows: "ABC123"
- Click "Connect"

**Result**: Connection established! Status now shows "Connected" on both devices.

---

## Configure Master/Client Role

Exactly **one device** must be Master (source of input); all others are Clients (receivers).

### Option 1: GUI Configuration

**On Device 1 (Windows)**:
- Click "Configuration" menu
- Select "Master" radio button
- Click "Save"
- Status: "This device is the Master"

**On Device 2 (MacBook)**:
- Click "Configuration" menu
- Select "Client" radio button
- Click "Save"
- Status: "This device is a Client. Waiting for input from Master..."

### Option 2: Auto-Assignment

If you don't manually select roles, the **first device to start** becomes Master automatically. Other devices connecting later become Clients.

---

## Enable Input Sharing

**On the Master Device (Windows)**:
- Look for "Input Sharing" toggle in main window
- Toggle to **ON** (blue)
- Status: "Input Sharing is ACTIVE"

**Result**: 
- Physical keyboard and mouse on Windows (Master) are now shared
- Type on Windows keyboard → text appears in MacBook (Client)
- Move Windows mouse → MacBook cursor moves

---

## Configure Screen Layout (Optional but Recommended)

Layout setup allows smooth cursor movement between devices. If you skip this, cursor still works but requires clicking to switch devices.

### Add Layout Configuration

**On the Master Device (Windows)**:
- Click "Layout Settings"
- You see: "Device: MacBook" (list of connected devices)
- For MacBook: Set coordinates
  - X offset: `1920` (place MacBook to the right of Windows)
  - Y offset: `0` (align at top)
  - Screen width: `2560`
  - Screen height: `1600`
  - Orientation: Landscape
- Click "Save Layout"

**Result**: 
- Move mouse to the **right edge** of Windows screen → cursor appears on **left edge** of MacBook
- Seamless transition without clicking

### Visual Layout Editor (Future / v1.1)

In future versions, you'll see a visual canvas:
- Drag-and-drop devices to arrange
- Auto-detect screen resolutions
- Preview cursor movement

For v1.0, use the form-based entry above.

---

## Keyboard Input Routing

**Default behavior**: Keyboard input goes to whichever device the **mouse cursor is on**.

### Example Workflow

1. Master (Windows): Mouse is on Windows screen
2. Type "Hello" → Text appears on Windows
3. Move mouse to right edge of Windows → Cursor appears on MacBook screen
4. Type "World" → Text appears on MacBook
5. Press hotkey: `Ctrl+Alt+Shift+Right Arrow` → Keyboard focus switches to the right device in layout

---

## Manual Role Switching (Change Master/Client)

If you want to switch control from Windows to MacBook:

### Option 1: Hotkey
- Press `Ctrl+Alt+Shift+Left Arrow` on Windows (switches to left device in layout)
- Keyboard focus moves to left device (MacBook)

### Option 2: GUI
On the device you want to be new Master:
- Click "Configuration"
- Select "Master"
- Click "Save"
- System shows warning: "Switching master will pause input for 2 seconds. Continue?" → Yes

**Result**: Old Master becomes Client; new Master takes over input control.

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| **Device not discovered** | Check both devices on same WiFi. Restart app on both. Check firewall allows port 19999. |
| **Passphrase mismatch** | Re-check the passphrase displayed on Master. Numbers/letters are case-sensitive. |
| **Input not working** | (1) Check Input Sharing toggle is ON. (2) Check roles are Master/Client, not both Master. (3) Click on MacBook window to focus it first. |
| **Cursor won't move smoothly** | (1) Configure layout (see above). (2) Check both devices have correct screen resolution saved. |
| **Keyboard input goes to wrong device** | Press the focus hotkey to manually switch: `Ctrl+Alt+Shift+Right Arrow`. |
| **App crashes on startup** | (Windows) Disable antivirus temporarily (may block input hook). Check Windows Defender settings. |
| **macOS: "Permission Denied"** | Grant Accessibility permission: System Preferences → Security & Privacy → Accessibility. Add Keyboard Mouse Share to list. |

---

## Next Steps

- **Read**: Full end-user guide in [USER_GUIDE.md](../../docs/USER_GUIDE.md)
- **Feedback**: Report issues on [GitHub Issues](https://github.com/example/keyboard-mouse-share/issues)
- **Advanced**: Configure in JSON for more options in [CONFIG.md](../../docs/CONFIG.md)

---

**Quick Start Version**: 1.0.0 | **Created**: 2026-02-09
