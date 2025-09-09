"""
Фабрика для создания и управления сервисами
"""

from database.repository import DatabaseRepository
from services.vk_service import VKService
from services.user_service import UserService
from services.search_service import SearchService
from services.favorite_service import FavoriteService


class ServiceFactory:
    _instance = None
    _vk_service = None
    _db_repository = None
    _user_service = None
    _search_service = None
    _favorite_service = None
    _state_handler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_vk_service(cls) -> VKService:
        """Возвращает экземпляр VKService"""
        if cls._vk_service is None:
            cls._vk_service = VKService()
        return cls._vk_service

    @classmethod
    def get_db_repository(cls) -> DatabaseRepository:
        """Возвращает экземпляр DatabaseRepository"""
        if cls._db_repository is None:
            cls._db_repository = DatabaseRepository()
        return cls._db_repository

    @classmethod
    def get_user_service(cls) -> UserService:
        """Возвращает экземпляр UserService"""
        if cls._user_service is None:
            cls._user_service = UserService(
                db_repository=cls.get_db_repository(),
                vk_service=cls.get_vk_service()
            )
        return cls._user_service

    @classmethod
    def get_search_service(cls) -> SearchService:
        """Возвращает экземпляр SearchService"""
        if cls._search_service is None:
            cls._search_service = SearchService(
                vk_service=cls.get_vk_service(),
                db_repository=cls.get_db_repository()
            )
        return cls._search_service

    @classmethod
    def get_favorite_service(cls) -> FavoriteService:
        """Возвращает экземпляр FavoriteService"""
        if cls._favorite_service is None:
            cls._favorite_service = FavoriteService(
                db_repository=cls.get_db_repository()
            )
        return cls._favorite_service

    @classmethod
    async def shutdown(cls):
        """Корректно завершает работу всех сервисов"""
        if cls._db_repository:
            cls._db_repository.close()

        cls._vk_service = None
        cls._db_repository = None
        cls._user_service = None
        cls._search_service = None