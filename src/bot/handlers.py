"""
Handlers module for PolyTerm Telegram Bot.
Contains all message and callback handlers.
"""
import asyncio
import subprocess
import logging
from datetime import datetime
from typing import Optional

from aiogram import Router, F, types, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from . import database as db
from .database import get_db_cursor
from .data.config import (
    ADMIN_PASSWORD,
    SUBSCRIBE_AMOUNT_BY_PLANS,
    USDT_TRC20_WALLET_ADDRESS,
    USDT_CONTRACT,
    TRADING_AGENTS_PATH,
    TRADING_AGENTS_TIMEOUT,
)
from . import polyterm
from . import payment
from .keyboards import (
    get_main_menu_keyboard,
    get_subscription_plans_keyboard,
    get_payment_keyboard,
    get_admin_keyboard,
    get_back_to_menu_keyboard,
)

logger = logging.getLogger(__name__)

router = Router()

# In-memory storage for pending payments
pending_payments: dict = {}


class AdminStates(StatesGroup):
    """States for admin operations."""
    waiting_broadcast = State()
    waiting_txhash = State()


class BroadcastStates(StatesGroup):
    """States for broadcast message."""
    waiting_message = State()


def is_user_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return db.is_admin(user_id)


def has_active_subscription(user_id: int) -> bool:
    """Check if user has active subscription."""
    if is_user_admin(user_id):
        return True
    return db.check_subscription_active(user_id)


async def send_long_message(message: Message, text: str, max_length: int = 4096) -> None:
    """Send a long message by splitting if necessary."""
    if len(text) <= max_length:
        await message.answer(text)
        return
    
    # Split message
    parts = []
    current = ""
    for line in text.split('\n'):
        if len(current) + len(line) + 1 > max_length:
            if current:
                parts.append(current)
            current = line
        else:
            current += '\n' + line if current else line
    
    if current:
        parts.append(current)
    
    for part in parts:
        await message.answer(part)
        await asyncio.sleep(0.5)


# Command handlers
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Create or update user
    db.create_user(user_id, username, full_name)
    
    welcome_text = (
        "👋 Welcome to <b>PolyTerm Bot</b>!\n\n"
        "I provide access to PolyTerm commands and TradingAgents analysis.\n\n"
    )
    
    if has_active_subscription(user_id):
        welcome_text += "✅ You have an active subscription.\n\nSelect an option from the menu below:"
    else:
        welcome_text += (
            "❌ You don't have an active subscription.\n\n"
            "Subscribe to access all features!\n\n"
            "💰 Plans:\n"
            "• 1 month - 9.99 USDT\n"
            "• 3 months - 14.99 USDT\n"
            "• 6 months - 19.99 USDT\n"
            "• 12 months - 34.99 USDT"
        )
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_active_subscription(user_id))
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = (
        "📖 <b>Available Commands:</b>\n\n"
        "/start - Main menu\n"
        "/help - Show this help\n"
        "/status - Check subscription status\n"
        "/subscribe - Buy subscription\n"
        "/trade <ticker> - TradingAgents analysis\n"
        "/admin_login <password> - Admin login\n"
        "/admin - Admin panel\n\n"
        "<b>PolyTerm Commands:</b>\n"
        "Use the menu buttons to access PolyTerm features.\n\n"
        "<b>TradingAgents:</b>\n"
        "Use /trade <ticker> to analyze stocks, crypto, or ETFs.\n"
        "Examples: /trade AAPL, /trade BTC-USD, /trade SPY"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Handle /status command."""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ User not found.")
        return
    
    if is_user_admin(user_id):
        status_text = "✅ <b>Status:</b> Admin\n"
    elif has_active_subscription(user_id):
        subscribed_until = datetime.fromisoformat(user['subscribed_until'])
        status_text = (
            f"✅ <b>Subscription Active</b>\n\n"
            f"📅 Expires: {subscribed_until.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        status_text = (
            "❌ <b>No Active Subscription</b>\n\n"
            "Use /subscribe to purchase a subscription."
        )
    
    await message.answer(status_text, parse_mode="HTML")


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    """Handle /subscribe command."""
    user_id = message.from_user.id
    
    if has_active_subscription(user_id):
        await message.answer(
            "✅ You already have an active subscription!\n\nUse /status to check your subscription details.",
            reply_markup=get_main_menu_keyboard(True)
        )
        return
    
    await message.answer(
        "💳 <b>Select Subscription Plan</b>\n\nChoose a plan that works for you:",
        parse_mode="HTML",
        reply_markup=get_subscription_plans_keyboard()
    )


@router.message(Command("admin_login"))
async def cmd_admin_login(message: Message) -> None:
    """Handle /admin_login command."""
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer("❌ Usage: /admin_login <password>")
        return
    
    password = parts[1]
    
    if password != ADMIN_PASSWORD:
        await message.answer("❌ Invalid password.")
        logger.warning(f"Failed admin login attempt from user {user_id}")
        return
    
    # Add as admin
    db.add_admin(user_id)
    
    # Update user's admin status
    with db.get_db_cursor() as cursor:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
    
    logger.info(f"User {user_id} logged in as admin")
    await message.answer(
        "✅ Successfully logged in as admin!",
        reply_markup=get_admin_keyboard()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Handle /admin command."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        await message.answer("❌ Access denied. Admins only.")
        return
    
    await message.answer(
        "⚙️ <b>Admin Panel</b>\n\nSelect an option:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    """Handle /broadcast command."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        await message.answer("❌ Access denied. Admins only.")
        return
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer("❌ Usage: /broadcast <message>")
        return
    
    broadcast_message = parts[1]
    
    # Send to all users
    users = db.get_all_users()
    success_count = 0
    error_count = 0
    
    status_msg = await message.answer("📤 Sending broadcast...")
    
    for user in users:
        try:
            await message.bot.send_message(
                user['user_id'],
                f"📢 <b>Broadcast Message:</b>\n\n{broadcast_message}",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user['user_id']}: {e}")
            error_count += 1
    
    await status_msg.edit_text(
        f"✅ Broadcast sent!\n\nSuccess: {success_count}\nFailed: {error_count}"
    )


@router.message(Command("trade"))
async def cmd_trade(message: Message) -> None:
    """Handle /trade command for TradingAgents analysis."""
    user_id = message.from_user.id
    
    # Check subscription
    if not has_active_subscription(user_id):
        await message.answer(
            "❌ This feature requires an active subscription.\n\nUse /subscribe to purchase one.",
            reply_markup=get_subscription_plans_keyboard()
        )
        return
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer(
            "❌ Usage: /trade <ticker>\n\n"
            "Examples:\n"
            "• Stocks: /trade AAPL, /trade TSLA\n"
            "• Crypto: /trade BTC-USD, /trade ETH-USD\n"
            "• ETF: /trade SPY, /trade QQQ"
        )
        return
    
    ticker = parts[1].upper().strip()
    
    # Validate ticker format
    valid_tickers = [
        'AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'BTC-USD', 'ETH-USD', 'SOL-USD',
        'SPY', 'QQQ', 'DIA'
    ]
    
    if ticker not in valid_tickers:
        await message.answer(
            f"❌ Unsupported ticker: {ticker}\n\n"
            f"Supported tickers:\n"
            f"• Stocks: AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META\n"
            f"• Crypto: BTC-USD, ETH-USD, SOL-USD\n"
            f"• ETF: SPY, QQQ, DIA"
        )
        return
    
    # Log command
    db.log_command(user_id, f"/trade {ticker}")
    
    status_msg = await message.answer(
        f"🔍 Running TradingAgents analysis for <b>{ticker}</b>...\n\n"
        "This may take up to 5 minutes. Please wait.",
        parse_mode="HTML"
    )
    
    # Run TradingAgents
    try:
        result = await run_trading_analysis(ticker)
        
        await status_msg.edit_text(
            f"📊 <b>TradingAgents Analysis for {ticker}</b>\n\n{result}",
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"TradingAgents error for {ticker}: {e}")
        await status_msg.edit_text(
            f"❌ Error running analysis: {str(e)}",
            reply_markup=get_back_to_menu_keyboard()
        )


async def run_trading_analysis(ticker: str) -> str:
    """Run TradingAgents analysis."""
    analysis_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        result = subprocess.run(
            [
                "python", "-m", "tradingagents.cli.main",
                "analyze", ticker, "--date", analysis_date
            ],
            cwd=TRADING_AGENTS_PATH,
            capture_output=True,
            text=True,
            timeout=TRADING_AGENTS_TIMEOUT
        )
        
        if result.returncode == 0:
            return result.stdout[:4000]  # Limit output length
        else:
            return f"Analysis completed with warnings:\n{result.stderr[:2000]}"
            
    except subprocess.TimeoutExpired:
        return "Analysis timed out after 5 minutes."
    except FileNotFoundError:
        return "TradingAgents not found. Please install it first."
    except Exception as e:
        return f"Error running analysis: {str(e)}"


# Callback handlers
@router.callback_query(F.data == "cmd_back_main")
async def callback_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle back to main menu."""
    await state.clear()
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "🏠 <b>Main Menu</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_active_subscription(user_id))
    )


@router.callback_query(F.data == "cmd_cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle cancel operation."""
    await state.clear()
    await callback.answer("❌ Cancelled")
    await callback.message.edit_text(
        "Operation cancelled.",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data == "cmd_check_subscription")
async def callback_check_subscription(callback: CallbackQuery) -> None:
    """Handle check subscription button."""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if is_user_admin(user_id):
        text = "✅ <b>Status:</b> Admin\n"
    elif has_active_subscription(user_id):
        subscribed_until = datetime.fromisoformat(user['subscribed_until'])
        text = (
            f"✅ <b>Subscription Active</b>\n\n"
            f"📅 Expires: {subscribed_until.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        text = (
            "❌ <b>No Active Subscription</b>\n\n"
            "Click below to subscribe:"
        )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_active_subscription(user_id))
    )


@router.callback_query(F.data == "cmd_buy_subscription")
async def callback_buy_subscription(callback: CallbackQuery) -> None:
    """Handle buy subscription button."""
    await callback.message.edit_text(
        "💳 <b>Select Subscription Plan</b>\n\nChoose a plan that works for you:",
        parse_mode="HTML",
        reply_markup=get_subscription_plans_keyboard()
    )


@router.callback_query(F.data == "cmd_my_stats")
async def callback_my_stats(callback: CallbackQuery) -> None:
    """Handle my stats button."""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    # Get user's command count
    with db.get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM command_log WHERE user_id = ?",
            (user_id,)
        )
        command_count = cursor.fetchone()[0]
    
    created_at = datetime.fromisoformat(user['created_at']).strftime('%Y-%m-%d') if user else 'N/A'
    
    stats_text = (
        "📊 <b>Your Statistics</b>\n\n"
        f"👤 User ID: {user_id}\n"
        f"📅 Member since: {created_at}\n"
        f"⚡ Commands used: {command_count}\n"
    )
    
    if has_active_subscription(user_id) and user:
        subscribed_until = datetime.fromisoformat(user['subscribed_until'])
        stats_text += f"📅 Subscription expires: {subscribed_until.strftime('%Y-%m-%d')}"
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data.startswith("sub_plan_"))
async def callback_subscription_plan(callback: CallbackQuery) -> None:
    """Handle subscription plan selection."""
    user_id = callback.from_user.id
    plan_months = int(callback.data.split("_")[-1])
    amount = SUBSCRIBE_AMOUNT_BY_PLANS[plan_months]
    
    # Store in memory for payment verification
    pending_payments[user_id] = {
        'plan_months': plan_months,
        'amount': amount
    }
    
    plan_name = "1 month" if plan_months == 1 else f"{plan_months} months"
    
    payment_text = (
        "💳 <b>Payment Instructions</b>\n\n"
        f"Plan: {plan_name}\n"
        f"Amount: <code>{amount:.2f} USDT</code>\n\n"
        f"<b>⚠️ Important:</b>\n"
        f"1. Send exactly <code>{amount:.2f} USDT</code> to the address below\n"
        f"2. Use <b>TRC20 network</b> only\n"
        f"3. After payment, click 'I've Paid'\n\n"
        f"<b>Wallet Address:</b>\n"
        f"<code>{USDT_TRC20_WALLET_ADDRESS}</code>\n\n"
        f"<b>USDT Contract:</b>\n"
        f"<code>{USDT_CONTRACT}</code>"
    )
    
    await callback.message.edit_text(
        payment_text,
        parse_mode="HTML",
        reply_markup=get_payment_keyboard(plan_months, amount)
    )


@router.callback_query(F.data.startswith("check_payment_"))
async def callback_check_payment(callback: CallbackQuery, bot: Bot) -> None:
    """Handle check payment button."""
    user_id = callback.from_user.id
    plan_months = int(callback.data.split("_")[-1])
    
    # Get stored payment info
    payment_info = pending_payments.get(user_id, {})
    amount = payment_info.get('amount', SUBSCRIBE_AMOUNT_BY_PLANS.get(plan_months, 9.99))
    
    status_msg = await callback.message.edit_text(
        f"⏳ Checking for payment of {amount:.2f} USDT...\n\n"
        "This will take up to 20 minutes. You'll be notified when payment is confirmed."
    )
    
    # Start payment monitoring in background
    asyncio.create_task(
        payment.monitor_payment(user_id, amount, plan_months, bot, callback.message.chat.id)
    )
    
    await asyncio.sleep(3)
    await status_msg.edit_text(
        f"🔄 Monitoring for payment...\n\n"
        f"Amount expected: {amount:.2f} USDT\n"
        f"Plan: {plan_months} month(s)\n\n"
        f"Make sure you've sent the payment to:\n"
        f"<code>{USDT_TRC20_WALLET_ADDRESS}</code>\n\n"
        "You'll receive a notification when payment is confirmed.",
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data == "copy_wallet")
async def callback_copy_wallet(callback: CallbackQuery) -> None:
    """Handle copy wallet button."""
    await callback.answer("📋 Wallet address copied!", show_alert=True)


# Admin callbacks
@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery) -> None:
    """Handle admin stats button."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    stats = db.get_bot_statistics()
    
    stats_text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total users: {stats['total_users']}\n"
        f"✅ Active subscribers: {stats['active_subscribers']}\n"
        f"💰 Total revenue: {stats['total_revenue']:.2f} USDT\n"
        f"⏳ Pending payments: {stats['pending_payments']}"
    )
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery) -> None:
    """Handle admin users list button."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    users = db.get_all_users()
    
    if not users:
        text = "No users yet."
    else:
        text = "👥 <b>Users List</b>\n\n"
        for i, user in enumerate(users[:50], 1):  # Limit to 50 users
            status = "✅" if user['subscription_active'] else "❌"
            admin = "👑" if user['is_admin'] else ""
            text += f"{i}. {user['user_id']} {status}{admin}\n"
        
        if len(users) > 50:
            text += f"\n...and {len(users) - 50} more users"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_revenue")
async def callback_admin_revenue(callback: CallbackQuery) -> None:
    """Handle admin revenue button."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    total = db.get_total_revenue()
    stats = db.get_bot_statistics()
    
    revenue_text = (
        "💵 <b>Revenue Information</b>\n\n"
        f"💰 Total confirmed: {total:.2f} USDT\n"
        f"📊 Active subscribers: {stats['active_subscribers']}\n"
        f"⏳ Pending payments: {stats['pending_payments']}"
    )
    
    await callback.message.edit_text(
        revenue_text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle admin broadcast button."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\n"
        "Send the message you want to broadcast to all users.\n\n"
        "Use /broadcast <message> command or click Cancel.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_message)


# PolyTerm command callbacks
@router.callback_query(F.data.startswith("cmd_"))
async def callback_polyterm_command(callback: CallbackQuery, bot: Bot) -> None:
    """Handle PolyTerm command callbacks."""
    user_id = callback.from_user.id
    
    # Check subscription
    if not has_active_subscription(user_id):
        await callback.answer(
            "❌ Subscription required!",
            show_alert=True
        )
        await callback.message.edit_text(
            "❌ This feature requires an active subscription.\n\n"
            "Please subscribe to access all features.",
            reply_markup=get_subscription_plans_keyboard()
        )
        return
    
    # Get command key
    command_key = callback.data[4:]  # Remove "cmd_" prefix
    
    # Map to PolyTerm command
    command_map = {
        "monitor_markets": ("Monitor Markets", "monitor --limit 5 --once"),
        "live_monitor": ("Live Monitor", "monitor --refresh 5 --limit 5"),
        "whale_activity": ("Whale Activity", "whales --hours 24"),
        "watch_market": ("Watch Market", "quick watch"),
        "market_analytics": ("Market Analytics", "stats"),
        "portfolio": ("Portfolio", "portfolio"),
        "export_data": ("Export Data", "export --format json"),
        "settings": ("Settings", "config"),
        "arbitrage": ("Arbitrage", "arbitrage"),
        "predictions": ("Predictions", "predict"),
        "wallets": ("Wallets", "wallets"),
        "alerts": ("Alerts", "alerts"),
        "order_book": ("Order Book", "orderbook"),
        "risk_assessment": ("Risk Assessment", "risk"),
        "copy_trading": ("Copy Trading", "follow --list"),
        "parlay": ("Parlay", "parlay -i"),
        "bookmarks": ("Bookmarks", "bookmarks --list"),
        "dashboard": ("Dashboard", "dashboard"),
        "tutorial": ("Tutorial", "tutorial"),
        "glossary": ("Glossary", "glossary"),
        "simulate": ("Simulate P&L", "simulate -i"),
        "help": ("Help", "tutorial"),
        "tradingagents": ("TradingAgents Analysis", None),
    }
    
    if command_key == "tradingagents":
        await callback.message.edit_text(
            "⭐ <b>TradingAgents Analysis</b>\n\n"
            "Use the command:\n"
            "<code>/trade &lt;ticker&gt;</code>\n\n"
            "Examples:\n"
            "• <code>/trade AAPL</code> - Apple stock\n"
            "• <code>/trade BTC-USD</code> - Bitcoin\n"
            "• <code>/trade SPY</code> - S&P 500 ETF",
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    if command_key not in command_map:
        await callback.answer("❌ Unknown command", show_alert=True)
        return
    
    label, command = command_map[command_key]
    
    # Log command
    db.log_command(user_id, f"PolyTerm: {label}")
    
    await callback.message.edit_text(
        f"⏳ Running <b>{label}</b>...\n\nPlease wait...",
        parse_mode="HTML"
    )
    
    # Execute PolyTerm command
    result = polyterm.execute_polyterm_command(command)
    
    # Send result
    await send_long_message(
        callback.message,
        f"📊 <b>{label}</b>\n\n{result}",
        max_length=4096
    )
    
    await callback.message.answer(
        "🔙 Back to menu:",
        reply_markup=get_main_menu_keyboard(True)
    )


# Message handler for broadcast state
@router.message(BroadcastStates.waiting_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    """Process broadcast message from admin."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        await state.clear()
        await message.answer("❌ Access denied.")
        return
    
    broadcast_message = message.text
    
    # Send to all users
    users = db.get_all_users()
    success_count = 0
    error_count = 0
    
    status_msg = await message.answer("📤 Sending broadcast...")
    
    for user in users:
        try:
            await message.bot.send_message(
                user['user_id'],
                f"📢 <b>Broadcast Message:</b>\n\n{broadcast_message}",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {user['user_id']}: {e}")
            error_count += 1
    
    await state.clear()
    await status_msg.edit_text(
        f"✅ Broadcast sent!\n\nSuccess: {success_count}\nFailed: {error_count}",
        reply_markup=get_admin_keyboard()
    )
