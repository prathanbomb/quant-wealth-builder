# Multi-Formula Stock Screening Bot

Automated stock screening bot that implements multiple value investing formulas. Runs daily on weekdays and sends top stock picks to Discord.

## Supported Formulas

The bot supports 5 proven value investing formulas, each with its own ranking methodology:

### 1. Magic Formula (Greenblatt)
Combines two key metrics to find "good" companies at "cheap" prices:
- **Earnings Yield** = EBIT / Enterprise Value (how cheap)
- **Return on Capital** = EBIT / (Total Assets - Current Liabilities) (how good)
- Ranks stocks by combined score

### 2. Piotroski F-Score
A 9-point fundamental strength score that measures:
- Profitability (ROA, CFO vs Net Income, Accruals)
- Leverage (long-term debt change, current ratio)
- Efficiency (asset turnover, gross margin, shares outstanding)
- Higher score = stronger fundamentals

### 3. Graham Number
Benjamin Graham's intrinsic value calculation:
- **Graham Number** = √(22.5 × EPS × BVPS)
- **Margin of Safety** = (Graham Number - Price) / Graham Number
- Ranks by most undervalued (highest margin)

### 4. Acquirer's Multiple
A deep value metric used by leveraged buyout firms:
- **Acquirer's Multiple** = Enterprise Value / EBIT
- Lower multiple = cheaper stock
- Ranks ascending (lowest multiple first)

### 5. Altman Z-Score
Bankruptcy prediction model assessing financial health:
- **Safe Zone**: Z > 2.99 (low bankruptcy risk)
- **Grey Zone**: 1.81 < Z < 2.99 (moderate risk)
- **Distress Zone**: Z < 1.81 (high risk)
- Only ranks Safe Zone stocks, highest Z-Score first

## Features

- Fetches financial data from Yahoo Finance (via yfinance)
- Screens 88 major US stocks across multiple sectors
- Filters by market cap ($100M+) and excludes Financial/Utilities sectors
- Runs multiple formulas concurrently (all enabled by default)
- Sends unified Discord notification with color-coded sections
- Formula toggles to enable/disable individual formulas
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
3. Add the following secrets:
   - Name: `DISCORD_WEBHOOK_URL`
   - Name: `ENABLE_MAGIC_FORMULA` (optional, default: true)
   - Name: `ENABLE_PIOTROSKI` (optional, default: true)
   - Name: `ENABLE_GRAHAM` (optional, default: true)
   - Name: `ENABLE_ACQUIRER` (optional, default: true)
   - Name: `ENABLE_ALTMAN` (optional, default: true)

At least one formula must be enabled for the bot to run.

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
# Set ENABLE_* variables to enable/disable formulas
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

Environment variables (in `.env` or GitHub Secrets):

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | *required* | Discord webhook URL for notifications |
| `ENABLE_MAGIC_FORMULA` | true | Enable Magic Formula screening |
| `ENABLE_PIOTROSKI` | true | Enable Piotroski F-Score screening |
| `ENABLE_GRAHAM` | true | Enable Graham Number screening |
| `ENABLE_ACQUIRER` | true | Enable Acquirer's Multiple screening |
| `ENABLE_ALTMAN` | true | Enable Altman Z-Score screening |

Additional configuration in `src/config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_MARKET_CAP` | 100,000,000 | Minimum market cap filter ($) |
| `EXCLUDED_SECTORS` | Financial Services, Utilities | Sectors to exclude |
| `TARGET_EXCHANGES` | NYSE, NASDAQ | Exchanges to include |
| `TOP_N_STOCKS` | 5 | Number of top picks per formula |

## Project Structure

```
quant-wealth-builder/
├── src/
│   ├── config.py              # Configuration and env vars
│   ├── stock_data_client.py    # yfinance data fetching
│   ├── magic_formula.py        # Magic Formula calculations
│   ├── piotroski_fscore.py     # Piotroski F-Score calculations
│   ├── graham_number.py        # Graham Number calculations
│   ├── acquirer_multiple.py    # Acquirer's Multiple calculations
│   ├── altman_zscore.py        # Altman Z-Score calculations
│   ├── discord_notifier.py     # Discord webhook integration
│   └── main.py                 # Main orchestrator
├── tests/                      # Test suite (273 tests)
├── .github/workflows/          # GitHub Actions workflow
└── requirements.txt            # Python dependencies
```

## Formula Output Examples

Each formula produces a separate top 5 list with formula-specific metrics:

- **Magic Formula**: Symbol, Price, Magic Score, Earnings Yield, ROC
- **Piotroski F-Score**: Symbol, Price, F-Score (0-9)
- **Graham Number**: Symbol, Price, Fair Value, Margin of Safety %
- **Acquirer's Multiple**: Symbol, Price, EV/EBIT multiple
- **Altman Z-Score**: Symbol, Price, Z-Score, Risk Zone indicator

## References

- *The Little Book That Beats the Market* by Joel Greenblatt (Magic Formula)
- *Value Investing: From Graham to Buffett and Beyond* by Joseph D. Piotroski (F-Score)
- *The Intelligent Investor* by Benjamin Graham (Graham Number)
- *Super Stocks* by Kenneth L. Fisher (Acquirer's Multiple)
- *Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy* by Edward I. Altman (Z-Score)

## Disclaimer

This bot is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions. Past performance does not guarantee future results.

## License

MIT
