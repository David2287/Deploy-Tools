"""
Диалог запроса прав администратора
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import sys
import os


class AdminElevationDialog:
    """Диалог для запроса прав администратора"""

    def __init__(self, parent=None):
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Требуется запуск от имени администратора")
        self.root.geometry("550x300")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.transient(parent) if parent else None

        self._setup_ui()
        self._center_window()

    def _setup_ui(self):
        """Настройка интерфейса"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Иконка и заголовок
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=10)

        # Иконка предупреждения
        icon_label = ttk.Label(header_frame, text="⚠", font=('Segoe UI', 48))
        icon_label.pack(side='left', padx=10)

        # Заголовок
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side='left', fill='x', expand=True)

        ttk.Label(
            title_frame,
            text="Требуется запуск от имени администратора",
            font=('Segoe UI', 14, 'bold')
        ).pack(anchor='w')

        ttk.Label(
            title_frame,
            text="Повышение привилегий необходимо для работы",
            font=('Segoe UI', 9)
        ).pack(anchor='w', pady=5)

        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        # Информация
        info_frame = ttk.LabelFrame(main_frame, text="Почему это требуется?", padding=10)
        info_frame.pack(fill='x', pady=10)

        reasons = [
            "• Установка программного обеспечения на удалённых ПК",
            "• Доступ к административным сетевым ресурсам (C$)",
            "• Выполнение PowerShell скриптов с повышенными правами",
            "• Запись в системные разделы реестра",
            "• Управление службами Windows"
        ]

        for reason in reasons:
            ttk.Label(info_frame, text=reason).pack(anchor='w', pady=2)

        # Статус текущих прав
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x', pady=10)

        ttk.Label(status_frame, text="Текущий статус:").pack(side='left')

        self.status_label = ttk.Label(
            status_frame,
            text="❌ Обычные права пользователя",
            foreground='red',
            font=('Segoe UI', 9, 'bold')
        )
        self.status_label.pack(side='left', padx=5)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        self.elevate_button = ttk.Button(
            button_frame,
            text="🔐 Запустить с правами администратора",
            command=self._on_elevate,
            style='Accent.TButton'
        )
        self.elevate_button.pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text="❌ Выйти",
            command=self._on_exit
        ).pack(side='left', padx=5)

        # Стиль
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='blue', font=('Segoe UI', 10, 'bold'))

    def _center_window(self):
        """Центрирование окна"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")

    def _on_elevate(self):
        """Запрос прав администратора"""
        try:
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])

            # Запуск через UAC
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{script}" {params}',
                None,
                1
            )

            self.root.destroy()
            sys.exit(0)

        except Exception as e:
            messagebox.showerror(
                "Ошибка повышения прав",
                f"Не удалось запросить права администратора.\n\n"
                f"Ошибка: {e}\n\n"
                "Запустите программу вручную:\n"
                "1. Правая кнопка на main.pyw\n"
                "2. 'Запуск от имени администратора'",
                parent=self.root
            )

    def _on_exit(self):
        """Выход"""
        if messagebox.askyesno(
                "Выход",
                "Без прав администратора программа не будет работать.\n\n"
                "Вы уверены, что хотите выйти?",
                parent=self.root
        ):
            self.root.destroy()
            sys.exit(0)

    def show(self):
        """Показать диалог"""
        self.root.wait_window()


def check_and_request_admin():
    """Проверить и запросить права администратора"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        dialog = AdminElevationDialog()
        dialog.show()
        return False

    return True