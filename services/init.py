"""
Services package for VKinder Bot
"""

from .vk_service import VKService
from .user_service import UserService
from .search_service import SearchService
from .favorite_service import FavoriteService  # Добавляем импорт
from .service_factory import ServiceFactory

__all__ = [
    'VKService', 
    'UserService', 
    'SearchService', 
    'FavoriteService',  # Добавляем
    'ServiceFactory'
]