"""
Модуль интеграции TradingAgents.
Предоставляет AI-анализ рынка для акций, криптовалют и ETF.
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Add the workspace path to sys.path to import TradingAgents
WORKSPACE_PATH = os.environ.get("TRADINGAGENTS_PATH", "/workspace")
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

logger = logging.getLogger(__name__)

# Supported tickers
SUPPORTED_STOCKS = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "INTC", "NFLX"]
SUPPORTED_CRYPTO = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"]
SUPPORTED_ETF = ["SPY", "QQQ", "DIA", "IWM", "VTI"]

ALL_SUPPORTED_TICKERS = SUPPORTED_STOCKS + SUPPORTED_CRYPTO + SUPPORTED_ETF


def check_tradingagents_installed() -> bool:
    """Проверить доступность фреймворка TradingAgents."""
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        return True
    except ImportError as e:
        logger.error(f"TradingAgents не установлен: {e}")
        return False


def get_ticker_info(ticker: str) -> Dict[str, str]:
    """Получить тип и информацию о тикере."""
    ticker_upper = ticker.upper()
    
    if ticker_upper in SUPPORTED_STOCKS:
        return {"type": "stock", "name": ticker_upper}
    elif ticker_upper in SUPPORTED_CRYPTO:
        return {"type": "crypto", "name": ticker_upper}
    elif ticker_upper in SUPPORTED_ETF:
        return {"type": "etf", "name": ticker_upper}
    else:
        return {"type": "unknown", "name": ticker_upper}


def validate_ticker(ticker: str) -> Tuple[bool, str]:
    """Проверить поддержку тикера."""
    ticker_upper = ticker.upper().strip()
    
    if ticker_upper in ALL_SUPPORTED_TICKERS:
        return True, ticker_upper
    
    # Попытка найти похожие тикеры
    suggestions = []
    for supported in ALL_SUPPORTED_TICKERS:
        if ticker_upper in supported or supported in ticker_upper:
            suggestions.append(supported)
    
    if suggestions:
        return False, f"Похожие тикеры: {', '.join(suggestions[:5])}"
    
    return False, f"Не поддерживается. Используйте: {', '.join(ALL_SUPPORTED_TICKERS[:10])}..."


async def run_trading_analysis(
    ticker: str,
    trade_date: str = None,
    debug: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Запустить TradingAgents анализ для тикера.
    
    Args:
        ticker: Символ тикера акции, криптовалюты или ETF
        trade_date: Дата анализа (формат YYYY-MM-DD). По умолчанию сегодня.
        debug: Включить режим отладки
        
    Returns:
        Кортеж (результат_анализа, сообщение_об_ошибке)
    """
    if not check_tradingagents_installed():
        return "", "❌ Фреймворк TradingAgents не установлен или настроен неправильно."
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # Проверить тикер
        is_valid, result = validate_ticker(ticker)
        if not is_valid:
            return "", f"❌ Неверный тикер: {result}"
        
        ticker = result
        
        # Получить информацию о тикере
        ticker_info = get_ticker_info(ticker)
        
        # Использовать сегодня, если дата не указана
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Запуск TradingAgents анализа для {ticker} на дату {trade_date}")
        
        # Инициализировать граф
        config = DEFAULT_CONFIG.copy()
        ta = TradingAgentsGraph(debug=debug, config=config)
        
        # Запустить анализ
        _, decision = ta.propagate(ticker, trade_date, asset_type=ticker_info["type"])
        
        # Форматировать ответ
        if decision:
            formatted_result = format_analysis_result(ticker, ticker_info, decision)
            return formatted_result, None
        else:
            return "", "❌ TradingAgents не сгенерировал решение."
            
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return "", f"❌ Отсутствуют зависимости: {str(e)}"
    except Exception as e:
        logger.error(f"Ошибка при запуске TradingAgents: {e}")
        return "", f"❌ Ошибка анализа: {str(e)}"


def format_analysis_result(ticker: str, ticker_info: Dict[str, str], decision: str) -> str:
    """Форматировать результат анализа для отображения в Телеграм."""
    ticker_type_map = {
        "stock": "📈 Акция",
        "crypto": "₿ Криптовалюта",
        "etf": "📊 ETF"
    }
    
    type_label = ticker_type_map.get(ticker_info["type"], "📈 Актив")
    
    result = (
        f"⭐ <b>TradingAgents анализ: {ticker}</b>\n"
        f"{type_label}\n\n"
        f"📋 <b>Решение:</b>\n"
        f"{decision}\n\n"
        f"_Анализ сгенерирован AI агентами_"
    )
    
    return result


def get_supported_tickers_list() -> str:
    """Получить форматированный список поддерживаемых тикеров."""
    return (
        "📈 <b>Поддерживаемые акции:</b>\n"
        f"{', '.join(SUPPORTED_STOCKS)}\n\n"
        "₿ <b>Поддерживаемая криптовалюта:</b>\n"
        f"{', '.join(SUPPORTED_CRYPTO)}\n\n"
        "📊 <b>Поддерживаемые ETF:</b>\n"
        f"{', '.join(SUPPORTED_ETF)}"
    )
