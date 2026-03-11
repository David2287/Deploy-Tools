"""
Deploy Tool - Точка входа
"""

import sys
import os
import ctypes

# Добавляем корень проекта в путь поиска модулей
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Теперь импортируем
def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def show_error(title, message):
    """Показать ошибку в GUI"""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showerror(title, message)
    root.destroy()

def main():
    """Основная функция"""

    # Проверка прав администратора
    if not is_admin():
        show_error(
            "Требуется запуск от имени администратора",
            "Щёлкните правой кнопкой на main.pyw и выберите 'Запуск от имени администратора'"
        )
        sys.exit(1)

    # Проверка Python версии
    if sys.version_info < (3, 8):
        show_error("Ошибка версии", "Требуется Python 3.8 или выше!")
        sys.exit(1)

    # Проверка наличия модулей
    try:
        import gui
        import core
        import utils
        import config
    except ImportError as e:
        show_error(
            "Ошибка импорта модулей",
            f"Не удалось загрузить модули:\n{e}\n\n"
            f"Путь поиска:\n{sys.path}\n\n"
            f"Текущая директория:\n{script_dir}\n\n"
            "Убедитесь, что все папки (gui, core, utils, config) "
            "находятся рядом с main.pyw и содержат __init__.py"
        )
        sys.exit(1)

    # Импорт и запуск GUI
    try:
        from gui.main_window import MainWindow

        app = MainWindow()
        app.run()

    except ImportError as e:
        show_error(
            "Ошибка импорта",
            f"Не удалось загрузить gui.main_window:\n{e}\n\n"
            f"Проверьте:\n"
            f"1. Существует ли файл gui/main_window.py\n"
            f"2. Существует ли файл gui/__init__.py\n"
            f"3. Нет ли ошибок в коде main_window.py"
        )
        sys.exit(1)
    except Exception as e:
        show_error("Критическая ошибка", f"Приложение не удалось запустить:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()