"""
Главное приложение VKinder Bot
"""

import asyncio
import logging
import signal
import sys
import traceback
from typing import List

# Проверяем платформу для обработки сигналов
import platform
IS_WINDOWS = platform.system() == 'Windows'

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import vk_api

from config.settings import config
from handlers.message_handler import MessageHandler
from services.service_factory import ServiceFactory
from utils import setup_logging

# Настройка логирования
setup_logging(config.LOG_LEVEL, 'vkinder_bot.log')

logger = logging.getLogger(__name__)

class VKinderBot:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # Инициализация VK API
        try:
            self.vk_session = vk_api.VkApi(token=config.VK.GROUP_TOKEN)
            self.longpoll = VkBotLongPoll(self.vk_session, config.VK.GROUP_ID)
            self.logger.info("VK API инициализирован успешно")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации VK API: {e}")
            raise
    
    async def startup(self):
        """Запускает приложение"""
        self.logger.info("🚀 Запуск VKinder Bot...")
        
        # Инициализация сервисов
        try:
            # Проверяем подключение к БД
            db_repo = ServiceFactory.get_db_repository()
            self.logger.info("✅ База данных подключена успешно")
            
            # Проверяем VK API
            vk_service = ServiceFactory.get_vk_service()
            self.logger.info("✅ VK Service инициализирован успешно")
            
            # Инициализируем обработчик сообщений
            self.message_handler = MessageHandler()
            
            self.is_running = True
            self.logger.info("🤖 Бот запущен и готов к работе")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации сервисов: {e}")
            self.logger.error(f"Трассировка: {traceback.format_exc()}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Корректно завершает работу приложения"""
        self.logger.info("🛑 Завершение работы бота...")
        self.is_running = False
        
        try:
            await ServiceFactory.shutdown()
            self.logger.info("✅ Сервисы корректно остановлены")
        except Exception as e:
            self.logger.error(f"Ошибка при остановке сервисов: {e}")
        
        self.logger.info("👋 Бот завершил работу")
    
    async def handle_message(self, event):
        """Обрабатывает входящее сообщение"""
        try:
            message_data = event.obj.message
            user_id = message_data['from_id']
            message_text = message_data['text']
            payload = message_data.get('payload')
            
            self.logger.info(f"📩 Сообщение от {user_id}: {message_text}")
            if payload:
                self.logger.info(f"📦 Payload: {payload}")
            
            # Создаем словарь с данными сообщения для передачи в обработчик
            message_dict = {
                'id': message_data.get('id'),
                'from_id': user_id,
                'text': message_text,
                'payload': payload
            }
            
            # Передаем словарь в обработчик сообщений
            await self.message_handler.handle_message(message_dict)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            self.logger.error(f"Трассировка: {traceback.format_exc()}")
    
    async def run(self):
        """Основной цикл работы бота"""
        try:
            await self.startup()
        except Exception as e:
            self.logger.error(f"Не удалось запустить бота: {e}")
            return
        # Кроссплатформенная обработка сигналов
        if not IS_WINDOWS:
            # Для Unix-систем используем сигналы
            loop = asyncio.get_running_loop()
            for sig in [signal.SIGINT, signal.SIGTERM]:
                try:
                    loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
                except NotImplementedError:
                    self.logger.warning(f"Сигнал {sig} не поддерживается на этой платформе")
        else:
            # Для Windows используем KeyboardInterrupt в main()
            self.logger.info("🖥️ Запущено на Windows - для остановки используйте Ctrl+C")
        
        try:
            while self.is_running:
                try:
                    for event in self.longpoll.listen():
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            await self.handle_message(event)
                        
                        # Проверяем флаг running после каждой итерации
                        if not self.is_running:
                            break
                
                except Exception as e:
                    self.logger.error(f"Ошибка в основном цикле: {e}")
                    self.logger.error(f"Трассировка: {traceback.format_exc()}")
                    await asyncio.sleep(5)  # Пауза перед повторной попыткой
                    
        except asyncio.CancelledError:
            self.logger.info("Работа бота прервана")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка в основном цикле: {e}")
            self.logger.error(f"Трассировка: {traceback.format_exc()}")
        finally:
            if self.is_running:
                await self.shutdown()

async def main():
    """Точка входа приложения"""
    bot = VKinderBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем (Ctrl+C)")
        await bot.shutdown()
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        print(f"📋 Трассировка: {traceback.format_exc()}")
        await bot.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    # Простая обработка Ctrl+C для Windows
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")