"""
Модуль развёртывания программного обеспечения
Метод: Сетевой ресурс → Админ ПК → Целевой ПК
"""

import subprocess
import json
import re
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Tuple
from utils.logger import logger
from config.settings import APPLICATIONS, POWERSHELL_CONFIG

class DeployManager:
    """Управление развёртыванием ПО (двухэтапное копирование)"""

    def __init__(self, computer_name: str, username: str, password: str, os_type: str = 'Win10'):
        self.computer_name = computer_name
        self.username = username
        self.password = password
        self.os_type = os_type
        self.admin_temp_dir = "C:\\Temp\\Deploy"  # На админском ПК
        self.remote_temp_dir = "C:\\Temp\\Install"  # На целевом ПК
        self.progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Установить callback для обновления прогресса"""
        self.progress_callback = callback

    def _run_local_powershell(self, script: str, timeout: int = None) -> Tuple[bool, str, str]:
        """Выполнение PowerShell скрипта локально"""
        try:
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-Command', script],
                capture_output=True,
                text=True,
                timeout=timeout or 120,
                encoding='utf-8',
                errors='replace'
            )

            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""

            return result.returncode == 0, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)

    def check_network_packages(self, app_names: List[str]) -> Dict[str, bool]:
        """1. Проверка пакетов на сетевом ресурсе"""
        logger.info("Проверка пакетов на сетевом ресурсе...")

        results = {}

        for app_name in app_names:
            if app_name not in APPLICATIONS:
                logger.error(f"Приложение не найдено в конфиге: {app_name}")
                results[app_name] = False
                continue

            app_config = APPLICATIONS[app_name]
            source_path = app_config.get(self.os_type, app_config.get('Win10'))

            if not source_path:
                logger.error(f"Путь не найден для {app_name}")
                results[app_name] = False
                continue

            # Проверяем существование файла
            if Path(source_path).exists():
                logger.success(f"✓ Пакет доступен: {app_name}")
                logger.debug(f"  Путь: {source_path}")
                results[app_name] = True
            else:
                logger.error(f"✗ Пакет не найден: {app_name}")
                logger.error(f"  Путь: {source_path}")
                results[app_name] = False

        return results

    def create_admin_temp_folder(self) -> bool:
        """2. Создание папки Temp на админском ПК"""
        logger.info("Создание временной папки на админском ПК...")

        try:
            admin_temp = Path(self.admin_temp_dir)

            if not admin_temp.exists():
                admin_temp.mkdir(parents=True, exist_ok=True)
                logger.success(f"Папка создана: {self.admin_temp_dir}")
            else:
                logger.debug(f"Папка уже существует: {self.admin_temp_dir}")

            return True

        except Exception as e:
            logger.error(f"Не удалось создать папку: {e}")
            return False

    def copy_to_admin_temp(self, app_names: List[str]) -> Dict[str, bool]:
        """3. Перенос файлов установки на устройство админа"""
        logger.info("Копирование установщиков в локальную папку...")

        results = {}

        for app_name in app_names:
            if app_name not in APPLICATIONS:
                results[app_name] = False
                continue

            app_config = APPLICATIONS[app_name]
            source_path = app_config.get(self.os_type, app_config.get('Win10'))

            if not source_path or not Path(source_path).exists():
                results[app_name] = False
                continue

            file_name = Path(source_path).name
            dest_path = Path(self.admin_temp_dir) / file_name

            try:
                logger.info(f"Копирование: {app_name}")
                shutil.copy2(source_path, dest_path)

                if dest_path.exists():
                    logger.success(f"✓ Скопировано: {app_name}")
                    logger.debug(f"  Размер: {dest_path.stat().st_size / 1024 / 1024:.2f} MB")
                    results[app_name] = True
                else:
                    logger.error(f"✗ Не скопировано: {app_name}")
                    results[app_name] = False

            except Exception as e:
                logger.error(f"Ошибка копирования {app_name}: {e}")
                results[app_name] = False

        return results

    def create_remote_temp_folder(self) -> bool:
        """4. Создание папки Temp на целевом устройстве"""
        logger.info("Создание временной папки на целевом устройстве...")

        try:
            # Используем PowerShell для создания папки через SMB
            script = f"""
            $path = "{self.remote_temp_dir}"
            if (-not (Test-Path $path)) {{
                New-Item -ItemType Directory -Path $path -Force -ErrorAction Stop | Out-Null
            }}
            
            if (Test-Path $path) {{
                Write-Output "SUCCESS"
            }} else {{
                Write-Output "FAILED"
            }}
            """

            # Выполняем через сетевой путь
            remote_script = f"""
            $script = {{
                $path = "{self.remote_temp_dir}"
                if (-not (Test-Path $path)) {{
                    New-Item -ItemType Directory -Path $path -Force -ErrorAction Stop | Out-Null
                }}
                if (Test-Path $path) {{ "SUCCESS" }} else {{ "FAILED" }}
            }}
            Invoke-Command -ComputerName "{self.computer_name}" -ScriptBlock $script
            """

            success, stdout, stderr = self._run_local_powershell(remote_script, timeout=30)

            if success and 'SUCCESS' in stdout:
                logger.success(f"Папка создана: {self.remote_temp_dir}")
                return True
            else:
                # Пробуем прямой доступ через SMB
                try:
                    remote_path = f"\\{self.computer_name}\\C$\\Temp"
                    Path(remote_path).mkdir(parents=True, exist_ok=True)
                    Path(remote_path + "\\Install").mkdir(parents=True, exist_ok=True)
                    logger.success(f"Папка создана через SMB: {self.remote_temp_dir}")
                    return True
                except Exception as smb_error:
                    logger.error(f"Не удалось создать папку: {smb_error}")
                    return False

        except Exception as e:
            logger.error(f"Ошибка создания папки: {e}")
            return False

    def copy_to_remote_device(self, app_names: List[str]) -> Dict[str, bool]:
        """5. Перенос файлов с админского ПК на целевое устройство"""
        logger.info("Копирование установщиков на целевое устройство...")

        results = {}

        for app_name in app_names:
            if app_name not in APPLICATIONS:
                results[app_name] = False
                continue

            file_name = Path(APPLICATIONS[app_name].get(self.os_type, '')).name
            source_path = Path(self.admin_temp_dir) / file_name

            # Используем полный сетевой путь
            remote_share = f"\\\\{self.computer_name}\\C$\\Temp\\Install"
            remote_dest = f"{remote_share}\\{file_name}"

            if not source_path.exists():
                logger.error(f"Файл не найден: {source_path}")
                results[app_name] = False
                continue

            try:
                logger.info(f"Копирование на {self.computer_name}: {app_name}")
                logger.debug(f"  Источник: {source_path}")
                logger.debug(f"  Назначение: {remote_dest}")

                # Проверяем доступность сетевого пути
                if not Path(remote_share).exists():
                    logger.error(f"Сетевой путь недоступен: {remote_share}")
                    results[app_name] = False
                    continue

                # Копируем файл
                shutil.copy2(source_path, remote_dest)

                # Проверяем наличие файла на удалённом ПК
                if Path(remote_dest).exists():
                    file_size = Path(remote_dest).stat().st_size / 1024 / 1024
                    logger.success(f"✓ Скопировано: {app_name}")
                    logger.debug(f"  Размер: {file_size:.2f} MB")
                    results[app_name] = True
                else:
                    logger.error(f"✗ Файл не найден после копирования: {remote_dest}")
                    results[app_name] = False

            except PermissionError as e:
                logger.error(f"Ошибка доступа {app_name}: {e}")
                logger.error(f"  Проверьте права на \\\\{self.computer_name}\\C$")
                results[app_name] = False
            except FileNotFoundError as e:
                logger.error(f"Файл не найден {app_name}: {e}")
                logger.error(f"  Проверьте доступность сетевого пути")
                results[app_name] = False
            except Exception as e:
                logger.error(f"Ошибка копирования {app_name}: {type(e).__name__}: {e}")
                results[app_name] = False

        return results

    def execute_installation(self, app_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """6. Выполнение установки программ"""
        logger.info("Выполнение установки программ...")

        results = {}

        for app_name in app_names:
            if app_name not in APPLICATIONS:
                continue

            app_config = APPLICATIONS[app_name]
            file_name = Path(app_config.get(self.os_type, '')).name
            args = app_config.get('args', '/S')
            timeout = app_config.get('timeout', 300)

            logger.info(f"Установка: {app_name}")

            if self.progress_callback:
                self.progress_callback('install', app_name, False)

            remote_exe = f"{self.remote_temp_dir}\\{file_name}"

            # Скрипт установки с явным выводом в консоль
            install_script = f"""
            $ErrorActionPreference = 'Continue'

            $filePath = "{remote_exe}"
            $arguments = "{args}"

            if (-not (Test-Path $filePath)) {{
                Write-Host "ERROR: File not found: $filePath"
                exit 1
            }}

            Write-Host "Starting installation: $filePath"

            $process = Start-Process -FilePath $filePath -ArgumentList $arguments -Wait -PassThru

            Write-Host "Process ExitCode: $($process.ExitCode)"

            $isSuccess = ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010)

            # Явный вывод результата в формате, который легко парсить
            Write-Host "RESULT:SUCCESS=$isSuccess"
            Write-Host "RESULT:EXITCODE=$($process.ExitCode)"

            if ($isSuccess) {{
                Write-Host "INSTALLATION_COMPLETED_SUCCESSFULLY"
            }} else {{
                Write-Host "INSTALLATION_FAILED"
            }}
            """

            try:
                # Выполняем на удалённом компьютере
                remote_script = f"""
                Invoke-Command -ComputerName "{self.computer_name}" -ScriptBlock {{
                    {install_script}
                }}
                """

                success, stdout, stderr = self._run_local_powershell(remote_script, timeout=timeout + 60)

                logger.debug(f"PS Output: {stdout[:500]}")

                # Парсим результат по явным маркерам
                exit_code = -1
                is_success = False

                # Ищем RESULT:SUCCESS=True/False
                if 'RESULT:SUCCESS=True' in stdout or 'RESULT:SUCCESS=True' in stderr:
                    is_success = True
                elif 'INSTALLATION_COMPLETED_SUCCESSFULLY' in stdout:
                    is_success = True

                # Ищем код выхода
                import re
                exit_match = re.search(r'RESULT:EXITCODE=(\d+)', stdout)
                if exit_match:
                    exit_code = int(exit_match.group(1))
                else:
                    exit_match = re.search(r'Process ExitCode:\s*(\d+)', stdout)
                    if exit_match:
                        exit_code = int(exit_match.group(1))

                # Fallback: если видим стандартный вывод успеха
                if not is_success and ('Success.*True' in stdout or 'ExitCode.*0' in stdout):
                    is_success = True
                    exit_code = 0

                if is_success or exit_code in [0, 3010]:
                    logger.success(f"✓ {app_name} установлен (Code: {exit_code})")
                    results[app_name] = {'success': True, 'exit_code': exit_code, 'error': None}
                else:
                    error_msg = stderr or stdout
                    logger.error(f"✗ {app_name} ошибка: {error_msg[:200]}")
                    results[app_name] = {'success': False, 'exit_code': exit_code, 'error': error_msg}

            except Exception as e:
                logger.error(f"Ошибка установки {app_name}: {e}")
                results[app_name] = {'success': False, 'exit_code': -1, 'error': str(e)}

            if self.progress_callback:
                self.progress_callback('install', app_name, results[app_name].get('success', False))

        return results

    def cleanup_all(self):
        """7. Удаление файлов и папок Temp"""
        logger.info("Очистка временных файлов...")

        # 7a. Удаляем на целевом ПК
        logger.info("Очистка на целевом устройстве...")
        try:
            cleanup_remote = f"""
            $path = "{self.remote_temp_dir}"
            if (Test-Path $path) {{
                Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
                Write-Output "REMOTE_CLEANED"
            }} else {{
                Write-Output "REMOTE_NOT_FOUND"
            }}
            """

            self._run_local_powershell(cleanup_remote, timeout=30)
            logger.success("Папка удалена на целевом ПК")

        except Exception as e:
            logger.warning(f"Не удалось очистить удалённую папку: {e}")

        # 7b. Удаляем на админском ПК
        logger.info("Очистка на админском ПК...")
        try:
            admin_temp = Path(self.admin_temp_dir)
            if admin_temp.exists():
                shutil.rmtree(admin_temp, ignore_errors=True)
                logger.success(f"Папка удалена: {self.admin_temp_dir}")
            else:
                logger.debug(f"Папка не найдена: {self.admin_temp_dir}")

        except Exception as e:
            logger.warning(f"Не удалось очистить локальную папку: {e}")

    def deploy(self, app_names: List[str]) -> Dict[str, Any]:
        """Полный процесс развёртывания (7 этапов)"""
        logger.info("=" * 70)
        logger.info(f"НАЧАЛО РАЗВЁРТЫВАНИЯ: {self.computer_name}")
        logger.info(f"ОС: {self.os_type}")
        logger.info(f"Приложения: {', '.join(app_names)}")
        logger.info("=" * 70)

        result = {
            'computer_name': self.computer_name,
            'os_type': self.os_type,
            'applications': {},
            'success': False,
            'error': None,
            'stages': {}
        }

        try:
            # Этап 1: Проверка пакетов
            logger.info("\n[ЭТАП 1/7] Проверка пакетов на сетевом ресурсе...")
            check_results = self.check_network_packages(app_names)
            result['stages']['check_packages'] = check_results

            if not all(check_results.values()):
                result['error'] = "Не все пакеты доступны на сетевом ресурсе"
                return result

            # Этап 2: Создание папки на админском ПК
            logger.info("\n[ЭТАП 2/7] Создание папки на админском ПК...")
            if not self.create_admin_temp_folder():
                result['error'] = "Не удалось создать папку на админском ПК"
                return result
            result['stages']['admin_temp_created'] = True

            # Этап 3: Копирование на админский ПК
            logger.info("\n[ЭТАП 3/7] Копирование на админский ПК...")
            copy_admin_results = self.copy_to_admin_temp(app_names)
            result['stages']['copy_to_admin'] = copy_admin_results

            if not all(copy_admin_results.values()):
                result['error'] = "Не удалось скопировать файлы на админский ПК"
                return result

            # Этап 4: Создание папки на целевом ПК
            logger.info("\n[ЭТАП 4/7] Создание папки на целевом ПК...")
            if not self.create_remote_temp_folder():
                result['error'] = "Не удалось создать папку на целевом ПК"
                return result
            result['stages']['remote_temp_created'] = True

            # Этап 5: Копирование на целевой ПК
            logger.info("\n[ЭТАП 5/7] Копирование на целевой ПК...")
            copy_remote_results = self.copy_to_remote_device(app_names)
            result['stages']['copy_to_remote'] = copy_remote_results

            if not all(copy_remote_results.values()):
                result['error'] = "Не удалось скопировать файлы на целевой ПК"
                return result

            # Этап 6: Установка
            logger.info("\n[ЭТАП 6/7] Установка программ...")
            install_results = self.execute_installation(app_names)
            result['applications'] = install_results
            result['stages']['installation'] = install_results

            # Этап 7: Очистка
            logger.info("\n[ЭТАП 7/7] Очистка временных файлов...")
            self.cleanup_all()
            result['stages']['cleanup_done'] = True

            # Итоговый статус
            all_success = all(r.get('success', False) for r in install_results.values())
            result['success'] = all_success

            logger.info("\n" + "=" * 70)
            if all_success:
                logger.success("РАЗВЁРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            else:
                logger.warning("РАЗВЁРТЫВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            result['error'] = str(e)

        return result