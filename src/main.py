"""Main orchestrator for Magic Formula DCA Bot."""

import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.config import (
    DISCORD_WEBHOOK_URL,
    MIN_MARKET_CAP,
    EXCLUDED_SECTORS,
    TARGET_EXCHANGES,
    TOP_N_STOCKS,
    validate_config,
    ConfigurationError,
)
from src.stock_data_client import StockDataClient
from src.discord_notifier import DiscordNotifier
from src.magic_formula import (
    calculate_earnings_yield,
    calculate_roc,
    rank_stocks,
    get_top_picks,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def fetch_stock_data(
    client: StockDataClient,
    symbols: List[str],
    min_market_cap: int = 0,
    excluded_sectors: List[str] = None,
) -> pd.DataFrame:
    """
    Fetch financial data for each stock and build a DataFrame.

    Args:
        client: Initialized stock data client.
        symbols: List of stock symbols to fetch.
        min_market_cap: Minimum market cap filter.
        excluded_sectors: Sectors to exclude.

    Returns:
        DataFrame with stock data including financial metrics.
    """
    if excluded_sectors is None:
        excluded_sectors = []

    stock_data = []
    total = len(symbols)

    for idx, symbol in enumerate(symbols, start=1):
        logger.info(f"Processing {idx}/{total}: {symbol}")

        # Fetch all financial data for the stock
        data = client.get_stock_data(
            symbol,
            min_market_cap=min_market_cap,
            excluded_sectors=excluded_sectors,
        )

        # Skip if data is unavailable or filtered out
        if data is None:
            continue

        stock_data.append({
            "symbol": data["symbol"],
            "company_name": data["company_name"],
            "price": data["price"],
            "ebit": data["ebit"],
            "enterprise_value": data["enterprise_value"],
            "total_assets": data["total_assets"],
            "current_liabilities": data["current_liabilities"],
        })

    logger.info(f"Successfully fetched data for {len(stock_data)} stocks")
    return pd.DataFrame(stock_data)


def run() -> int:
    """
    Execute the Magic Formula DCA Bot logic.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting Magic Formula DCA Bot")

    # Load and validate configuration
    try:
        validate_config()
        logger.info("Configuration validated successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Initialize clients
    stock_client = StockDataClient()
    discord_notifier = DiscordNotifier(webhook_url=DISCORD_WEBHOOK_URL)

    logger.info(f"Configuration: Market Cap >= ${MIN_MARKET_CAP:,}")
    logger.info(f"Configuration: Exchanges = {TARGET_EXCHANGES}")
    logger.info(f"Configuration: Excluded Sectors = {EXCLUDED_SECTORS}")
    logger.info(f"Configuration: Top N = {TOP_N_STOCKS}")

    # Get stock universe
    logger.info("Getting stock universe...")
    symbols = stock_client.get_stock_universe(
        exchanges=TARGET_EXCHANGES,
        min_market_cap=MIN_MARKET_CAP,
        excluded_sectors=EXCLUDED_SECTORS,
    )

    if not symbols:
        logger.error("No stocks in universe")
        return 1

    logger.info(f"Stock universe contains {len(symbols)} symbols")

    # Fetch financial data for each stock
    logger.info("Fetching financial data for each stock...")
    df = fetch_stock_data(
        stock_client,
        symbols,
        min_market_cap=MIN_MARKET_CAP,
        excluded_sectors=EXCLUDED_SECTORS,
    )

    if df.empty:
        logger.error("No valid stock data after fetching financials")
        return 1

    # Calculate earnings yield and ROC for each stock
    logger.info("Calculating Magic Formula metrics...")
    df["earnings_yield"] = df.apply(
        lambda row: calculate_earnings_yield(row["ebit"], row["enterprise_value"]),
        axis=1,
    )
    df["roc"] = df.apply(
        lambda row: calculate_roc(
            row["ebit"], row["total_assets"], row["current_liabilities"]
        ),
        axis=1,
    )

    # Filter out stocks with invalid metrics
    initial_count = len(df)
    df = df.dropna(subset=["earnings_yield", "roc"])
    filtered_count = len(df)

    if filtered_count < initial_count:
        logger.warning(
            f"Filtered out {initial_count - filtered_count} stocks with invalid metrics"
        )

    if df.empty:
        logger.error("No stocks with valid metrics after calculation")
        return 1

    logger.info(f"Calculated metrics for {len(df)} stocks")

    # Rank stocks and get top picks
    logger.info("Ranking stocks using Magic Formula...")
    ranked_df = rank_stocks(df)
    top_picks = get_top_picks(ranked_df, n=TOP_N_STOCKS)

    # Handle case where fewer than requested stocks are available
    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} valid stocks found (requested {TOP_N_STOCKS}). "
            f"Proceeding with available stocks."
        )

    # Log top picks
    logger.info(f"Top {len(top_picks)} Magic Formula picks:")
    for idx, row in top_picks.iterrows():
        logger.info(
            f"  {idx + 1}. {row['symbol']} - Score: {row['magic_score']} "
            f"(EY: {row['earnings_yield']:.1%}, ROC: {row['roc']:.1%})"
        )

    # Get current month/year
    month_year = datetime.now().strftime("%B %Y")

    # Convert top picks to list of dicts for Discord notifier
    top_picks_list = top_picks.to_dict("records")

    # Send Discord notification
    logger.info("Sending Discord notification...")
    success = discord_notifier.send_magic_formula_alert(
        stocks=top_picks_list,
        month_year=month_year,
    )

    if success:
        logger.info("Magic Formula DCA Bot completed successfully")
        return 0
    else:
        logger.error("Failed to send Discord notification")
        return 1


def main() -> int:
    """
    Main entry point with error handling wrapper.

    Wraps the run() function in try-except to catch and log
    any unhandled exceptions.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        return run()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
