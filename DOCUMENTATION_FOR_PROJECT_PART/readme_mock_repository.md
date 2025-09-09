# 🧩 MockDatabaseRepository

## ✨ Назначение
`MockDatabaseRepository` — это заглушка для базы данных PostgreSQL, которая хранит данные **в оперативной памяти**.  
Она используется для тестирования логики приложения без необходимости подключаться к реальной БД.

---

## 📦 Основные возможности

### 👤 Пользователи
- `add_or_update_user(user: VKUser)` — добавляет или обновляет пользователя.  
- `get_user_by_vk_id(vk_id: int)` — возвращает пользователя по его ID.  
- `add_found_user(user_data: dict)` — сохраняет найденного пользователя.  
- `get_found_user(vk_id: int)` — получает найденного пользователя.

### 🖼 Фото
- `add_user_photos(vk_id: int, photos: List[UserPhoto])` — добавляет фото пользователю.  
- `get_user_photos(vk_id: int)` — возвращает список фото пользователя.

### ⭐ Избранное
- `add_to_favorites(user_vk_id: int, target_vk_id: int)` — добавляет пользователя в избранное.  
- `remove_from_favorites(user_vk_id: int, target_vk_id: int)` — удаляет пользователя из избранного.  
- `get_user_favorites(user_vk_id: int)` — возвращает список ID избранных.  
- `get_favorites(user_vk_id: int)` — возвращает избранных с именем и ссылкой.  
- `is_in_favorites(user_vk_id: int, target_vk_id: int)` — проверяет, есть ли пользователь в избранном.

### 🔄 Состояния (FSM)
- `set_user_state(vk_id: int, state: UserState)` — устанавливает состояние пользователя.  
- `get_user_state(vk_id: int)` — получает состояние пользователя.  
- `update_user_state(user_id: int, state: str, state_data: Optional[dict])` — обновляет состояние.  
- `delete_user_state(vk_id: int)` — удаляет состояние пользователя.

### 🔍 История поиска
- `add_search_history(user_vk_id: int, target_vk_id: int, action: str)` — добавляет запись в историю поиска.  
- `get_search_history(user_vk_id: int, limit: int = 50)` — возвращает историю поиска пользователя.

### 👀 Просмотренные профили
- `add_to_viewed(user_id: int, viewed_vk_id: int)` — добавляет просмотренного пользователя.  
- `get_viewed_users(user_id: int)` — возвращает список просмотренных профилей.

### 👍 Оценки
- `add_user_rating(user_id: int, rated_vk_id: int, rating_type: str)` — сохраняет оценку (лайк/дизлайк/бан).  
- `get_user_rating(user_id: int, rated_vk_id: int)` — получает оценку пользователя.

---

## 🛠 Интерфейс базы данных
- `cursor()` — возвращает заглушку `MockCursor`.  
- `close()` — закрывает соединение (логически).  
- Поддержка контекстного менеджера (`with ... as ...`).

`MockCursor` эмулирует работу с курсором PostgreSQL:
- `execute(query, params=None)` — имитация выполнения запроса.  
- `fetchone()` — возвращает одну строку.  
- `fetchall()` — возвращает все строки.

---

## ✅ Пример использования

```python
from database.mock_repository import MockDatabaseRepository
from database.models import VKUser

db = MockDatabaseRepository()

# Добавляем пользователя
user = VKUser(vk_id=1, first_name="Ivan", last_name="Petrov")
db.add_or_update_user(user)

# Получаем пользователя
u = db.get_user_by_vk_id(1)
print(u.first_name)  # Ivan

# Добавляем в избранное
db.add_to_favorites(1, 2)

# Проверяем избранное
print(db.get_user_favorites(1))  # [2]
```

---
