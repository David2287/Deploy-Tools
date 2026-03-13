"""
Кастомные виджеты для GUI
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ConsoleWidget(tk.Frame):
    """Виджет консоли для вывода логов"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Label
        self.label = ttk.Label(self, text="Журнал выполнения:")
        self.label.pack(anchor='w', padx=5, pady=(5, 0))

        # Text widget с scrollbar
        self.text_frame = tk.Frame(self)
        self.text_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(self.text_frame)
        self.scrollbar.pack(side='right', fill='y')

        self.text = tk.Text(
            self.text_frame,
            wrap='word',
            yscrollcommand=self.scrollbar.set,
            bg='#020617',      # почти чёрный фон (Gray 950)
            fg='#e5e7eb',      # светлый текст (Gray 200)
            insertbackground='#e5e7eb',
            font=('Consolas', 10),
            state='disabled',
            borderwidth=0,
            highlightthickness=0
        )
        self.text.pack(side='left', fill='both', expand=True)
        self.scrollbar.config(command=self.text.yview)

        # Теги для цветов (в духе Material / системных сообщений)
        self.text.tag_configure('DEBUG', foreground='#9ca3af')     # серый текст
        self.text.tag_configure('INFO', foreground='#e5e7eb')      # обычный текст
        self.text.tag_configure('SUCCESS', foreground='#4ade80')   # зелёный (Green 400)
        self.text.tag_configure('WARNING', foreground='#facc15')   # жёлтый (Yellow 400)
        self.text.tag_configure('ERROR', foreground='#f97373')     # красный (Red 400)

    def append(self, message: str, level: str = 'INFO'):
        """Добавить сообщение в консоль"""
        self.text.configure(state='normal')
        self.text.insert('end', message + '\n', level)
        self.text.see('end')
        self.text.configure(state='disabled')

    def clear(self):
        """Очистить консоль"""
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.configure(state='disabled')


class StatusLabel(ttk.Label):
    """Label с цветовым статусом"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._colors = {
            'normal': '#666666',
            'success': '#00aa00',
            'warning': '#ffaa00',
            'error': '#ff0000'
        }

    def set_status(self, status: str, text: str = None):
        """Установить статус и цвет"""
        if text:
            self.config(text=text)
        self.config(foreground=self._colors.get(status, '#666666'))