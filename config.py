"""Конфигурация приложения Deploy-Tools"""

import os
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent
RESOURCES_DIR = BASE_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
FONTS_DIR = RESOURCES_DIR / "fonts"

# Настройки UI
APP_NAME = "Deploy Tools"
APP_VERSION = "1.0.0"
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900

# Масштабирование
MIN_SCALE = 0.75
MAX_SCALE = 1.5
DEFAULT_SCALE = 1.0
SCALE_STEP = 0.05

# Цветовая схема (Тёмная тема - VS Code inspired)
COLORS = {
    # Фоны
    'bg_primary': '#1e1e1e',
    'bg_secondary': '#252526',
    'bg_tertiary': '#2d2d30',
    'bg_hover': '#2a2d2e',
    'bg_active': '#37373d',

    # Акценты
    'accent': '#0e639c',
    'accent_hover': '#1177bb',
    'accent_light': '#4fc1ff',

    # Текст
    'text_primary': '#cccccc',
    'text_secondary': '#858585',
    'text_bright': '#ffffff',

    # Статусы
    'success': '#4ec9b0',
    'warning': '#ce9178',
    'error': '#f44747',
    'info': '#4fc1ff',

    # Границы
    'border': '#3c3c3c',
    'border_light': '#5a5a5a',

    # Специфичные
    'terminal_bg': '#0d0d0d',
    'terminal_green': '#0dbc79',
    'sidebar_bg': '#252526',
}

# Шрифты
FONTS = {
    'primary': 'Segoe UI',
    'monospace': 'Consolas, Monaco, monospace',
    'sizes': {
        'xs': 10,
        'sm': 12,
        'base': 14,
        'lg': 16,
        'xl': 20,
        '2xl': 24,
        '3xl': 32,
    }
}