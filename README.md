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

### 6. Configure TradingAgents path (optional)

If your TradingAgents framework is not at `/workspace`, set the path in config.py or environment:

```bash
export TRADINGAGENTS_PATH=/path/to/tradingagents
```

### 7. Run the bot

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
│       ├── tradingagents.py     # TradingAgents integration module
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

## TradingAgents Analysis

The bot integrates with the TradingAgents framework to provide AI-powered market analysis.

### Supported Tickers

**Stocks**: AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META, AMD, INTC, NFLX

**Crypto**: BTC-USD, ETH-USD, SOL-USD, BNB-USD, XRP-USD

**ETF**: SPY, QQQ, DIA, IWM, VTI

### Usage

```
/trade AAPL     # Stock analysis
/trade BTC-USD  # Crypto analysis
/trade SPY      # ETF analysis
```

### How It Works

1. The bot validates the ticker symbol
2. Runs the TradingAgents multi-agent analysis pipeline
3. Returns a formatted decision (BUY/SELL/HOLD) with supporting analysis

### Extended Supported Tickers

The bot supports additional tickers beyond the basic set:
- **More Stocks**: AMD, INTC, NFLX
- **More Crypto**: BNB-USD, XRP-USD
- **More ETF**: IWM, VTI

## TradingAgents Module Functions

The `tradingagents.py` module provides the following functions:

### `check_tradingagents_installed()`
- Checks if the TradingAgents framework is available
- Returns: `bool`

### `get_ticker_info(ticker)`
- Get ticker type and info
- Args: `ticker` (str) - ticker symbol
- Returns: `dict` with keys: `type` ("stock"/"crypto"/"etf"), `name`

### `validate_ticker(ticker)`
- Validate if ticker is supported
- Args: `ticker` (str) - ticker symbol
- Returns: `Tuple[bool, str]` - (is_valid, normalized_ticker_or_error)

### `run_trading_analysis(ticker, trade_date=None, debug=False)`
- Run TradingAgents analysis for a given ticker
- Args:
  - `ticker` (str) - Stock, crypto, or ETF ticker symbol
  - `trade_date` (str, optional) - Date for analysis (YYYY-MM-DD), defaults to today
  - `debug` (bool) - Enable debug mode
- Returns: `Tuple[str, Optional[str]]` - (analysis_result, error_message)

### `format_analysis_result(ticker, ticker_info, decision)`
- Format the analysis result for Telegram display
- Args: ticker, ticker_info dict, decision string
- Returns: `str` - formatted message

### `get_supported_tickers_list()`
- Get formatted list of supported tickers
- Returns: `str` - HTML formatted list

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
- TradingAgents analysis requests

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

### TradingAgents analysis not working
1. Verify TradingAgents path is correct in config.py
2. Ensure all dependencies are installed (yfinance, tradingagents)
3. Check that LLM API keys are configured in the TradingAgents .env

## License

MIT License
