"""
Сервис для работы с избранными пользователями
"""

import logging
import json  # Добавляем импорт json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# from database.repository import DatabaseRepository  # Используем ServiceFactory
from utils import async_retry, ValidationError

logger = logging.getLogger(__name__)

class FavoriteService:
    def __init__(self, db_repository):
        self.db_repository = db_repository
    
    @async_retry(max_attempts=3, delay=1.0)
    async def add_to_favorites(self, user_id: int, favorite_vk_id: int, 
                             notes: Optional[str] = None) -> bool:
        """
        Добавляет пользователя в избранное
        
        Args:
            user_id: ID пользователя бота
            favorite_vk_id: ID пользователя ВКонтакте
            notes: Заметки пользователя
            
        Returns:
            bool: True если успешно добавлено
        """
        try:
            # Проверяем, существует ли пользователь в найденных
            favorite_user = self.db_repository.get_found_user(favorite_vk_id)
            if not favorite_user:
                logger.warning(f"Пользователь {favorite_vk_id} не найден в БД")
                # Все равно пытаемся добавить, возможно пользователь был найден ранее
                pass
            
            # Добавляем в избранное
            success = self.db_repository.add_to_favorites(user_id, favorite_vk_id)
            
            if success and notes:
                # Сохраняем заметки
                self._update_favorite_notes(user_id, favorite_vk_id, notes)
            
            if success:
                logger.info(f"Пользователь {favorite_vk_id} добавлен в избранное user_id {user_id}")
            else:
                logger.warning(f"Не удалось добавить пользователя {favorite_vk_id} в избранное")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении в избранное: {e}")
            return False
    
    async def remove_from_favorites(self, user_id: int, favorite_vk_id: int) -> bool:
        """
        Удаляет пользователя из избранного
        
        Args:
            user_id: ID пользователя бота
            favorite_vk_id: ID пользователя ВКонтакте
            
        Returns:
            bool: True если успешно удалено
        """
        try:
            success = self.db_repository.remove_from_favorites(user_id, favorite_vk_id)
            
            if success:
                logger.info(f"Пользователь {favorite_vk_id} удален из избранного user_id {user_id}")
            else:
                logger.warning(f"Пользователь {favorite_vk_id} не найден в избранном user_id {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при удалении из избранного: {e}")
            return False
    
    async def get_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получает список избранных пользователей с деталями
        
        Args:
            user_id: ID пользователя бота
            
        Returns:
            List[Dict[str, Any]]: Список избранных с деталями
        """
        try:
            favorites = self.db_repository.get_favorites_with_details(user_id)
            
            result = []
            for fav in favorites:
                # fav: (vk_id, first_name, last_name, profile_link, created_at, notes)
                favorite_data = {
                    'vk_id': fav[0],
                    'first_name': fav[1],
                    'last_name': fav[2],
                    'profile_link': fav[3],
                    'added_at': fav[4],
                    'notes': fav[5] if len(fav) > 5 else None,
                    'photos': self.db_repository.get_user_photos(fav[0])
                }
                result.append(favorite_data)
            
            logger.info(f"Получено {len(result)} избранных для user_id {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении избранного: {e}")
            return []
    
    async def get_favorites_basic(self, user_id: int) -> List[Tuple]:
        """
        Получает базовый список избранных (только ID и names)
        
        Args:
            user_id: ID пользователя бота
            
        Returns:
            List[Tuple]: Список избранных в формате (vk_id, first_name, last_name, profile_link)
        """
        try:
            return self.db_repository.get_favorites(user_id)
        except Exception as e:
            logger.error(f"Ошибка при получении базового списка избранных: {e}")
            return []
    
    async def update_favorite_notes(self, user_id: int, favorite_vk_id: int, 
                                  notes: str) -> bool:
        """
        Обновляет заметки для избранного пользователя
        
        Args:
            user_id: ID пользователя бота
            favorite_vk_id: ID пользователя ВКонтакте
            notes: Новые заметки
            
        Returns:
            bool: True если успешно обновлено
        """
        try:
            success = self._update_favorite_notes(user_id, favorite_vk_id, notes)
            
            if success:
                logger.info(f"Заметки для пользователя {favorite_vk_id} обновлены")
            else:
                logger.warning(f"Не удалось обновить заметки для пользователя {favorite_vk_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении заметки: {e}")
            return False
    
    def _update_favorite_notes(self, user_id: int, favorite_vk_id: int, notes: str) -> bool:
        """
        Внутренний метод для обновления заметок
        
        Args:
            user_id: ID пользователя бота
            favorite_vk_id: ID пользователя ВКонтакте
            notes: Новые заметки
            
        Returns:
            bool: True если успешно обновлено
        """
        return self.db_repository.update_favorite_notes(user_id, favorite_vk_id, notes)
    
    async def is_favorite(self, user_id: int, vk_id: int) -> bool:
        """
        Проверяет, находится ли пользователь в избранном
        
        Args:
            user_id: ID пользователя бота
            vk_id: ID пользователя ВКонтакте
            
        Returns:
            bool: True если пользователь в избранном
        """
        try:
            favorites = await self.get_favorites_basic(user_id)
            return any(fav[0] == vk_id for fav in favorites)
        except Exception as e:
            logger.error(f"Ошибка при проверке избранного: {e}")
            return False
    
    async def get_favorite_count(self, user_id: int) -> int:
        """
        Получает количество избранных пользователей
        
        Args:
            user_id: ID пользователя бота
            
        Returns:
            int: Количество избранных
        """
        try:
            favorites = await self.get_favorites_basic(user_id)
            return len(favorites)
        except Exception as e:
            logger.error(f"Ошибка при получении количества избранных: {e}")
            return 0
    
    async def clear_favorites(self, user_id: int) -> bool:
        """
        Очищает все избранное пользователя
        
        Args:
            user_id: ID пользователя бота
            
        Returns:
            bool: True если успешно очищено
        """
        try:
            # Получаем все избранные
            favorites = await self.get_favorites_basic(user_id)
            
            # Удаляем каждую запись
            success_count = 0
            for fav in favorites:
                if self.db_repository.remove_from_favorites(user_id, fav[0]):
                    success_count += 1
            
            logger.info(f"Очищено {success_count} из {len(favorites)} избранных для user_id {user_id}")
            return success_count == len(favorites)
            
        except Exception as e:
            logger.error(f"Ошибка при очистке избранного: {e}")
            return False
    
    async def export_favorites(self, user_id: int) -> Optional[str]:
        """
        Экспортирует избранное в формате JSON
        
        Args:
            user_id: ID пользователя бота
            
        Returns:
            Optional[str]: JSON строка с избранными или None
        """
        try:
            favorites = await self.get_favorites(user_id)
            
            # Форматируем данные для экспорта
            export_data = []
            for fav in favorites:
                export_data.append({
                    'vk_id': fav['vk_id'],
                    'name': f"{fav['first_name']} {fav['last_name']}",
                    'profile_url': fav['profile_link'],
                    'added_date': fav['added_at'].isoformat() if fav['added_at'] else None,
                    'notes': fav['notes'],
                    'photos_count': len(fav['photos']) if fav['photos'] else 0
                })
            
            return json.dumps(export_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте избранного: {e}")
            return None
    
    async def search_in_favorites(self, user_id: int, search_term: str) -> List[Dict[str, Any]]:
        """
        Ищет в избранных по имени или заметкам
        
        Args:
            user_id: ID пользователя бота
            search_term: Поисковый запрос
            
        Returns:
            List[Dict[str, Any]]: Найденные избранные
        """
        try:
            favorites = await self.get_favorites(user_id)
            search_lower = search_term.lower()
            
            results = []
            for fav in favorites:
                # Поиск по имени
                name_match = (
                    search_lower in fav['first_name'].lower() or
                    search_lower in fav['last_name'].lower() or
                    search_lower in f"{fav['first_name']} {fav['last_name']}".lower()
                )
                
                # Поиск по заметкам
                notes_match = (
                    fav['notes'] and 
                    search_lower in fav['notes'].lower()
                )
                
                if name_match or notes_match:
                    results.append(fav)
            
            logger.info(f"Найдено {len(results)} избранных по запросу '{search_term}'")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске в избранном: {e}")
            return []