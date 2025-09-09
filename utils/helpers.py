"""
Утилиты и вспомогательные функции для VKinder Bot
"""

import logging
import re
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
import aiohttp
import asyncpg
from dataclasses import asdict, is_dataclass

# Настройка логирования
logger = logging.getLogger(__name__)


class VKinderError(Exception):
    """Базое исключение для VKinder Bot"""
    pass


class VKAPIError(VKinderError):
    """Ошибка API ВКонтакте"""
    pass


class DatabaseError(VKinderError):
    """Ошибка базы данных"""
    pass


class ValidationError(VKinderError):
    """Ошибка валидации данных"""
    pass


# Временно определяем базовые классы здесь, чтобы избежать циклических импортов
# Эти классы будут переопределены при импорте из handlers.state_handler
class _UserState:
    """Заглушка для UserState"""
    MAIN_MENU = "main_menu"


class _StateData:
    """Заглушка для StateData"""
    def __init__(self, current_state=None):
        self.current_state = current_state


# Создаем экземпляры для временного использования
UserState = _UserState()
StateData = _StateData


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Декоратор для повторного выполнения асинхронных функций при ошибках
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Функция {func.__name__} завершилась ошибкой после {max_attempts} попыток: {e}")
                        raise
                    
                    logger.warning(f"Попытка {attempts} функции {func.__name__} не удалась: {e}. Повтор через {current_delay}с")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


def async_retry_method(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Декоратор для повторного выполнения асинхронных методов класса
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Метод {func.__name__} завершился ошибкой после {max_attempts} попыток: {e}")
                        raise
                    
                    logger.warning(f"Попытка {attempts} метода {func.__name__} не удалась: {e}. Повтор через {current_delay}с")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator


def validate_vk_user_id(user_id: Any) -> int:
    """
    Валидирует и преобразует ID пользователя ВКонтакте
    """
    try:
        user_id_int = int(user_id)
        if user_id_int <= 0:
            raise ValidationError(f"Невалидный ID пользователя: {user_id}")
        return user_id_int
    except (ValueError, TypeError):
        raise ValidationError(f"ID пользователя должен быть числом: {user_id}")


def validate_age(age: Any) -> int:
    """
    Валидирует возраст пользователя
    """
    try:
        age_int = int(age)
        if not (16 <= age_int <= 100):
            raise ValidationError(f"Возраст должен быть от 16 до 100 лет: {age}")
        return age_int
    except (ValueError, TypeError):
        raise ValidationError(f"Возраст должен быть числом: {age}")


def validate_city(city: str) -> str:
    """
    Валидирует название города
    """
    if not city or not isinstance(city, str):
        raise ValidationError("Название города обязательно")

    city_clean = city.strip()
    if len(city_clean) < 2:
        raise ValidationError("Название города слишком короткое")

    if len(city_clean) > 100:
        raise ValidationError("Название города слишком длинное")

    if not re.match(r'^[а-яёА-ЯЁa-zA-Z\s\-\.]+$', city_clean):
        raise ValidationError("Название города содержит недопустимые символы")

    return city_clean


def validate_sex(sex: Any) -> int:
    """
    Валидирует пол пользователя
    """
    try:
        sex_int = int(sex)
        if sex_int not in (0, 1, 2):
            raise ValidationError(f"Пол должен быть 0, 1 или 2: {sex}")
        return sex_int
    except (ValueError, TypeError):
        raise ValidationError(f"Пол должен быть числом: {sex}")


def parse_vk_date(bdate: Optional[str]) -> Optional[Tuple[int, int, int]]:
    """
    Парсит дату рождения из формата ВКонтакте
    """
    if not bdate:
        return None

    try:
        parts = bdate.split('.')
        if len(parts) >= 2:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2]) if len(parts) == 3 else None
            
            if year:
                return (year, month, day)
    except (ValueError, IndexError):
        pass

    return None


def calculate_age(bdate: Optional[str]) -> Optional[int]:
    """
    Вычисляет возраст из даты рождения ВКонтакте
    """
    date_parts = parse_vk_date(bdate)
    if not date_parts or len(date_parts) != 3:
        return None
    
    birth_year, birth_month, birth_day = date_parts
    today = datetime.now()

    age = today.year - birth_year
    if (today.month, today.day) < (birth_month, birth_day):
        age -= 1

    return age


def format_user_profile(user_data: Dict[str, Any], photos: List[Tuple[str, int]]) -> Tuple[str, str]:
    """
    Форматирует профиль пользователя для отправки
    """
    first_name = user_data.get('first_name', '')
    last_name = user_data.get('last_name', '')
    profile_link = user_data.get('profile_link', '')

    message = (
        f"👤 {first_name} {last_name}\n"
        f"🔗 Профиль: {profile_link}\n"
        f"📸 Топ-{len(photos)} фотографии:"
    )

    attachment = ','.join([photo[0] for photo in photos])

    return message, attachment


def format_favorites_list(favorites: List[Tuple]) -> str:
    """
    Форматирует список избранных для отправки
    """
    if not favorites:
        return "📝 В избранном пока никого нет"

    message = "⭐ Ваши избранные:\n\n"
    for i, (vk_id, first_name, last_name, profile_link) in enumerate(favorites, 1):
        message += f"{i}. {first_name} {last_name}\n🔗 {profile_link}\n\n"

    return message.strip()


def create_profile_link(vk_id: int, domain: Optional[str] = None) -> str:
    """
    Создает ссылку на профиль ВКонтакте
    """
    if domain and domain != f"id{vk_id}":
        return f"https://vk.com/{domain}"
    else:
        return f"https://vk.com/id{vk_id}"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Разбивает список на chunks указанного размера
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def safe_json_request(url: str, params: Dict[str, Any],
                            session: aiohttp.ClientSession,
                            timeout: int = 30) -> Dict[str, Any]:
    """
    Безопасно выполняет JSON запрос с обработкой ошибок
    """
    try:
        async with session.get(url, params=params, timeout=timeout) as response:
            if response.status != 200:
                raise VKAPIError(f"HTTP error {response.status}: {await response.text()}")
            
            data = await response.json()
            if 'error' in data:
                error_msg = data['error'].get('error_msg', 'Unknown VK error')
                raise VKAPIError(f"VK API error: {error_msg}")

            return data

    except asyncio.TimeoutError:
        raise VKAPIError("Request timeout")
    except aiohttp.ClientError as e:
        raise VKAPIError(f"Network error: {e}")
    except json.JSONDecodeError as e:
        raise VKAPIError(f"JSON decode error: {e}")


async def safe_close(connection: Any) -> None:
    """Безопасно закрывает соединение с обработкой ошибок"""
    try:
        if hasattr(connection, 'close'):
            if hasattr(connection.close, '__call__'):
                if hasattr(connection.close, '__await__'):
                    await connection.close()
                else:
                    connection.close()
    except Exception as e:
        logger.warning(f"Ошибка при закрытии соединения: {e}")


def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Конвертирует dataclass объект в словарь
    """
    if is_dataclass(obj):
        return asdict(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise ValueError("Object is not a dataclass or doesn't have __dict__")


def format_timedelta(delta: timedelta) -> str:
    """
    Форматирует timedelta в читаемый вид
    """
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}ч {minutes}м"
    elif minutes > 0:
        return f"{minutes}м {seconds}с"
    else:
        return f"{seconds}с"


class RateLimiter:
    """
    Класс для ограничения частоты запросов
    """
    def __init__(self, max_requests: int, period: float):
        self.max_requests = max_requests
        self.period = period
        self.requests = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Получает разрешение на выполнение запроса"""
        async with self.lock:
            now = datetime.now()

            self.requests = [req_time for req_time in self.requests
                             if (now - req_time).total_seconds() < self.period]

            if len(self.requests) >= self.max_requests:
                oldest_request = self.requests[0]
                wait_time = self.period - (now - oldest_request).total_seconds()
                await asyncio.sleep(wait_time)

                now = datetime.now()
                self.requests = [req_time for req_time in self.requests
                                 if (now - req_time).total_seconds() < self.period]

            self.requests.append(now)


class DatabaseConnectionPool:
    """
    Простой пул соединений с базой данных
    """
    def __init__(self, dsn: str, max_size: int = 10):
        self.dsn = dsn
        self.max_size = max_size
        self.pool = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Инициализирует пул соединений"""
        if self.pool is None:
            async with self._lock:
                if self.pool is None:
                    self.pool = await asyncpg.create_pool(
                        dsn=self.dsn,
                        min_size=1,
                        max_size=self.max_size,
                        command_timeout=60
                    )

    async def acquire(self):
        """Получает соединение из пула"""
        if self.pool is None:
            await self.initialize()
        return await self.pool.acquire()

    async def release(self, connection):
        """Возвращает соединение в пул"""
        if self.pool:
            await self.pool.release(connection)

    async def close(self):
        """Закрывает пул соединений"""
        if self.pool:
            await self.pool.close()
            self.pool = None


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Настраивает логирование для приложения
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def with_error_handling(func):
    """
    Декоратор для обработки ошибок и восстановления состояния
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except VKAPIError as e:
            logger.error(f"VK API Error in {func.__name__}: {e}")
            raise
        except DatabaseError as e:
            logger.error(f"Database Error in {func.__name__}: {e}")
            raise
        except ValidationError as e:
            logger.warning(f"Validation Error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected Error in {func.__name__}: {e}")
            raise

    return wrapper

# Убираем проблемную функцию recover_state, так как она требует конкретных импортов
# Вместо этого создадим общую функцию восстановления


async def recover_user_state(user_id: int, state_handler: Any) -> Any:
    """
    Восстанавливает состояние пользователя после ошибки (общая версия)
    """
    try:
        if hasattr(state_handler, 'get_user_state'):
            state_data = await state_handler.get_user_state(user_id)
            return state_data
        return None
    except Exception as e:
        logger.error(f"Error recovering state for user {user_id}: {e}")
        return None


# Синонимы для обратной совместимости
validate_vk_id = validate_vk_user_id
format_profile = format_user_profile
format_favorites = format_favorites_list
