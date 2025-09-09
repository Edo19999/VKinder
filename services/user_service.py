"""
Сервис для работы с пользователями бота
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

# from database.repository import DatabaseRepository  # Используем ServiceFactory
from services.vk_service import VKService


logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db_repository, vk_service: VKService):
        self.db_repository = db_repository
        self.vk_service = vk_service

    def process_user(self, user_id: int):
        """Обрабатывает пользователя: получает и сохраняет информацию"""
        # Сначала проверяем, есть ли пользователь в базе данных
        existing_user = self.db_repository.get_user_by_vk_id(user_id)
        logger.info(f"Existing user from DB: {existing_user}")
        
        # Получаем актуальные данные из VK API
        vk_user_info = self.vk_service.get_user_info(user_id)
        if not vk_user_info:
            return existing_user if existing_user else None
        
        logger.info(f"VK user info: {vk_user_info}")

        # Если пользователь уже есть в БД, объединяем данные
        if existing_user:
            logger.info(f"Merging data - existing age: {existing_user.age}, vk age: {vk_user_info.age}")
            # Сохраняем введённые пользователем данные (возраст, город, пол)
            if existing_user.age is not None:
                vk_user_info.age = existing_user.age
                logger.info(f"Set age from existing user: {existing_user.age}")
            if existing_user.city and existing_user.city != vk_user_info.city:
                vk_user_info.city = existing_user.city
                logger.info(f"Set city from existing user: {existing_user.city}")
            if existing_user.sex is not None and existing_user.sex != vk_user_info.sex:
                vk_user_info.sex = existing_user.sex
                logger.info(f"Set sex from existing user: {existing_user.sex}")

        logger.info(f"Final user info before save: {vk_user_info}")
        # Сохраняем обновлённые данные в БД
        success = self.db_repository.add_or_update_user(vk_user_info)
        if not success:
            logger.warning(f"Failed to save user {user_id} to database")

        return vk_user_info

    def find_next_match(self, user_id: int, user_info) -> Optional[Dict[str, Any]]:
        """Находит следующего подходящего пользователя"""
        if not user_info.age or not user_info.city or not user_info.sex:
            return None

        # Получаем уже просмотренных пользователей
        viewed_users = self.db_repository.get_viewed_users(user_id)

        # Ищем новых пользователей
        found_users = self.vk_service.search_users(
            user_info.age, user_info.sex, user_info.city, len(viewed_users)
        )

        for user in found_users:
            if user['id'] not in viewed_users:
                # Получаем фотографии
                photos = self.vk_service.get_top_photos(user['id'])

                if photos:
                    # Сохраняем найденного пользователя
                    found_user_data = {
                        'vk_id': user['id'],
                        'first_name': user.get('first_name', ''),
                        'last_name': user.get('last_name', ''),
                        'age': user_info.age,
                        'city': user_info.city,
                        'sex': user_info.sex,
                        'profile_link': self.create_profile_link(user['id'], user.get('domain'))
                    }

                    self.add_found_user(found_user_data)
                    
                    # Сохраняем фотографии пользователя
                    self.db_repository.add_user_photos(user['id'], photos)

                    # Добавляем в просмотренные
                    self.db_repository.add_to_viewed(user_id, user['id'])

                    return {
                        'user': found_user_data,
                        'photos': photos
                    }

        return None

    def add_found_user(self, user_data: Dict[str, Any]) -> bool:
        """Добавляет найденного пользователя в БД"""
        try:
            # Создаем ссылку на профиль (ИСПРАВЛЕННАЯ СТРОКА)
            domain = user_data.get('domain', f"id{user_data['vk_id']}")
            profile_link = f"https://vk.com/{domain}"
            
            # Подготавливаем данные как словарь для repository
            user_db_data = {
                'vk_id': user_data['vk_id'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'age': user_data.get('age'),
                'city': user_data.get('city'),
                'sex': user_data.get('sex'),
                'profile_link': profile_link
            }

            return self.db_repository.add_found_user(user_db_data)

        except Exception as e:
            logger.error(f"Error adding found user: {e}")
            return False

    def add_to_favorites(self, user_id: int, favorite_id: int) -> bool:
        """Добавляет пользователя в избранное"""
        return self.db_repository.add_to_favorites(user_id, favorite_id)

    def get_favorites_list(self, user_id: int) -> List[Tuple]:
        """Получает список избранных"""
        return self.db_repository.get_favorites(user_id)

    def update_user_state(self, user_id: int, state: str, state_data: Optional[dict] = None) -> bool:
        """Обновляет состояние пользователя"""
        return self.db_repository.update_user_state(user_id, state, state_data)

    def get_user_state(self, user_id: int) -> Optional[str]:
        """Получает состояние пользователя"""
        state = self.db_repository.get_user_state(user_id)
        return state.current_state if state else 'main_menu'

    def create_profile_link(self, vk_id: int, domain: Optional[str] = None) -> str:
        """Создает ссылку на профиль ВКонтакте"""
        if domain and domain != f"id{vk_id}":
            return f"https://vk.com/{domain}"
        else:
            return f"https://vk.com/id{vk_id}"
    
    async def update_user_preferences(self, user_id: int, min_age: int = None, max_age: int = None, city: str = None) -> bool:
        """Обновляет предпочтения пользователя для поиска"""
        try:
            # Получаем текущие предпочтения пользователя
            current_preferences = self.db_repository.get_user_preferences(user_id) or {}
            
            # Обновляем предпочтения
            if min_age is not None:
                current_preferences['min_age'] = min_age
            if max_age is not None:
                current_preferences['max_age'] = max_age
            if city is not None:
                current_preferences['city'] = city
            
            # Сохраняем изменения в таблицу user_preferences
            success = self.db_repository.save_user_preferences(user_id, current_preferences)
            if success:
                logger.info(f"Предпочтения пользователя {user_id} обновлены: min_age={min_age}, max_age={max_age}, city={city}")
            else:
                logger.error(f"Ошибка при сохранении предпочтений пользователя {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении предпочтений пользователя {user_id}: {e}")
            return False