@echo off
chcp 65001 >nul
echo ============================================
echo   Deploy Tool - Сборка в EXE
echo ============================================
echo.

echo [1/4] Очистка...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist DeployTool.spec del DeployTool.spec

echo [2/4] Создание spec файла...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo block_cipher = None
echo.
echo a = Analysis(
echo     ['main.pyw'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ('gui', 'gui'),
echo         ('core', 'core'),
echo         ('utils', 'utils'),
echo         ('config', 'config'),
echo     ],
echo     hiddenimports=[
echo         'gui',
echo         'gui.main_window',
echo         'gui.widgets',
echo         'core',
echo         'core.checker',
echo         'core.deploy',
echo         'core.ad_checker',
echo         'utils',
echo         'utils.logger',
echo         'config',
echo         'config.settings',
echo         'tkinter',
echo         'tkinter.ttk',
echo         'tkinter.messagebox',
echo         'tkinter.filedialog',
echo         'ldap3',
echo         'PIL',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo )
echo.
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
echo.
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='DeployTool',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo )
) > DeployTool.spec

echo [3/4] Сборка...
pyinstaller DeployTool.spec --clean

echo [4/4] Проверка...
if exist dist\DeployTool.exe (
    echo.
    echo ============================================
    echo   ГОТОВО!
    echo   Файл: dist\DeployTool.exe
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   ОШИБКА СБОРКИ!
    echo ============================================
)

pause