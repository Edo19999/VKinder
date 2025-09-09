"""
Обработчик состояний пользователя (Finite State Machine) для VKinder Bot
"""

import logging
import json
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum, auto
from dataclasses import dataclass

from utils.data_models import UserState, StateData 

# from database.repository import DatabaseRepository  # Используем ServiceFactory
from services.vk_service import VKService
from utils import ValidationError, validate_age, validate_city, validate_sex
from services.search_service import SearchService  
from services.favorite_service import FavoriteService  
from services.service_factory import ServiceFactory  
from utils import ValidationError, validate_age, validate_city, validate_sex
from keyboards.keyboard_manager import KeyboardManager 


logger = logging.getLogger(__name__)

class UserState(Enum):
    """Состояния пользователя в FSM"""
    MAIN_MENU = auto()
    SEARCHING = auto()
    VIEWING_PROFILE = auto()
    SETTING_PREFERENCES = auto()
    SETTING_AGE = auto()
    SETTING_CITY = auto()
    SETTING_SEX = auto()
    VIEWING_FAVORITES = auto()

@dataclass
class StateData:
    """Данные состояния пользователя"""
    current_state: UserState
    context: Dict[str, Any] = None
    temp_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.temp_data is None:
            self.temp_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь для сохранения в БД"""
        return {
            'current_state': self.current_state.name,
            'context': self.context,
            'temp_data': self.temp_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateData':
        """Создает из словаря (из БД)"""
        if not data:
            return cls(current_state=UserState.MAIN_MENU)
        
        return cls(
            current_state=UserState[data.get('current_state', 'MAIN_MENU')],
            context=data.get('context', {}),
            temp_data=data.get('temp_data', {})
        )

"""
Обработчик состояний пользователя (Finite State Machine) для VKinder Bot
"""

import logging
import json
from typing import Dict, Any, Optional, Callable, Awaitable

# Убираем импорт из models, так как теперь импортируем из своего модуля
from .models import UserState, StateData  # Изменено здесь

# from database.repository import DatabaseRepository  # Используем ServiceFactory
from services.vk_service import VKService
from services.search_service import SearchService  # Оставляем этот импорт
from services.favorite_service import FavoriteService
from services.service_factory import ServiceFactory
from utils import ValidationError, validate_age, validate_city, validate_sex
from keyboards.keyboard_manager import KeyboardManager

logger = logging.getLogger(__name__)

"""
Обработчик состояний пользователя (Finite State Machine) для VKinder Bot
"""

import logging
import json
from typing import Dict, Any, Optional, Callable, Awaitable

# Убираем импорт из models, так как теперь импортируем из своего модуля
from .models import UserState, StateData  # Изменено здесь

# from database.repository import DatabaseRepository  # Используем ServiceFactory
from services.vk_service import VKService
from services.search_service import SearchService  # Оставляем этот импорт
from services.favorite_service import FavoriteService
from services.service_factory import ServiceFactory
from utils import ValidationError, validate_age, validate_city, validate_sex
from keyboards.keyboard_manager import KeyboardManager

logger = logging.getLogger(__name__)

class StateHandler:
    def __init__(self, db_repository, vk_service: VKService):
        self.db_repository = db_repository
        self.vk_service = vk_service
        self.search_service = SearchService(vk_service, db_repository)  # Используем напрямую
        self.favorite_service = FavoriteService(db_repository)
        self.keyboard_manager = KeyboardManager()
        
        self.state_handlers = {
            UserState.MAIN_MENU: self._handle_main_menu,
            UserState.SEARCHING: self._handle_searching,
            UserState.VIEWING_PROFILE: self._handle_viewing_profile,
            UserState.SETTING_PREFERENCES: self._handle_setting_preferences,
            UserState.SETTING_AGE: self._handle_setting_age,
            UserState.SETTING_CITY: self._handle_setting_city,
            UserState.SETTING_SEX: self._handle_setting_sex,
            UserState.VIEWING_FAVORITES: self._handle_viewing_favorites,
        }
    
    async def get_user_state(self, user_id: int) -> StateData:
        """Получает состояние пользователя"""
        try:
            state_record = self.db_repository.get_user_state(user_id)
            if state_record and state_record.state_data:
                return StateData.from_dict(state_record.state_data)
        except Exception as e:
            logger.error(f"Ошибка получения состояния пользователя {user_id}: {e}")
        
        return StateData(current_state=UserState.MAIN_MENU)
    
    async def set_user_state(self, user_id: int, state_data: StateData) -> bool:
        """Устанавливает состояние пользователя"""
        try:
            return self.db_repository.update_user_state(
                user_id, 
                state_data.current_state.name, 
                state_data.to_dict()
            )
        except Exception as e:
            logger.error(f"Ошибка установки состояния пользователя {user_id}: {e}")
            return False
    
    async def handle_message(self, user_id: int, message: str, payload: Any = None) -> None:
        """Обрабатывает сообщение based on текущего состояния"""
        state_data = await self.get_user_state(user_id)
        handler = self.state_handlers.get(state_data.current_state)
        
        if handler:
            await handler(user_id, message, payload, state_data)
        else:
            logger.warning(f"Неизвестное состояние: {state_data.current_state}")
            await self._handle_unknown_state(user_id, message, state_data)
    
    async def _handle_main_menu(self, user_id: int, message: str, 
                              payload: Any, state_data: StateData) -> None:
        """Обработчик главного меню"""
        message_lower = message.lower()
        
        if message_lower in ['поиск', 'найти', 'искать', 'search']:
            await self._start_search(user_id, state_data)
        elif message_lower in ['избранное', 'favorites', 'fav']:
            await self._show_favorites(user_id, state_data)
        elif message_lower in ['настройки', 'settings', 'preferences']:
            await self._start_settings(user_id, state_data)
        else:
            await self._show_main_menu(user_id)
    
    async def _handle_searching(self, user_id: int, message: str,
                              payload: Any, state_data: StateData) -> None:
        """Обработчик состояния поиска"""
        message_lower = message.lower()
        
        if message_lower in ['далее', 'следующий', 'next']:
            await self._show_next_profile(user_id, state_data)
        elif message_lower in ['в избранное', 'добавить', 'add']:
            await self._add_to_favorites(user_id, state_data)
        elif message_lower in ['меню', 'главная', 'main']:
            await self._return_to_main_menu(user_id, state_data)
        else:
            await self._show_current_profile(user_id, state_data)
    
    async def _handle_viewing_profile(self, user_id: int, message: str,
                                    payload: Any, state_data: StateData) -> None:
        """Обработчик просмотра профиля"""
        # Реализация просмотра деталей профиля
        await self._handle_searching(user_id, message, payload, state_data)
    
    async def _handle_setting_preferences(self, user_id: int, message: str,
                                        payload: Any, state_data: StateData) -> None:
        """Обработчик настроек поиска"""
        message_lower = message.lower()
        
        if message_lower in ['возраст', 'age']:
            await self._start_setting_age(user_id, state_data)
        elif message_lower in ['город', 'city']:
            await self._start_setting_city(user_id, state_data)
        elif message_lower in ['пол', 'sex', 'gender']:
            await self._start_setting_sex(user_id, state_data)
        elif message_lower in ['назад', 'back']:
            await self._return_to_main_menu(user_id, state_data)
        else:
            await self._show_preferences_menu(user_id, state_data)
    
    async def _handle_setting_age(self, user_id: int, message: str,
                                payload: Any, state_data: StateData) -> None:
        """Обработчик установки возраста"""
        try:
            age = validate_age(message)
            # Сохраняем возраст
            state_data.context['age'] = age
            await self.set_user_state(user_id, state_data)
            await self.vk_service.send_message(user_id, f"✅ Возраст установлен: {age} лет")
            await self._show_preferences_menu(user_id, state_data)
        except ValidationError as e:
            await self.vk_service.send_message(user_id, f"❌ {e}\nПопробуйте еще раз:")
    
    async def _handle_setting_city(self, user_id: int, message: str,
                                 payload: Any, state_data: StateData) -> None:
        """Обработчик установки города"""
        try:
            city = validate_city(message)
            # Сохраняем город
            state_data.context['city'] = city
            await self.set_user_state(user_id, state_data)
            await self.vk_service.send_message(user_id, f"✅ Город установлен: {city}")
            await self._show_preferences_menu(user_id, state_data)
        except ValidationError as e:
            await self.vk_service.send_message(user_id, f"❌ {e}\nПопробуйте еще раз:")
    
    async def _handle_setting_sex(self, user_id: int, message: str,
                                payload: Any, state_data: StateData) -> None:
        """Обработчик установки пола"""
        try:
            sex_map = {
                '1': 1, 'женский': 1, 'девушка': 1, 'woman': 1,
                '2': 2, 'мужской': 2, 'парень': 2, 'man': 2,
                '0': 0, 'любой': 0, 'any': 0
            }
            
            sex_input = message.lower()
            sex = sex_map.get(sex_input)
            
            if sex is None:
                raise ValidationError("Используйте: 1 (женский), 2 (мужской) или 0 (любой)")
            
            # Сохраняем пол
            state_data.context['sex'] = sex
            await self.set_user_state(user_id, state_data)
            
            sex_names = {1: "женский", 2: "мужской", 0: "любой"}
            await self.vk_service.send_message(user_id, f"✅ Пол установлен: {sex_names[sex]}")
            await self._show_preferences_menu(user_id, state_data)
            
        except ValidationError as e:
            await self.vk_service.send_message(user_id, f"❌ {e}\nПопробуйте еще раз:")
    
    async def _handle_viewing_favorites(self, user_id: int, message: str,
                                      payload: Any, state_data: StateData) -> None:
        """Обработчик просмотра избранного"""
        if message.lower() in ['меню', 'главная', 'main']:
            await self._return_to_main_menu(user_id, state_data)
        else:
            await self._show_favorites(user_id, state_data)
    
    async def _handle_unknown_state(self, user_id: int, message: str,
                                  state_data: StateData) -> None:
        """Обработчик неизвестного состояния"""
        logger.warning(f"Неизвестное состояние у пользователя {user_id}: {state_data.current_state}")
        await self._return_to_main_menu(user_id, state_data)
    
    # Вспомогательные методы
    async def _show_main_menu(self, user_id: int) -> None:
        """Показывает главное меню"""
        from keyboards.keyboard_manager import KeyboardManager
        keyboard = KeyboardManager.create_main_keyboard()
        
        message = (
            "👋 Добро пожаловать в VKinder Bot!\n\n"
            "📋 Выберите действие:\n"
            "• 🔍 Поиск - найти людей для знакомств\n"
            "• ⭐ Избранное - ваши понравившиеся профили\n"
            "• ⚙️ Настройки - изменить критерии поиска"
        )
        
        await self.vk_service.send_message(user_id, message, keyboard)
        await self.set_user_state(user_id, StateData(current_state=UserState.MAIN_MENU))
    
    async def _start_search(self, user_id: int, state_data: StateData) -> None:
        """Начинает поиск"""
        # Проверяем наличие настроек
        if not all(key in state_data.context for key in ['age', 'city', 'sex']):
            await self.vk_service.send_message(
                user_id,
                "⚠️ Сначала настройте критерии поиска в разделе Настройки"
            )
            return
        
        from keyboards.keyboard_manager import KeyboardManager
        keyboard = KeyboardManager.create_search_keyboard()
        
        await self.vk_service.send_message(
            user_id,
            "🔍 Начинаем поиск...",
            keyboard
        )
        
        state_data.current_state = UserState.SEARCHING
        await self.set_user_state(user_id, state_data)
        await self._show_next_profile(user_id, state_data)
    
    async def _show_next_profile(self, user_id: int, state_data: StateData) -> None:
        """Показывает следующий профиль"""
        # Здесь будет интеграция с SearchService
        await self.vk_service.send_message(user_id, "🔄 Ищем подходящих людей...")
        # TODO: Интеграция с поисковым сервисом
    
    async def _add_to_favorites(self, user_id: int, state_data: StateData) -> None:
        """Добавляет текущий профиль в избранное"""
        # TODO: Интеграция с сервисом избранного
        await self.vk_service.send_message(user_id, "✅ Добавлено в избранное!")
    
    async def _show_current_profile(self, user_id: int, state_data: StateData) -> None:
        """Показывает текущий профиль повторно"""
        # TODO: Показать текущий профиль
        await self.vk_service.send_message(user_id, "📋 Текущий профиль:")
    
    async def _show_favorites(self, user_id: int, state_data: StateData) -> None:
        """Показывает избранное"""
        from keyboards.keyboard_manager import KeyboardManager
        keyboard = KeyboardManager.create_favorites_keyboard()
        
        # TODO: Получить избранное из БД
        favorites = []  # Заглушка
        
        if not favorites:
            message = "📝 В избранном пока никого нет"
        else:
            message = "⭐ Ваши избранные:\n\n"
            for i, fav in enumerate(favorites, 1):
                message += f"{i}. {fav['name']}\n"
        
        await self.vk_service.send_message(user_id, message, keyboard)
        state_data.current_state = UserState.VIEWING_FAVORITES
        await self.set_user_state(user_id, state_data)
    
    async def _start_settings(self, user_id: int, state_data: StateData) -> None:
        """Начинает настройки"""
        from keyboards.keyboard_manager import KeyboardManager
        
        message = (
            "⚙️ Настройки поиска\n\n"
            "Выберите параметр для изменения:\n"
            "• 🎂 Возраст - установить возраст для поиска\n"
            "• 🏙️ Город - установить город для поиска\n"
            "• 👫 Пол - установить пол для поиска"
        )
        
        keyboard = json.dumps({
            "one_time": False,
            "inline": True,
            "buttons": [
                [{"action": {"type": "text", "label": "🎂 Возраст", "payload": json.dumps({"command": "age"})}, "color": "primary"}],
                [{"action": {"type": "text", "label": "🏙️ Город", "payload": json.dumps({"command": "city"})}, "color": "primary"}],
                [{"action": {"type": "text", "label": "👫 Пол", "payload": json.dumps({"command": "sex"})}, "color": "primary"}],
                [{"action": {"type": "text", "label": "↩️ Назад", "payload": json.dumps({"command": "back"})}, "color": "secondary"}]
            ]
        }, ensure_ascii=False)
        
        await self.vk_service.send_message(user_id, message, keyboard)
        state_data.current_state = UserState.SETTING_PREFERENCES
        await self.set_user_state(user_id, state_data)
    
    async def _show_preferences_menu(self, user_id: int, state_data: StateData) -> None:
        """Показывает меню настроек"""
        await self._start_settings(user_id, state_data)
    
    async def _start_setting_age(self, user_id: int, state_data: StateData) -> None:
        """Начинает установку возраста"""
        await self.vk_service.send_message(
            user_id,
            "🎂 Введите возраст для поиска (от 18 до 100 лет):"
        )
        state_data.current_state = UserState.SETTING_AGE
        await self.set_user_state(user_id, state_data)
    
    async def _start_setting_city(self, user_id: int, state_data: StateData) -> None:
        """Начинает установку города"""
        await self.vk_service.send_message(
            user_id,
            "🏙️ Введите город для поиска:"
        )
        state_data.current_state = UserState.SETTING_CITY
        await self.set_user_state(user_id, state_data)
    
    async def _start_setting_sex(self, user_id: int, state_data: StateData) -> None:
        """Начинает установку пола"""
        await self.vk_service.send_message(
            user_id,
            "👫 Выберите пол для поиска:\n"
            "1 - женский\n"
            "2 - мужской\n"
            "0 - любой"
        )
        state_data.current_state = UserState.SETTING_SEX
        await self.set_user_state(user_id, state_data)
    
    async def _return_to_main_menu(self, user_id: int, state_data: StateData) -> None:
        """Возвращает в главное меню"""
        await self._show_main_menu(user_id)