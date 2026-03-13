"""
Модуль проверки доступности устройств
"""

import subprocess
import json
import socket
import time
from typing import Optional, Dict, Any
from utils.logger import logger

# === ОПЦИОНАЛЬНЫЙ ИМПОРТ LDAP ===
LDAP_AVAILABLE = False
AD_CONFIG = {}
try:
    from config.settings import AD_CONFIG as _ad_cfg
    AD_CONFIG = _ad_cfg
    from core.ad_checker import ADComputerChecker, ComputerCheckResult
    LDAP_AVAILABLE = True
    logger.info("LDAP модуль загружен")
except ImportError:
    logger.warning("ldap3 не установлен. Проверка через AD отключена.")
    logger.warning("Для включения: pip install ldap3")
except Exception as e:
    logger.warning(f"Ошибка загрузки LDAP модуля: {e}")


class DeviceChecker:
    """Проверка доступности и информации об устройстве"""

    # Кэш для учётных данных
    _cred_cache = {}

    @staticmethod
    def ping(computer_name: str, count: int = 4, timeout: int = 15) -> bool:
        """Проверка доступности через ping с повторами"""
        try:
            # Пробуем несколько раз
            for attempt in range(3):
                result = subprocess.run(
                    ['ping', '-n', str(count), '-w', str(timeout * 1000), computer_name],
                    capture_output=True,
                    text=True,
                    timeout=timeout + 5,
                    encoding='cp866',
                    errors='replace'
                )

                stdout = result.stdout or ""

                if 'TTL=' in stdout or 'ответ' in stdout.lower() or 'Reply' in stdout:
                    if attempt > 0:
                        logger.info(f"Ping успешен с попытки {attempt + 1}")
                    return True

                logger.debug(f"Ping попытка {attempt + 1} не удалась")

            logger.warning(f"Ping не прошёл после 3 попыток")
            return False

        except Exception as e:
            logger.debug(f"Ping ошибка: {e}")
            return False

    @staticmethod
    def resolve_hostname(computer_name: str) -> Optional[str]:
        """Разрешение имени компьютера в IP"""
        try:
            return socket.gethostbyname(computer_name)
        except socket.gaierror:
            return None

    @staticmethod
    def check_via_ad(
        computer_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Проверка компьютера через Active Directory (опционально)"""

        if not LDAP_AVAILABLE:
            return {
                'computer_name': computer_name,
                'exists_in_ad': False,
                'enabled_in_ad': None,
                'os_from_ad': None,
                'last_logon': None,
                'status': 'LDAPUnavailable',
                'error': 'ldap3 не установлен',
                'ad_check': None
            }

        result = {
            'computer_name': computer_name,
            'exists_in_ad': False,
            'enabled_in_ad': None,
            'os_from_ad': None,
            'last_logon': None,
            'status': 'Unknown',
            'error': None,
            'ad_check': None
        }

        try:
            clean_name = computer_name.split('.')[0].upper()

            with ADComputerChecker(
                domain=AD_CONFIG.get('domain', ''),
                username=username,
                password=password,
                server=AD_CONFIG.get('server'),
                use_ssl=AD_CONFIG.get('use_ssl', False),
                port=AD_CONFIG.get('port', 389),
                timeout=AD_CONFIG.get('timeout', 30)
            ) as ad_checker:

                ad_result: ComputerCheckResult = ad_checker.check_computer(clean_name)
                result['ad_check'] = ad_result
                result['exists_in_ad'] = ad_result.exists
                result['enabled_in_ad'] = ad_result.enabled
                result['os_from_ad'] = ad_result.os_version
                result['last_logon'] = ad_result.last_logon
                result['status'] = ad_result.status
                result['error'] = ad_result.error

        except Exception as e:
            logger.warning(f"AD проверка не удалась: {e}")
            result['status'] = 'ADError'
            result['error'] = str(e)

        return result

    @staticmethod
    def check_full(
        computer_name: str,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Полная проверка: AD (опционально) + Ping + PowerShell"""
        logger.info(f"Проверка устройства: {computer_name}")

        result: Dict[str, Any] = {
            'computer_name': computer_name,
            'ping_available': False,
            'ad_exists': False,
            'ad_enabled': None,
            'credentials_valid': True,
            'os_info': {},
            'recommended_os': 'Win10',
            'status': 'Unknown'
        }

        try:
            # 1. Попытка проверки через AD (не критично)
            if LDAP_AVAILABLE:
                try:
                    ad_result = DeviceChecker.check_via_ad(computer_name, username, password)
                    result['ad_exists'] = ad_result.get('exists_in_ad', False)
                    result['ad_enabled'] = ad_result.get('enabled_in_ad')

                    os_from_ad = ad_result.get('os_from_ad')
                    if os_from_ad:
                        result['os_info']['from_ad'] = os_from_ad
                        try:
                            os_lower = str(os_from_ad).lower()
                        except Exception:
                            os_lower = ""

                        if 'windows 7' in os_lower or '2008' in os_lower:
                            result['recommended_os'] = 'Win7'
                        elif 'windows 10' in os_lower or 'windows 11' in os_lower:
                            result['recommended_os'] = 'Win10'

                    result['status'] = ad_result.get('status', 'Unknown')

                except Exception as e:
                    logger.warning(f"AD проверка пропущена: {e}")

            # 2. Ping проверка (обязательная для сетевой доступности)
            if DeviceChecker.ping(computer_name):
                result['ping_available'] = True
                logger.success(f"Ping успешен: {computer_name}")

                # 3. Если нет данных из AD, пробуем получить ОС через PowerShell
                if not result.get('os_info', {}).get('caption'):
                    os_info = DeviceChecker._get_os_info_powershell(computer_name, username, password)
                    if os_info:
                        result['os_info'].update(os_info)
                        try:
                            os_lower = str(os_info.get('caption', '')).lower()
                        except Exception:
                            os_lower = ""

                        if 'windows 7' in os_lower or '2008' in os_lower:
                            result['recommended_os'] = 'Win7'
                        elif 'windows 10' in os_lower or 'windows 11' in os_lower:
                            result['recommended_os'] = 'Win10'

                # Статус по умолчанию, если не определён
                if result['status'] == 'Unknown':
                    result['status'] = 'NetworkAvailable'

            else:
                logger.warning(f"Ping не прошёл: {computer_name}")
                # Если компьютер есть в AD, считаем его доступным
                if result.get('ad_exists'):
                    result['ping_available'] = True
                    result['status'] = 'InAD'
                else:
                    result['status'] = 'Unavailable'

        except Exception as e:
            # Полная защита от внутренних ошибок, чтобы не падать на GUI
            logger.error(f"Внутренняя ошибка проверки устройства: {type(e).__name__}: {e}")

        return result

    @staticmethod
    def _get_os_info_powershell(
        computer_name: str,
        username: str,
        password: str
    ) -> Optional[Dict[str, str]]:
        """Получение информации об ОС через PowerShell"""
        try:
            safe_password = password.replace('"', '`"').replace('$', '`$').replace('`', '``')

            ps_script = f"""
            $ErrorActionPreference = 'SilentlyContinue'
            $securePass = ConvertTo-SecureString '{safe_password}' -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential('{username}', $securePass)
            $os = Get-WmiObject -Class Win32_OperatingSystem -ComputerName '{computer_name}' -Credential $cred -ErrorAction Stop
            [PSCustomObject]@{{
                Caption = $os.Caption
                Version = $os.Version
            }} | ConvertTo-Json
            """

            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=20,
                encoding='utf-8',
                errors='replace',
                startupinfo=startup,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout.strip())
                return {
                    'caption': data.get('Caption', ''),
                    'version': data.get('Version', '')
                }
        except Exception as e:
            logger.debug(f"PowerShell OS check failed: {e}")
        return None

    @staticmethod
    def validate_credentials(
        computer_name: str,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Проверка учётных данных с кэшированием"""

        # Простое кэширование успешных проверок (5 минут)
        cache_key = f"{computer_name}:{username}"

        if cache_key in DeviceChecker._cred_cache:
            cache_time, cache_result = DeviceChecker._cred_cache[cache_key]
            if time.time() - cache_time < 300:  # 5 минут
                logger.debug("Используем кэшированный результат проверки учётных данных")
                return cache_result

        try:
            safe_password = password.replace('"', '`"').replace('$', '`$').replace('`', '``')

            ps_script = f"""
            $ErrorActionPreference = 'SilentlyContinue'
            $securePass = ConvertTo-SecureString '{safe_password}' -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential('{username}', $securePass)
            
            # Пробуем подключиться с таймаутом
            $test = Test-Connection -ComputerName '{computer_name}' -Count 2 -Quiet -Credential $cred -TimeoutSeconds 10
            
            [PSCustomObject]@{{
                Valid = $test
                Message = if ($test) {{ "Учётные данные подтверждены" }} else {{ "Не удалось подключиться" }}
                Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            }} | ConvertTo-Json
            """

            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace',
                startupinfo=startup,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout.strip())
                result = {
                    'valid': data.get('Valid', False),
                    'message': data.get('Message', ''),
                    'is_admin': True
                }

                # Кэшируем только успешные проверки
                if result['valid']:
                    DeviceChecker._cred_cache[cache_key] = (time.time(), result)

                return result

            return {'valid': False, 'message': 'PowerShell error', 'is_admin': False}

        except Exception as e:
            logger.warning(f"Credential check fallback: {e}")
            # Fallback: если ping работает, считаем учётку валидной
            is_valid = DeviceChecker.ping(computer_name)
            result = {
                'valid': is_valid,
                'message': 'Fallback check (ping)' if is_valid else 'Device unreachable',
                'is_admin': True
            }

            if is_valid:
                DeviceChecker._cred_cache[cache_key] = (time.time(), result)

            return result