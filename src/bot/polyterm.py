"""
Модуль исполнителя PolyTerm.
Обрабатывает выполнение команд PolyTerm.
"""
import subprocess
import os
from typing import Optional, Dict
import logging

from .data.config import POLYTERM_PATH, POLYTERM_TIMEOUT

logger = logging.getLogger(__name__)


def check_polyterm_installed() -> bool:
    """Проверить установлен ли PolyTerm."""
    if os.path.exists(POLYTERM_PATH):
        return True
    # Также проверить polyterm в PATH
    try:
        result = subprocess.run(
            ["which", "polyterm"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def execute_polyterm_command(command: str) -> str:
    """
    Выполнить команду PolyTerm с таймаутом.
    
    Args:
        command: Команда PolyTerm для выполнения
        
    Returns:
        Вывод команды или сообщение об ошибке
    """
    if not check_polyterm_installed():
        return "❌ Ошибка: PolyTerm не установлен.\n\nПожалуйста, установите PolyTerm сначала."
    
    try:
        # Использовать polyterm из PATH если не по настроенному пути
        polyterm_cmd = POLYTERM_PATH if os.path.exists(POLYTERM_PATH) else "polyterm"
        
        result = subprocess.run(
            polyterm_cmd.split() + command.split(),
            capture_output=True,
            text=True,
            timeout=POLYTERM_TIMEOUT
        )
        
        if result.returncode == 0:
            return f"✅ Вывод:\n\n{result.stdout}"
        else:
            return f"❌ Ошибка:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return f"❌ Ошибка: Время выполнения команды истекло через {POLYTERM_TIMEOUT} секунд."
    except FileNotFoundError:
        return "❌ Ошибка: Исполняемый файл PolyTerm не найден."
    except Exception as e:
        logger.error(f"Ошибка выполнения команды PolyTerm: {e}")
        return f"❌ Ошибка выполнения команды: {str(e)}"


# Соответствие меток кнопок командам PolyTerm
POLYTERM_COMMANDS: Dict[str, str] = {
    "monitor_markets": "monitor --limit 5 --once",
    "live_monitor": "monitor --refresh 5 --limit 5",
    "whale_activity": "whales --hours 24",
    "watch_market": "quick watch",
    "market_analytics": "stats",
    "portfolio": "portfolio",
    "export_data": "export --format json",
    "settings": "config",
    "arbitrage": "arbitrage",
    "predictions": "predict",
    "wallets": "wallets",
    "alerts": "alerts",
    "order_book": "orderbook",
    "risk_assessment": "risk",
    "copy_trading": "follow --list",
    "parlay": "parlay -i",
    "bookmarks": "bookmarks --list",
    "dashboard": "dashboard",
    "tutorial": "tutorial",
    "glossary": "glossary",
    "simulate": "simulate -i",
    "help": "tutorial",
}


def execute_command_by_key(command_key: str) -> str:
    """
    Выполнить команду PolyTerm по её ключу.
    
    Args:
        command_key: Ключ из POLYTERM_COMMANDS
        
    Returns:
        Вывод команды или сообщение об ошибке
    """
    if command_key not in POLYTERM_COMMANDS:
        return f"❌ Неизвестная команда: {command_key}"
    
    command = POLYTERM_COMMANDS[command_key]
    return execute_polyterm_command(command)
