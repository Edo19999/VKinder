"""
Точка входа для запуска бота как пакета
python -m vk_dating_bot
"""

from app import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())