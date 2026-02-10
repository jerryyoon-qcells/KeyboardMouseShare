#Requires -Version 5.1
<#
.SYNOPSIS
Build script for creating Windows installer for Keyboard Mouse Share

.DESCRIPTION
This script automates the process of creating a Windows 11/10 installer using PyInstaller and Inno Setup

.PARAMETER BuildType
Build type: 'release' (default) or 'debug'

.PARAMETER SkipTests
Skip running tests before building

.PARAMETER SkipClean
Don't clean previous builds

.EXAMPLE
.\build_windows_installer.ps1 -BuildType release
#>

param(
    [ValidateSet('release', 'debug')]
    [string]$BuildType = 'release',
    
    [switch]$SkipTests,
    [switch]$SkipClean
)

$ErrorActionPreference = 'Stop'
$VerbosePreference = 'Continue'

# Colors for output
function Write-Info { Write-Host "ℹ  $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Info "Building Keyboard Mouse Share Windows Installer"
Write-Info "Build Type: $BuildType"
Write-Info "Working Directory: $(Get-Location)"

# Check prerequisites
Write-Info ""
Write-Info "Checking prerequisites..."

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python not found. Please install Python 3.11+ from python.org"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path .venv)) {
    Write-Warning ".venv not found. Run 'python -m venv .venv' first"
    exit 1
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated"

# Install/upgrade build tools
Write-Info ""
Write-Info "Installing/upgrading build tools..."
pip install --upgrade pyinstaller setuptools wheel | Out-Null
Write-Success "Build tools ready"

# Run tests if not skipped
if (-not $SkipTests) {
    Write-Info ""
    Write-Info "Running tests..."
    
    try {
        pytest tests/ -q --tb=short
        Write-Success "All tests passed"
    } catch {
        Write-Error "Tests failed. Fix errors before building installer."
        exit 1
    }
}

# Clean previous builds
if (-not $SkipClean) {
    Write-Info ""
    Write-Info "Cleaning previous builds..."
    
    if (Test-Path build) { Remove-Item -Recurse build -Force -ErrorAction SilentlyContinue }
    if (Test-Path dist) { Remove-Item -Recurse dist -Force -ErrorAction SilentlyContinue }
    
    Write-Success "Clean complete"
}

# Create output directories
Write-Info ""
Write-Info "Creating output directories..."
$distDir = Join-Path $scriptDir "dist" "windows"
$null = New-Item -ItemType Directory -Path $distDir -Force

# Build executable with PyInstaller
Write-Info ""
Write-Info "Building executable with PyInstaller..."
Write-Info "This may take 1-2 minutes..."

$pyiArgs = @(
    'keyboard_mouse_share.spec'
)

if ($BuildType -eq 'debug') {
    $pyiArgs += '--debug=imports'
}

try {
    & pyinstaller @pyiArgs 2>&1 | Where-Object { $_ -notmatch '^\s*$' } | ForEach-Object { Write-Info $_ }
    Write-Success "Executable created: dist\KeyboardMouseShare\KeyboardMouseShare.exe"
} catch {
    Write-Error "PyInstaller build failed: $_"
    exit 1
}

# Check Inno Setup installation
Write-Info ""
Write-Info "Checking for Inno Setup..."

$isccPath = $null
$possiblePaths = @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files (x86)\Inno Setup 5\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $isccPath = $path
        break
    }
}

if (-not $isccPath) {
    Write-Warning "Inno Setup not found!"
    Write-Info ""
    Write-Info "To create the installer, install Inno Setup:"
    Write-Info "1. Download from: https://jrsoftware.org/isdl.php"
    Write-Info "2. Install and run this script again"
    Write-Info ""
    Write-Info "Or manually build with: iscc keyboard_mouse_share.iss"
    Write-Info ""
    Write-Success "Executable ready at: dist\KeyboardMouseShare\KeyboardMouseShare.exe"
    exit 0
}

Write-Success "Inno Setup found: $isccPath"

# Copy required files for installer
Write-Info ""
Write-Info "Preparing installer files..."

# Copy LICENSE and README
Copy-Item LICENSE.txt . -ErrorAction SilentlyContinue
Copy-Item README.md . -ErrorAction SilentlyContinue

Write-Success "Files prepared"

# Build installer
Write-Info ""
Write-Info "Building Windows installer with Inno Setup..."

try {
    & $isccPath keyboard_mouse_share.iss | Out-Null
    Write-Success "Installer created successfully!"
    
    # Get installer filename
    $installerFile = Get-ChildItem $distDir -Filter "*.exe" | Select-Object -First 1
    
    Write-Info ""
    Write-Success "Build Complete!"
    Write-Info ""
    Write-Info "Output location:"
    Write-Info "  Executable: $(Get-Item 'dist\KeyboardMouseShare\KeyboardMouseShare.exe' | Select-Object -ExpandProperty FullName)"
    Write-Info "  Installer:  $($installerFile.FullName)"
    Write-Info ""
    Write-Info "File sizes:"
    $exe = Get-Item 'dist\KeyboardMouseShare\KeyboardMouseShare.exe'
    $installer = Get-Item $installerFile.FullName
    Write-Info "  Executable: $($exe.Length / 1MB -as [int]) MB"
    Write-Info "  Installer:  $($installer.Length / 1MB -as [int]) MB"
    Write-Info ""
    Write-Info "Ready to distribute!"
    
} catch {
    Write-Error "Inno Setup build failed: $_"
    Write-Info "Try manually: iscc keyboard_mouse_share.iss"
    exit 1
}
