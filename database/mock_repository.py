import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import json

from database.models import VKUser, UserPhoto, UserState

# Настройка логгера
logger = logging.getLogger(__name__)


class MockDatabaseRepository:
    """Заглушка для базы данных, работающая в памяти"""
    
    def __init__(self):
        # Хранилища данных в памяти (словари и списки)
        self.users = {}             # Пользователи {vk_id: VKUser}
        self.photos = {}            # Фото пользователей {vk_id: [UserPhoto]}
        self.favorites = {}         # Избранные пользователи {user_vk_id: set(vk_ids)}
        self.user_states = {}       # Состояния пользователей {vk_id: UserState}
        self.search_history = []    # История поиска [{...}, {...}]
        self.found_users = {}       # Найденные пользователи {vk_id: dict}
        self.viewed_profiles = {}   # Просмотренные профили {user_id: [vk_ids]}
        self.conn = self            # Заглушка для conn (имитация подключения к БД)
        logger.info("Mock database repository initialized")
    
    def cursor(self):
        """Заглушка для cursor метода (возвращает объект MockCursor)"""
        return MockCursor()
    
    def add_found_user(self, user_data: dict) -> bool:
        """Добавляет найденного пользователя"""
        try:
            vk_id = user_data.get('vk_id')
            if vk_id:
                self.found_users[vk_id] = user_data
                logger.info(f"Found user {vk_id} added to mock database")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding found user: {e}")
            return False
    
    def get_found_user(self, vk_id: int) -> Optional[dict]:
        """Получает найденного пользователя"""
        return self.found_users.get(vk_id)

    def add_or_update_user(self, user: VKUser) -> bool:
        """Добавляет или обновляет пользователя"""
        try:
            self.users[user.vk_id] = user
            logger.info(f"User {user.vk_id} added/updated in mock database")
            return True
        except Exception as e:
            logger.error(f"Error adding/updating user: {e}")
            return False

    def get_user_by_vk_id(self, vk_id: int) -> Optional[VKUser]:
        """Получает пользователя по vk_id"""
        return self.users.get(vk_id)

    def add_user_photos(self, vk_id: int, photos: List[UserPhoto]) -> bool:
        """Добавляет фото пользователю"""
        try:
            if vk_id not in self.photos:
                self.photos[vk_id] = []
            self.photos[vk_id].extend(photos)
            logger.info(f"Added {len(photos)} photos for user {vk_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding photos: {e}")
            return False

    def get_user_photos(self, vk_id: int) -> List[UserPhoto]:
        """Получает фото пользователя"""
        return self.photos.get(vk_id, [])

    def add_to_favorites(self, user_vk_id: int, target_vk_id: int) -> bool:
        """Добавляет пользователя в избранное"""
        try:
            if user_vk_id not in self.favorites:
                self.favorites[user_vk_id] = set()
            self.favorites[user_vk_id].add(target_vk_id)
            logger.info(f"User {target_vk_id} added to favorites of {user_vk_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            return False

    def remove_from_favorites(self, user_vk_id: int, target_vk_id: int) -> bool:
        """Удаляет пользователя из избранного"""
        try:
            if user_vk_id in self.favorites:
                self.favorites[user_vk_id].discard(target_vk_id)
                logger.info(f"User {target_vk_id} removed from favorites of {user_vk_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing from favorites: {e}")
            return False

    def get_user_favorites(self, user_vk_id: int) -> List[int]:
        """Возвращает список ID избранных"""
        return list(self.favorites.get(user_vk_id, set()))
    
    def get_favorites(self, user_vk_id: int) -> List[Tuple]:
        """Возвращает список избранных в формате (vk_id, first_name, last_name, profile_link)"""
        favorite_ids = self.get_user_favorites(user_vk_id)
        result = []
        for fav_id in favorite_ids:
            # Ищем пользователя среди найденных
            user_data = self.found_users.get(fav_id)
            if user_data:
                result.append((
                    fav_id,
                    user_data.get('first_name', 'Unknown'),
                    user_data.get('last_name', ''),
                    f"https://vk.com/id{fav_id}"
                ))
        return result

    def is_in_favorites(self, user_vk_id: int, target_vk_id: int) -> bool:
        """Проверяет, есть ли пользователь в избранном"""
        return target_vk_id in self.favorites.get(user_vk_id, set())

    def set_user_state(self, vk_id: int, state: UserState) -> bool:
        """Устанавливает состояние пользователя"""
        try:
            self.user_states[vk_id] = state
            logger.info(f"State set for user {vk_id}: {state.state}")
            return True
        except Exception as e:
            logger.error(f"Error setting user state: {e}")
            return False

    def get_user_state(self, vk_id: int) -> Optional[UserState]:
        """Получает состояние пользователя"""
        return self.user_states.get(vk_id)

    def update_user_state(self, user_id: int, state: str, state_data: Optional[dict] = None) -> bool:
        """Обновляет состояние пользователя (эмуляция записи в БД)"""
        try:
            user_state = UserState(
                state_id=user_id,             # Подставляем user_id как state_id
                vk_user_id=user_id,
                current_state=state,
                state_data=json.dumps(state_data) if state_data else None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.user_states[user_id] = user_state
            logger.info(f"User state for {user_id} updated to {state} in mock database")
            return True
        except Exception as e:
            logger.error(f"Error updating user state: {e}")
            return False

    def delete_user_state(self, vk_id: int) -> bool:
        """Удаляет состояние пользователя"""
        try:
            if vk_id in self.user_states:
                del self.user_states[vk_id]
                logger.info(f"State deleted for user {vk_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user state: {e}")
            return False

    def add_search_history(self, user_vk_id: int, target_vk_id: int, action: str) -> bool:
        """Добавляет запись в историю поиска"""
        try:
            self.search_history.append({
                'user_vk_id': user_vk_id,
                'target_vk_id': target_vk_id,
                'action': action,
                'timestamp': datetime.now()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding search history: {e}")
            return False

    def get_search_history(self, user_vk_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает историю поиска пользователя (по времени, с ограничением limit)"""
        user_history = [h for h in self.search_history if h['user_vk_id'] == user_vk_id]
        return sorted(user_history, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def add_to_viewed(self, user_id: int, viewed_vk_id: int) -> bool:
        """Добавляет пользователя в список просмотренных"""
        try:
            if user_id not in self.viewed_profiles:
                self.viewed_profiles[user_id] = []
            if viewed_vk_id not in self.viewed_profiles[user_id]:
                self.viewed_profiles[user_id].append(viewed_vk_id)
                logger.info(f"User {viewed_vk_id} added to viewed list of {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding to viewed: {e}")
            return False

    def get_viewed_users(self, user_id: int) -> List[int]:
        """Получает список ID просмотренных пользователей"""
        try:
            return self.viewed_profiles.get(user_id, [])
        except Exception as e:
            logger.error(f"Error getting viewed users: {e}")
            return []

    def add_user_rating(self, user_id: int, rated_vk_id: int, rating_type: str) -> bool:
        """Добавляет оценку (лайк, дизлайк, бан)"""
        try:
            if not hasattr(self, 'user_ratings'):
                self.user_ratings = {}
            
            if user_id not in self.user_ratings:
                self.user_ratings[user_id] = {}
            
            self.user_ratings[user_id][rated_vk_id] = {
                'rating_type': rating_type,
                'timestamp': datetime.now()
            }
            
            logger.info(f"User {user_id} rated {rated_vk_id} as {rating_type}")
            return True
        except Exception as e:
            logger.error(f"Error adding user rating: {e}")
            return False

    def get_user_rating(self, user_id: int, rated_vk_id: int) -> Optional[str]:
        """Получает оценку пользователя для конкретного профиля"""
        try:
            if not hasattr(self, 'user_ratings'):
                return None
            user_ratings = self.user_ratings.get(user_id, {})
            rating_data = user_ratings.get(rated_vk_id)
            return rating_data['rating_type'] if rating_data else None
        except Exception as e:
            logger.error(f"Error getting user rating: {e}")
            return None

    def close(self):
        """Закрытие соединения (для совместимости)"""
        logger.info("Mock database repository closed")
        pass

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие"""
        self.close()


class MockCursor:
    """Заглушка для курсора базы данных"""
    
    def execute(self, query, params=None):
        """Эмуляция выполнения SQL-запроса"""
        logger.debug(f"Mock cursor executing: {query}")
        return True
    
    def fetchone(self):
        """Эмуляция получения одной строки результата"""
        return (1,)
    
    def fetchall(self):
        """Эмуляция получения всех строк результата"""
        return [(1,)]
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие"""
        pass
