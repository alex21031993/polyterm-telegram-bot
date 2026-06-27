"""
Модуль платежей для USDT TRC20 транзакций.
Обрабатывает верификацию платежей через TronGrid API.
"""
import requests
import time
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .data.config import (
    USDT_TRC20_WALLET_ADDRESS,
    USDT_CONTRACT,
    TRONGRID_URL,
    PAYMENT_CHECK_INTERVAL,
    PAYMENT_MAX_ATTEMPTS,
)
from . import database as db

logger = logging.getLogger(__name__)


def check_usdt_payment(
    wallet_address: str,
    expected_amount: float,
    since_timestamp: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Проверить USDT TRC20 платеж через TronGrid API.
    
    Args:
        wallet_address: Адрес кошелька для проверки
        expected_amount: Ожидаемая сумма платежа в USDT
        since_timestamp: Unix timestamp для поиска с
        
    Returns:
        Информация о транзакции если найдена, None в противном случае
    """
    try:
        # TronGrid API endpoint for TRC20 transactions
        url = f"{TRONGRID_URL}/v1/accounts/{USDT_TRC20_WALLET_ADDRESS}/transactions/trc20"
        
        params = {
            "contract_address": USDT_CONTRACT,
            "only_to": "true",
            "limit": 200,
        }
        
        if since_timestamp:
            params["min_timestamp"] = since_timestamp * 1000
        
        headers = {
            "Accept": "application/json",
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"TronGrid API error: {response.status_code}")
            return None
        
        data = response.json()
        
        if "data" not in data or not data["data"]:
            return None
        
        # Find matching transaction
        for tx in data["data"]:
            # Parse transaction data
            to_address = tx.get("to_address", "")
            amount_str = tx.get("value", "0")
            
            # Convert TRC20 amount (6 decimals for USDT) to human readable
            amount = int(amount_str) / 1_000_000
            
            # Check if transaction matches expected criteria
            if to_address.lower() == wallet_address.lower():
                if abs(amount - expected_amount) < 0.01:  # Allow small rounding difference
                    return {
                        "tx_hash": tx.get("transaction_id", ""),
                        "amount": amount,
                        "from_address": tx.get("from_address", ""),
                        "to_address": to_address,
                        "block_timestamp": tx.get("block_timestamp", 0),
                    }
        
        return None
        
    except requests.exceptions.Timeout:
        logger.error("TronGrid API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"TronGrid API request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка проверки USDT платежа: {e}")
        return None


async def monitor_payment(
    user_id: int,
    expected_amount: float,
    plan_months: int,
    bot,
    chat_id: int
) -> Optional[str]:
    """
    Фоновая задача для мониторинга USDT платежа.
    
    Args:
        user_id: ID пользователя
        expected_amount: Ожидаемая сумма платежа
        plan_months: Количество месяцев подписки
        bot: Экземпляр Aiogram бота
        chat_id: ID чата пользователя
        
    Returns:
        Хеш транзакции если найден, None в противном случае
    """
    start_time = int(time.time())
    
    for attempt in range(PAYMENT_MAX_ATTEMPTS):
        try:
            # Проверить платеж
            payment_info = check_usdt_payment(
                USDT_TRC20_WALLET_ADDRESS,
                expected_amount,
                since_timestamp=start_time
            )
            
            if payment_info:
                tx_hash = payment_info["tx_hash"]
                
                # Проверить обработан ли платеж
                existing = db.get_payment_by_txhash(tx_hash)
                if existing:
                    if existing["status"] == "confirmed":
                        return tx_hash
                    continue
                
                # Создать запись о платеже
                payment_id = db.create_payment(
                    user_id=user_id,
                    amount=expected_amount,
                    tx_hash=tx_hash,
                    plan_months=plan_months
                )
                
                # Подтвердить платеж
                db.update_payment_status(payment_id, "confirmed")
                db.update_user_subscription(user_id, plan_months)
                
                # Уведомить пользователя
                await bot.send_message(
                    chat_id,
                    f"🎉 Платеж получен!\n\n"
                    f"Сумма: {expected_amount} USDT\n"
                    f"Транзакция: `{tx_hash}`\n"
                    f"Подписка: {plan_months} мес.\n\n"
                    f"Ваша подписка теперь активна!",
                    parse_mode="Markdown"
                )
                
                return tx_hash
            
            # Обновить прогресс каждые 5 попыток
            if attempt > 0 and attempt % 5 == 0:
                remaining = PAYMENT_MAX_ATTEMPTS - attempt
                remaining_minutes = remaining * PAYMENT_CHECK_INTERVAL // 60
                try:
                    await bot.send_message(
                        chat_id,
                        f"⏳ Ожидание платежа...\n"
                        f"Осталось проверок: {remaining} (~{remaining_minutes} мин)"
                    )
                except Exception:
                    pass
            
            # Ждать перед следующей проверкой
            await asyncio.sleep(PAYMENT_CHECK_INTERVAL)
            
        except asyncio.CancelledError:
            logger.info(f"Мониторинг платежа отменен для пользователя {user_id}")
            break
        except Exception as e:
            logger.error(f"Ошибка в мониторинге платежа: {e}")
            await asyncio.sleep(PAYMENT_CHECK_INTERVAL)
    
    # Достигнуто максимальное количество попыток, уведомить пользователя
    try:
        await bot.send_message(
            chat_id,
            "⏰ Платеж не получен в течение 20 минут.\n"
            "Пожалуйста, убедитесь, что отправили точную сумму на правильный адрес.\n"
            "Если вы уже сделали платеж, обратитесь в поддержку."
        )
    except Exception:
        pass
    
    return None


def validate_tx_hash(tx_hash: str) -> bool:
    """
    Проверить хеш транзакции.
    
    Args:
        tx_hash: Хеш транзакции для проверки
        
    Returns:
        True если валиден, False в противном случае
    """
    if not tx_hash:
        return False
    
    # TRC20 хеши транзакций - это 64-символьные hex строки
    if len(tx_hash) < 30:
        return False
    
    # Должен быть шестнадцатеричным
    try:
        int(tx_hash, 16)
        return True
    except ValueError:
        return False
