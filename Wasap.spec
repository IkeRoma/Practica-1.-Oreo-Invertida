# PyInstaller: compilar desde la raíz del proyecto.
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['client/main.py'],
    pathex=['client'],
    binaries=[],
    datas=[('config/client.env.example', 'config')],
    hiddenimports=collect_submodules('PySide6'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pyodbc'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Wasap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name='Wasap',
)
