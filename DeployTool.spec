# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.pyw'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui', 'gui'),
        ('core', 'core'),
        ('utils', 'utils'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'gui',
        'gui.main_window',
        'gui.widgets',
        'core',
        'core.checker',
        'core.deploy',
        'core.ad_checker',
        'utils',
        'utils.logger',
        'config',
        'config.settings',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.commondialog',
        'ldap3',
        'ldap3.strategy.sync',
        'ldap3.core.connection',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='DeployTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)