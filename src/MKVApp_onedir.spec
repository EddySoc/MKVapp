# -*- mode: python ; coding: utf-8 -*-

import os
import customtkinter as _ctk
from PyInstaller.utils.hooks import collect_submodules

current_dir = os.path.dirname(os.path.abspath(SPEC))

hiddenimports = (
    collect_submodules('actions')
    + collect_submodules('binding')
    + collect_submodules('config')
    + collect_submodules('decorators')
    + collect_submodules('menus')
    + collect_submodules('mkvapp')
    + collect_submodules('scripts')
    + collect_submodules('utils')
    + collect_submodules('widgets')
)

a = Analysis(
    ['app_launcher.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        ('Settings', 'Settings'),
        (_ctk.__path__[0], 'customtkinter'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MKVApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MKVApp_onedir',
)
