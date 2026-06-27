# PolyTerm Telegram Bot

A complete Telegram bot that integrates PolyTerm (terminal client for Polymarket) and TradingAgents (AI-powered market analysis) with a USDT TRC20 subscription system.

## Features

- **PolyTerm Integration**: Access all 23 PolyTerm commands via Telegram buttons
- **TradingAgents Analysis**: AI-powered market analysis for stocks, crypto, and ETFs
- **USDT TRC20 Payments**: Automated subscription system via TronGrid API
- **Admin Panel**: Statistics, user management, and broadcast messaging
- **SQLite Database**: Local storage for users, payments, and command logs

## Requirements

- Python 3.11+
- PolyTerm (installed at `/home/alexandr/.local/bin/polyterm`)
- TradingAgents framework
- Telegram Bot Token

## Installation

### 1. Clone/Create the project directory

```bash
mkdir -p ~/subscribe
cd ~/subscribe
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the bot

Create a `.env` file:

```bash
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_PASSWORD=
```

### 5. Initialize database

```bash
cd ~/subscribe
rm -rf db/database.db*
mkdir -p db
```

### 6. Run the bot

```bash
source venv/bin/activate
python -m src.bot.app
```

## Project Structure

```
~/subscribe/
├── src/
│   └── bot/
│       ├── app.py              # Main entry point
│       ├── handlers.py         # Command and callback handlers
│       ├── keyboards.py         # Inline keyboard definitions
│       ├── database.py          # SQLite database operations
│       ├── polyterm.py          # PolyTerm command executor
│       ├── payment.py           # USDT TRC20 payment verification
│       └── data/
│           └── config.py        # Configuration constants
├── db/
│   └── database.db             # SQLite database (created on first run)
├── .env                        # Environment variables
└── requirements.txt            # Python dependencies
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/help` | Show help information |
| `/status` | Check subscription status |
| `/subscribe` | Buy subscription |
| `/trade <ticker>` | TradingAgents analysis |
| `/admin_login <password>` | Admin login |
| `/admin` | Admin panel |
| `/broadcast <message>` | Broadcast message (admin) |

## Subscription Plans

| Plan | Price |
|------|-------|
| 1 Month | 9.99 USDT |
| 3 Months | 14.99 USDT |
| 6 Months | 19.99 USDT |
| 12 Months | 34.99 USDT |

## Payment Information

- **Wallet Address**: `TCSYEiTBp67GvUk3f2f1foL1jDRKu6upD8`
- **USDT Contract**: `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`
- **Network**: TRC20

## PolyTerm Commands (23 buttons)

1. Monitor Markets
2. Live Monitor
3. Whale Activity
4. Watch Market
5. Market Analytics
6. Portfolio
7. Export Data
8. Settings
9. Arbitrage
10. Predictions
11. Wallets
12. Alerts
13. Order Book
14. Risk Assessment
15. Copy Trading
16. Parlay
17. Bookmarks
18. Dashboard
19. Tutorial
20. Glossary
21. Simulate P&L
22. Help
23. TradingAgents Analysis

## TradingAgents Supported Tickers

**Stocks**: AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META

**Crypto**: BTC-USD, ETH-USD, SOL-USD

**ETF**: SPY, QQQ, DIA

## Admin Features

- Access all features without subscription
- View bot statistics
- View user list
- View revenue information
- Broadcast messages to all users

## Database Schema

### users
- `user_id` (PRIMARY KEY)
- `username`
- `full_name`
- `subscribed_until`
- `subscription_active`
- `created_at`
- `last_active`
- `is_admin`

### payments
- `id` (PRIMARY KEY)
- `user_id`
- `amount`
- `tx_hash` (UNIQUE)
- `plan_months`
- `status`
- `created_at`
- `confirmed_at`

### admins
- `user_id` (PRIMARY KEY)
- `added_at`

### command_log
- `id` (PRIMARY KEY)
- `user_id`
- `command`
- `executed_at`

## Logging

All bot activity is logged:
- User commands
- Payment transactions
- Errors and exceptions
- Admin actions

## Security

- Bot token stored in `.env` file
- Admin password in configuration
- Subscription check before command execution
- Transaction hash validation
- Command timeout protection

## Troubleshooting

### Bot not responding
1. Check if bot token is correct in `.env`
2. Ensure virtual environment is activated
3. Check logs for errors

### Payment not confirmed
1. Verify transaction was sent to correct address
2. Check blockchain confirmations
3. Ensure TRC20 network was used
4. Wait up to 20 minutes for auto-detection

### PolyTerm commands failing
1. Verify PolyTerm is installed at configured path
2. Check PolyTerm is in system PATH
3. Test PolyTerm manually in terminal

## License

MIT License
