"""
Утилиты для работы с правами администратора
"""

import ctypes
import sys
import os


def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_admin_status():
    """Получение подробной информации о правах"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()

        return {
            'is_admin': is_admin,
            'status': 'Administrator' if is_admin else 'Standard User',
            'can_elevate': True,  # Предполагаем, что можно запросить UAC
            'username': os.environ.get('USERNAME', 'Unknown'),
            'domain': os.environ.get('USERDOMAIN', 'Unknown')
        }
    except Exception as e:
        return {
            'is_admin': False,
            'status': f'Error: {e}',
            'can_elevate': False,
            'username': os.environ.get('USERNAME', 'Unknown'),
            'domain': os.environ.get('USERDOMAIN', 'Unknown')
        }


def request_elevation():
    """Запрос повышения прав через UAC"""
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])

        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1
        )
        return True
    except Exception as e:
        print(f"Ошибка повышения прав: {e}")
        return False


def restart_as_admin():
    """Перезапуск с правами администратора"""
    if request_elevation():
        sys.exit(0)
    return False