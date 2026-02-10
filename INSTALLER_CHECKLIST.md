Windows 11 Installer - Setup Checklist
========================================

PREPARATION CHECKLIST
---------------------
[ ] Python 3.11+ installed (verify: python --version)
[ ] Virtual environment created (.venv directory exists)
[ ] Dependencies installed (pip install -r requirements.txt)
[ ] All tests passing (pytest tests -q)
[ ] Inno Setup 6 installed (optional but recommended)


FILES CREATED
-------------
✓ keyboard_mouse_share.spec
  → PyInstaller configuration for executable creation
  → Bundles Python runtime and all dependencies

✓ keyboard_mouse_share.iss
  → Inno Setup installer script
  → Customizable installer appearance and behavior

✓ build_windows_installer.ps1
  → PowerShell build automation script (recommended)
  → Automatic testing, building, and packaging

✓ build_windows_installer.bat
  → Command Prompt batch build script
  → Alternative for non-PowerShell users

✓ WINDOWS_INSTALLER_GUIDE.md
  → Comprehensive guide for building and distributing
  → Troubleshooting and customization instructions

✓ WINDOWS_INSTALLER_SETUP.md
  → Overview and quick start guide

✓ build/windows/BEFORE_INSTALL.txt
  → User-facing pre-installation information
  → System requirements and setup instructions

✓ build/windows/SYSTEM_REQUIREMENTS.txt
  → Detailed system requirements for users
  → Compatibility information and troubleshooting

✓ requirements-build.txt
  → Python packages needed for building installer


QUICK START
-----------
1. Open PowerShell in project root
2. Activate virtual environment:
   .\.venv\Scripts\Activate.ps1

3. Install build dependencies:
   pip install -r requirements-build.txt

4. Run build script:
   .\build_windows_installer.ps1

5. Wait 2-5 minutes for build to complete

6. Find installer at:
   dist\windows\KeyboardMouseShare-Setup-1.0.0.exe


BUILD OUTPUTS
-------------
After successful build, you'll have:

Portable Executable:
  dist\KeyboardMouseShare\
    ├── KeyboardMouseShare.exe (main application)
    ├── _internal\ (all dependencies)
    └── Python runtime (bundled)

Windows Installer:
  dist\windows\
    └── KeyboardMouseShare-Setup-1.0.0.exe (100-150 MB)


WHAT THE INSTALLER INCLUDES
----------------------------
✓ Complete Python 3.11+ runtime
✓ All required libraries:
  - PyQt5 for UI
  - pynput for input simulation
  - zeroconf for network discovery
  - cryptography for TLS/SSL
✓ Application code and resources
✓ System requirement validation
✓ Windows registry integration
✓ Uninstaller
✓ Desktop shortcuts (optional)
✓ Startup launch option (optional)


INSTALLER FEATURES
------------------
✓ Silent installation option
✓ Progress bar
✓ Custom installation path
✓ System requirement checks
✓ Firewall integration warnings
✓ Automatic uninstaller
✓ Start menu entry
✓ Desktop icon (optional)
✓ Startup launch (optional)
✓ Application restart after install


DISTRIBUTION
-----------
For Windows users, distribute:
  → KeyboardMouseShare-Setup-1.0.0.exe

Users:
1. Download the .exe
2. Double-click to run
3. Follow installer prompts
4. Application is ready to use

No additional installation needed by users.


BUILD SCRIPT OPTIONS
-------------------
PowerShell Advanced Usage:

.\build_windows_installer.ps1 -BuildType release
  → Optimized production build (default)

.\build_windows_installer.ps1 -BuildType debug
  → Debug build with verbose output

.\build_windows_installer.ps1 -SkipTests
  → Skip running tests before build

.\build_windows_installer.ps1 -SkipClean
  → Keep previous build artifacts


MANUAL BUILD
-----------
If you want to build step-by-step:

Step 1: Create executable
  pyinstaller keyboard_mouse_share.spec
  → Output: dist\KeyboardMouseShare\KeyboardMouseShare.exe

Step 2: Create installer
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" keyboard_mouse_share.iss
  → Output: dist\windows\KeyboardMouseShare-Setup-1.0.0.exe


CUSTOMIZATION
-----------
Edit keyboard_mouse_share.iss to customize:
  - Installation directory default
  - Installer title and text
  - License file display
  - System requirement checks
  - Registry entries
  - Start menu items
  - Icon and images
  - Supported Windows versions


VERSION UPDATES
-----------
To update to version 1.0.1:

1. Edit pyproject.toml:
   version = "1.0.1"

2. Edit keyboard_mouse_share.iss:
   #define MyAppVersion "1.0.1"

3. Edit src/main.py:
   version="%(prog)s 1.0.1-dev"

4. Rebuild:
   .\build_windows_installer.ps1


TROUBLESHOOTING
-----------
Problem: Module not found error
→ Ensure .venv\Scripts\Activate.ps1 was run

Problem: PyInstaller command not found
→ Run: pip install pyinstaller

Problem: Inno Setup not found
→ Download from https://jrsoftware.org/isdl.php
→ Download required, script still creates .exe

Problem: Tests fail before build
→ Fix test failures first
→ Or use -SkipTests flag (not recommended)


SECURITY CONSIDERATIONS
-----------
The executable:
✓ Is unsigned (causes SmartScreen prompt)
✓ Should be code-signed for distribution (requires certificate)
✓ Contains all dependencies bundled

To sign the installer:
1. Obtain code signing certificate
2. Install signtool (part of Windows SDK)
3. Run: signtool sign /f cert.pfx /p password installer.exe


NEXT STEPS
---------
[ ] Install build dependencies: pip install -r requirements-build.txt
[ ] Optionally install Inno Setup 6
[ ] Run build script: .\build_windows_installer.ps1
[ ] Test installer on clean Windows system
[ ] Upload to GitHub releases or website
[ ] Document installation instructions for users


For detailed information, see:
  → WINDOWS_INSTALLER_GUIDE.md (comprehensive)
  → build/windows/SYSTEM_REQUIREMENTS.txt (for users)
  → build/windows/BEFORE_INSTALL.txt (for users)


Build Environment:
OS: Windows 10/11 (64-bit)
Python: 3.11 or later
PowerShell: 5.1 or later
Inno Setup: 6.x (optional)

Ready to build? Run:
  .\build_windows_installer.ps1
