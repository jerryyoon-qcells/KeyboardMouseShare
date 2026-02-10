# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Keyboard Mouse Share
# Build command: cd C:\path\to\project && pyinstaller build/windows/pyinstaller.spec

import os

# Use environment variable or current working directory
project_root = os.getcwd()
python_src = os.path.join(project_root, 'python', 'src')
main_py = os.path.join(python_src, 'main.py')

a = Analysis(
    [main_py],
    pathex=[python_src],
    binaries=[],
    datas=[(python_src, 'src')],
    hiddenimports=[
        'zeroconf',
        'pynput',
        'cryptography',
        'socket',
        'ssl',
        'json',
        'logging',
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KeyboardMouseShare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KeyboardMouseShare',
)
