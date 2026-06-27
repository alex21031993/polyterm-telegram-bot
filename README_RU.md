# PolyTerm Telegram Бот

Телеграм-бот, который объединяет PolyTerm (терминальный клиент для Polymarket) и TradingAgents (AI-анализ рынка) с системой подписки через USDT TRC20.

## Функции

- **Интеграция PolyTerm**: Доступ к 23 командам PolyTerm через кнопки Телеграм
- **TradingAgents Анализ**: AI-анализ рынка для акций, криптовалют и ETF
- **USDT TRC20 Платежи**: Автоматическая система подписки через TronGrid API
- **Админ-панель**: Статистика, управление пользователями и рассылка сообщений
- **SQLite База данных**: Локальное хранение пользователей, платежей и логов команд

## Требования

- Python 3.11+
- PolyTerm (установлен в `/home/alexandr/.local/bin/polyterm`)
- TradingAgents фреймворк (настраивается через `TRADINGAGENTS_PATH`)
- Telegram Bot Token

## Установка

### 1. Создайте директорию проекта

```bash
mkdir -p ~/subscribe
cd ~/subscribe
```

### 2. Создайте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Настройте бота

Создайте файл `.env`:

```bash
BOT_TOKEN=ваш_telegram_bot_token
ADMIN_PASSWORD=Alex1234$
```

### 5. Инициализируйте базу данных

```bash
cd ~/subscribe
rm -rf db/database.db*
mkdir -p db
```

### 6. Настройте путь к TradingAgents (опционально)

Если TradingAgents не находится в `/workspace`, укажите путь в config.py или через переменную окружения:

```bash
export TRADINGAGENTS_PATH=/путь/к/tradingagents
```

### 7. Запустите бота

```bash
source venv/bin/activate
python -m src.bot.app
```

## Структура проекта

```
~/subscribe/
├── src/
│   └── bot/
│       ├── app.py              # Главная точка входа
│       ├── handlers.py         # Обработчики команд и callback'ов
│       ├── keyboards.py        # Определения inline-клавиатур
│       ├── database.py         # Операции с SQLite базой данных
│       ├── polyterm.py         # Исполнитель команд PolyTerm
│       ├── tradingagents.py    # Модуль интеграции TradingAgents
│       ├── payment.py          # Верификация USDT TRC20 платежей
│       └── data/
│           └── config.py       # Конфигурационные константы
├── db/
│   └── database.db             # SQLite база данных (создается при первом запуске)
├── .env                        # Переменные окружения
└── requirements.txt            # Python зависимости
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/help` | Показать справку |
| `/status` | Проверить статус подписки |
| `/subscribe` | Купить подписку |
| `/trade <тикер>` | TradingAgents анализ |
| `/admin_login <пароль>` | Вход для админа |
| `/admin` | Админ-панель |
| `/broadcast <сообщение>` | Рассылка сообщений (админ) |

## Планы подписки

| План | Цена |
|------|-------|
| 1 Месяц | 9.99 USDT |
| 3 Месяца | 14.99 USDT |
| 6 Месяцев | 19.99 USDT |
| 12 Месяцев | 34.99 USDT |

## Платежная информация

- **Адрес кошелька**: `TCSYEiTBp67GvUk3f2f1foL1jDRKu6upD8`
- **USDT Контракт**: `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`
- **Сеть**: TRC20

## Команды PolyTerm (23 кнопки)

1. Мониторинг рынков
2. Живой мониторинг
3. Активность китов
4. Следить за рынком
5. Аналитика рынка
6. Портфель
7. Экспорт данных
8. Настройки
9. Арбитраж
10. Прогнозы
11. Кошельки
12. Оповещения
13. Книга ордеров
14. Оценка рисков
15. Копи-трейдинг
16. Парлай
17. Закладки
18. Панель управления
19. Обучение
20. Глоссарий
21. Симуляция P&L
22. Помощь
23. TradingAgents Анализ

## TradingAgents Анализ

Бот интегрирован с фреймворком TradingAgents для AI-анализа рынка.

### Поддерживаемые тикеры

**Акции**: AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META, AMD, INTC, NFLX

**Криптовалюта**: BTC-USD, ETH-USD, SOL-USD, BNB-USD, XRP-USD

**ETF**: SPY, QQQ, DIA, IWM, VTI

### Использование

```
/trade AAPL     # Анализ акций
/trade BTC-USD  # Анализ криптовалюты
/trade SPY      # Анализ ETF
```

### Как это работает

1. Бот проверяет тикер символ
2. Запускает многоагентный AI-пайплайн анализа TradingAgents
3. Возвращает решение (BUY/SELL/HOLD) с поддерживающим анализом

## Функции модуля TradingAgents

Модуль `tradingagents.py` предоставляет следующие функции:

### `check_tradingagents_installed()`
- Проверяет доступность фреймворка TradingAgents
- Возвращает: `bool`

### `get_ticker_info(ticker)`
- Получить тип и информацию о тикере
- Параметры: `ticker` (str) - символ тикера
- Возвращает: `dict` с ключами: `type` ("stock"/"crypto"/"etf"), `name`

### `validate_ticker(ticker)`
- Проверить поддержку тикера
- Параметры: `ticker` (str) - символ тикера
- Возвращает: `Tuple[bool, str]` - (валидность, нормализованный_тикер_или_ошибка)

### `run_trading_analysis(ticker, trade_date=None, debug=False)`
- Запустить TradingAgents анализ для тикера
- Параметры:
  - `ticker` (str) - символ акции, криптовалюты или ETF
  - `trade_date` (str, опционально) - дата анализа (YYYY-MM-DD), по умолчанию сегодня
  - `debug` (bool) - режим отладки
- Возвращает: `Tuple[str, Optional[str]]` - (результат_анализа, сообщение_об_ошибке)

### `format_analysis_result(ticker, ticker_info, decision)`
- Форматировать результат анализа для отображения в Телеграм
- Параметры: ticker, ticker_info dict, decision string
- Возвращает: `str` - форматированное сообщение

### `get_supported_tickers_list()`
- Получить форматированный список поддерживаемых тикеров
- Возвращает: `str` - HTML форматированный список

## Функции админа

- Доступ ко всем функциям без подписки
- Просмотр статистики бота
- Просмотр списка пользователей
- Просмотр информации о доходах
- Рассылка сообщений всем пользователям

## Структура базы данных

### users (пользователи)
- `user_id` (PRIMARY KEY)
- `username`
- `full_name`
- `subscribed_until`
- `subscription_active`
- `created_at`
- `last_active`
- `is_admin`

### payments (платежи)
- `id` (PRIMARY KEY)
- `user_id`
- `amount`
- `tx_hash` (UNIQUE)
- `plan_months`
- `status`
- `created_at`
- `confirmed_at`

### admins (админы)
- `user_id` (PRIMARY KEY)
- `added_at`

### command_log (лог команд)
- `id` (PRIMARY KEY)
- `user_id`
- `command`
- `executed_at`

## Логирование

Все действия бота логируются:
- Команды пользователей
- Платежные транзакции
- Ошибки и исключения
- Действия админов
- Запросы TradingAgents анализа

## Безопасность

- Bot token хранится в файле `.env`
- Пароль админа в конфигурации
- Проверка подписки перед выполнением команд
- Валидация хеша транзакции
- Защита от таймаута команд

## Решение проблем

### Бот не отвечает
1. Проверьте корректность bot token в `.env`
2. Убедитесь, что виртуальное окружение активировано
3. Проверьте логи на ошибки

### Платеж не подтвержден
1. Убедитесь, что транзакция отправлена на правильный адрес
2. Проверьте подтверждения блокчейна
3. Убедитесь, что использовалась сеть TRC20
4. Подождите до 20 минут для автоопределения

### Команды PolyTerm не работают
1. Проверьте, что PolyTerm установлен по указанному пути
2. Проверьте, что PolyTerm есть в системном PATH
3. Протестируйте PolyTerm вручную в терминале

### TradingAgents анализ не работает
1. Проверьте правильность пути к TradingAgents в config.py
2. Убедитесь, что все зависимости установлены (yfinance, tradingagents)
3. Проверьте настройку LLM API ключей в .env файле TradingAgents

## Лицензия

MIT License
