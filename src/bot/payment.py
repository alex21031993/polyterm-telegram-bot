"""
Payment module for USDT TRC20 transactions.
Handles payment verification via TronGrid API.
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
    Check for USDT TRC20 payment via TronGrid API.
    
    Args:
        wallet_address: The wallet address to check
        expected_amount: Expected payment amount in USDT
        since_timestamp: Unix timestamp to search from
        
    Returns:
        Transaction info if found, None otherwise
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
        logger.error(f"Error checking USDT payment: {e}")
        return None


async def monitor_payment(
    user_id: int,
    expected_amount: float,
    plan_months: int,
    bot,
    chat_id: int
) -> Optional[str]:
    """
    Background task to monitor for USDT payment.
    
    Args:
        user_id: User ID
        expected_amount: Expected payment amount
        plan_months: Subscription plan months
        bot: Aiogram bot instance
        chat_id: User's chat ID
        
    Returns:
        Transaction hash if found, None otherwise
    """
    start_time = int(time.time())
    
    for attempt in range(PAYMENT_MAX_ATTEMPTS):
        try:
            # Check for payment
            payment_info = check_usdt_payment(
                USDT_TRC20_WALLET_ADDRESS,
                expected_amount,
                since_timestamp=start_time
            )
            
            if payment_info:
                tx_hash = payment_info["tx_hash"]
                
                # Check if payment already processed
                existing = db.get_payment_by_txhash(tx_hash)
                if existing:
                    if existing["status"] == "confirmed":
                        return tx_hash
                    continue
                
                # Create payment record
                payment_id = db.create_payment(
                    user_id=user_id,
                    amount=expected_amount,
                    tx_hash=tx_hash,
                    plan_months=plan_months
                )
                
                # Confirm payment
                db.update_payment_status(payment_id, "confirmed")
                db.update_user_subscription(user_id, plan_months)
                
                # Notify user
                await bot.send_message(
                    chat_id,
                    f"🎉 Payment received!\n\n"
                    f"Amount: {expected_amount} USDT\n"
                    f"Transaction: `{tx_hash}`\n"
                    f"Subscription: {plan_months} month(s)\n\n"
                    f"Your subscription is now active!",
                    parse_mode="Markdown"
                )
                
                return tx_hash
            
            # Update progress every 5 attempts
            if attempt > 0 and attempt % 5 == 0:
                remaining = PAYMENT_MAX_ATTEMPTS - attempt
                remaining_minutes = remaining * PAYMENT_CHECK_INTERVAL // 60
                try:
                    await bot.send_message(
                        chat_id,
                        f"⏳ Still waiting for payment...\n"
                        f"Remaining checks: {remaining} (~{remaining_minutes} min)"
                    )
                except Exception:
                    pass
            
            # Wait before next check
            await asyncio.sleep(PAYMENT_CHECK_INTERVAL)
            
        except asyncio.CancelledError:
            logger.info(f"Payment monitoring cancelled for user {user_id}")
            break
        except Exception as e:
            logger.error(f"Error in payment monitoring: {e}")
            await asyncio.sleep(PAYMENT_CHECK_INTERVAL)
    
    # Max attempts reached, notify user
    try:
        await bot.send_message(
            chat_id,
            "⏰ Payment not received within 20 minutes.\n"
            "Please make sure you sent the exact amount to the correct address.\n"
            "If you already made the payment, contact support."
        )
    except Exception:
        pass
    
    return None


def validate_tx_hash(tx_hash: str) -> bool:
    """
    Validate a transaction hash.
    
    Args:
        tx_hash: Transaction hash to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not tx_hash:
        return False
    
    # TRC20 transaction hashes are 64 character hex strings
    if len(tx_hash) < 30:
        return False
    
    # Should be hexadecimal
    try:
        int(tx_hash, 16)
        return True
    except ValueError:
        return False
