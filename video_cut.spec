# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect opentimelineio data files, binaries, and hidden imports
otio_datas, otio_binaries, otio_hiddenimports = collect_all('opentimelineio')

a = Analysis(
    ['src/video_cut/main.py'],
    pathex=['src'],
    binaries=otio_binaries,
    datas=otio_datas,
    hiddenimports=otio_hiddenimports + [
        'video_cut',
        'video_cut.cli',
        'video_cut.core',
        'video_cut.tools',
        'video_cut.typedefs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='video_cut',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
