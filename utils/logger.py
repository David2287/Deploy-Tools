"""
Модуль логирования для Deploy Tool
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
import threading

class DeployLogger:
    """Кастомный логгер с поддержкой GUI"""

    _instance: Optional['DeployLogger'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        from config.settings import LOG_DIR, LOG_CONFIG

        self.log_dir = LOG_DIR
        self.log_file = self.log_dir / f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        self.logger = logging.getLogger('DeployTool')
        self.logger.setLevel(logging.DEBUG)  # Установили DEBUG уровень

        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_CONFIG['format'], LOG_CONFIG['date_format']))
        self.logger.addHandler(file_handler)

        # Console handler (для отладки)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_CONFIG['format'], LOG_CONFIG['date_format']))
        self.logger.addHandler(console_handler)

        # Callback для GUI
        self.gui_callback = None

        self._initialized = True

    def set_gui_callback(self, callback):
        """Установить callback для обновления GUI"""
        self.gui_callback = callback

    def _log(self, level: str, message: str):
        """Внутренний метод логирования"""
        log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}"

        # Запись в файл через стандартный logger
        getattr(self.logger, level.lower())(message)

        # Обновление GUI
        if self.gui_callback:
            self.gui_callback(log_entry, level)

    def debug(self, message: str):
        """DEBUG уровень"""
        self._log('DEBUG', message)

    def info(self, message: str):
        """INFO уровень"""
        self._log('INFO', message)

    def success(self, message: str):
        """SUCCESS уровень (как INFO)"""
        self._log('INFO', f"✓ {message}")

    def warning(self, message: str):
        """WARNING уровень"""
        self._log('WARNING', f"⚠ {message}")

    def error(self, message: str):
        """ERROR уровень"""
        self._log('ERROR', f"✗ {message}")

    def get_log_file(self) -> Path:
        return self.log_file

# Глобальный экземпляр
logger = DeployLogger()