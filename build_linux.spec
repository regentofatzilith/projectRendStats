# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Linux builds.

Build on Linux host/container:
  pyinstaller build_linux.spec
"""

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

app_name = 'TowerConquestAnalytics'
main_script = 'app.py'

# Project data needed at runtime.
datas = [
    ('assets', 'assets'),
    ('pages', 'pages'),
    ('functions', 'functions'),
]

# Collect dynamic imports used by Dash pages and scientific stack.
hiddenimports = []
for pkg in [
    'dash',
    'plotly',
    'dash_bootstrap_components',
    'pandas',
    'numpy',
    'scipy',
    'sklearn',
    'requests',
    'bs4',
]:
    hiddenimports += collect_submodules(pkg)

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PyQt5',
        'PySide2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
