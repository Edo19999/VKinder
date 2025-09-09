import json
from typing import Optional

class KeyboardManager:
    @staticmethod
    def create_main_keyboard(inline: bool = False) -> str:
        """Создает главную клавиатуру"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "🔍 Найти человека",
                        "payload": json.dumps({"command": "search"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "⭐ Избранные",
                        "payload": json.dumps({"command": "favorites"})
                    },
                    "color": "secondary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "💕 Предпочтения по полу",
                        "payload": json.dumps({"command": "preferred_sex"})
                    },
                    "color": "secondary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "⚙️ Редактировать профиль",
                        "payload": json.dumps({"command": "edit_profile"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_search_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для поиска с системой оценок"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "❤️ Лайк",
                        "payload": json.dumps({"command": "like"})
                    },
                    "color": "positive"
                }, {
                    "action": {
                        "type": "text",
                        "label": "👎 Дизлайк",
                        "payload": json.dumps({"command": "dislike"})
                    },
                    "color": "negative"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🚫 Черный список",
                        "payload": json.dumps({"command": "blacklist"})
                    },
                    "color": "secondary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "⭐ Добавить в избранные",
                        "payload": json.dumps({"command": "add_to_favorites"})
                    },
                    "color": "positive"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "➡️ Пропустить",
                        "payload": json.dumps({"command": "skip"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🏠 Главное меню",
                        "payload": json.dumps({"command": "main_menu"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_favorites_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для избранного"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "🏠 Главное меню",
                        "payload": json.dumps({"command": "main_menu"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_profile_setup_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для настройки профиля"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "🎂 Указать возраст",
                        "payload": json.dumps({"command": "age"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🏙️ Указать город",
                        "payload": json.dumps({"command": "city"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "👫 Указать пол",
                        "payload": json.dumps({"command": "sex"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🏠 Главное меню",
                        "payload": json.dumps({"command": "main_menu"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_age_selection_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для выбора возраста"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "18-25 лет",
                        "payload": json.dumps({"command": "age_selected", "age_range": "18-25"})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "26-35 лет",
                        "payload": json.dumps({"command": "age_selected", "age_range": "26-35"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "36-45 лет",
                        "payload": json.dumps({"command": "age_selected", "age_range": "36-45"})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "46-60 лет",
                        "payload": json.dumps({"command": "age_selected", "age_range": "46-60"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "60+ лет",
                        "payload": json.dumps({"command": "age_selected", "age_range": "60+"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🔙 Назад",
                        "payload": json.dumps({"command": "main_menu"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_city_selection_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для выбора города"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "Москва",
                        "payload": json.dumps({"command": "city_selected", "city": "Москва"})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "Санкт-Петербург",
                        "payload": json.dumps({"command": "city_selected", "city": "Санкт-Петербург"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "Новосибирск",
                        "payload": json.dumps({"command": "city_selected", "city": "Новосибирск"})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "Екатеринбург",
                        "payload": json.dumps({"command": "city_selected", "city": "Екатеринбург"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "Казань",
                        "payload": json.dumps({"command": "city_selected", "city": "Казань"})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "Нижний Новгород",
                        "payload": json.dumps({"command": "city_selected", "city": "Нижний Новгород"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "Челябинск",
                        "payload": json.dumps({"command": "city_selected", "city": "Челябинск"})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "Самара",
                        "payload": json.dumps({"command": "city_selected", "city": "Самара"})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "✏️ Ввести другой город",
                        "payload": json.dumps({"command": "city_input"})
                    },
                    "color": "secondary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🔙 Назад",
                        "payload": json.dumps({"command": "main_menu"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_sex_selection_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для выбора пола"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "label": "👨 Мужской",
                        "payload": json.dumps({"command": "sex_selected", "sex": 2})
                    },
                    "color": "primary"
                }, {
                    "action": {
                        "type": "text",
                        "label": "👩 Женский",
                        "payload": json.dumps({"command": "sex_selected", "sex": 1})
                    },
                    "color": "primary"
                }],
                [{
                    "action": {
                        "type": "text",
                        "label": "🔙 Назад",
                        "payload": json.dumps({"command": "main_menu"})
                    },
                    "color": "secondary"
                }]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_preferred_sex_selection_keyboard(inline: bool = False) -> str:
        """Создает клавиатуру для выбора предпочтений по полу"""
        keyboard = {
            "one_time": False,
            "inline": inline,
            "buttons": [
                [{"action": {"type": "text", "label": "👩 Женский", "payload": json.dumps({"preferred_sex": 1})}, "color": "primary"}],
                [{"action": {"type": "text", "label": "👨 Мужской", "payload": json.dumps({"preferred_sex": 2})}, "color": "primary"}],
                [{"action": {"type": "text", "label": "🤷 Любой", "payload": json.dumps({"preferred_sex": 0})}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "🏠 Главное меню", "payload": json.dumps({"command": "main_menu"})}, "color": "negative"}]
            ]
        }
        return json.dumps(keyboard, ensure_ascii=False)

    @staticmethod
    def create_empty_keyboard() -> str:
        """Создает пустую клавиатуру (скрывает предыдущую)"""
        return json.dumps({"buttons": [], "one_time": True})