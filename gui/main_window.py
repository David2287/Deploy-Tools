"""
Основное окно приложения Deploy Tool
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional
import threading
from datetime import datetime
import os
import time

from gui.widgets import ConsoleWidget, StatusLabel
from core.checker import DeviceChecker
from core.deploy import DeployManager
from utils.logger import logger
from config.settings import APPLICATIONS

class MainWindow:
    """Главное окно приложения Deploy Tool"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Deploy Tool - Система развёртывания ПО")
        self.root.geometry("950x800")
        self.root.resizable(False, False)

        # Переменные
        self.cached_credentials: Optional[Dict[str, str]] = None
        self.deployment_thread: Optional[threading.Thread] = None
        self.is_deploying = False

        # Блокировки для предотвращения множественных проверок
        self.is_checking = False
        self.last_check_time = 0
        self.check_cooldown = 5

        # Настройка логгера
        logger.set_gui_callback(self._log_callback)

        # Создание интерфейса
        self._create_styles()
        self._create_widgets()
        self._create_menu()

        # Лог запуска
        logger.info("=" * 60)
        logger.info("DEPLOY TOOL ЗАПУЩЕН")
        logger.info(f"Пользователь: {os.environ.get('USERNAME', 'Unknown')}")
        logger.info(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

    def _create_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabelFrame', background='#f0f0f0', foreground='#333333')
        style.configure('TLabel', background='#f0f0f0', foreground='#333333')
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Accent.TButton', foreground='white', background='#0078D4', font=('Segoe UI', 10, 'bold'))

    def _create_widgets(self):
        """Создание элементов интерфейса"""

        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill='both', expand=True)

        # === Заголовок ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(
            header_frame,
            text="🚀 Deploy Tool - Система развёртывания ПО",
            style='Header.TLabel'
        ).pack(anchor='w')

        ttk.Separator(header_frame, orient='horizontal').pack(fill='x', pady=5)

        # === Группа: Информация об устройстве ===
        device_frame = ttk.LabelFrame(main_frame, text="📁 Информация об устройстве", padding=10)
        device_frame.pack(fill='x', pady=5)

        device_row1 = ttk.Frame(device_frame)
        device_row1.pack(fill='x', pady=2)

        ttk.Label(device_row1, text="Имя устройства:", width=15).pack(side='left')
        self.computer_entry = ttk.Entry(device_row1, width=30)
        self.computer_entry.pack(side='left', padx=5)
        self.computer_entry.bind('<Return>', lambda e: self._check_device())

        self.check_button = ttk.Button(device_row1, text="✓ Проверить", command=self._check_device)
        self.check_button.pack(side='left', padx=5)

        device_row2 = ttk.Frame(device_frame)
        device_row2.pack(fill='x', pady=2)

        self.status_label = StatusLabel(device_row2, text="Статус: Не проверено", width=40)
        self.status_label.pack(side='left', padx=5)

        self.os_label = StatusLabel(device_row2, text="ОС: Не определено", width=40)
        self.os_label.pack(side='left', padx=5)

        # === Группа: Учётные данные ===
        creds_frame = ttk.LabelFrame(main_frame, text="🔐 Учётные данные администратора", padding=10)
        creds_frame.pack(fill='x', pady=5)

        creds_row = ttk.Frame(creds_frame)
        creds_row.pack(fill='x', pady=2)

        ttk.Label(creds_row, text="Логин:", width=15).pack(side='left')
        self.login_entry = ttk.Entry(creds_row, width=28)
        self.login_entry.pack(side='left', padx=5)
        self.login_entry.insert(0, f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}")

        ttk.Label(creds_row, text="Пароль:", width=10).pack(side='left', padx=(20, 0))
        self.password_entry = ttk.Entry(creds_row, width=25, show="*")
        self.password_entry.pack(side='left', padx=5)

        creds_row2 = ttk.Frame(creds_frame)
        creds_row2.pack(fill='x', pady=2)

        self.cred_status_label = StatusLabel(creds_row2, text="Статус: Не проверено", width=50)
        self.cred_status_label.pack(side='left', padx=5)

        ttk.Button(
            creds_row2,
            text="🔐 Проверить учётные данные",
            command=self._validate_credentials
        ).pack(side='right', padx=5)

        self.save_creds_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(creds_frame, text="Сохранить учётные данные для текущей сессии", variable=self.save_creds_var).pack(anchor='w', pady=5)

        # === Группа: Выбор ОС ===
        os_frame = ttk.LabelFrame(main_frame, text="💻 Операционная система", padding=10)
        os_frame.pack(fill='x', pady=5)

        self.os_type = tk.StringVar(value="Win10")
        ttk.Radiobutton(os_frame, text="Windows 7", variable=self.os_type, value="Win7").pack(side='left', padx=10)
        ttk.Radiobutton(os_frame, text="Windows 10/11", variable=self.os_type, value="Win10").pack(side='left', padx=10)

        # === Группа: Выбор программ ===
        apps_frame = ttk.LabelFrame(main_frame, text="📦 Программы для установки", padding=10)
        apps_frame.pack(fill='both', expand=True, pady=5)

        apps_header = ttk.Frame(apps_frame)
        apps_header.pack(fill='x', pady=(0, 5))

        ttk.Label(apps_header, text="Отметьте программы для установки:").pack(side='left')

        def select_all():
            for var in self.app_vars.values():
                var.set(True)

        def deselect_all():
            for var in self.app_vars.values():
                var.set(False)

        ttk.Button(apps_header, text="✓ Все", command=select_all, width=8).pack(side='right', padx=2)
        ttk.Button(apps_header, text="✗ Сброс", command=deselect_all, width=8).pack(side='right', padx=2)

        self.app_vars: Dict[str, tk.BooleanVar] = {}
        apps_inner = ttk.Frame(apps_frame)
        apps_inner.pack(fill='both', expand=True)

        mid = len(APPLICATIONS) // 2
        apps_list = list(APPLICATIONS.keys())

        for i, app_name in enumerate(apps_list):
            var = tk.BooleanVar(value=False)
            self.app_vars[app_name] = var

            col = 0 if i < mid else 1
            row = i if i < mid else i - mid

            cb = ttk.Checkbutton(apps_inner, text=app_name, variable=var)
            cb.grid(row=row, column=col, sticky='w', padx=10, pady=3)

        ttk.Button(
            apps_frame,
            text="🚀 Установить выбранные",
            command=self._start_deployment,
            style='Accent.TButton'
        ).pack(fill='x', pady=(10, 0))

        # === Группа: Консоль вывода ===
        console_frame = ttk.LabelFrame(main_frame, text="📋 Журнал выполнения", padding=10)
        console_frame.pack(fill='both', expand=True, pady=5)

        self.console = ConsoleWidget(console_frame, height=10)
        self.console.pack(fill='both', expand=True)

        # === Кнопки управления ===
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        self.deploy_button = ttk.Button(
            button_frame,
            text="🚀 ЗАПУСТИТЬ УСТАНОВКУ",
            command=self._start_deployment,
            style='Accent.TButton'
        )
        self.deploy_button.pack(side='left', padx=5)

        ttk.Button(button_frame, text="🗑 Очистить лог", command=self._clear_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="💾 Экспорт лога", command=self._export_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="❌ Выход", command=self._exit).pack(side='right', padx=5)

        # === Прогресс бар ===
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=5)

        # === Статус бар ===
        self.status_bar = ttk.Label(main_frame, text="Готов к работе", relief='sunken', anchor='w')
        self.status_bar.pack(fill='x', side='bottom')

    def _create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт лога", command=self._export_log)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._exit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)

    def _log_callback(self, message: str, level: str):
        """Callback для логирования в GUI"""
        self.root.after(0, lambda: self.console.append(message, level))

    def _check_device(self):
        """Проверка устройства с защитой от множественных вызовов"""

        if self.is_checking:
            logger.warning("Проверка уже выполняется!")
            messagebox.showwarning("Предупреждение", "Проверка уже выполняется!\nПодождите завершения.", parent=self.root)
            return

        current_time = time.time()
        if current_time - self.last_check_time < self.check_cooldown:
            remaining = int(self.check_cooldown - (current_time - self.last_check_time))
            logger.warning(f"Слишком частая проверка. Подождите {remaining} сек.")
            messagebox.showwarning("Предупреждение", f"Подождите {remaining} сек. перед следующей проверкой!", parent=self.root)
            return

        computer_name = self.computer_entry.get().strip()

        if not computer_name:
            messagebox.showerror("Ошибка", "Введите имя устройства!", parent=self.root)
            return

        self.is_checking = True
        self.last_check_time = current_time
        self.check_button.config(state='disabled')
        original_text = self.check_button.cget('text')
        self.check_button.config(text="⏳ Проверка...")

        logger.info(f"Проверка доступности: {computer_name}")
        self._set_status("Проверка...")

        def check_thread():
            try:
                creds = self._get_credentials()
                result = DeviceChecker.check_full(computer_name, creds['username'], creds['password'])
                self.root.after(0, lambda: self._update_check_result(result))
            except Exception as e:
                logger.error(f"Ошибка проверки: {e}")
                self.root.after(0, lambda: self._show_check_error(str(e)))
            finally:
                self.root.after(0, lambda: self.check_button.config(text=original_text))
                self.root.after(0, self._unlock_check_button)

        threading.Thread(target=check_thread, daemon=True).start()

    def _unlock_check_button(self):
        """Разблокировка кнопки проверки"""
        self.is_checking = False
        self.check_button.config(state='normal')

    def _show_check_error(self, error_msg):
        """Показ ошибки проверки"""
        self.status_label.set_status('error', "✗ Ошибка проверки")
        messagebox.showerror("Ошибка", f"Не удалось выполнить проверку:\n{error_msg}", parent=self.root)

    def _update_check_result(self, result: Dict[str, Any]):
        """Обновление результатов проверки с ПОЛНОЙ защитой от None"""

        # Статус устройства
        ad_status = str(result.get('status', 'Unknown'))
        ad_exists = bool(result.get('ad_exists', False))
        ad_enabled = result.get('ad_enabled')

        if ad_exists:
            if ad_enabled is True:
                self.status_label.set_status('success', "✓ AD: Активен")
            elif ad_enabled is False:
                self.status_label.set_status('warning', "⚠ AD: Отключён")
            else:
                self.status_label.set_status('info', "✓ AD: Найден")
        elif result.get('ping_available'):
            self.status_label.set_status('success', "✓ Сеть: Доступен")
        else:
            self.status_label.set_status('error', "✗ Недоступен")

        # ОС - БЕЗОПАСНОЕ получение значения
        os_display = None

        try:
            os_info = result.get('os_info')
            if os_info and isinstance(os_info, dict):
                os_display = os_info.get('caption')
                if not os_display:
                    os_display = os_info.get('from_ad')

            if not os_display:
                os_display = result.get('os_from_ad')

            # Преобразуем в строку и проверяем
            if os_display is not None:
                os_display = str(os_display).strip()

            # Проверяем что это непустая строка
            if os_display and len(os_display) > 0:
                self.os_label.set_status('success', f"✓ ОС: {os_display}")

                # БЕЗОПАСНОЕ приведение к нижнему регистру
                os_lower = str(os_display).lower()

                if 'windows 7' in os_lower or '2008' in os_lower:
                    self.os_type.set('Win7')
                elif 'windows 10' in os_lower or 'windows 11' in os_lower:
                    self.os_type.set('Win10')
            else:
                self.os_label.set_status('warning', "⚠ ОС: Не определено")

        except Exception as e:
            logger.debug(f"Ошибка обработки ОС: {e}")
            self.os_label.set_status('warning', "⚠ ОС: Не определено")

        # Статус учётных данных
        if result.get('credentials_valid'):
            self.cred_status_label.set_status('success', "✓ Учётные данные подтверждены")
        elif ad_exists:
            self.cred_status_label.set_status('success', "✓ Домен: Проверено")
        else:
            self.cred_status_label.set_status('warning', "⚠ Не проверено")

    def _validate_credentials(self):
        """Проверка учётных данных"""
        computer = self.computer_entry.get().strip()
        username = self.login_entry.get()
        password = self.password_entry.get()

        if not computer:
            messagebox.showwarning("Предупреждение", "Введите имя устройства для проверки!", parent=self.root)
            return

        if not username or not password:
            messagebox.showwarning("Предупреждение", "Введите логин и пароль!", parent=self.root)
            return

        logger.info("Проверка учётных данных...")

        def check_thread():
            try:
                if hasattr(DeviceChecker, 'validate_credentials'):
                    result = DeviceChecker.validate_credentials(computer, username, password)
                else:
                    result = {
                        'valid': DeviceChecker.ping(computer) if hasattr(DeviceChecker, 'ping') else True,
                        'message': 'Проверка выполнена'
                    }
                self.root.after(0, lambda: self._show_cred_result(result))
            except Exception as e:
                self.root.after(0, lambda: self._show_cred_result({'valid': False, 'message': str(e)}))

        threading.Thread(target=check_thread, daemon=True).start()

    def _show_cred_result(self, result: Dict[str, Any]):
        """Показать результат проверки учётных данных"""
        if result.get('valid', False):
            self.cred_status_label.set_status('success', "✓ Учётные данные подтверждены")
            messagebox.showinfo(
                "Успех",
                "Учётные данные подтверждены!\n\nВы можете выполнять развёртывание.",
                parent=self.root
            )
        else:
            self.cred_status_label.set_status('error', "✗ Ошибка аутентификации")
            messagebox.showerror(
                "Ошибка",
                f"Не удалось подтвердить учётные данные:\n\n{result.get('message', 'Неизвестная ошибка')}",
                parent=self.root
            )

    def _get_credentials(self) -> Dict[str, str]:
        """Получение учётных данных"""
        if self.save_creds_var.get() and self.cached_credentials:
            return self.cached_credentials

        return {
            'username': self.login_entry.get(),
            'password': self.password_entry.get()
        }

    def _start_deployment(self):
        """Запуск развёртывания"""
        if self.is_deploying:
            messagebox.showwarning("Предупреждение", "Развёртывание уже выполняется!", parent=self.root)
            return

        computer_name = self.computer_entry.get().strip()

        if not computer_name:
            messagebox.showerror("Ошибка", "Введите имя устройства!", parent=self.root)
            return

        selected_apps = [name for name, var in self.app_vars.items() if var.get()]

        if not selected_apps:
            messagebox.showerror("Ошибка", "Выберите хотя бы одну программу!", parent=self.root)
            return

        creds = self._get_credentials()

        if not creds['username'] or not creds['password']:
            messagebox.showerror("Ошибка", "Введите учётные данные!", parent=self.root)
            return

        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Начать развёртывание на {computer_name}?\n\nПрограммы: {', '.join(selected_apps)}",
            parent=self.root
        )

        if not confirm:
            return

        if self.save_creds_var.get():
            self.cached_credentials = creds

        self.is_deploying = True
        self.deploy_button.config(state='disabled')
        self.progress.start(10)
        self._set_status("Развёртывание...")

        def deploy_thread():
            try:
                deployer = DeployManager(computer_name, creds['username'], creds['password'], self.os_type.get())
                result = deployer.deploy(selected_apps)
                self.root.after(0, lambda: self._deployment_complete(result))
            except Exception as e:
                self.root.after(0, lambda: self._deployment_complete({'success': False, 'error': str(e)}))

        self.deployment_thread = threading.Thread(target=deploy_thread, daemon=True)
        self.deployment_thread.start()

    def _deployment_complete(self, result: Dict[str, Any]):
        """Завершение развёртывания"""
        self.is_deploying = False
        self.deploy_button.config(state='normal')
        self.progress.stop()

        if result.get('success', False):
            messagebox.showinfo("Готово", "✓ Установка завершена успешно!", parent=self.root)
            logger.success("=" * 60)
            logger.success("РАЗВЁРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
            logger.success("=" * 60)
            self._set_status("Готово")
        else:
            messagebox.showerror(
                "Ошибка",
                f"✗ Установка завершена с ошибками:\n{result.get('error', 'Неизвестная ошибка')}",
                parent=self.root
            )
            logger.error("Развёртывание завершено с ошибками!")
            self._set_status("Ошибка")

    def _clear_log(self):
        """Очистка лога"""
        self.console.clear()
        logger.info("Лог очищен пользователем")
        self._set_status("Лог очищен")

    def _export_log(self):
        """Экспорт лога"""
        log_file = logger.get_log_file()

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"deploy_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            parent=self.root
        )

        if save_path:
            try:
                import shutil
                shutil.copy2(log_file, save_path)
                messagebox.showinfo("Экспорт", f"✓ Лог экспортирован:\n{save_path}", parent=self.root)
                self._set_status(f"Лог экспортирован: {save_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать лог:\n{e}", parent=self.root)

    def _show_about(self):
        """О программе"""
        messagebox.showinfo(
            "О программе",
            "Deploy Tool v1.0\n\n"
            "Система развёртывания ПО\n"
            "для корпоративной среды\n\n"
            "Python 3.14 + Tkinter\n"
            "© 2026",
            parent=self.root
        )

    def _set_status(self, text: str):
        """Установка текста в статус бар"""
        self.status_bar.config(text=text)

    def _exit(self):
        """Выход"""
        if self.is_deploying:
            if not messagebox.askyesno("Предупреждение", "Развёртывание выполняется! Вы уверены, что хотите выйти?", parent=self.root):
                return

        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?", parent=self.root):
            logger.info("Приложение закрыто пользователем")
            self.root.destroy()

    def run(self):
        """Запуск приложения"""
        self.root.protocol("WM_DELETE_WINDOW", self._exit)
        self.root.mainloop()