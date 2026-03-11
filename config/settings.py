"""
Конфигурация приложения Deploy Tool
"""

from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

LOG_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# === КОНФИГУРАЦИЯ ACTIVE DIRECTORY ===
AD_CONFIG = {
    "domain": "rosstat.local",
    "server": None,
    "use_ssl": False,
    "port": 389,
    "timeout": 30
}

# === КОНФИГУРАЦИЯ ПРИЛОЖЕНИЙ ===
APPLICATIONS: Dict[str, Dict[str, Any]] = {
    # === Архиваторы ===
    "7-Zip": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\7z2501-x64.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\7z2501-x64.exe",
        "args": "/S",
        "timeout": 180
    },

    "WinRAR (Rus)": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\WinRar621_RusX32.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\WinRar621_RusX32.exe",
        "args": "/S",
        "timeout": 180
    },

    "WinRAR (Eng)": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\WinRar621_EngX64.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\WinRar621_EngX64.exe",
        "args": "/S",
        "timeout": 180
    },

    # === Редакторы ===
    "Notepad++": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\npp.8.8.6.Installer.x64.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\npp.8.8.6.Installer.x64.exe",
        "args": "/S",
        "timeout": 300
    },

    # === Браузеры ===
    "Google Chrome": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\ChromeStandaloneSetup64.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\ChromeStandaloneSetup64.exe",
        "args": "/silent /install",
        "timeout": 300
    },

    "Chromium GOST": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\chromium-gost-142.0.7444.176-windows-amd64-installer.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\chromium-gost-142.0.7444.176-windows-amd64-installer.exe",
        "args": "/silent /install",
        "timeout": 300
    },

    "Yandex Browser": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\Yandex.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\Yandex.exe",
        "args": "/silent",
        "timeout": 300
    },

    # === Мессенджеры ===
    "Telegram": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\tsetup-x64.6.5.1.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\tsetup-x64.6.5.1.exe",
        "args": "/S",
        "timeout": 180
    },

    "Yandex Telemost": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\YandexTelemostSetup.msi",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\YandexTelemostSetup.msi",
        "args": "/qn /norestart",
        "timeout": 300,
        "type": "msi"
    },

    # === Офисные программы ===
    "Microsoft Office 2016 Pro": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\Office 2016 pro\setup.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\Office 2016 pro\setup.exe",
        "args": "/quiet /norestart",
        "timeout": 1800
    },

    # === Системные компоненты ===
    "Visual C++ Redistributable": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\vc_redist.x64.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\vc_redist.x64.exe",
        "args": "/quiet /norestart",
        "timeout": 300
    },

    # === Виртуализация ===
    "Oracle VirtualBox": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\VirtualBox-7.2.4-170995-Win.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\VirtualBox-7.2.4-170995-Win.exe",
        "args": "--silent",
        "timeout": 600
    },

    # === Специализированное ПО ===
    "Среда разработки": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\sredasetup.exe",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\sredasetup.exe",
        "args": "/S",
        "timeout": 600
    },

    "Offline Application": {
        "Win7": r"\\10.177.55.240\IT_Shahe_All\Installers\OfflineApplicationSetup_3_0_19.msi",
        "Win10": r"\\10.177.55.240\IT_Shahe_All\Installers\OfflineApplicationSetup_3_0_19.msi",
        "args": "/qn /norestart",
        "timeout": 600,
        "type": "msi"
    },
}

# Настройки PowerShell
POWERSHELL_CONFIG = {
    "execution_policy": "Bypass",
    "timeout": 3600,
    "temp_dir": "C:\\Temp\\Installers"
}

# Настройки логирования
LOG_CONFIG = {
    "level": "INFO",
    "format": "[%(asctime)s] [%(levelname)s] %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "max_size_mb": 10,
    "backup_count": 5
}