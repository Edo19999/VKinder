import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def safe_int(value, default=0):
    """Безопасно преобразует в int"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        logger.warning(f"Не удалось преобразовать '{value}' в int, используется значение по умолчанию {default}")
        return default

@dataclass
class DatabaseConfig:
    NAME: str = os.getenv('DB_NAME', 'vkinder_bot_vk')
    USER: str = os.getenv('DB_USER', 'postgres')
    PASSWORD: str = os.getenv('DB_PASSWORD', '')
    HOST: str = os.getenv('DB_HOST', 'localhost')
    PORT: int = safe_int(os.getenv('DB_PORT'), 5432)

@dataclass
class VKConfig:
    USER_TOKEN: str = os.getenv('VK_USER_TOKEN')
    GROUP_TOKEN: str = os.getenv('VK_GROUP_TOKEN')
    GROUP_ID: int = safe_int(os.getenv('VK_GROUP_ID'), 0)
    API_VERSION: str = '5.131'
    SEARCH_LIMIT: int = 100
    PHOTOS_LIMIT: int = 3
    MAX_AGE_DIFFERENCE: int = 5

@dataclass
class AppConfig:
    DATABASE: DatabaseConfig = field(default_factory=DatabaseConfig)  # Исправлено здесь
    VK: VKConfig = field(default_factory=VKConfig)  # И здесь
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

config = AppConfig()