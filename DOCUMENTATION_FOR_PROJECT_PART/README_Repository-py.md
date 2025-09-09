# DatabaseRepository — документация

Этот класс инкапсулирует работу с PostgreSQL для проекта VKinder Bot.  
Он управляет пользователями, фото, избранным, просмотренными профилями, состояниями и настройками.

---

## 📌 Методы класса

### Инициализация и соединение
- **__init__()** — создаёт соединение при инициализации.
- **_create_connection()** — внутренний метод для подключения к PostgreSQL.  
  Использует параметры из `config.DATABASE`.

### Работа с пользователями
- **add_or_update_user(user: VKUser) -> bool**  
  Добавляет нового пользователя или обновляет данные существующего (по vk_user_id).

- **get_user_by_vk_id(vk_id: int) -> Optional[VKUser]**  
  Возвращает объект `VKUser` по его ID или `None`.

### Работа с фотографиями
- **add_user_photos(vk_id: int, photos: List[Tuple[str, int]]) -> bool**  
  Удаляет старые фото и сохраняет новые (url + количество лайков).

- **get_user_photos(vk_id: int) -> List[UserPhoto]**  
  Возвращает список фото пользователя, отсортированных по лайкам.

### Избранные профили
- **add_to_favorites(user_id: int, favorite_vk_id: int) -> bool**  
  Добавляет пользователя в избранное (без дублей).

- **get_favorites(user_id: int) -> List[Tuple]**  
  Получает список избранных (id, имя, фамилия, ссылка).

- **get_favorites_with_details(user_id: int) -> List[tuple]**  
  То же самое, но с датой добавления и заметками.

- **remove_from_favorites(user_id: int, favorite_vk_id: int) -> bool**  
  Удаляет запись из избранного.

- **update_favorite_notes(user_id: int, favorite_vk_id: int, notes: str) -> bool**  
  Добавляет/обновляет заметку для избранного пользователя.

### Просмотренные профили
- **add_to_viewed(user_id: int, viewed_vk_id: int) -> bool**  
  Добавляет просмотренный профиль.

- **get_viewed_users(user_id: int) -> List[int]**  
  Получает список ID просмотренных профилей.

### Состояния пользователей (FSM)
- **update_user_state(user_id: int, state: str, state_data: Optional[dict]) -> bool**  
  Сохраняет текущее состояние пользователя (с данными).

- **get_user_state(user_id: int) -> Optional[UserState]**  
  Возвращает объект `UserState` или `None`.

### Настройки пользователей
- **save_user_preferences(user_id: int, preferences: Dict[str, Any]) -> bool**  
  Сохраняет предпочтения (город, возраст, пол и т.п.).

- **get_user_preferences(user_id: int) -> Optional[Dict[str, Any]]**  
  Возвращает сохранённые предпочтения (словарь).

### Найденные пользователи
- **add_found_user(user_data: Dict[str, Any]) -> bool**  
  Добавляет найденного в таблицу vk_found_users (с обновлением).

- **get_found_user(vk_id: int) -> Optional[tuple]**  
  Возвращает данные найденного пользователя (id, имя, фамилия, ссылка).

### Рейтинги и чёрный список
- **add_user_rating(user_id: int, rated_vk_id: int, rating_type: str) -> bool**  
  Сохраняет оценку профиля (like/dislike/blacklist).

- **get_user_rating(user_id: int, rated_vk_id: int) -> Optional[str]**  
  Возвращает тип оценки (или None).

- **get_rated_users(user_id: int, rating_type: str) -> List[int]**  
  Получает список оценённых пользователей. Если не указан `rating_type` — возвращает всех.

- **get_blacklisted_users(user_id: int) -> List[int]**  
  Возвращает список пользователей из чёрного списка.

### Завершение работы
- **close()**  
  Закрывает соединение с базой данных.

---

## ⚙️ Использование
```python
repo = DatabaseRepository()

# Добавление пользователя
user = VKUser(vk_id=1, first_name="Ivan", last_name="Ivanov")
repo.add_or_update_user(user)

# Получение состояния пользователя
state = repo.get_user_state(1)

# Добавление фото
repo.add_user_photos(1, [("http://photo.url/1.jpg", 100)])

# Закрытие соединения
repo.close()
```
