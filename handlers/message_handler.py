import logging
import json
from typing import Dict, Any, Optional
from .state_handler import StateHandler
from .models import StateData, UserState
from services.service_factory import ServiceFactory

from services.service_factory import ServiceFactory
from keyboards.keyboard_manager import KeyboardManager
from utils import format_user_profile, format_favorites_list
from utils import async_retry, ValidationError

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        self.user_service = ServiceFactory.get_user_service()
        self.search_service = ServiceFactory.get_search_service()
        self.state_handler = StateHandler(
            ServiceFactory.get_db_repository(),
            ServiceFactory.get_vk_service()
        )
        self.keyboard_manager = KeyboardManager()
        self.current_matches: Dict[int, Dict[str, Any]] = {}
        self.favorite_service = ServiceFactory.get_favorite_service()
        
    async def handle_message(self, message: dict) -> None:
        """Обрабатывает входящие сообщения"""
        try:
            user_id = message.get('from_id')
            message_text = message.get('text', '')
            payload = message.get('payload')
            
            logger.info(f"Обработка сообщения: user_id={user_id}, text={message_text}, payload={payload}")
            
            # Логируем полученный payload
            if payload:
                logger.info(f"Получен payload: {payload}")
                
            # Обрабатываем команды из payload
            command = None
            if payload:
                command = self._parse_command(payload)
                logger.info(f"Извлечена команда из payload: {command}")
            
            # Получаем текущее состояние пользователя
            user_state_data = await self.state_handler.get_user_state(user_id)
            logger.info(f"Текущее состояние пользователя {user_id}: {user_state_data}")
            
            if command:
                logger.info(f"Обрабатываем команду: {command}")
                await self._handle_command(user_id, command, payload)
            else:
                # Обрабатываем ввод в зависимости от состояния
                current_state = user_state_data.current_state.name if user_state_data and user_state_data.current_state else 'MAIN_MENU'
                logger.info(f"Текущее состояние (строка): {current_state}")
                
                if current_state == 'SETTING_AGE':
                    logger.info(f"Обрабатываем ввод возраста: {message_text}")
                    await self._process_age_input(user_id, message_text)
                elif current_state == 'SETTING_CITY':
                    logger.info(f"Обрабатываем ввод города: {message_text}")
                    await self._process_city_input(user_id, message_text)
                else:
                    logger.info(f"Обрабатываем текстовое сообщение: {message_text}")
                    await self._handle_text_message(user_id, message_text)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.user_service.vk_service.send_message(
                user_id, 
                "❌ Произошла ошибка. Попробуйте позже.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
    
    def _parse_command(self, payload: str) -> Optional[str]:
        """Парсит команду из payload"""
        try:
            if not payload:
                return None
                
            payload_data = json.loads(payload)
            
            # Обработка выбора пола
            if 'sex' in payload_data:
                self.sex_value = payload_data.get('sex')
                return 'sex_selected'  # Специальная команда для обработки выбора пола
                
            # Получаем команду из payload
            command = payload_data.get('command')
            logger.info(f"Получена команда из payload: {command}")
            return command
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Ошибка при парсинге payload: {e}, payload: {payload}")
            return None

    async def _handle_command(self, user_id: int, command: str, payload: str = None) -> None:
        """Обрабатывает команды из payload"""
        logger.info(f"Обработка команды: {command} для пользователя {user_id}")
        
        # Парсим дополнительные данные из payload
        payload_data = {}
        if payload:
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить payload: {payload}")
        
        command_handlers = {
            'search': self._handle_search,
            'next': self._handle_next,
            'add_favorite': self._handle_add_favorite,
            'favorites': self._handle_favorites,
            'main_menu': self._handle_main_menu,
            'age': self._handle_age,
            'city': self._handle_city,
            'sex': self._handle_sex,
            'sex_selected': self._handle_sex_selected,
            'preferred_sex': self._handle_preferred_sex,
            'preferred_sex_selected': self._handle_preferred_sex_selected,
            'age_selected': self._handle_age_selected,
            'city_selected': self._handle_city_selected,
            'city_input': self._handle_city_input,
            'back': self._handle_main_menu,
            'like': self._handle_like,
            'dislike': self._handle_dislike,
            'blacklist': self._handle_blacklist,
            'skip': self._handle_skip,
            'add_to_favorites': self._handle_add_to_favorites,
            'edit_profile': self._handle_edit_profile
        }
        
        handler = command_handlers.get(command)
        if handler:
            logger.info(f"Найден обработчик для команды {command}")
            if command in ['age_selected', 'city_selected', 'city_input', 'sex_selected', 'preferred_sex_selected']:
                await handler(user_id, payload_data)
            else:
                await handler(user_id)
        else:
            logger.warning(f"Неизвестная команда: {command}")
            await self._handle_main_menu(user_id)

    async def _handle_text_message(self, user_id: int, message: str) -> None:
        """Обрабатывает текстовые сообщения"""
        message = message.lower().strip()
        
        if message in ['начать', 'start', 'меню', 'главное', '🏠 главное меню']:
            await self._handle_main_menu(user_id)
        elif message in ['поиск', 'найти', 'искать', '🔍 найти человека']:
            await self._handle_search(user_id)
        elif message in ['далее', 'следующий', '➡️ следующий']:
            await self._handle_next(user_id)
        elif message in ['избранное', 'избранные', '⭐ избранные']:
            await self._handle_favorites(user_id)
        elif message in ['в избранное', 'добавить', '❤️ в избранное']:
            await self._handle_add_favorite(user_id)
            await self._handle_favorites(user_id)
        else:
            await self._handle_main_menu(user_id)

    async def _handle_main_menu(self, user_id: int) -> None:
        """Показывает главное меню"""
        welcome_text = (
            "👋 Добро пожаловать в бот знакомств!\n\n"
            "📋 Выберите действие:\n"
            "• 🔍 Найти человека - поиск по вашим критериям\n"
            "• ⭐ Избранные - просмотр вашего списка избранных"
        )
        
        await self.user_service.vk_service.send_message(
            user_id,
            welcome_text,
            self.keyboard_manager.create_main_keyboard(inline=True)
        )
        self.user_service.update_user_state(user_id, 'main_menu')

    async def _handle_search(self, user_id: int) -> None:
        """Начинает поиск"""
        logger.info(f"Начинаем поиск для пользователя {user_id}")
        
        # Получаем информацию о пользователе
        user_info = self.user_service.process_user(user_id)
        logger.info(f"Получена информация о пользователе: {user_info}")
        
        if not user_info:
            logger.warning(f"Не удалось получить информацию о пользователе {user_id}")
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Не удалось получить ваши данные. Проверьте настройки приватности.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
            return
            
        # Проверяем наличие необходимых данных
        logger.info(f"Проверяем данные пользователя: age={user_info.age}, city={user_info.city}, sex={user_info.sex}, preferred_sex={getattr(user_info, 'preferred_sex', None)}")
        
        if not user_info.age or not user_info.city or not user_info.sex:
            logger.info(f"У пользователя {user_id} не хватает данных для поиска")
            missing_fields = []
            if not user_info.age:
                missing_fields.append("• Дата рождения")
            if not user_info.city:
                missing_fields.append("• Город")
            if not user_info.sex:
                missing_fields.append("• Пол")
            
            await self.user_service.vk_service.send_message(
                user_id,
                f"📝 Для поиска нужно заполнить профиль:\n\n{chr(10).join(missing_fields)}\n\nВыберите, что хотите указать:",
                self.keyboard_manager.create_profile_setup_keyboard(inline=True)
            )
            return
            
        # Проверяем рекомендуемые настройки
        preferred_sex = getattr(user_info, 'preferred_sex', None)
        if preferred_sex is None:
            await self.user_service.vk_service.send_message(
                user_id,
                "💡 Рекомендуем настроить предпочтения по полу для более точного поиска.\n\nВы можете сделать это в главном меню или продолжить поиск с текущими настройками.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
            
        # Ищем первого пользователя
        logger.info(f"Все данные есть, начинаем показ профилей для пользователя {user_id}")
        await self._show_next_match(user_id, user_info)

    async def _handle_next(self, user_id: int) -> None:
        """Показывает следующего пользователя"""
        user_info = self.user_service.process_user(user_id)
        if user_info:
            await self._show_next_match(user_id, user_info)

    async def _handle_add_favorite(self, user_id: int) -> None:
        """Добавляет текущего пользователя в избранное"""
        if user_id in self.current_matches:
            match_data = self.current_matches[user_id]
            favorite_id = match_data['user'].vk_id
            
            success = self.user_service.add_to_favorites(user_id, favorite_id)
            if success:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "✅ Добавлено в избранное!",
                    self.keyboard_manager.create_search_keyboard(inline=True)
                )
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось добавить в избранное",
                    self.keyboard_manager.create_search_keyboard(inline=True)
                )
        else:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Нет активного пользователя для добавления",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )

    async def _handle_favorites(self, user_id: int) -> None:
        """Показывает список избранных"""
        favorites = self.user_service.get_favorites_list(user_id)
        
        # Используем функцию из helpers для форматирования
        message = format_favorites_list(favorites)
        
        await self.user_service.vk_service.send_message(
            user_id,
            message,
            self.keyboard_manager.create_favorites_keyboard(inline=True)
        )

    async def _handle_add_to_favorites(self, user_id: int) -> None:
        """Добавляет текущего просматриваемого пользователя в избранное"""
        if user_id in self.current_matches:
            match_data = self.current_matches[user_id]
            favorite_id = match_data['user']['vk_id']
            
            success = self.user_service.add_to_favorites(user_id, favorite_id)
            if success:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "✅ Пользователь добавлен в избранное!",
                    self.keyboard_manager.create_search_keyboard(inline=True)
                )
                # Показываем следующего пользователя
                user_info = self.user_service.process_user(user_id)
                await self._show_next_match(user_id, user_info)
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось добавить в избранное. Возможно, пользователь уже в списке.",
                    self.keyboard_manager.create_search_keyboard(inline=True)
                )
        else:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Нет активного пользователя для добавления в избранное",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )

    async def _handle_age(self, user_id: int) -> None:
        """Обрабатывает команду установки возраста"""
        keyboard = self.keyboard_manager.create_age_selection_keyboard()
        await self.user_service.vk_service.send_message(
            user_id,
            "🎂 Выберите ваш возраст:",
            keyboard=keyboard
        )
        
    async def _handle_city(self, user_id: int) -> None:
        """Обрабатывает команду установки города"""
        keyboard = self.keyboard_manager.create_city_selection_keyboard()
        await self.user_service.vk_service.send_message(
            user_id,
            "🏙️ Выберите ваш город:",
            keyboard=keyboard
        )
        
    async def _handle_sex(self, user_id: int) -> None:
        """Обрабатывает команду установки пола"""
        await self.user_service.vk_service.send_message(
            user_id,
            "👫 Выберите ваш пол:",
            self.keyboard_manager.create_sex_selection_keyboard(inline=True)
        )
        self.user_service.update_user_state(user_id, 'setting_sex')
        
    async def _handle_sex_selected(self, user_id: int, payload_data: dict) -> None:
        """Обрабатывает выбор пола пользователем"""
        try:
            sex_value = payload_data.get('sex')
            if not sex_value:
                logger.error("Не найден sex в payload")
                return
            
            # Получаем текущую информацию о пользователе
            user_info = self.user_service.process_user(user_id)
            if not user_info:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось получить информацию о пользователе",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                return
            
            # Обновляем пол пользователя
            user_info.sex = sex_value
            success = self.user_service.db_repository.add_or_update_user(user_info)
            
            if success:
                sex_text = "мужской" if sex_value == 2 else "женский"
                await self.user_service.vk_service.send_message(
                    user_id,
                    f"✅ Пол успешно установлен: {sex_text}\n\n🎉 Отлично! Все данные заполнены.\nТеперь можете начать поиск!",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                self.user_service.update_user_state(user_id, 'main_menu')
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось сохранить пол. Попробуйте позже.",
                    self.keyboard_manager.create_sex_selection_keyboard(inline=True)
                )
        except Exception as e:
            logger.error(f"Ошибка при обработке выбора пола: {e}")
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Произошла ошибка при выборе пола. Попробуйте еще раз.",
                self.keyboard_manager.create_sex_selection_keyboard(inline=True)
            )

    async def _handle_preferred_sex(self, user_id: int) -> None:
        """Обрабатывает команду установки предпочтений по полу"""
        await self.user_service.vk_service.send_message(
            user_id,
            "💕 Выберите предпочтения по полу для поиска:",
            self.keyboard_manager.create_preferred_sex_selection_keyboard(inline=True)
        )
        self.user_service.update_user_state(user_id, 'setting_preferred_sex')
        
    async def _handle_preferred_sex_selected(self, user_id: int, payload_data: dict) -> None:
        """Обрабатывает выбор предпочтений по полу пользователем"""
        try:
            preferred_sex_value = payload_data.get('preferred_sex')
            if preferred_sex_value is None:
                logger.error("Не найден preferred_sex в payload")
                return
            
            # Получаем текущую информацию о пользователе
            user_info = await self.user_service.process_user(user_id)
            if not user_info:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось получить информацию о пользователе",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                return
            
            # Обновляем предпочтения по полу
            user_info.preferred_sex = preferred_sex_value
            success = self.user_service.db_repository.add_or_update_user(user_info)
            
            if success:
                if preferred_sex_value == 0:
                    sex_text = "любой"
                elif preferred_sex_value == 1:
                    sex_text = "женский"
                else:
                    sex_text = "мужской"
                    
                await self.user_service.vk_service.send_message(
                    user_id,
                    f"✅ Предпочтения по полу успешно установлены: {sex_text}",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                self.user_service.update_user_state(user_id, 'main_menu')
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось сохранить предпочтения по полу. Попробуйте позже.",
                    self.keyboard_manager.create_preferred_sex_selection_keyboard(inline=True)
                )
        except Exception as e:
            logger.error(f"Ошибка при обработке выбора предпочтений по полу: {e}")
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Произошла ошибка при выборе предпочтений по полу. Попробуйте еще раз.",
                self.keyboard_manager.create_preferred_sex_selection_keyboard(inline=True)
            )

    async def _process_age_input(self, user_id: int, message: str) -> None:
        """Обрабатывает ввод возраста"""
        try:
            # Проверяем, что введено число
            age = int(message.strip())
            
            # Проверяем диапазон возраста
            if 18 <= age <= 100:
                # Получаем текущую информацию о пользователе
                user_info = await self.user_service.process_user(user_id)
                
                if user_info:
                    # Обновляем возраст пользователя
                    user_info.age = age
                    success = self.user_service.db_repository.add_or_update_user(user_info)
                    
                    if success:
                        # Обновляем состояние на главное меню
                        await self.state_handler.set_user_state(user_id, StateData(UserState.MAIN_MENU))
                        
                        # Проверяем, заполнен ли город
                        if not user_info.city:
                            await self.user_service.vk_service.send_message(
                                user_id,
                                f"✅ Возраст успешно установлен: {age} лет\n\n📍 Теперь укажите ваш город:",
                                self.keyboard_manager.create_profile_setup_keyboard(inline=True)
                            )
                            return
                        # Если город есть, но нет пола
                        elif not user_info.sex:
                            await self.user_service.vk_service.send_message(
                                user_id,
                                f"✅ Возраст успешно установлен: {age} лет\n\n👤 Теперь выберите ваш пол:",
                                self.keyboard_manager.create_sex_keyboard(inline=True)
                            )
                            return
                        else:
                            await self.user_service.vk_service.send_message(
                                user_id,
                                f"✅ Возраст успешно установлен: {age} лет\n\nВсе данные заполнены! Теперь можете начать поиск.",
                                self.keyboard_manager.create_main_keyboard(inline=True)
                            )
                            self.user_service.update_user_state(user_id, 'main_menu')
                            return
                    else:
                        await self.user_service.vk_service.send_message(
                            user_id,
                            "❌ Не удалось сохранить возраст. Попробуйте позже.",
                            self.keyboard_manager.create_profile_setup_keyboard(inline=True)
                        )
                else:
                    await self.user_service.vk_service.send_message(
                        user_id,
                        "❌ Не удалось получить информацию о пользователе. Попробуйте позже.",
                        self.keyboard_manager.create_profile_setup_keyboard(inline=True)
                    )
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Возраст должен быть от 18 до 100 лет. Попробуйте еще раз:",
                    self.keyboard_manager.create_profile_setup_keyboard(inline=True)
                )
                return
        except ValueError:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Пожалуйста, введите корректный возраст (число от 18 до 100):",
                self.keyboard_manager.create_profile_setup_keyboard(inline=True)
            )
            return
            
        # Состояние обновляется в блоке успешного сохранения
        
    async def _process_city_input(self, user_id: int, message: str) -> None:
        """Обрабатывает ввод города"""
        city = message.strip()
        
        if len(city) > 0:
            # Получаем текущую информацию о пользователе
            user_info = self.user_service.process_user(user_id)
            
            if user_info:
                # Обновляем город пользователя
                user_info.city = city
                success = self.user_service.db_repository.add_or_update_user(user_info)
                
                if success:
                    # Проверяем, заполнен ли пол
                    if not user_info.sex:
                        await self.user_service.vk_service.send_message(
                            user_id,
                            f"✅ Город успешно установлен: {city}\n\n👤 Теперь выберите ваш пол:",
                            self.keyboard_manager.create_sex_keyboard(inline=True)
                        )
                        self.user_service.update_user_state(user_id, 'main_menu')
                        return
                    else:
                        await self.user_service.vk_service.send_message(
                            user_id,
                            f"✅ Город успешно установлен: {city}\n\nВсе данные заполнены! Теперь можете начать поиск.",
                            self.keyboard_manager.create_main_keyboard(inline=True)
                        )
                        self.user_service.update_user_state(user_id, 'main_menu')
                        return
                else:
                    await self.user_service.vk_service.send_message(
                        user_id,
                        "❌ Не удалось сохранить город. Попробуйте позже.",
                        self.keyboard_manager.create_profile_setup_keyboard(inline=True)
                    )
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось получить информацию о пользователе. Попробуйте позже.",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
        else:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Название города не может быть пустым. Попробуйте еще раз:",
                self.keyboard_manager.create_profile_setup_keyboard(inline=True)
            )
            return
            
        # Возвращаемся в главное меню
        self.user_service.update_user_state(user_id, 'main_menu')
    
    async def _show_next_match(self, user_id: int, user_info: Any) -> None:
        """Показывает следующего подходящего пользователя"""
        # Создаем StateData объект с информацией о пользователе
        from utils.data_models import StateData, UserState
        
        state_data = StateData(
            current_state=UserState.SEARCHING,
            context={
                'age': user_info.age,
                'city': user_info.city,
                'sex': user_info.sex
            }
        )
        
        match = self.user_service.find_next_match(user_id, user_info)
        
        if not match:
            await self.user_service.vk_service.send_message(
                user_id,
                "😢 Больше нет подходящих пользователей\n\n"
                "Попробуйте изменить критерии поиска или проверьте позже.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
            return
            
        user = match['user']
        photos = match['photos']
        
        # Используем функцию из helpers для форматирования
        message, attachment = format_user_profile(user, photos)
        
        # Отправляем сообщение
        success = await self.user_service.vk_service.send_message(
            user_id,
            message,
            self.keyboard_manager.create_search_keyboard(inline=True),
            attachment
        )
        
        if success:
            # Сохраняем текущего пользователя
            self.current_matches[user_id] = match
            self.user_service.update_user_state(user_id, 'searching')
        else:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Ошибка при отправке профиля",
                self.keyboard_manager.create_main_keyboard()
            )

    async def _handle_like(self, user_id: int) -> None:
        """Обрабатывает лайк пользователя"""
        await self._handle_rating(user_id, 'like', '❤️ Лайк поставлен!')

    async def _handle_dislike(self, user_id: int) -> None:
        """Обрабатывает дизлайк пользователя"""
        await self._handle_rating(user_id, 'dislike', '👎 Дизлайк поставлен!')

    async def _handle_blacklist(self, user_id: int) -> None:
        """Добавляет пользователя в черный список"""
        await self._handle_rating(user_id, 'blacklist', '🚫 Пользователь добавлен в черный список!')

    async def _handle_skip(self, user_id: int) -> None:
        """Пропускает пользователя без оценки"""
        if user_id in self.current_matches:
            # Просто показываем следующего без сохранения оценки
            user_info = self.user_service.process_user(user_id)
            await self._show_next_match(user_id, user_info)
        else:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Нет активного профиля для пропуска",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )

    async def _handle_rating(self, user_id: int, rating_type: str, success_message: str) -> None:
        """Общий метод для обработки оценок пользователей"""
        if user_id not in self.current_matches:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Нет активного профиля для оценки",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
            return

        current_match = self.current_matches[user_id]
        rated_user_id = current_match['user']['vk_id']
        
        # Сохраняем оценку в базе данных
        db_repository = ServiceFactory.get_db_repository()
        success = db_repository.add_user_rating(user_id, rated_user_id, rating_type)
        
        if success:
            # Отправляем сообщение об успехе
            await self.user_service.vk_service.send_message(
                user_id,
                success_message,
                None
            )
            
            # Показываем следующего пользователя
            user_info = self.user_service.process_user(user_id)
            await self._show_next_match(user_id, user_info)
        else:
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Произошла ошибка при сохранении оценки",
                self.keyboard_manager.create_search_keyboard(inline=True)
            )
    
    async def _handle_age_selected(self, user_id: int, payload_data: dict) -> None:
        """Обрабатывает выбор возраста из кнопок"""
        try:
            age_range = payload_data.get('age_range')
            if not age_range:
                logger.error("Не найден age_range в payload")
                return
            
            logger.info(f"Пользователь {user_id} выбрал возрастной диапазон: {age_range}")
            
            # Парсим диапазон возраста
            if age_range == "18-25":
                min_age, max_age = 18, 25
            elif age_range == "26-35":
                min_age, max_age = 26, 35
            elif age_range == "36-45":
                min_age, max_age = 36, 45
            elif age_range == "46+":
                min_age, max_age = 46, 100
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Неверный возрастной диапазон",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                return
            
            # Получаем информацию о пользователе
            user_info = self.user_service.process_user(user_id)
            if not user_info:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Не удалось получить информацию о пользователе",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                return
            
            # Устанавливаем собственный возраст пользователя (средний возраст диапазона)
            user_age = (min_age + max_age) // 2
            user_info.age = user_age
            
            # Обновляем предпочтения пользователя
            success = await self.user_service.update_user_preferences(
                user_id, 
                min_age=min_age, 
                max_age=max_age
            )
            
            # Сохраняем обновленную информацию пользователя
            user_success = self.user_service.db_repository.add_or_update_user(user_info)
            success = success and user_success
            
            if success:
                await self.user_service.vk_service.send_message(
                    user_id,
                    f"✅ Возрастной диапазон установлен: {age_range} лет",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Произошла ошибка при сохранении возраста",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке выбора возраста: {e}")
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Произошла ошибка. Попробуйте позже.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
    
    async def _handle_city_selected(self, user_id: int, payload_data: dict) -> None:
        """Обрабатывает выбор города из кнопок"""
        try:
            city = payload_data.get('city')
            if not city:
                logger.error("Не найден city в payload")
                return
            
            logger.info(f"Пользователь {user_id} выбрал город: {city}")
            
            # Обновляем предпочтения пользователя
            success = await self.user_service.update_user_preferences(
                user_id, 
                city=city
            )
            
            if success:
                await self.user_service.vk_service.send_message(
                    user_id,
                    f"✅ Город установлен: {city}",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
            else:
                await self.user_service.vk_service.send_message(
                    user_id,
                    "❌ Произошла ошибка при сохранении города",
                    self.keyboard_manager.create_main_keyboard(inline=True)
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке выбора города: {e}")
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Произошла ошибка. Попробуйте позже.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
    
    async def _handle_city_input(self, user_id: int, payload_data: dict) -> None:
        """Обрабатывает запрос на ввод своего города"""
        try:
            # Устанавливаем состояние ввода города
            await self.state_handler.set_user_state(user_id, StateData(UserState.SETTING_CITY))
            
            await self.user_service.vk_service.send_message(
                user_id,
                "📍 Введите название вашего города:",
                self.keyboard_manager.create_empty_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса ввода города: {e}")
            await self.user_service.vk_service.send_message(
                user_id,
                "❌ Произошла ошибка. Попробуйте позже.",
                self.keyboard_manager.create_main_keyboard(inline=True)
            )
    
    async def _handle_edit_profile(self, user_id: int) -> None:
        """Обрабатывает запрос на редактирование профиля"""
        # Получаем текущую информацию о пользователе
        user_info = self.user_service.process_user(user_id)
        
        if user_info:
            current_info = []
            if user_info.age:
                current_info.append(f"• Возраст: {user_info.age} лет")
            if user_info.city:
                current_info.append(f"• Город: {user_info.city}")
            if user_info.sex:
                sex_text = "мужской" if user_info.sex == 2 else "женский"
                current_info.append(f"• Пол: {sex_text}")
                
            current_text = "\n".join(current_info) if current_info else "Профиль не заполнен"
            
            message = (
                "⚙️ Редактирование профиля\n\n"
                "📋 Текущие данные:\n"
                f"{current_text}\n\n"
                "Выберите, что хотите изменить:"
            )
        else:
            message = (
                "⚙️ Редактирование профиля\n\n"
                "Выберите, что хотите заполнить:"
            )
            
        await self.user_service.vk_service.send_message(
            user_id,
            message,
            self.keyboard_manager.create_profile_setup_keyboard(inline=True)
        )