"""
Модуль проверки компьютеров в Active Directory через LDAP
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import socket
import time

try:
    from ldap3 import Server, Connection, ALL, SUBTREE, NTLM
    from ldap3.core.exceptions import LDAPException, LDAPSocketOpenError
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    print("ldap3 не установлен!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComputerCheckResult:
    computer_name: str
    exists: bool = False
    enabled: Optional[bool] = None
    distinguished_name: Optional[str] = None
    last_logon: Optional[datetime] = None
    os_version: Optional[str] = None
    status: str = "Unknown"
    error: Optional[str] = None
    ad_attributes: Dict[str, Any] = field(default_factory=dict)

class ADComputerChecker:
    """Проверка компьютеров в Active Directory через LDAP"""

    # Классовые переменные для кэширования соединения
    _cached_connection = None
    _cache_time = 0
    _cache_ttl = 300  # 5 минут

    def __init__(
        self,
        domain: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        use_ssl: bool = False,
        port: int = 389,
        timeout: int = 30
    ):
        self.domain = domain.lower()
        self.username = username
        self.password = password
        self.server_name = server or domain
        self.use_ssl = use_ssl
        self.port = 636 if use_ssl else port
        self.timeout = timeout
        self.connection: Optional[Connection] = None

    def connect(self) -> bool:
        """Подключение к домену с кэшированием"""
        if not LDAP_AVAILABLE:
            logger.error("ldap3 библиотека не доступна")
            return False

        # Проверяем кэш
        current_time = time.time()

        if (ADComputerChecker._cached_connection and
            ADComputerChecker._cached_connection.bound and
            current_time - ADComputerChecker._cache_time < ADComputerChecker._cache_ttl):
            logger.debug("Используем кэшированное LDAP соединение")
            self.connection = ADComputerChecker._cached_connection
            return True

        try:
            server_address = self._find_domain_controller()
            if not server_address:
                server_address = self.server_name

            logger.info(f"Подключение к DC: {server_address}:{self.port}")

            server = Server(
                server_address,
                port=self.port,
                use_ssl=self.use_ssl,
                get_info=ALL,
                connect_timeout=self.timeout
            )

            user_dn = self._format_username()
            logger.info(f"Имя пользователя для LDAP: {user_dn}")

            self.connection = Connection(
                server,
                user=user_dn,
                password=self.password,
                authentication=NTLM,
                auto_bind=True,
                read_only=True,
                receive_timeout=self.timeout * 1000
            )

            if self.connection.bound:
                logger.info(f"Подключение к домену {self.domain} успешно")
                # Кэшируем соединение
                ADComputerChecker._cached_connection = self.connection
                ADComputerChecker._cache_time = current_time
                return True
            else:
                logger.warning("Соединение создано, но не авторизовано")
                return False

        except LDAPSocketOpenError as e:
            logger.error(f"Не удалось открыть соединение: {e}")
            # Очищаем кэш при ошибке
            ADComputerChecker._cached_connection = None
            return False
        except LDAPException as e:
            logger.error(f"LDAP ошибка подключения: {e}")
            ADComputerChecker._cached_connection = None
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка подключения: {type(e).__name__}: {e}")
            ADComputerChecker._cached_connection = None
            return False

    def _find_domain_controller(self) -> Optional[str]:
        """Поиск контроллера домена через DNS"""
        try:
            # Попытка найти DC через DNS SRV запись
            import dns.resolver

            try:
                answers = dns.resolver.resolve(f'_ldap._tcp.{self.domain}', 'SRV')
                if answers:
                    dc = str(answers[0].target).rstrip('.')
                    logger.info(f"Найден DC через DNS: {dc}")
                    return dc
            except:
                pass

            # Fallback: пробуем разрешить имя домена
            ip = socket.gethostbyname(self.domain)
            logger.info(f"Разрешено имя домена: {ip}")
            return ip

        except Exception as e:
            logger.debug(f"Не удалось найти DC: {e}")
            return None

    def _format_username(self) -> str:
        """Форматирование имени пользователя для NTLM"""
        if not self.username:
            return ""

        # Если уже есть формат user@domain
        if '@' in self.username:
            return self.username

        # Если формат DOMAIN\user
        if '\\' in self.username:
            parts = self.username.split('\\', 1)
            return f"{parts[0]}\\{parts[1]}"

        # Если только username, добавляем домен
        return f"{self.domain}\\{self.username}"

    def disconnect(self):
        """Закрытие соединения"""
        if self.connection and self.connection.bound:
            self.connection.unbind()
            logger.info("Соединение с AD закрыто")

    def _get_base_dn(self) -> str:
        """Получение базового DN из домена"""
        parts = [p for p in self.domain.split('.') if p]
        return ','.join(f'DC={part}' for part in parts)

    def _parse_windows_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Конвертация Windows времени в datetime"""
        if not timestamp:
            return None
        try:
            windows_time = int(timestamp)
            if windows_time > 0:
                return datetime(1601, 1, 1) + timedelta(microseconds=windows_time / 10)
        except (ValueError, TypeError):
            pass
        return None

    def check_computer(self, computer_name: str, check_enabled: bool = True) -> ComputerCheckResult:
        """Проверка одного компьютера в AD"""
        result = ComputerCheckResult(computer_name=computer_name)

        if not self.connection or not self.connection.bound:
            result.status = "NotConnected"
            result.error = "Нет подключения к Active Directory"
            return result

        try:
            cn_name = computer_name.replace(f".{self.domain}", "").upper()
            search_filter = f'(&(objectClass=computer)(|(cn={cn_name})(name={cn_name})))'

            logger.debug(f"LDAP поиск: {search_filter}")
            logger.debug(f"Base DN: {self._get_base_dn()}")

            attributes = [
                'distinguishedName', 'userAccountControl', 'lastLogon',
                'whenCreated', 'operatingSystem', 'operatingSystemVersion',
                'description', 'location', 'managedBy'
            ]

            search_success = self.connection.search(
                search_base=self._get_base_dn(),
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes
            )

            logger.debug(f"LDAP поиск завершён: {search_success}")
            logger.debug(f"Найдено записей: {len(self.connection.entries)}")

            if not self.connection.entries:
                result.status = "NotFound"
                result.error = f"Компьютер '{computer_name}' не найден в домене {self.domain}"
                return result

            entry = self.connection.entries[0]
            result.exists = True
            result.distinguished_name = str(entry.distinguishedName.value) if entry.distinguishedName.value else None

            for attr in attributes:
                if hasattr(entry, attr) and entry[attr].value:
                    result.ad_attributes[attr] = entry[attr].value

            if entry.userAccountControl.value:
                uac = int(entry.userAccountControl.value)
                is_disabled = bool(uac & 2)
                result.enabled = not is_disabled
            else:
                result.enabled = True

            if check_enabled:
                result.status = "Active" if result.enabled else "Disabled"
            else:
                result.status = "Found"

            if entry.lastLogon.value:
                result.last_logon = self._parse_windows_timestamp(entry.lastLogon.value)

            if entry.operatingSystem.value:
                result.os_version = str(entry.operatingSystem.value)
                if entry.operatingSystemVersion.value:
                    result.os_version += f" {entry.operatingSystemVersion.value}"

            logger.info(f"Компьютер {computer_name}: {result.status}")
            return result

        except LDAPException as e:
            result.status = "Error"
            result.error = f"LDAP ошибка: {str(e)}"
            logger.error(f"Ошибка проверки {computer_name}: {e}")
            return result
        except Exception as e:
            result.status = "Error"
            result.error = f"Неизвестная ошибка: {str(e)}"
            logger.error(f"Неожиданная ошибка при проверке {computer_name}: {e}")
            return result

    def check_computers(
        self,
        computer_names: List[str],
        check_enabled: bool = True
    ) -> List[ComputerCheckResult]:
        """Проверка нескольких компьютеров"""
        results = []
        for name in computer_names:
            results.append(self.check_computer(name, check_enabled))
        return results

    def __enter__(self):
        """Контекстный менеджер: вход"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        self.disconnect()
        return False