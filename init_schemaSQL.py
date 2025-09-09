"""
Скрипт для инициализации структуры БД из schema.sql
"""

import psycopg2
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self):
        # Загружаем переменные окружения из .env файла
        load_dotenv()
        
        # Параметры подключения из .env
        self.db_params = {
            'dbname': os.getenv('DB_NAME', 'vkinder_bot_vk'),
            'user': os.getenv('DB_USER', 'vkinder_bot_vk_admin'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        self.schema_file = Path('database/schema.sql')
    
    def read_schema_file(self):
        """Читает файл схемы БД"""
        if not self.schema_file.exists():
            logger.error(f"Файл схемы не найден: {self.schema_file}")
            return None
            
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Ошибка чтения файла схемы: {e}")
            return None
    
    def initialize_schema(self):
        """Инициализирует структуру БД из schema.sql"""
        schema_sql = self.read_schema_file()
        if not schema_sql:
            return False
        
        try:
            conn = psycopg2.connect(**self.db_params)
            conn.autocommit = True
            cur = conn.cursor()
            
            # Выполняем SQL из файла схемы
            cur.execute(schema_sql)
            
            conn.close()
            logger.info("✅ Структура БД успешно инициализирована")
            return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации схемы: {e}")
            return False
    
    def test_connection(self):
        """Тестирует подключение к БД"""
        try:
            conn = psycopg2.connect(**self.db_params)
            
            # Проверяем, что можем выполнять запросы
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                result = cur.fetchone()
                logger.info(f"Версия PostgreSQL: {result[0]}")
            
            conn.close()
            logger.info("✅ Подключение к БД успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    def run(self):
        """Основной метод"""
        print("🚀 Инициализация структуры базы данных VKinder Bot")
        print("="*50)
        print(f"Параметры подключения из .env файла:")
        print(f"DB: {self.db_params['dbname']}")
        print(f"User: {self.db_params['user']}")
        print(f"Host: {self.db_params['host']}")
        print(f"Port: {self.db_params['port']}")
        print("="*50)
        
        # Сначала проверяем подключение
        if not self.test_connection():
            return False
        
        # Затем инициализируем схему
        logger.info("🔄 Инициализация структуры БД...")
        if not self.initialize_schema():
            return False
        
        print("\n🎉 СТРУКТУРА БАЗЫ ДАННЫХ УСПЕШНО ИНИЦИАЛИЗИРОВАНА!")
        print("="*50)
        return True

if __name__ == "__main__":
    initializer = DatabaseInitializer()
    success = initializer.run()
    sys.exit(0 if success else 1)