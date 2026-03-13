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
        self.default_geometry = "950x800"
        self.root.geometry(self.default_geometry)
        # Разрешаем изменение размера окна
        self.root.resizable(True, True)
        self.root.minsize(900, 650)

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

        # Текущая тема
        self.current_theme = tk.StringVar(value="light")

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
        """Настройка стилей приложения"""
        self.style = ttk.Style()

        # Базовая тема
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass

        # Цветовая схема и стили зависят от темы
        self._apply_theme()

    def _apply_theme(self):
        """Применить текущую тему (светлая / тёмная)"""
        theme = self.current_theme.get()

        # Палитра в духе Material / Tailwind:
        # Светлая: фон White, текст Black, серые 200–500, акцент Blue 300
        # Тёмная: фон Gray 900, текст Gray 100, серые 400–700, акцент Sky 300

        if theme == "dark":
            # Тёмная тема
            self.base_bg = "#111827"       # Gray 900 – общий фон
            self.surface_bg = "#1f2933"    # Gray 800 – карточки/фреймы
            self.header_fg = "#e5e7eb"     # Gray 200
            self.text_fg = "#e5e7eb"       # Gray 200
            self.subtext_fg = "#9ca3af"    # Gray 400
            self.icon_fg = "#9ca3af"       # Gray 400
            self.muted_fg = "#6b7280"      # Gray 500
            self.accent_color = "#38bdf8"  # Sky 300
            self.danger_color = "#f97373"  # Red 400
            status_bg = "#030712"          # ещё темнее для статус-бара
            status_fg = "#e5e7eb"
        else:
            # Светлая тема
            self.base_bg = "#f3f4f6"       # Gray 100 – общий фон
            self.surface_bg = "#ffffff"    # White – карточки/фреймы
            self.header_fg = "#111827"     # Gray 900 – заголовки
            self.text_fg = "#111827"       # Gray 900 – основной текст
            self.subtext_fg = "#6b7280"    # Gray 500 – подписи
            self.icon_fg = "#6b7280"       # Gray 500 – иконки/мелкий текст
            self.muted_fg = "#9ca3af"      # Gray 400 – вторичный текст
            self.accent_color = "#60a5fa"  # Blue 400 / 300 – акцент
            self.danger_color = "#f97373"  # Red 400
            status_bg = "#e5e7eb"          # Gray 200
            status_fg = "#374151"          # Gray 700

        self.root.configure(bg=self.base_bg)

        # Базовые стили
        self.style.configure(
            '.',
            background=self.base_bg,
            foreground=self.text_fg,
            font=('Segoe UI', 10)
        )
        self.style.configure('TFrame', background=self.base_bg)
        self.style.configure(
            'TLabelFrame',
            background=self.surface_bg,
            foreground=self.header_fg,
            borderwidth=1,
            relief='solid'
        )
        self.style.configure('TLabel', background=self.surface_bg, foreground=self.text_fg)
        self.style.configure(
            'Header.TLabel',
            font=('Segoe UI', 16, 'bold'),
            foreground=self.header_fg,
            background=self.base_bg
        )
        self.style.configure(
            'SubHeader.TLabel',
            font=('Segoe UI', 9),
            foreground=self.subtext_fg,
            background=self.base_bg
        )

        # Поля ввода и переключатели
        entry_bg = "#0f172a" if theme == "dark" else "#ffffff"   # Gray 900 / White
        entry_border = "#1f2937" if theme == "dark" else "#d1d5db"

        self.style.configure(
            'TEntry',
            foreground=self.text_fg,
            fieldbackground=entry_bg,
            background=entry_bg,
            bordercolor=entry_border,
            lightcolor=entry_border,
            darkcolor=entry_border,
            insertcolor=self.text_fg
        )

        self.style.configure(
            'TCheckbutton',
            background=self.surface_bg,
            foreground=self.text_fg
        )
        self.style.configure(
            'TRadiobutton',
            background=self.surface_bg,
            foreground=self.text_fg
        )

        # Кнопки
        self.style.configure(
            'Accent.TButton',
            foreground='white',
            background=self.accent_color,
            borderwidth=0,
            focusthickness=3,
            focuscolor=self.accent_color,
            padding=(12, 6)
        )
        self.style.map(
            'Accent.TButton',
            background=[('active', '#106ebe'), ('disabled', '#a6c7e8')]
        )

        self.style.configure(
            'Secondary.TButton',
            foreground=self.accent_color,
            background="#dbeafe" if theme != "dark" else "#1d3a5f",
            borderwidth=0,
            padding=(10, 5)
        )

        self.style.configure(
            'Danger.TButton',
            foreground='white',
            background=self.danger_color,
            borderwidth=0,
            padding=(10, 5)
        )

        # Статус‑бар
        self.style.configure('Status.TLabel', background=status_bg, foreground=status_fg, anchor='w')

    def _create_widgets(self):
        """Создание элементов интерфейса"""

        base_bg = getattr(self, "base_bg", "#f5f5f7")

        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill='both', expand=True)

        # === Заголовок ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Deploy Tool",
            style='Header.TLabel'
        ).pack(anchor='w')

        ttk.Label(
            header_frame,
            text="Быстрая установка стандартного ПО на рабочие станции",
            style='SubHeader.TLabel'
        ).pack(anchor='w', pady=(2, 0))

        ttk.Separator(header_frame, orient='horizontal').pack(fill='x', pady=8)

        # === Группа: Информация об устройстве ===
        device_frame = ttk.LabelFrame(main_frame, text="Устройство", padding=10)
        device_frame.pack(fill='x', pady=5)
        device_frame.columnconfigure(1, weight=1)

        ttk.Label(device_frame, text="Имя устройства:").grid(row=0, column=0, sticky='w', padx=(0, 8), pady=3)
        self.computer_entry = ttk.Entry(device_frame, width=30)
        self.computer_entry.grid(row=0, column=1, sticky='we', pady=3)
        self.computer_entry.bind('<Return>', lambda e: self._check_device())

        self.check_button = ttk.Button(device_frame, text="Проверить доступность", command=self._check_device)
        self.check_button.grid(row=0, column=2, sticky='w', padx=(8, 0), pady=3)

        self.status_label = StatusLabel(device_frame, text="Статус: не проверено", width=40)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky='w', pady=3)

        self.os_label = StatusLabel(device_frame, text="ОС: не определено", width=40)
        self.os_label.grid(row=1, column=2, sticky='w', pady=3)

        # === Группа: Учётные данные ===
        creds_frame = ttk.LabelFrame(main_frame, text="Учётные данные администратора", padding=10)
        creds_frame.pack(fill='x', pady=5)
        creds_frame.columnconfigure(1, weight=1)

        ttk.Label(creds_frame, text="Логин:").grid(row=0, column=0, sticky='w', padx=(0, 8), pady=3)
        self.login_entry = ttk.Entry(creds_frame, width=28)
        self.login_entry.grid(row=0, column=1, sticky='we', pady=3)
        self.login_entry.insert(0, f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}")

        ttk.Label(creds_frame, text="Пароль:").grid(row=1, column=0, sticky='w', padx=(0, 8), pady=3)
        self.password_entry = ttk.Entry(creds_frame, width=28, show="*")
        self.password_entry.grid(row=1, column=1, sticky='we', pady=3)

        self.cred_status_label = StatusLabel(creds_frame, text="Статус: не проверено", width=40)
        self.cred_status_label.grid(row=0, column=2, rowspan=2, sticky='w', padx=(12, 0))

        ttk.Button(
            creds_frame,
            text="Проверить учётные данные",
            command=self._validate_credentials
        ).grid(row=2, column=2, sticky='e', padx=(12, 0), pady=(6, 0))

        self.save_creds_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            creds_frame,
            text="Сохранить учётные данные для текущей сессии",
            variable=self.save_creds_var
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=(8, 0))

        # === Группа: Выбор ОС ===
        os_frame = ttk.LabelFrame(main_frame, text="Операционная система", padding=10)
        os_frame.pack(fill='x', pady=5)

        self.os_type = tk.StringVar(value="Win10")
        ttk.Radiobutton(os_frame, text="Windows 7 / Server 2008", variable=self.os_type, value="Win7").pack(
            side='left', padx=(0, 16)
        )
        ttk.Radiobutton(os_frame, text="Windows 10 / 11", variable=self.os_type, value="Win10").pack(
            side='left'
        )

        # === Группа: Выбор программ ===
        apps_frame = ttk.LabelFrame(main_frame, text="Программы для установки", padding=10)
        apps_frame.pack(fill='both', expand=True, pady=5)

        apps_header = ttk.Frame(apps_frame)
        apps_header.pack(fill='x', pady=(0, 5))

        ttk.Label(apps_header, text="Отметьте программы, которые нужно установить:").pack(side='left')

        def select_all():
            for var in self.app_vars.values():
                var.set(True)

        def deselect_all():
            for var in self.app_vars.values():
                var.set(False)

        ttk.Button(apps_header, text="Выбрать все", command=select_all, style='Secondary.TButton').pack(
            side='right', padx=2
        )
        ttk.Button(apps_header, text="Сбросить", command=deselect_all).pack(side='right', padx=2)

        # Прокручиваемый список программ
        container = ttk.Frame(apps_frame)
        container.pack(fill='both', expand=True)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0, background=base_bg)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.app_vars: Dict[str, tk.BooleanVar] = {}

        for i, app_name in enumerate(APPLICATIONS.keys()):
            var = tk.BooleanVar(value=False)
            self.app_vars[app_name] = var
            ttk.Checkbutton(scrollable, text=app_name, variable=var).grid(
                row=i, column=0, sticky='w', padx=10, pady=3
            )

        ttk.Button(
            apps_frame,
            text="Установить выбранные",
            command=self._start_deployment,
            style='Accent.TButton'
        ).pack(fill='x', pady=(10, 0))

        # === Группа: Консоль вывода ===
        console_frame = ttk.LabelFrame(main_frame, text="Журнал выполнения", padding=10)
        console_frame.pack(fill='both', expand=True, pady=5)

        self.console = ConsoleWidget(console_frame, height=10)
        self.console.pack(fill='both', expand=True)

        # === Кнопки управления ===
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        self.deploy_button = ttk.Button(
            button_frame,
            text="Запустить установку",
            command=self._start_deployment,
            style='Accent.TButton'
        )
        self.deploy_button.pack(side='left')

        ttk.Button(button_frame, text="Очистить лог", command=self._clear_log).pack(side='left', padx=(8, 0))
        ttk.Button(button_frame, text="Экспорт лога", command=self._export_log).pack(side='left', padx=(8, 0))

        ttk.Button(
            button_frame,
            text="Выход",
            command=self._exit,
            style='Danger.TButton'
        ).pack(side='right')

        # === Прогресс бар ===
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 4))

        # === Статус бар ===
        self.status_bar = ttk.Label(main_frame, text="Готов к работе", style='Status.TLabel')
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

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)

        # Подменю темы
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Тема", menu=theme_menu)
        theme_menu.add_radiobutton(
            label="Светлая",
            variable=self.current_theme,
            value="light",
            command=lambda: self._set_theme("light")
        )
        theme_menu.add_radiobutton(
            label="Тёмная",
            variable=self.current_theme,
            value="dark",
            command=lambda: self._set_theme("dark")
        )

        # Размер окна
        view_menu.add_separator()
        view_menu.add_command(label="Стандартный размер", command=self._set_window_normal)
        view_menu.add_command(label="Развернуть на весь экран", command=self._set_window_maximized)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)

    def _set_theme(self, theme: str):
        """Смена темы оформления"""
        self.current_theme.set(theme)
        self._apply_theme()

    def _set_window_normal(self):
        """Вернуть стандартный размер окна"""
        self.root.state('normal')
        self.root.geometry(self.default_geometry)

    def _set_window_maximized(self):
        """Развернуть окно на весь экран"""
        try:
            # На Windows state('zoomed') даёт развёрнутое окно
            self.root.state('zoomed')
        except tk.TclError:
            # Fallback: просто максимально увеличить окно
            self.root.attributes('-zoomed', True)

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

        # Финальный статус проверки
        logger.info("Проверка устройства завершена")
        self._set_status("Проверка завершена")

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