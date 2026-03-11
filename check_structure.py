import os
import sys

print("=" * 60)
print("ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
print("=" * 60)

script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"\nКорневая директория: {script_dir}")

required_files = [
    "main.pyw",
    "gui/__init__.py",
    "gui/main_window.py",
    "gui/widgets.py",
    "core/__init__.py",
    "core/deploy.py",
    "core/checker.py",
    "utils/__init__.py",
    "utils/logger.py",
    "config/__init__.py",
    "config/settings.py",
]

print("\nПроверка файлов:")
all_ok = True
for file_path in required_files:
    full_path = os.path.join(script_dir, file_path)
    exists = os.path.exists(full_path)
    status = "✓" if exists else "✗"
    print(f"  {status} {file_path}")
    if not exists:
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✓ Все файлы на месте!")
else:
    print("✗ Некоторые файлы отсутствуют!")
print("=" * 60)

input("\nНажмите Enter для выхода...")