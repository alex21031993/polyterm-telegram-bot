"""
PolyTerm executor module.
Handles execution of PolyTerm commands.
"""
import subprocess
import os
from typing import Optional, Dict
import logging

from .data.config import POLYTERM_PATH, POLYTERM_TIMEOUT

logger = logging.getLogger(__name__)


def check_polyterm_installed() -> bool:
    """Check if PolyTerm is installed."""
    if os.path.exists(POLYTERM_PATH):
        return True
    # Also check if polyterm is in PATH
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
    Execute a PolyTerm command with timeout.
    
    Args:
        command: The PolyTerm command to execute
        
    Returns:
        Command output or error message
    """
    if not check_polyterm_installed():
        return "❌ Error: PolyTerm is not installed.\n\nPlease install PolyTerm first."
    
    try:
        # Use polyterm from PATH if not at configured path
        polyterm_cmd = POLYTERM_PATH if os.path.exists(POLYTERM_PATH) else "polyterm"
        
        result = subprocess.run(
            polyterm_cmd.split() + command.split(),
            capture_output=True,
            text=True,
            timeout=POLYTERM_TIMEOUT
        )
        
        if result.returncode == 0:
            return f"✅ Output:\n\n{result.stdout}"
        else:
            return f"❌ Error:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return f"❌ Error: Command timed out after {POLYTERM_TIMEOUT} seconds."
    except FileNotFoundError:
        return "❌ Error: PolyTerm executable not found."
    except Exception as e:
        logger.error(f"Error executing PolyTerm command: {e}")
        return f"❌ Error executing command: {str(e)}"


# Mapping of button labels to PolyTerm commands
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
    Execute a PolyTerm command by its key.
    
    Args:
        command_key: The key from POLYTERM_COMMANDS
        
    Returns:
        Command output or error message
    """
    if command_key not in POLYTERM_COMMANDS:
        return f"❌ Unknown command: {command_key}"
    
    command = POLYTERM_COMMANDS[command_key]
    return execute_polyterm_command(command)
