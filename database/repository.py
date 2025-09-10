# Импортируем стандартный модуль логирования для вывода ошибок и служебной информации
import logging

# Импортируем библиотеку psycopg2 для работы с PostgreSQL
import psycopg2
from psycopg2 import sql   # Модуль sql позволяет безопасно собирать SQL-запросы

# Импортируем типы для аннотаций
from typing import List, Optional, Tuple, Dict, Any

# Импортируем datetime для работы с временными метками
from datetime import datetime

# Импортируем json для сериализации/десериализации словарей в строку
import json

# Импортируем конфигурацию из настроек (переменные БД)
from config.settings import config

# Импортируем модели данных (описанные через dataclass)
from database.models import VKUser, UserPhoto, UserState

# Создаём логгер для текущего модуля
logger = logging.getLogger(__name__)


# Основной класс-репозиторий для работы с PostgreSQL
class DatabaseRepository:
    def __init__(self):
        # При инициализации сразу создаём соединение с базой
        self.conn = self._create_connection()

    # Внутренний метод для подключения к PostgreSQL
    def _create_connection(self):
        try:
            return psycopg2.connect(
                dbname=config.DATABASE.NAME,     # Имя базы
                user=config.DATABASE.USER,       # Пользователь
                password=config.DATABASE.PASSWORD, # Пароль
                host=config.DATABASE.HOST,       # Хост
                port=config.DATABASE.PORT        # Порт
            )
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise   # Пробрасываем ошибку дальше


    # Добавление или обновление пользователя в таблице vk_bot_users
    def add_or_update_user(self, user: VKUser) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vk_bot_users 
                    (vk_user_id, first_name, last_name, age, city, sex, profile_link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vk_user_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    age = EXCLUDED.age,
                    city = EXCLUDED.city,
                    sex = EXCLUDED.sex,
                    profile_link = EXCLUDED.profile_link,
                    last_active = CURRENT_TIMESTAMP
                """, (
                    user.vk_id, user.first_name, user.last_name, 
                    user.age, user.city, user.sex, user.profile_link
                ))
                self.conn.commit()  # Фиксируем изменения
                return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            self.conn.rollback()   # Откатываем транзакцию при ошибке
            return False


    # Получение пользователя по vk_id
    def get_user_by_vk_id(self, vk_id: int) -> Optional[VKUser]:
        """Получает пользователя по VK ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT vk_user_id, first_name, last_name, age, city, sex, preferred_sex,
                           profile_link, created_at, last_active
                    FROM vk_bot_users 
                    WHERE vk_user_id = %s
                """, (vk_id,))
                result = cur.fetchone()
                if result:
                    # Преобразуем строку результата в объект VKUser
                    return VKUser(
                        vk_id=result[0],
                        first_name=result[1],
                        last_name=result[2],
                        age=result[3],
                        city=result[4],
                        sex=result[5],
                        preferred_sex=result[6],
                        profile_link=result[7],
                        created_at=result[8],
                        last_active=result[9]
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting user by VK ID {vk_id}: {e}")
            return None


    # Добавление фотографий пользователя (сначала удаляются старые)
    def add_user_photos(self, vk_id: int, photos: List[Tuple[str, int]]) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM vk_user_photos WHERE vk_id = %s", (vk_id,))
                for photo_url, likes_count in photos:
                    cur.execute("""
                        INSERT INTO vk_user_photos (vk_id, photo_url, likes_count)
                        VALUES (%s, %s, %s)
                    """, (vk_id, photo_url, likes_count))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding photos: {e}")
            self.conn.rollback()
            return False


    # Получение фото пользователя в виде объектов UserPhoto
    def get_user_photos(self, vk_id: int) -> List[UserPhoto]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT photo_id, vk_id, photo_url, likes_count, created_at
                    FROM vk_user_photos 
                    WHERE vk_id = %s 
                    ORDER BY likes_count DESC
                """, (vk_id,))
                return [UserPhoto(*row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting photos: {e}")
            return []


    # Добавление пользователя в избранное
    def add_to_favorites(self, user_id: int, favorite_vk_id: int) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO favorites (vk_user_id, favorite_vk_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (user_id, favorite_vk_id))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            self.conn.rollback()
            return False


    # Получение списка избранных с базовыми данными
    def get_favorites(self, user_id: int) -> List[Tuple]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT fv.vk_id, fv.first_name, fv.last_name, fv.profile_link
                    FROM favorites f
                    JOIN vk_found_users fv ON f.favorite_vk_id = fv.vk_id
                    WHERE f.vk_user_id = %s
                    ORDER BY f.created_at DESC
                """, (user_id,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            return []


    # Добавление просмотренного профиля
    def add_to_viewed(self, user_id: int, viewed_vk_id: int) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO viewed_profiles (vk_user_id, viewed_vk_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (user_id, viewed_vk_id))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding to viewed: {e}")
            self.conn.rollback()
            return False


    # Получение списка просмотренных профилей
    def get_viewed_users(self, user_id: int) -> List[int]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT viewed_vk_id FROM viewed_profiles 
                    WHERE vk_user_id = %s
                """, (user_id,))
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting viewed users: {e}")
            return []


    # Обновление состояния пользователя
    def update_user_state(self, user_id: int, state: str, state_data: Optional[dict] = None) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_states (vk_user_id, current_state, state_data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (vk_user_id) DO UPDATE SET
                    current_state = EXCLUDED.current_state,
                    state_data = EXCLUDED.state_data,
                    updated_at = CURRENT_TIMESTAMP
                """, (user_id, state, json.dumps(state_data) if state_data else None))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user state: {e}")
            self.conn.rollback()
            return False


    # Получение текущего состояния пользователя
    def get_user_state(self, user_id: int) -> Optional[UserState]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT state_id, vk_user_id, current_state, state_data, created_at, updated_at
                    FROM user_states 
                    WHERE vk_user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                return UserState(*result) if result else None
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            return None


    # Сохранение пользовательских предпочтений
    def save_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Сохраняет настройки поиска пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM user_preferences WHERE user_id = %s", (user_id,))
                if cur.fetchone():
                    cur.execute("""
                        UPDATE user_preferences 
                        SET preferences = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """, (json.dumps(preferences), user_id))
                else:
                    cur.execute("""
                        INSERT INTO user_preferences (user_id, preferences)
                        VALUES (%s, %s)
                    """, (user_id, json.dumps(preferences)))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
            self.conn.rollback()
            return False


    # Получение пользовательских предпочтений
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает настройки поиска пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT preferences FROM user_preferences WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
                return None
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None


    # Добавление найденного пользователя в таблицу vk_found_users
    def add_found_user(self, user_data: Dict[str, Any]) -> bool:
        """Добавляет найденного пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO vk_found_users (vk_id, first_name, last_name, age, city, sex, profile_link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vk_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    age = EXCLUDED.age,
                    city = EXCLUDED.city,
                    sex = EXCLUDED.sex,
                    profile_link = EXCLUDED.profile_link,
                    last_updated = CURRENT_TIMESTAMP
                ''', (
                    user_data['vk_id'], 
                    user_data['first_name'], 
                    user_data['last_name'],
                    user_data.get('age'),
                    user_data.get('city'),
                    user_data.get('sex'),
                    user_data.get('profile_link')
                ))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding found user: {e}")
            self.conn.rollback()
            return False


    # Получение избранных с дополнительными данными
    def get_favorites_with_details(self, user_id: int) -> List[tuple]:
        """Получает избранных с деталями"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT f.favorite_vk_id, fv.first_name, fv.last_name, 
                           fv.profile_link, f.created_at, f.notes
                    FROM favorites f
                    JOIN vk_found_users fv ON f.favorite_vk_id = fv.vk_id
                    WHERE f.vk_user_id = %s
                    ORDER BY f.created_at DESC
                """, (user_id,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting favorites with details: {e}")
            return []


    # Удаление пользователя из избранных
    def remove_from_favorites(self, user_id: int, favorite_vk_id: int) -> bool:
        """Удаляет из избранного"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM favorites 
                    WHERE vk_user_id = %s AND favorite_vk_id = %s
                """, (user_id, favorite_vk_id))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing from favorites: {e}")
            self.conn.rollback()
            return False


    # Обновление заметок для избранного профиля
    def update_favorite_notes(self, user_id: int, favorite_vk_id: int, notes: str) -> bool:
        """Обновляет заметки избранного"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE favorites 
                    SET notes = %s
                    WHERE vk_user_id = %s AND favorite_vk_id = %s
                """, (notes, user_id, favorite_vk_id))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating favorite notes: {e}")
            self.conn.rollback()
            return False


    # Получение информации о найденном пользователе
    def get_found_user(self, vk_id: int) -> Optional[tuple]:
        """Получает пользователя из найденных"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT vk_id, first_name, last_name, profile_link
                    FROM vk_found_users 
                    WHERE vk_id = %s
                """, (vk_id,))
                return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting found user: {e}")
            return None


    # Получение фотографий пользователя
    def get_user_photos(self, vk_id: int) -> List[tuple]:
        """Получает фотографии пользователя"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT photo_url, likes_count 
                    FROM vk_user_photos 
                    WHERE vk_id = %s 
                    ORDER BY likes_count DESC
                """, (vk_id,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting user photos: {e}")
            return []


    # Добавление или обновление оценки пользователя (лайк/дизлайк/чёрный список)
    def add_user_rating(self, user_id: int, rated_vk_id: int, rating_type: str) -> bool:
        """Добавляет оценку пользователя (лайк, дизлайк, черный список)"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_ratings (vk_user_id, rated_vk_id, rating_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (vk_user_id, rated_vk_id) 
                    DO UPDATE SET rating_type = EXCLUDED.rating_type, created_at = CURRENT_TIMESTAMP
                """, (user_id, rated_vk_id, rating_type))
                self.conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding user rating: {e}")
            self.conn.rollback()
            return False


    # Получение оценки пользователя для конкретного профиля
    def get_user_rating(self, user_id: int, rated_vk_id: int) -> Optional[str]:
        """Получает оценку пользователя для конкретного профиля"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT rating_type FROM user_ratings 
                    WHERE vk_user_id = %s AND rated_vk_id = %s
                """, (user_id, rated_vk_id))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user rating: {e}")
            return None


    # Получение всех пользователей, которым текущий поставил оценки
    def get_rated_users(self, user_id: int, rating_type: str = None) -> List[int]:
        """Получает список оцененных пользователей"""
        try:
            with self.conn.cursor() as cur:
                if rating_type:
                    cur.execute("""
                        SELECT rated_vk_id FROM user_ratings 
                        WHERE vk_user_id = %s AND rating_type = %s
                    """, (user_id, rating_type))
                else:
                    cur.execute("""
                        SELECT rated_vk_id FROM user_ratings 
                        WHERE vk_user_id = %s
                    """, (user_id,))
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting rated users: {e}")
            return []


    # Получение всех пользователей из чёрного списка
    def get_blacklisted_users(self, user_id: int) -> List[int]:
        """Получает список пользователей в черном списке"""
        return self.get_rated_users(user_id, 'blacklist')


    # Закрытие соединения с базой данных
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
