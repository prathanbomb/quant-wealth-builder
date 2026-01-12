"""Main orchestrator for Multi-Formula Stock Screening Bot."""

import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config import (
    DISCORD_WEBHOOK_URL,
    MIN_MARKET_CAP,
    EXCLUDED_SECTORS,
    TARGET_EXCHANGES,
    TOP_N_STOCKS,
    get_enabled_formulas,
    validate_config,
    ConfigurationError,
)
from src.stock_data_client import StockDataClient
from src.reddit_client import RedditClient
from src.discord_notifier import DiscordNotifier
from src.magic_formula import (
    calculate_earnings_yield,
    calculate_roc,
    rank_stocks,
    get_top_picks,
)
from src.piotroski_fscore import rank_by_fscore, get_top_fscore_picks
from src.graham_number import rank_by_margin_of_safety, get_top_graham_picks
from src.acquirer_multiple import rank_by_acquirer_multiple, get_top_acquirer_picks
from src.altman_zscore import rank_by_zscore, get_top_zscore_picks
from src.reddit_momentum_formula import (
    filter_by_stock_universe,
    rank_by_momentum,
    get_top_momentum_picks,
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
        DataFrame with stock data including all financial metrics.
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

        # Build stock data dict with all required fields for all formulas
        stock_record = {
            # Basic info
            "symbol": data["symbol"],
            "company_name": data["company_name"],
            "price": data["price"],
            # Magic Formula fields
            "ebit": data["ebit"],
            "enterprise_value": data["enterprise_value"],
            "total_assets": data["total_assets"],
            "current_liabilities": data["current_liabilities"],
            # Piotroski F-Score fields
            "net_income": data.get("net_income"),
            "net_income_prev": data.get("net_income_prev"),
            "operating_cash_flow": data.get("operating_cash_flow"),
            "roa": data.get("roa"),
            "roa_prev": data.get("roa_prev"),
            "gross_margin": data.get("gross_margin"),
            "gross_margin_prev": data.get("gross_margin_prev"),
            "asset_turnover": data.get("asset_turnover"),
            "asset_turnover_prev": data.get("asset_turnover_prev"),
            "total_assets_prev": data.get("total_assets_prev"),
            "long_term_debt": data.get("long_term_debt"),
            "long_term_debt_prev": data.get("long_term_debt_prev"),
            "current_ratio": data.get("current_ratio"),
            "current_ratio_prev": data.get("current_ratio_prev"),
            "shares_outstanding": data.get("shares_outstanding"),
            "shares_outstanding_prev": data.get("shares_outstanding_prev"),
            # Graham Number fields
            "eps": data.get("eps"),
            "book_value_per_share": data.get("book_value_per_share"),
            # Acquirer's Multiple (uses ebit, enterprise_value already fetched)
            # Altman Z-Score fields
            "working_capital": data.get("working_capital"),
            "retained_earnings": data.get("retained_earnings"),
            "market_cap": data.get("market_cap"),
            "total_liabilities": data.get("total_liabilities"),
            "revenue": data.get("revenue"),
        }

        stock_data.append(stock_record)

    logger.info(f"Successfully fetched data for {len(stock_data)} stocks")
    return pd.DataFrame(stock_data)


def run_magic_formula(df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
    """
    Execute Magic Formula ranking and return top picks.

    Args:
        df: DataFrame with all required financial metrics.

    Returns:
        List of stock dictionaries for top picks, or None if no valid stocks.
    """
    logger.info("Calculating Magic Formula metrics...")

    # Calculate earnings yield and ROC for each stock
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
    df_filtered = df.dropna(subset=["earnings_yield", "roc"])
    filtered_count = len(df_filtered)

    if filtered_count < initial_count:
        logger.warning(
            f"Filtered out {initial_count - filtered_count} stocks with invalid Magic Formula metrics"
        )

    if df_filtered.empty:
        logger.warning("No stocks with valid Magic Formula metrics")
        return None

    logger.info(f"Calculated Magic Formula metrics for {len(df_filtered)} stocks")

    # Rank stocks and get top picks
    logger.info("Ranking stocks using Magic Formula...")
    ranked_df = rank_stocks(df_filtered)
    top_picks = get_top_picks(ranked_df, n=TOP_N_STOCKS)

    # Handle case where fewer than requested stocks are available
    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} valid Magic Formula stocks found (requested {TOP_N_STOCKS})"
        )

    # Log top picks
    logger.info(f"Top {len(top_picks)} Magic Formula picks:")
    for idx, row in top_picks.iterrows():
        logger.info(
            f"  {idx + 1}. {row['symbol']} - Score: {row['magic_score']} "
            f"(EY: {row['earnings_yield']:.1%}, ROC: {row['roc']:.1%})"
        )

    return top_picks.to_dict("records")


def run_piotroski(df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
    """
    Execute Piotroski F-Score ranking and return top picks.

    Args:
        df: DataFrame with all required financial metrics.

    Returns:
        List of stock dictionaries for top picks, or None if no valid stocks.
    """
    logger.info("Ranking stocks using Piotroski F-Score...")

    ranked_df = rank_by_fscore(df)

    if ranked_df.empty:
        logger.warning("No stocks with valid Piotroski F-Score")
        return None

    top_picks = get_top_fscore_picks(ranked_df, n=TOP_N_STOCKS)

    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} valid Piotroski stocks found (requested {TOP_N_STOCKS})"
        )

    logger.info(f"Top {len(top_picks)} Piotroski F-Score picks:")
    for idx, row in top_picks.iterrows():
        logger.info(f"  {idx + 1}. {row['symbol']} - F-Score: {int(row['fscore'])}/9")

    return top_picks.to_dict("records")


def run_graham(df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
    """
    Execute Graham Number ranking and return top picks.

    Args:
        df: DataFrame with all required financial metrics.

    Returns:
        List of stock dictionaries for top picks, or None if no valid stocks.
    """
    logger.info("Ranking stocks using Graham Number...")

    ranked_df = rank_by_margin_of_safety(df)

    if ranked_df.empty:
        logger.warning("No stocks with valid Graham Number")
        return None

    top_picks = get_top_graham_picks(ranked_df, n=TOP_N_STOCKS)

    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} valid Graham Number stocks found (requested {TOP_N_STOCKS})"
        )

    logger.info(f"Top {len(top_picks)} Graham Number picks:")
    for idx, row in top_picks.iterrows():
        logger.info(
            f"  {idx + 1}. {row['symbol']} - Graham: ${row['graham_number']:.2f}, "
            f"Margin: {row['margin_of_safety']:.1f}%"
        )

    return top_picks.to_dict("records")


def run_acquirer(df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
    """
    Execute Acquirer's Multiple ranking and return top picks.

    Args:
        df: DataFrame with all required financial metrics.

    Returns:
        List of stock dictionaries for top picks, or None if no valid stocks.
    """
    logger.info("Ranking stocks using Acquirer's Multiple...")

    ranked_df = rank_by_acquirer_multiple(df)

    if ranked_df.empty:
        logger.warning("No stocks with valid Acquirer's Multiple")
        return None

    top_picks = get_top_acquirer_picks(ranked_df, n=TOP_N_STOCKS)

    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} valid Acquirer's Multiple stocks found (requested {TOP_N_STOCKS})"
        )

    logger.info(f"Top {len(top_picks)} Acquirer's Multiple picks:")
    for idx, row in top_picks.iterrows():
        logger.info(f"  {idx + 1}. {row['symbol']} - EV/EBIT: {row['acquirer_multiple']:.2f}x")

    return top_picks.to_dict("records")


def run_altman(df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
    """
    Execute Altman Z-Score ranking and return top picks.

    Args:
        df: DataFrame with all required financial metrics.

    Returns:
        List of stock dictionaries for top picks, or None if no valid stocks.
    """
    logger.info("Ranking stocks using Altman Z-Score...")

    ranked_df = rank_by_zscore(df)

    if ranked_df.empty:
        logger.warning("No stocks in Safe Zone (Altman Z-Score)")
        return None

    top_picks = get_top_zscore_picks(ranked_df, n=TOP_N_STOCKS)

    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} Safe Zone stocks found (requested {TOP_N_STOCKS})"
        )

    logger.info(f"Top {len(top_picks)} Altman Z-Score picks:")
    for idx, row in top_picks.iterrows():
        logger.info(
            f"  {idx + 1}. {row['symbol']} - Z-Score: {row['zscore']:.2f} ({row['risk_zone']})"
        )

    return top_picks.to_dict("records")


def run_reddit_momentum(
    reddit_client: RedditClient,
    stock_universe: List[str],
) -> Optional[List[Dict[str, Any]]]:
    """
    Execute Reddit Momentum ranking and return top picks.

    Args:
        reddit_client: Initialized Reddit client.
        stock_universe: List of valid stock symbols.

    Returns:
        List of stock dictionaries for top picks, or None if no data available.
    """
    logger.info("Fetching Reddit sentiment data...")

    # Fetch raw Reddit data
    raw_data = reddit_client.fetch_sentiment_data()
    if raw_data is None:
        logger.warning("No Reddit data available")
        return None

    logger.info(f"Received Reddit data for {len(raw_data)} stocks")

    # Filter to stock universe
    df = filter_by_stock_universe(raw_data, stock_universe)
    if df.empty:
        logger.warning("No Reddit data matches stock universe")
        return None

    logger.info(f"Filtered to {len(df)} stocks in universe")

    # Rank by momentum
    ranked_df = rank_by_momentum(df)
    top_picks = get_top_momentum_picks(ranked_df, n=TOP_N_STOCKS)

    if len(top_picks) < TOP_N_STOCKS:
        logger.warning(
            f"Only {len(top_picks)} bullish Reddit stocks found (requested {TOP_N_STOCKS})"
        )

    logger.info(f"Top {len(top_picks)} Reddit Momentum picks:")
    for idx, row in top_picks.iterrows():
        logger.info(
            f"  {idx + 1}. {row['ticker']} - Score: {row['momentum_score']:.2f} "
            f"({row['sentiment']}, {row['no_of_comments']} comments)"
        )

    return top_picks.to_dict("records")


def run() -> int:
    """
    Execute the Multi-Formula Stock Screening Bot logic.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting Multi-Formula Stock Screening Bot")

    # Load and validate configuration
    try:
        validate_config()
        logger.info("Configuration validated successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Get enabled formulas
    enabled_formulas = get_enabled_formulas()

    if not enabled_formulas:
        logger.warning("No formulas are enabled. Please enable at least one formula.")
        return 1

    logger.info(f"Enabled formulas: {', '.join(enabled_formulas)}")

    # Initialize clients
    stock_client = StockDataClient()
    discord_notifier = DiscordNotifier(webhook_url=DISCORD_WEBHOOK_URL)

    # Initialize Reddit client if Reddit Momentum is enabled
    reddit_client = None
    if "reddit_momentum" in enabled_formulas:
        reddit_client = RedditClient()
        logger.info("Reddit Momentum enabled, initialized Reddit client")

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

    logger.info(f"Successfully fetched data for {len(df)} stocks")

    # Execute each enabled formula and collect results
    results: Dict[str, List[Dict[str, Any]]] = {}

    # Make a copy for Magic Formula since it modifies the DataFrame
    if "magic_formula" in enabled_formulas:
        result = run_magic_formula(df.copy())
        if result:
            results["magic_formula"] = result

    # Other formulas don't modify the DataFrame, so no copy needed
    if "piotroski" in enabled_formulas:
        result = run_piotroski(df)
        if result:
            results["piotroski"] = result

    if "graham" in enabled_formulas:
        result = run_graham(df)
        if result:
            results["graham"] = result

    if "acquirer" in enabled_formulas:
        result = run_acquirer(df)
        if result:
            results["acquirer"] = result

    if "altman" in enabled_formulas:
        result = run_altman(df)
        if result:
            results["altman"] = result

    # Reddit Momentum (uses separate data source)
    if "reddit_momentum" in enabled_formulas:
        result = run_reddit_momentum(reddit_client, symbols)
        if result:
            results["reddit_momentum"] = result

    # Check if we have any results
    if not results:
        logger.error("No valid results from any enabled formula")
        return 1

    # Get current month/year
    month_year = datetime.now().strftime("%B %Y")

    # Send Discord notification
    logger.info("Sending Discord notification...")
    success = discord_notifier.send_multi_formula_alert(
        results=results,
        month_year=month_year,
        enabled_formulas=enabled_formulas,
    )

    if success:
        logger.info("Multi-Formula Stock Screening Bot completed successfully")
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
