"""
Модели данных для всего приложения (чтобы избежать циклических импортов)
"""
# Этот модуль содержит общие модели данных,
# чтобы другие части приложения могли их использовать без зацикливания импортов.

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum, auto

# Класс перечисления для описания состояний пользователя в FSM (Finite State Machine)
class UserState(Enum):
    """Состояния пользователя в FSM"""
    MAIN_MENU = auto()            # Пользователь находится в главном меню
    SEARCHING = auto()            # Пользователь выполняет поиск
    VIEWING_PROFILE = auto()      # Пользователь просматривает профиль
    SETTING_PREFERENCES = auto()  # Пользователь настраивает предпочтения
    SETTING_AGE = auto()          # Пользователь указывает возраст
    SETTING_CITY = auto()         # Пользователь указывает город
    SETTING_SEX = auto()          # Пользователь указывает пол
    VIEWING_FAVORITES = auto()    # Пользователь просматривает избранное

# Класс для хранения данных состояния пользователя
@dataclass
class StateData:
    """Данные состояния пользователя"""
    current_state: UserState              # Текущее состояние пользователя (одно из значений UserState)
    context: Dict[str, Any] = None        # Контекстные данные (например, настройки пользователя)
    temp_data: Dict[str, Any] = None      # Временные данные (например, вводимые значения)

    # Метод выполняется сразу после инициализации dataclass
    def __post_init__(self):
        if self.context is None:
            self.context = {}             # Если контекст не передан — создаём пустой словарь
        if self.temp_data is None:
            self.temp_data = {}           # Если временные данные не переданы — создаём пустой словарь

    # Метод для конвертации объекта в словарь (для сохранения в БД)
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь для сохранения в БД"""
        return {
            'current_state': self.current_state.name,  # Сохраняем имя состояния (строкой)
            'context': self.context,                  # Сохраняем контекст
            'temp_data': self.temp_data               # Сохраняем временные данные
        }

    # Альтернативный конструктор — создаёт объект из словаря (например, загруженного из БД)
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateData':
        """Создает из словаря (из БД)"""
        if not data:
            # Если словарь пустой — создаём состояние по умолчанию (главное меню)
            return cls(current_state=UserState.MAIN_MENU)

        # Восстанавливаем объект из словаря
        return cls(
            current_state=UserState[data.get('current_state', 'MAIN_MENU')],  # Получаем состояние по имени
            context=data.get('context', {}),                                  # Контекст (или пустой словарь)
            temp_data=data.get('temp_data', {})                               # Временные данные (или пустой словарь)
        )
