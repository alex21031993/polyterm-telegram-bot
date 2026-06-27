"""
Определения клавиатур для PolyTerm Telegram бота.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard(is_subscribed: bool = False) -> InlineKeyboardMarkup:
    """Получить клавиатуру главного меню в зависимости от статуса подписки."""
    builder = InlineKeyboardBuilder()
    
    if is_subscribed:
        # Полное меню для подписанных пользователей
        builder.row(
            InlineKeyboardButton(text="1️⃣ Мониторинг рынков", callback_data="cmd_monitor_markets"),
            InlineKeyboardButton(text="2️⃣ Живой мониторинг", callback_data="cmd_live_monitor")
        )
        builder.row(
            InlineKeyboardButton(text="3️⃣ Активность китов", callback_data="cmd_whale_activity"),
            InlineKeyboardButton(text="4️⃣ Следить за рынком", callback_data="cmd_watch_market")
        )
        builder.row(
            InlineKeyboardButton(text="5️⃣ Аналитика рынка", callback_data="cmd_market_analytics"),
            InlineKeyboardButton(text="6️⃣ Портфель", callback_data="cmd_portfolio")
        )
        builder.row(
            InlineKeyboardButton(text="7️⃣ Экспорт данных", callback_data="cmd_export_data"),
            InlineKeyboardButton(text="8️⃣ Настройки", callback_data="cmd_settings")
        )
        builder.row(
            InlineKeyboardButton(text="9️⃣ Арбитраж", callback_data="cmd_arbitrage"),
            InlineKeyboardButton(text="🔟 Прогнозы", callback_data="cmd_predictions")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣1️⃣ Кошельки", callback_data="cmd_wallets"),
            InlineKeyboardButton(text="1️⃣2️⃣ Оповещения", callback_data="cmd_alerts")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣3️⃣ Книга ордеров", callback_data="cmd_order_book"),
            InlineKeyboardButton(text="1️⃣4️⃣ Оценка рисков", callback_data="cmd_risk_assessment")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣5️⃣ Копи-трейдинг", callback_data="cmd_copy_trading"),
            InlineKeyboardButton(text="1️⃣6️⃣ Парлай", callback_data="cmd_parlay")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣7️⃣ Закладки", callback_data="cmd_bookmarks"),
            InlineKeyboardButton(text="📊 Панель управления", callback_data="cmd_dashboard")
        )
        builder.row(
            InlineKeyboardButton(text="📖 Обучение", callback_data="cmd_tutorial"),
            InlineKeyboardButton(text="📚 Глоссарий", callback_data="cmd_glossary")
        )
        builder.row(
            InlineKeyboardButton(text="💹 Симуляция P&L", callback_data="cmd_simulate"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="cmd_help")
        )
        builder.row(
            InlineKeyboardButton(text="⭐ TradingAgents анализ", callback_data="cmd_tradingagents")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Моя статистика", callback_data="cmd_my_stats"),
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="cmd_back_main")
        )
    else:
        # Ограниченное меню для неподписанных пользователей
        builder.row(
            InlineKeyboardButton(text="✅ Проверить подписку", callback_data="cmd_check_subscription")
        )
        builder.row(
            InlineKeyboardButton(text="💳 Купить подписку", callback_data="cmd_buy_subscription")
        )
        builder.row(
            InlineKeyboardButton(text="📊 Моя статистика", callback_data="cmd_my_stats")
        )
    
    return builder.as_markup()


def get_subscription_plans_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру для выбора тарифного плана."""
    from .data.config import SUBSCRIBE_AMOUNT_BY_PLANS
    
    builder = InlineKeyboardBuilder()
    
    for months, price in SUBSCRIBE_AMOUNT_BY_PLANS.items():
        if months == 1:
            label = f"📅 1 Месяц - {price:.2f} USDT"
        elif months == 12:
            label = f"📅 12 Месяцев - {price:.2f} USDT"
        else:
            label = f"📅 {months} Месяцев - {price:.2f} USDT"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"sub_plan_{months}")
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="cmd_back_main")
    )
    
    return builder.as_markup()


def get_payment_keyboard(plan_months: int, amount: float) -> InlineKeyboardMarkup:
    """Получить клавиатуру с адресом оплаты и подтверждением."""
    from .data.config import USDT_TRC20_WALLET_ADDRESS
    
    builder = InlineKeyboardBuilder()
    
    # Информация об оплате
    wallet = USDT_TRC20_WALLET_ADDRESS
    builder.row(
        InlineKeyboardButton(text="📋 Копировать адрес кошелька", callback_data="copy_wallet")
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Я оплатил - Проверить платеж",
            callback_data=f"check_payment_{plan_months}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="cmd_buy_subscription")
    )
    
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру админ-панели."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats"),
        InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_users")
    )
    builder.row(
        InlineKeyboardButton(text="💵 Доходы", callback_data="admin_revenue"),
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="cmd_back_main")
    )
    
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура возврата в меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="cmd_back_main")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены операции."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cmd_cancel")
    )
    return builder.as_markup()
