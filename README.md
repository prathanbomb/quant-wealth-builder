# Magic Formula DCA Bot

Automated stock screening bot that implements Joel Greenblatt's Magic Formula investing strategy. Runs daily on weekdays and sends top stock picks to Discord.

## What is the Magic Formula?

The Magic Formula, created by Joel Greenblatt in "The Little Book That Beats the Market", ranks stocks by combining two metrics:

1. **Earnings Yield** = EBIT / Enterprise Value
   - Measures how cheap a stock is relative to its earnings
   - Higher is better (more earnings per dollar invested)

2. **Return on Capital** = EBIT / (Total Assets - Current Liabilities)
   - Measures how efficiently a company uses its capital
   - Higher is better (more profit per dollar of capital)

Stocks are ranked by each metric, and the combined rank (Magic Score) identifies companies that are both **cheap** and **good**.

## Features

- Fetches financial data from Yahoo Finance (via yfinance)
- Screens 88 major US stocks across multiple sectors
- Filters by market cap ($100M+) and excludes Financial/Utilities sectors
- Calculates Earnings Yield and Return on Capital
- Ranks stocks and selects Top 5 picks
- Sends formatted notifications to Discord
- Runs automatically on weekdays via GitHub Actions

## Setup

### 1. Discord Webhook

1. Open Discord and go to your server
2. Click the gear icon next to your target channel
3. Go to **Integrations** > **Webhooks**
4. Click **New Webhook** and copy the URL

### 2. GitHub Repository Secrets

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Add a new secret:
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: Your Discord webhook URL

### 3. Enable GitHub Actions

The bot runs automatically every weekday at 14:00 UTC (9:00 AM EST). You can also trigger it manually from the Actions tab.

## Local Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env and add your DISCORD_WEBHOOK_URL
```

### Run the Bot

```bash
python -m src.main
```

### Run Tests

```bash
pytest tests/ -v
```

## Configuration

Edit `src/config.py` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_MARKET_CAP` | 100,000,000 | Minimum market cap filter ($) |
| `EXCLUDED_SECTORS` | Financial Services, Utilities | Sectors to exclude |
| `TARGET_EXCHANGES` | NYSE, NASDAQ | Exchanges to include |
| `TOP_N_STOCKS` | 5 | Number of top picks to return |

## Project Structure

```
quant-wealth-builder/
├── src/
│   ├── config.py           # Configuration and env vars
│   ├── stock_data_client.py # yfinance data fetching
│   ├── magic_formula.py    # Ranking calculations
│   ├── discord_notifier.py # Discord webhook integration
│   └── main.py             # Main orchestrator
├── tests/                  # Test suite (82 tests)
├── .github/workflows/      # GitHub Actions workflow
└── requirements.txt        # Python dependencies
```

## Disclaimer

This bot is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions. Past performance does not guarantee future results.

## License

MIT
