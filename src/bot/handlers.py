"""
Модуль обработчиков для PolyTerm Telegram бота.
Содержит все обработчики сообщений и callback-запросов.
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
from . import tradingagents
from .keyboards import (
    get_main_menu_keyboard,
    get_subscription_plans_keyboard,
    get_payment_keyboard,
    get_admin_keyboard,
    get_back_to_menu_keyboard,
    get_cancel_keyboard,
)

logger = logging.getLogger(__name__)

router = Router()

# In-memory storage for pending payments
pending_payments: dict = {}


class AdminStates(StatesGroup):
    """Состояния для операций администратора."""
    waiting_broadcast = State()
    waiting_txhash = State()


class BroadcastStates(StatesGroup):
    """Состояния для рассылки сообщений."""
    waiting_message = State()


def is_user_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом."""
    return db.is_admin(user_id)


def has_active_subscription(user_id: int) -> bool:
    """Проверить наличие активной подписки у пользователя."""
    if is_user_admin(user_id):
        return True
    return db.check_subscription_active(user_id)


async def send_long_message(message: Message, text: str, max_length: int = 4096) -> None:
    """Отправить длинное сообщение, разбив его при необходимости."""
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


# Обработчики команд
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработка команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Создать или обновить пользователя
    db.create_user(user_id, username, full_name)
    
    welcome_text = (
        "👋 Добро пожаловать в <b>PolyTerm Бот</b>!\n\n"
        "Я предоставляю доступ к командам PolyTerm и анализу TradingAgents.\n\n"
    )
    
    if has_active_subscription(user_id):
        welcome_text += "✅ У вас активная подписка.\n\nВыберите опцию из меню ниже:"
    else:
        welcome_text += (
            "❌ У вас нет активной подписки.\n\n"
            "Подпишитесь, чтобы получить доступ ко всем функциям!\n\n"
            "💰 Тарифы:\n"
            "• 1 месяц - 9.99 USDT\n"
            "• 3 месяца - 14.99 USDT\n"
            "• 6 месяцев - 19.99 USDT\n"
            "• 12 месяцев - 34.99 USDT"
        )
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_active_subscription(user_id))
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработка команды /help."""
    help_text = """📖 <b>PolyTerm Бот - Полная справка</b>

━━━━━━━━━━━━━━━━━━━━

<b>📊 Команды меню:</b>

1️⃣ Мониторинг рынков - Отслеживание рынков в реальном времени
2️⃣ Живой мониторинг - Отдельное окно терминала
3️⃣ Активность китов - Рыночная активность крупных игроков
4️⃣ Следить за рынком - Отслеживание конкретного рынка
5️⃣ Аналитика рынка - Тренды и прогнозы
6️⃣ Портфель - Просмотр ваших позиций
7️⃣ Экспорт данных - Экспорт в JSON/CSV
8️⃣ Настройки - Конфигурация

━━━━━━━━━━━━━━━━━━━━

<b>💰 Дополнительные функции:</b>

📈 Arbitrage - Сканирование арбитражных возможностей
🔮 Predictions - Сигнальный анализ
👛 Wallets - Отслеживание умных денег
🔔 Alerts - Управление уведомлениями
📖 Order Book - Анализ глубины рынка
🛡️ Risk - Оценка рыночных рисков
👥 Copy Trading - Копирование кошельков
🎰 Parlay - Комбинирование ставок
🔖 Bookmarks - Сохранённые рынки

━━━━━━━━━━━━━━━━━━━━

<b>⚡ Быстрые команды:</b>

/trade AAPL - Анализ акций Apple
/trade BTC-USD - Анализ Bitcoin
/trade TSLA - Анализ акций Tesla
/trade SPY - Анализ ETF S&P 500

━━━━━━━━━━━━━━━━━━━━

<b>🔑 Команды администратора:</b>

/admin_login Alex1234$ - Вход для админа
/broadcast <текст> - Рассылка

━━━━━━━━━━━━━━━━━━━━

<b>💡 Поддерживаемые тикеры:</b>

📈 Акции: AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META, AMD, INTC, NFLX
₿ Крипто: BTC-USD, ETH-USD, SOL-USD, BNB-USD, XRP-USD
📊 ETF: SPY, QQQ, DIA, IWM, VTI

━━━━━━━━━━━━━━━━━━━━

<b>📚 Информация:</b>

API Status:
✅ Gamma API - Рыночные данные в реальном времени
✅ CLOB API - Данные книги ордеров

💰 Тарифы подписки:
• 1 месяц - 9.99 USDT
• 3 месяца - 14.99 USDT
• 6 месяцев - 19.99 USDT
• 12 месяцев - 34.99 USDT"""
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Обработка команды /status."""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден.")
        return
    
    if is_user_admin(user_id):
        status_text = "✅ <b>Статус:</b> Администратор\n"
    elif has_active_subscription(user_id):
        subscribed_until = datetime.fromisoformat(user['subscribed_until'])
        status_text = (
            f"✅ <b>Подписка активна</b>\n\n"
            f"📅 Истекает: {subscribed_until.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        status_text = (
            "❌ <b>Нет активной подписки</b>\n\n"
            "Используйте /subscribe для покупки подписки."
        )
    
    await message.answer(status_text, parse_mode="HTML")


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    """Обработка команды /subscribe."""
    user_id = message.from_user.id
    
    if has_active_subscription(user_id):
        await message.answer(
            "✅ У вас уже есть активная подписка!\n\nИспользуйте /status для проверки деталей подписки.",
            reply_markup=get_main_menu_keyboard(True)
        )
        return
    
    await message.answer(
        "💳 <b>Выберите тарифный план</b>\n\nВыберите подходящий вам план:",
        parse_mode="HTML",
        reply_markup=get_subscription_plans_keyboard()
    )


@router.message(Command("admin_login"))
async def cmd_admin_login(message: Message) -> None:
    """Обработка команды /admin_login."""
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer("❌ Использование: /admin_login <пароль>")
        return
    
    password = parts[1]
    
    if password != ADMIN_PASSWORD:
        await message.answer("❌ Неверный пароль.")
        logger.warning(f"Неудачная попытка входа админа от пользователя {user_id}")
        return
    
    # Добавить как админа
    db.add_admin(user_id)
    
    # Обновить статус админа пользователя
    with db.get_db_cursor() as cursor:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
    
    logger.info(f"Пользователь {user_id} вошел как админ")
    await message.answer(
        "✅ Успешный вход в качестве администратора!",
        reply_markup=get_admin_keyboard()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Обработка команды /admin."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        await message.answer("❌ Доступ запрещен. Только для администраторов.")
        return
    
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\nВыберите опцию:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    """Обработка команды /broadcast."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        await message.answer("❌ Доступ запрещен. Только для администраторов.")
        return
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer("❌ Использование: /broadcast <сообщение>")
        return
    
    broadcast_message = parts[1]
    
    # Отправить всем пользователям
    users = db.get_all_users()
    success_count = 0
    error_count = 0
    
    status_msg = await message.answer("📤 Отправка рассылки...")
    
    for user in users:
        try:
            # Экранируем HTML символы для безопасности
            safe_message = broadcast_message.replace("<", "&lt;").replace(">", "&gt;")
            
            await message.bot.send_message(
                user['user_id'],
                f"📢 <b>Сообщение:</b>\n\n{safe_message}",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Не удалось отправить пользователю {user['user_id']}: {e}")
            error_count += 1
    
    await status_msg.edit_text(
        f"✅ Рассылка отправлена!\n\nУспешно: {success_count}\nНеудачно: {error_count}"
    )


@router.message(Command("trade"))
async def cmd_trade(message: Message) -> None:
    """Обработка команды /trade для TradingAgents анализа."""
    user_id = message.from_user.id
    
    # Проверка подписки
    if not has_active_subscription(user_id):
        await message.answer(
            "❌ Эта функция требует активной подписки.\n\nИспользуйте /subscribe для покупки.",
            reply_markup=get_subscription_plans_keyboard()
        )
        return
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        # Показать поддерживаемые тикеры
        supported_list = tradingagents.get_supported_tickers_list()
        await message.answer(
            f"❌ Использование: /trade <тикер>\n\n{supported_list}",
            parse_mode="HTML"
        )
        return
    
    ticker = parts[1].upper().strip()
    
    # Валидация тикера
    is_valid, validation_result = tradingagents.validate_ticker(ticker)
    
    if not is_valid:
        await message.answer(
            f"❌ Неверный тикер: {validation_result}\n\n"
            f"Используйте /trade <тикер> с поддерживаемым тикером.",
            parse_mode="HTML"
        )
        return
    
    ticker = validation_result  # Использовать нормализованный тикер
    
    # Записать команду
    db.log_command(user_id, f"/trade {ticker}")
    
    status_msg = await message.answer(
        f"🔍 Запуск TradingAgents анализа для <b>{ticker}</b>...\n\n"
        "⏳ Это может занять 2-5 минут. Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    # Запустить TradingAgents анализ
    try:
        result, error = await tradingagents.run_trading_analysis(ticker)
        
        if error:
            await status_msg.edit_text(
                f"{error}\n\nПопробуйте снова или обратитесь в поддержку.",
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
        else:
            await status_msg.edit_text(
                result,
                parse_mode="HTML",
                reply_markup=get_back_to_menu_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка TradingAgents для {ticker}: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при выполнении анализа: {str(e)}",
            reply_markup=get_back_to_menu_keyboard()
        )


# Обработчики callback-запросов
@router.callback_query(F.data == "cmd_back_main")
async def callback_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка возврата в главное меню."""
    await state.clear()
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_active_subscription(user_id))
    )


@router.callback_query(F.data == "cmd_cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка отмены операции."""
    await state.clear()
    await callback.answer("❌ Отменено")
    await callback.message.edit_text(
        "Операция отменена.",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data == "cmd_check_subscription")
async def callback_check_subscription(callback: CallbackQuery) -> None:
    """Обработка кнопки проверки подписки."""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if is_user_admin(user_id):
        text = "✅ <b>Статус:</b> Администратор\n"
    elif has_active_subscription(user_id):
        subscribed_until = datetime.fromisoformat(user['subscribed_until'])
        text = (
            f"✅ <b>Подписка активна</b>\n\n"
            f"📅 Истекает: {subscribed_until.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        text = (
            "❌ <b>Нет активной подписки</b>\n\n"
            "Нажмите ниже для подписки:"
        )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(has_active_subscription(user_id))
    )


@router.callback_query(F.data == "cmd_buy_subscription")
async def callback_buy_subscription(callback: CallbackQuery) -> None:
    """Обработка кнопки покупки подписки."""
    await callback.message.edit_text(
        "💳 <b>Выберите тарифный план</b>\n\nВыберите подходящий вам план:",
        parse_mode="HTML",
        reply_markup=get_subscription_plans_keyboard()
    )


@router.callback_query(F.data == "cmd_my_stats")
async def callback_my_stats(callback: CallbackQuery) -> None:
    """Обработка кнопки моей статистики."""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    # Получить количество команд пользователя
    with db.get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM command_log WHERE user_id = ?",
            (user_id,)
        )
        command_count = cursor.fetchone()[0]
    
    created_at = datetime.fromisoformat(user['created_at']).strftime('%Y-%m-%d') if user else 'N/A'
    
    stats_text = (
        "📊 <b>Ваша статистика</b>\n\n"
        f"👤 ID пользователя: {user_id}\n"
        f"📅 Участник с: {created_at}\n"
        f"⚡ Использовано команд: {command_count}\n"
    )
    
    if has_active_subscription(user_id) and user:
        subscribed_until = datetime.fromisoformat(user['subscribed_until'])
        stats_text += f"📅 Подписка истекает: {subscribed_until.strftime('%Y-%m-%d')}"
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data.startswith("sub_plan_"))
async def callback_subscription_plan(callback: CallbackQuery) -> None:
    """Обработка выбора тарифного плана."""
    user_id = callback.from_user.id
    plan_months = int(callback.data.split("_")[-1])
    amount = SUBSCRIBE_AMOUNT_BY_PLANS[plan_months]
    
    # Сохранить в памяти для верификации платежа
    pending_payments[user_id] = {
        'plan_months': plan_months,
        'amount': amount
    }
    
    plan_name = "1 месяц" if plan_months == 1 else f"{plan_months} месяцев"
    
    payment_text = (
        "💳 <b>Инструкция по оплате</b>\n\n"
        f"Тариф: {plan_name}\n"
        f"Сумма: <code>{amount:.2f} USDT</code>\n\n"
        f"<b>⚠️ Важно:</b>\n"
        f"1. Отправьте ровно <code>{amount:.2f} USDT</code> на адрес ниже\n"
        f"2. Используйте <b>только сеть TRC20</b>\n"
        f"3. После оплаты нажмите 'Я оплатил'\n\n"
        f"<b>Адрес кошелька:</b>\n"
        f"<code>{USDT_TRC20_WALLET_ADDRESS}</code>\n\n"
        f"<b>USDT контракт:</b>\n"
        f"<code>{USDT_CONTRACT}</code>"
    )
    
    await callback.message.edit_text(
        payment_text,
        parse_mode="HTML",
        reply_markup=get_payment_keyboard(plan_months, amount)
    )


@router.callback_query(F.data.startswith("check_payment_"))
async def callback_check_payment(callback: CallbackQuery, bot: Bot) -> None:
    """Обработка кнопки проверки платежа."""
    user_id = callback.from_user.id
    plan_months = int(callback.data.split("_")[-1])
    
    # Получить сохраненную информацию о платеже
    payment_info = pending_payments.get(user_id, {})
    amount = payment_info.get('amount', SUBSCRIBE_AMOUNT_BY_PLANS.get(plan_months, 9.99))
    
    status_msg = await callback.message.edit_text(
        f"⏳ Проверка платежа {amount:.2f} USDT...\n\n"
        "Это может занять до 20 минут. Вы получите уведомление при подтверждении платежа."
    )
    
    # Запустить мониторинг платежа в фоне
    asyncio.create_task(
        payment.monitor_payment(user_id, amount, plan_months, bot, callback.message.chat.id)
    )
    
    await asyncio.sleep(3)
    await status_msg.edit_text(
        f"🔄 Мониторинг платежа...\n\n"
        f"Ожидаемая сумма: {amount:.2f} USDT\n"
        f"Тариф: {plan_months} мес.\n\n"
        f"Убедитесь, что отправили платеж на:\n"
        f"<code>{USDT_TRC20_WALLET_ADDRESS}</code>\n\n"
        "Вы получите уведомление при подтверждении платежа.",
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(F.data == "copy_wallet")
async def callback_copy_wallet(callback: CallbackQuery) -> None:
    """Обработка кнопки копирования кошелька."""
    await callback.answer("📋 Адрес кошелька скопирован!", show_alert=True)


# Обработчики админ-панели
@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery) -> None:
    """Обработка кнопки статистики бота."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    stats = db.get_bot_statistics()
    
    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"✅ Активных подписчиков: {stats['active_subscribers']}\n"
        f"💰 Общий доход: {stats['total_revenue']:.2f} USDT\n"
        f"⏳ Ожидающих платежей: {stats['pending_payments']}"
    )
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery) -> None:
    """Обработка кнопки списка пользователей."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    users = db.get_all_users()
    
    if not users:
        text = "Пользователей пока нет."
    else:
        text = "👥 <b>Список пользователей</b>\n\n"
        for i, user in enumerate(users[:50], 1):  # Лимит 50 пользователей
            status = "✅" if user['subscription_active'] else "❌"
            admin = "👑" if user['is_admin'] else ""
            text += f"{i}. {user['user_id']} {status}{admin}\n"
        
        if len(users) > 50:
            text += f"\n...и еще {len(users) - 50} пользователей"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_revenue")
async def callback_admin_revenue(callback: CallbackQuery) -> None:
    """Обработка кнопки дохода."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    total = db.get_total_revenue()
    stats = db.get_bot_statistics()
    
    revenue_text = (
        "💵 <b>Информация о доходах</b>\n\n"
        f"💰 Всего подтверждено: {total:.2f} USDT\n"
        f"📊 Активных подписчиков: {stats['active_subscribers']}\n"
        f"⏳ Ожидающих платежей: {stats['pending_payments']}"
    )
    
    await callback.message.edit_text(
        revenue_text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка кнопки рассылки."""
    user_id = callback.from_user.id
    
    if not is_user_admin(user_id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям.\n\n"
        "Используйте команду /broadcast <сообщение> или нажмите Отмена.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_message)


# Обработчики команд PolyTerm
@router.callback_query(F.data.startswith("cmd_"))
async def callback_polyterm_command(callback: CallbackQuery, bot: Bot) -> None:
    """Обработка callback-запросов команд PolyTerm."""
    user_id = callback.from_user.id
    
    # Проверка подписки
    if not has_active_subscription(user_id):
        await callback.answer(
            "❌ Требуется подписка!",
            show_alert=True
        )
        await callback.message.edit_text(
            "❌ Эта функция требует активной подписки.\n\n"
            "Пожалуйста, подпишитесь для доступа ко всем функциям.",
            reply_markup=get_subscription_plans_keyboard()
        )
        return
    
    # Получить ключ команды
    command_key = callback.data[4:]  # Убрать префикс "cmd_"
    
    # Соответствие команд PolyTerm
    command_map = {
        "monitor_markets": ("Мониторинг рынков", "monitor --limit 5 --once"),
        "live_monitor": ("Живой мониторинг", "monitor --refresh 5 --limit 5"),
        "whale_activity": ("Активность китов", "whales --hours 24"),
        "watch_market": ("Следить за рынком", "quick watch"),
        "market_analytics": ("Аналитика рынка", "stats"),
        "portfolio": ("Портфель", "portfolio"),
        "export_data": ("Экспорт данных", "export --format json"),
        "settings": ("Настройки", "config"),
        "arbitrage": ("Арбитраж", "arbitrage"),
        "predictions": ("Прогнозы", "predict"),
        "wallets": ("Кошельки", "wallets"),
        "alerts": ("Оповещения", "alerts"),
        "order_book": ("Книга ордеров", "orderbook"),
        "risk_assessment": ("Оценка рисков", "risk"),
        "copy_trading": ("Копи-трейдинг", "follow --list"),
        "parlay": ("Парлай", "parlay -i"),
        "bookmarks": ("Закладки", "bookmarks --list"),
        "dashboard": ("Панель управления", "dashboard"),
        "tutorial": ("Обучение", "tutorial"),
        "glossary": ("Глоссарий", "glossary"),
        "simulate": ("Симуляция P&L", "simulate -i"),
        "help": ("Помощь", "tutorial"),
        "tradingagents": ("TradingAgents анализ", None),
    }
    
    if command_key == "tradingagents":
        await callback.message.edit_text(
            "⭐ <b>TradingAgents анализ</b>\n\n"
            "Используйте команду:\n"
            "<code>/trade &lt;тикер&gt;</code>\n\n"
            "Примеры:\n"
            "• <code>/trade AAPL</code> - Акции Apple\n"
            "• <code>/trade BTC-USD</code> - Биткоин\n"
            "• <code>/trade SPY</code> - ETF S&P 500",
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    if command_key not in command_map:
        await callback.answer("❌ Неизвестная команда", show_alert=True)
        return
    
    label, command = command_map[command_key]
    
    # Записать команду
    db.log_command(user_id, f"PolyTerm: {label}")
    
    await callback.message.edit_text(
        f"⏳ Выполнение <b>{label}</b>...\n\nПожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    # Выполнить команду PolyTerm
    result = polyterm.execute_polyterm_command(command)
    
    # Отправить результат
    await send_long_message(
        callback.message,
        f"📊 <b>{label}</b>\n\n{result}",
        max_length=4096
    )
    
    await callback.message.answer(
        "🔙 Вернуться в меню:",
        reply_markup=get_main_menu_keyboard(True)
    )


# Обработчик сообщений для состояния рассылки
@router.message(BroadcastStates.waiting_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    """Обработка сообщения рассылки от админа."""
    user_id = message.from_user.id
    
    if not is_user_admin(user_id):
        await state.clear()
        await message.answer("❌ Доступ запрещен.")
        return
    
    broadcast_message = message.text
    
    # Отправить всем пользователям
    users = db.get_all_users()
    success_count = 0
    error_count = 0
    
    status_msg = await message.answer("📤 Отправка рассылки...")
    
    for user in users:
        try:
            # Экранируем HTML символы для безопасности
            safe_message = broadcast_message.replace("<", "&lt;").replace(">", "&gt;")
            
            await message.bot.send_message(
                user['user_id'],
                f"📢 <b>Сообщение:</b>\n\n{safe_message}",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Не удалось отправить пользователю {user['user_id']}: {e}")
            error_count += 1
    
    await state.clear()
    await status_msg.edit_text(
        f"✅ Рассылка отправлена!\n\nУспешно: {success_count}\nНеудачно: {error_count}",
        reply_markup=get_admin_keyboard()
    )
