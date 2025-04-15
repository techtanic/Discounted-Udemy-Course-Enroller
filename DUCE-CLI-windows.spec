# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

# Collect all required rich modules for the CLI interface
hidden_imports = collect_submodules('rich')

a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[('base.py', '.'), ('colors.py', '.'), ('default-duce-cli-settings.json', '.'), ('README.md', '.'), ('LICENSE', '.')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PyQt5', 'PySide2', 'scipy'],
    noarchive=False,
    optimize=2,  # Enable Python bytecode optimization
)

# Remove unnecessary packages from the build
excluded_binaries = [
    'Qt5WebEngineCore.dll', 'libGLESv2.dll', 'Qt5DBus.dll', 'Qt5Network.dll',
    'Qt5Qml.dll', 'Qt5QmlModels.dll', 'opengl32sw.dll', 'd3dcompiler_47.dll',
    'api-ms-win', 'tcl86', 'tk86', 'ucrt', 'mfc140', 'VCRUNTIME140_1.dll',
    'vcruntime140.dll', 'msvcp140.dll', 'msvcp140_1.dll'
]

# Filter out excluded binaries
def filter_binaries(binaries):
    return [(name, path) for name, path in binaries 
            if not any(excluded in name.lower() for excluded in excluded_binaries)]

a.binaries = filter_binaries(a.binaries)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=None
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DUCE-CLI-windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols from the executable
    upx=True,    # Use UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['extra\\DUCE-LOGO.ico'],
    version='file_version_info.txt',
)