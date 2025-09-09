from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

# --- Модель пользователя ВКонтакте ---
@dataclass
class VKUser:
    vk_id: int                           # Уникальный идентификатор пользователя ВКонтакте
    first_name: str                      # Имя
    last_name: str                       # Фамилия
    age: Optional[int] = None            # Возраст (может быть неизвестен → None)
    city: Optional[str] = None           # Город (может быть None)
    sex: Optional[int] = None            # Пол (1 - женский, 2 - мужской, 0 или None - неизвестно)
    preferred_sex: Optional[int] = None  # Предпочитаемый пол для поиска (1 - ж, 2 - м, 0 - любой)
    profile_link: Optional[str] = None   # Ссылка на профиль пользователя
    last_active: Optional[datetime] = None  # Дата/время последней активности
    created_at: Optional[datetime] = None   # Когда запись о пользователе была создана в системе

# --- Модель фото пользователя ---
@dataclass
class UserPhoto:
    photo_id: int                        # Уникальный идентификатор фото
    vk_id: int                           # Идентификатор пользователя, которому принадлежит фото
    photo_url: str                       # Ссылка на фото
    likes_count: int                     # Количество лайков у фото
    created_at: datetime                 # Дата/время добавления фото в систему

# --- Модель "Избранное" ---
@dataclass
class Favorite:
    favorite_id: int                     # Уникальный идентификатор записи "избранное"
    user_id: int                         # ID пользователя, у которого есть избранное
    favorite_vk_id: int                  # ID пользователя ВК, который добавлен в избранное
    created_at: datetime                 # Дата/время добавления в избранное

# --- Модель просмотренного профиля ---
@dataclass
class ViewedProfile:
    view_id: int                         # Уникальный идентификатор записи "просмотр"
    user_id: int                         # ID пользователя, который смотрел профиль
    viewed_vk_id: int                    # ID просмотренного пользователя
    created_at: datetime                 # Дата/время просмотра профиля

# --- Модель состояния пользователя (FSM) ---
@dataclass
class UserState:
    state_id: int                        # Уникальный идентификатор состояния
    vk_user_id: int                      # ID пользователя ВК, для которого хранится состояние
    current_state: str                   # Текущее состояние (строкой, например "SEARCHING")
    state_data: Optional[dict] = None    # Доп. данные состояния (словарь, например выбранный фильтр)
    created_at: Optional[datetime] = None # Когда состояние было создано
    updated_at: Optional[datetime] = None # Когда состояние было обновлено
