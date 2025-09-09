# """
# Модели данных для StateHandler
# """

# from dataclasses import dataclass
# from typing import Dict, Any, Optional
# from datetime import datetime
# from enum import Enum, auto

# class UserState(Enum):
#     """Состояния пользователя в FSM"""
#     MAIN_MENU = auto()
#     SEARCHING = auto()
#     VIEWING_PROFILE = auto()
#     SETTING_PREFERENCES = auto()
#     SETTING_AGE = auto()
#     SETTING_CITY = auto()
#     SETTING_SEX = auto()
#     VIEWING_FAVORITES = auto()

# @dataclass
# class StateData:
#     """Данные состояния пользователя"""
#     current_state: UserState
#     context: Dict[str, Any] = None
#     temp_data: Dict[str, Any] = None
    
#     def __post_init__(self):
#         if self.context is None:
#             self.context = {}
#         if self.temp_data is None:
#             self.temp_data = {}
    
#     def to_dict(self) -> Dict[str, Any]:
#         """Конвертирует в словарь для сохранения в БД"""
#         return {
#             'current_state': self.current_state.name,
#             'context': self.context,
#             'temp_data': self.temp_data
#         }
    
#     @classmethod
#     def from_dict(cls, data: Dict[str, Any]) -> 'StateData':
#         """Создает из словаря (из БД)"""
#         if not data:
#             return cls(current_state=UserState.MAIN_MENU)
        
#         return cls(
#             current_state=UserState[data.get('current_state', 'MAIN_MENU')],
#             context=data.get('context', {}),
#             temp_data=data.get('temp_data', {})
#         )

"""
Модели данных (реэкспорт из utils.data_models для обратной совместимости)
"""

from utils.data_models import UserState, StateData

__all__ = ['UserState', 'StateData']