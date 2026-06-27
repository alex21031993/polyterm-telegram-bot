"""
Модуль конфигурации для PolyTerm Telegram бота.
Загружает переменные окружения и определяет константы.
"""
import os
from pathlib import Path
from environs import Env

# Project paths
project_filepath = Path(__file__).resolve().parent.parent.parent.parent
db_folder = project_filepath / "db"
db_folder.mkdir(exist_ok=True)
database_filename = "database.db"
sqlite_database_filepath = str(db_folder / database_filename)

# Environment variables
env = Env()
env.read_env(str(project_filepath / ".env"))

# Bot configuration
BOT_TOKEN = env.str("BOT_TOKEN", default="")

# Admin configuration
ADMIN_PASSWORD = env.str("ADMIN_PASSWORD", default="Alex1234$")
ADMINS_ID_LIST = []  # Will be populated from database

# USDT TRC20 Configuration
USDT_TRC20_WALLET_ADDRESS = "TCSYEiTBp67GvUk3f2f1foL1jDRKu6upD8"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
TRONGRID_URL = "https://api.trongrid.io"

# Subscription plans (months: price in USDT)
SUBSCRIBE_AMOUNT_BY_PLANS = {
    1: 9.99,
    3: 14.99,
    6: 19.99,
    12: 34.99,
}

# PolyTerm configuration
POLYTERM_PATH = "/home/alexandr/.local/bin/polyterm"
POLYTERM_TIMEOUT = 30  # seconds

# TradingAgents configuration
TRADING_AGENTS_PATH = str(project_filepath / "TradingAgents")
TRADING_AGENTS_TIMEOUT = 300  # seconds

# TradingAgents environment
TRADINGAGENTS_PATH = "/home/alexandr/tradingagents_env/venv/lib/python3.13/site-packages"

# Payment monitoring configuration
PAYMENT_CHECK_INTERVAL = 30  # seconds
PAYMENT_MAX_ATTEMPTS = 40  # 20 minutes total

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
