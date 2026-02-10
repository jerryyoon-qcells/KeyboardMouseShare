@echo off
REM Build script for Windows Installer - Keyboard Mouse Share
REM This script creates a Windows 11/10 installer using PyInstaller and Inno Setup
REM 
REM Usage:
REM   build_windows_installer.bat [release|debug]
REM
REM Examples:
REM   build_windows_installer.bat release
REM   build_windows_installer.bat debug

setlocal enabledelayedexpansion

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=release

if not "%BUILD_TYPE%"=="release" if not "%BUILD_TYPE%"=="debug" (
    echo Error: BUILD_TYPE must be 'release' or 'debug'
    exit /b 1
)

echo.
echo ===============================================
echo  Keyboard Mouse Share - Windows Installer Build
echo ===============================================
echo  Build Type: %BUILD_TYPE%
echo  Working Directory: %cd%
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ from https://www.python.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% found

REM Check virtual environment
if not exist ".venv\" (
    echo [ERROR] Virtual environment not found. Run: python -m venv .venv
    exit /b 1
)
echo [OK] Virtual environment found

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)
echo [OK] Virtual environment activated

REM Install/upgrade build tools
echo.
echo Installing build tools...
pip install --upgrade pyinstaller setuptools wheel >nul 2>&1
echo [OK] Build tools ready

REM Run tests
echo.
echo Running tests...
pytest tests -q --tb=short
if errorlevel 1 (
    echo [ERROR] Tests failed. Fix errors before building.
    exit /b 1
)
echo [OK] All tests passed

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "build\" rmdir /s /q "build"
if exist "dist\" rmdir /s /q "dist"
mkdir dist\windows >nul 2>&1
echo [OK] Clean complete

REM Build executable
echo.
echo Building executable with PyInstaller...
echo This may take 1-2 minutes...
pyinstaller keyboard_mouse_share.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    exit /b 1
)
echo [OK] Executable created at: dist\KeyboardMouseShare\KeyboardMouseShare.exe

REM Check Inno Setup
echo.
echo Checking for Inno Setup...
set ISCC_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set ISCC_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe
)

if "%ISCC_PATH%"=="" (
    echo [WARNING] Inno Setup not found
    echo.
    echo To create the Windows installer:
    echo   1. Download Inno Setup from https://jrsoftware.org/isdl.php
    echo   2. Install it
    echo   3. Run this script again
    echo.
    echo Or manually build with:
    echo   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" keyboard_mouse_share.iss
    echo.
    echo [OK] Portable executable ready at: dist\KeyboardMouseShare\KeyboardMouseShare.exe
    exit /b 0
)

echo [OK] Inno Setup found: %ISCC_PATH%

REM Build installer
echo.
echo Building Windows installer...
"%ISCC_PATH%" keyboard_mouse_share.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup build failed
    exit /b 1
)

echo.
echo ===============================================
echo  [OK] Build Complete!
echo ===============================================
echo.
echo Output locations:
echo   Executable: %cd%\dist\KeyboardMouseShare\KeyboardMouseShare.exe
for /f %%A in ('dir /b dist\windows\*.exe 2^>nul') do (
    echo   Installer:  %cd%\dist\windows\%%A
)
echo.
echo Ready to distribute!
echo.
pause
