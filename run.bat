@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Запуск Deploy Tool...
echo.

pythonw main.pyw

if errorlevel 1 (
    echo.
    echo Ошибка запуска!
    pause
)