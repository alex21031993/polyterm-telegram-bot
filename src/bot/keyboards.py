"""
Keyboard definitions for PolyTerm Telegram Bot.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard(is_subscribed: bool = False) -> InlineKeyboardMarkup:
    """Get main menu keyboard based on subscription status."""
    builder = InlineKeyboardBuilder()
    
    if is_subscribed:
        # Full menu for subscribed users
        builder.row(
            InlineKeyboardButton(text="1️⃣ Monitor Markets", callback_data="cmd_monitor_markets"),
            InlineKeyboardButton(text="2️⃣ Live Monitor", callback_data="cmd_live_monitor")
        )
        builder.row(
            InlineKeyboardButton(text="3️⃣ Whale Activity", callback_data="cmd_whale_activity"),
            InlineKeyboardButton(text="4️⃣ Watch Market", callback_data="cmd_watch_market")
        )
        builder.row(
            InlineKeyboardButton(text="5️⃣ Market Analytics", callback_data="cmd_market_analytics"),
            InlineKeyboardButton(text="6️⃣ Portfolio", callback_data="cmd_portfolio")
        )
        builder.row(
            InlineKeyboardButton(text="7️⃣ Export Data", callback_data="cmd_export_data"),
            InlineKeyboardButton(text="8️⃣ Settings", callback_data="cmd_settings")
        )
        builder.row(
            InlineKeyboardButton(text="9️⃣ Arbitrage", callback_data="cmd_arbitrage"),
            InlineKeyboardButton(text="🔟 Predictions", callback_data="cmd_predictions")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣1️⃣ Wallets", callback_data="cmd_wallets"),
            InlineKeyboardButton(text="1️⃣2️⃣ Alerts", callback_data="cmd_alerts")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣3️⃣ Order Book", callback_data="cmd_order_book"),
            InlineKeyboardButton(text="1️⃣4️⃣ Risk Assessment", callback_data="cmd_risk_assessment")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣5️⃣ Copy Trading", callback_data="cmd_copy_trading"),
            InlineKeyboardButton(text="1️⃣6️⃣ Parlay", callback_data="cmd_parlay")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣7️⃣ Bookmarks", callback_data="cmd_bookmarks"),
            InlineKeyboardButton(text="📊 Dashboard", callback_data="cmd_dashboard")
        )
        builder.row(
            InlineKeyboardButton(text="📖 Tutorial", callback_data="cmd_tutorial"),
            InlineKeyboardButton(text="📚 Glossary", callback_data="cmd_glossary")
        )
        builder.row(
            InlineKeyboardButton(text="💹 Simulate P&L", callback_data="cmd_simulate"),
            InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")
        )
        builder.row(
            InlineKeyboardButton(text="⭐ TradingAgents Analysis", callback_data="cmd_tradingagents")
        )
        builder.row(
            InlineKeyboardButton(text="📊 My Stats", callback_data="cmd_my_stats"),
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="cmd_back_main")
        )
    else:
        # Limited menu for non-subscribed users
        builder.row(
            InlineKeyboardButton(text="✅ Check Subscription", callback_data="cmd_check_subscription")
        )
        builder.row(
            InlineKeyboardButton(text="💳 Buy Subscription", callback_data="cmd_buy_subscription")
        )
        builder.row(
            InlineKeyboardButton(text="📊 My Stats", callback_data="cmd_my_stats")
        )
    
    return builder.as_markup()


def get_subscription_plans_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for subscription plan selection."""
    from .data.config import SUBSCRIBE_AMOUNT_BY_PLANS
    
    builder = InlineKeyboardBuilder()
    
    for months, price in SUBSCRIBE_AMOUNT_BY_PLANS.items():
        if months == 1:
            label = f"📅 1 Month - {price:.2f} USDT"
        elif months == 12:
            label = f"📅 12 Months - {price:.2f} USDT"
        else:
            label = f"📅 {months} Months - {price:.2f} USDT"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"sub_plan_{months}")
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cmd_back_main")
    )
    
    return builder.as_markup()


def get_payment_keyboard(plan_months: int, amount: float) -> InlineKeyboardMarkup:
    """Get keyboard with payment address and confirmation."""
    from .data.config import USDT_TRC20_WALLET_ADDRESS
    
    builder = InlineKeyboardBuilder()
    
    # Payment info
    wallet = USDT_TRC20_WALLET_ADDRESS
    builder.row(
        InlineKeyboardButton(text="📋 Copy Wallet Address", callback_data=f"copy_wallet")
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ I've Paid - Check Payment",
            callback_data=f"check_payment_{plan_months}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cmd_buy_subscription")
    )
    
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Bot Statistics", callback_data="admin_stats"),
        InlineKeyboardButton(text="📋 Users List", callback_data="admin_users")
    )
    builder.row(
        InlineKeyboardButton(text="💵 Revenue", callback_data="admin_revenue"),
        InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="cmd_back_main")
    )
    
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple back to menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Menu", callback_data="cmd_back_main")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel operation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Cancel", callback_data="cmd_cancel")
    )
    return builder.as_markup()
