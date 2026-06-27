"""
PolyTerm Telegram Bot - Main Application Entry Point

This bot provides access to PolyTerm commands and TradingAgents analysis
through a Telegram interface with USDT TRC20 subscription system.
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
    """Configure logging for the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def check_configuration() -> bool:
    """Check if all required configuration is set."""
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is not set in .env file!")
        return False
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("Please set your actual BOT_TOKEN in .env file!")
        return False
    
    return True


async def on_startup(bot: Bot) -> None:
    """Actions performed on bot startup."""
    logging.info("Bot starting up...")
    
    # Initialize database
    try:
        init_database()
        logging.info(f"Database initialized at: {sqlite_database_filepath}")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise
    
    # Get bot info
    try:
        bot_info = await bot.get_me()
        logging.info(f"Bot username: @{bot_info.username}")
        logging.info(f"Bot name: {bot_info.full_name}")
    except Exception as e:
        logging.error(f"Failed to get bot info: {e}")
        raise
    
    logging.info("Bot started successfully!")


async def on_shutdown(bot: Bot) -> None:
    """Actions performed on bot shutdown."""
    logging.info("Bot shutting down...")


def main() -> None:
    """Main entry point for the bot."""
    # Setup logging
    setup_logging()
    
    # Check configuration
    if not check_configuration():
        sys.exit(1)
    
    # Create bot instance
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create FSM storage for state management
    storage = MemoryStorage()
    
    # Create dispatcher
    dp = Dispatcher(storage=storage)
    
    # Include routers
    dp.include_router(router)
    
    # Register startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    logging.info("Starting bot polling...")
    
    try:
        asyncio.run(dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        ))
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot error: {e}")
        raise
    finally:
        logging.info("Bot shutdown complete")


if __name__ == "__main__":
    main()
