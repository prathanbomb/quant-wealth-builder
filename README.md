# Multi-Formula Stock Screening Bot

Automated stock screening bot that implements multiple value investing formulas and social sentiment analysis. Runs daily on weekdays and sends top stock picks to Discord.

## Supported Formulas

The bot supports 6 formulas combining fundamental analysis with social sentiment, plus portfolio-level risk analysis:

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

### 6. Reddit Momentum
Social sentiment analysis from Reddit's r/Wallstreetbets community:
- Fetches top 50 stocks discussed on r/Wallstreetbets (via Tradestie API)
- **Sentiment Score**: Bullish/Bearish sentiment from Reddit comments
- **Discussion Volume**: Number of comments (logarithmic scaling)
- **Momentum Score** = (Sentiment Score × 1000) + log(Comments + 1)
- Only ranks stocks with Bullish sentiment
- Updates every 15 minutes

### 7. Portfolio Analyzer
Portfolio-level risk analysis and optimization for each formula's top picks (via Portfolio Optimizer API):
- **Risk Metrics** (Phase 1):
  - **Volatility**: Portfolio risk (standard deviation of returns)
  - **Sharpe Ratio**: Risk-adjusted return (higher is better)
  - **Diversification Ratio**: Benefit from diversification (values > 1.0 indicate diversification benefit)
- **Optimized Portfolios** (Phase 2):
  - **Max Sharpe Portfolio**: Optimal weights for maximum risk-adjusted returns
  - **Min Variance Portfolio**: Optimal weights for lowest portfolio volatility
  - **Equal Risk Portfolio**: Risk parity allocation (each asset contributes equal risk)
- Uses 1 year of historical price data for covariance matrix computation
- Disabled by default (opt-in feature)

## Features

- Fetches financial data from Yahoo Finance (via yfinance)
- Fetches social sentiment data from Reddit r/Wallstreetbets (via Tradestie API)
- Fetches historical price data and computes portfolio risk metrics (via Portfolio Optimizer API)
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
   - Name: `ENABLE_REDDIT_MOMENTUM` (optional, default: true)
   - Name: `ENABLE_PORTFOLIO_ANALYZER` (optional, default: false)

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
| `ENABLE_REDDIT_MOMENTUM` | true | Enable Reddit Momentum screening |
| `ENABLE_PORTFOLIO_ANALYZER` | false | Enable Portfolio Analyzer (risk metrics & optimization) |
| `PORTFOLIO_HISTORY_PERIOD` | 1y | Historical data period for portfolio analysis |
| `PORTFOLIO_RISK_FREE_RATE` | 0.02 | Risk-free rate for Sharpe ratio calculation (2%) |
| `DISABLE_SSL_VERIFICATION` | false | Disable SSL verification (for API certificate issues) |

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
│   ├── config.py                      # Configuration and env vars
│   ├── stock_data_client.py            # yfinance data fetching
│   ├── reddit_client.py                # Tradestie Reddit API client
│   ├── portfolio_optimizer_client.py   # Portfolio Optimizer API client
│   ├── portfolio_data_utils.py         # Historical data & covariance utils
│   ├── magic_formula.py                # Magic Formula calculations
│   ├── piotroski_fscore.py             # Piotroski F-Score calculations
│   ├── graham_number.py                # Graham Number calculations
│   ├── acquirer_multiple.py            # Acquirer's Multiple calculations
│   ├── altman_zscore.py                # Altman Z-Score calculations
│   ├── reddit_momentum_formula.py      # Reddit Momentum calculations
│   ├── discord_notifier.py             # Discord webhook integration
│   └── main.py                         # Main orchestrator
├── tests/                              # Test suite (349+ tests)
├── .github/workflows/                  # GitHub Actions workflow
└── requirements.txt                    # Python dependencies
```

## Formula Output Examples

Each formula produces a separate top 5 list with formula-specific metrics:

- **Magic Formula**: Symbol, Price, Magic Score, Earnings Yield, ROC
- **Piotroski F-Score**: Symbol, Price, F-Score (0-9)
- **Graham Number**: Symbol, Price, Fair Value, Margin of Safety %
- **Acquirer's Multiple**: Symbol, Price, EV/EBIT multiple
- **Altman Z-Score**: Symbol, Price, Z-Score, Risk Zone indicator
- **Reddit Momentum**: Symbol, Comment Count, Momentum Score, Sentiment (Bullish/Bearish)

**Portfolio Analyzer** (when enabled) adds portfolio metrics to each formula:
- Risk metrics: Volatility, Sharpe Ratio, Diversification Ratio
- Optimized portfolios: Max Sharpe weights, Min Variance weights, Equal Risk weights

## Discord Notification Example

When enabled, the Reddit Momentum section appears as a yellow/orange embed:

```
🔥 Reddit Momentum
Top 5 trending stocks on r/Wallstreetbets (discussion volume + positive sentiment)

🥇 1. NVDA
💬 250 comments | 📊 Score: 180.5 🟢 Bullish

🥈 2. TSLA
💬 500 comments | 📊 Score: 222.4 🟢 Bullish

...
```

When Portfolio Analyzer is enabled, each formula section includes portfolio metrics:

```
📊 Portfolio Analysis (5 stocks)
📈 Volatility: 18.5%
🎯 Sharpe Ratio: 1.23
🔄 Diversification: 1.45x

**Max Sharpe Weights:**
AAPL: 35.0%, MSFT: 28.0%, GOOGL: 22.0%
Exp. Return: 15.2%
Volatility: 16.8%

**Min Variance Weights:**
GOOGL: 30.0%, MSFT: 25.0%, AAPL: 20.0%
Volatility: 14.2%

**Equal Risk Weights:**
AAPL: 22.0%, MSFT: 22.0%, GOOGL: 22.0%
Volatility: 15.8%
```

## References

- *The Little Book That Beats the Market* by Joel Greenblatt (Magic Formula)
- *Value Investing: From Graham to Buffett and Beyond* by Joseph D. Piotroski (F-Score)
- *The Intelligent Investor* by Benjamin Graham (Graham Number)
- *Super Stocks* by Kenneth L. Fisher (Acquirer's Multiple)
- *Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy* by Edward I. Altman (Z-Score)
- [Tradestie Reddit WallstreetBets API](https://tradestie.com/apps/reddit/api/) (Social sentiment data)
- [Portfolio Optimizer API](https://portfoliooptimizer.io/) (Portfolio analysis and optimization)

## Disclaimer

This bot is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions. Past performance does not guarantee future results.

## License

MIT
