import os
from pathlib import Path

print("=" * 60)
print("ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
print("=" * 60)

root = Path(__file__).parent
print(f"\nКорень: {root}\n")

files_to_check = [
    "main.pyw",
    "gui/__init__.py",
    "gui/main_window.py",
    "gui/widgets.py",
    "core/__init__.py",
    "core/deploy.py",
    "core/checker.py",
    "core/ad_checker.py",
    "utils/__init__.py",
    "utils/logger.py",
    "config/__init__.py",
    "config/settings.py",
]

missing = []
for file_path in files_to_check:
    full_path = root / file_path
    if full_path.exists():
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path} - ОТСУТСТВУЕТ!")
        missing.append(file_path)

print("\n" + "=" * 60)
if missing:
    print(f"✗ Отсутствует файлов: {len(missing)}")
    for m in missing:
        print(f"  - {m}")
else:
    print("✓ Все файлы на месте!")
print("=" * 60)

input("\nНажмите Enter...")