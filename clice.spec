# -*- mode: python ; coding: utf-8 -*-
import glob
import os
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
datas += collect_data_files('pexpect')
hiddenimports += collect_submodules('rich')
tmp_ret = collect_all('textual')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Textual screens load their own .tcss stylesheets via CSS_PATH at runtime -
# these aren't Python modules, so PyInstaller's import-following analysis
# never sees them on its own. Glob for every one under ui/ and preserve
# its directory structure in the bundle, so new screens/widgets that add
# a .tcss file later get picked up automatically without anyone needing
# to remember to update this list by hand.
for tcss_path in glob.glob("ui/**/*.tcss", recursive=True):
    dest_dir = os.path.dirname(tcss_path)
    datas.append((tcss_path, dest_dir))


a = Analysis(
    ['clice.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'yaml', 'matplotlib', 'scipy', 'pandas', 'tkinter', 'unittest', 'test', 'cryptography'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='clice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=True,
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
    strip=True,
    upx=False,
    upx_exclude=[],
    name='clice',
)
