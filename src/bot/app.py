"""
PolyTerm Telegram Бот - Главная точка входа приложения

Этот бот предоставляет доступ к командам PolyTerm и анализу TradingAgents
через интерфейс Telegram с системой подписки USDT TRC20.
"""
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from .data.config import (
    BOT_TOKEN,
    sqlite_database_filepath,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
)
from .database import init_database
from .handlers import router


def setup_logging() -> None:
    """Настроить логирование для бота."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Уменьшить шум от некоторых библиотек
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def check_configuration() -> bool:
    """Проверить установлена ли вся необходимая конфигурация."""
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не установлен в файле .env!")
        return False
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("Пожалуйста, установите ваш настоящий BOT_TOKEN в файле .env!")
        return False
    
    return True


async def on_startup(bot: Bot) -> None:
    """Действия при запуске бота."""
    logging.info("Бот запускается...")
    
    # Инициализировать базу данных
    try:
        init_database()
        logging.info(f"База данных инициализирована: {sqlite_database_filepath}")
    except Exception as e:
        logging.error(f"Не удалось инициализировать базу данных: {e}")
        raise
    
    # Получить информацию о боте
    try:
        bot_info = await bot.get_me()
        logging.info(f"Имя бота: @{bot_info.username}")
        logging.info(f"Полное имя: {bot_info.full_name}")
    except Exception as e:
        logging.error(f"Не удалось получить информацию о боте: {e}")
        raise
    
    logging.info("Бот успешно запущен!")


async def on_shutdown(bot: Bot) -> None:
    """Действия при остановке бота."""
    logging.info("Бот останавливается...")


def main() -> None:
    """Главная точка входа для бота."""
    # Настроить логирование
    setup_logging()
    
    # Проверить конфигурацию
    if not check_configuration():
        sys.exit(1)
    
    # Создать экземпляр бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создать FSM хранилище для управления состоянием
    storage = MemoryStorage()
    
    # Создать диспетчер
    dp = Dispatcher(storage=storage)
    
    # Включить роутеры
    dp.include_router(router)
    
    # Зарегистрировать хуки запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Начать опрос
    logging.info("Запуск опроса бота...")
    
    try:
        asyncio.run(dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        ))
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Ошибка бота: {e}")
        raise
    finally:
        logging.info("Бот полностью остановлен")


if __name__ == "__main__":
    main()
