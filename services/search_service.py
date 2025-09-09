"""
Сервис для поиска пользователей ВКонтакте
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import async_retry, VKAPIError, RateLimiter, ValidationError, validate_age, validate_city, validate_sex
# from database.repository import DatabaseRepository  # Используем ServiceFactory
from services.vk_service import VKService
from utils.data_models import StateData  # Только один импорт!

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, vk_service: VKService, db_repository):
        self.vk_service = vk_service
        self.db_repository = db_repository
        self.rate_limiter = RateLimiter(max_requests=3, period=1.0)
    
    def get_search_preferences(self, state_data: StateData, user_info=None) -> Dict[str, Any]:
        """
        Извлекает параметры поиска из состояния пользователя
        """
        preferences = state_data.context.get('preferences', {})
        
        # Используем значения по умолчанию, если нет настроек
        age = preferences.get('age', state_data.context.get('age'))
        city = preferences.get('city', state_data.context.get('city'))
        sex = preferences.get('sex', state_data.context.get('sex'))
        
        # Получаем предпочтения по полу из информации о пользователе
        preferred_sex = None
        if user_info and hasattr(user_info, 'preferred_sex'):
            preferred_sex = user_info.preferred_sex
        
        # Валидируем параметры
        if not all([age, city, sex is not None]):
            raise ValidationError("Не все параметры поиска установлены")
        
        search_params = {
            'age': validate_age(age),
            'city': validate_city(city),
            'sex': validate_sex(sex)
        }
        
        # Добавляем предпочтения по полу, если они установлены
        if preferred_sex is not None:
            search_params['preferred_sex'] = preferred_sex
            
        return search_params
    
    def save_search_preferences(self, user_id: int, state_data: StateData, 
                              preferences: Dict[str, Any]) -> bool:
        """
        Сохраняет параметры поиска в состояние пользователя
        """
        try:
            if 'preferences' not in state_data.context:
                state_data.context['preferences'] = {}
            
            state_data.context['preferences'].update(preferences)
            
            # Также сохраняем отдельно для быстрого доступа
            state_data.context['age'] = preferences.get('age')
            state_data.context['city'] = preferences.get('city')
            state_data.context['sex'] = preferences.get('sex')
            
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения preferences: {e}")
            return False
    
    @async_retry(max_attempts=3, delay=1.0)
    async def find_potential_matches(self, user_id: int, search_params: Dict[str, Any], 
                                   offset: int = 0) -> List[Dict[str, Any]]:
        """
        Ищет потенциальных matches для пользователя с учетом offset
        """
        try:
            await self.rate_limiter.acquire()
            
            # Ищем пользователей
            # Если установлены предпочтения по полу, используем их вместо пола пользователя
            search_sex = search_params.get('preferred_sex')
            if search_sex is None or search_sex == 0:  # 0 означает "любой пол"
                search_sex = search_params['sex']
            
            found_users = self.vk_service.search_users(
                age=search_params['age'],
                sex=search_sex,
                city=search_params['city'],
                offset=offset
            )
            
            logger.info(f"Найдено {len(found_users)} пользователей для user_id {user_id}")
            return found_users
            
        except VKAPIError as e:
            logger.error(f"Ошибка API при поиске пользователей: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при поиске: {e}")
            raise
    
    async def get_next_match(self, user_id: int, state_data: StateData) -> Optional[Dict[str, Any]]:
        """
        Получает следующего подходящего пользователя с учетом состояния
        """
        try:
            # Получаем информацию о пользователе для предпочтений
            user_info = self.db_repository.get_user_by_vk_id(user_id)
            
            # Получаем параметры поиска
            search_params = self.get_search_preferences(state_data, user_info)
            
            # Получаем уже просмотренных и оцененных пользователей
            viewed_users = self.db_repository.get_viewed_users(user_id)
            rated_users = self.db_repository.get_rated_users(user_id)
            excluded_users = set(viewed_users + rated_users)
            offset = len(excluded_users)
            
            # Ищем потенциальных matches
            potential_matches = await self.find_potential_matches(
                user_id, search_params, offset
            )
            
            for user in potential_matches:
                if user['id'] not in excluded_users:
                    # Получаем фотографии
                    photos = await self.process_user_photos(user['id'])
                    
                    if photos:
                        # Сохраняем пользователя в БД
                        user_data = {
                            'vk_id': user['id'],
                            'first_name': user.get('first_name', ''),
                            'last_name': user.get('last_name', ''),
                            'age': search_params['age'],
                            'city': search_params['city'],
                            'sex': search_params['sex'],
                            'profile_link': self.vk_service.create_profile_link(
                                user['id'], user.get('domain')
                            )
                        }
                        
                        self.db_repository.add_found_user(user_data)
                        
                        # Добавляем в просмотренные
                        self.db_repository.add_to_viewed(user_id, user['id'])
                        
                        return {
                            'user': user_data,
                            'photos': photos,
                            'search_params': search_params
                        }
            
            return None
            
        except ValidationError as e:
            logger.warning(f"Невалидные параметры поиска для user_id {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении следующего match: {e}")
            return None
    
    async def process_user_photos(self, vk_user_id: int) -> List[tuple]:
        """Обрабатывает фотографии пользователя"""
        try:
            await self.rate_limiter.acquire()
            photos = self.vk_service.get_top_photos(vk_user_id)
            
            if photos:
                self.db_repository.add_user_photos(vk_user_id, photos)
            
            return photos
            
        except VKAPIError as e:
            logger.error(f"Ошибка API при получении фотографий: {e}")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке фотографий: {e}")
            return []
    
    def get_search_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику поиска для пользователя"""
        viewed_count = len(self.db_repository.get_viewed_users(user_id))
        favorites_count = len(self.db_repository.get_favorites(user_id))
        
        return {
            'viewed_profiles': viewed_count,
            'favorites_count': favorites_count,
            'success_rate': favorites_count / viewed_count * 100 if viewed_count > 0 else 0
        }