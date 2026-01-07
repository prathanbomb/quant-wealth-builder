"""Stock data client module using yfinance."""

import logging
import time
from typing import Any, Dict, List, Optional

import yfinance as yf

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

# Stock universe - Major US stocks across various sectors
# Used since yfinance doesn't provide a screener endpoint
STOCK_UNIVERSE = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "META", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "AMD",
    "INTC", "CSCO", "IBM", "QCOM", "TXN", "NOW", "INTU", "AMAT", "MU", "LRCX",
    # Healthcare
    "UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY",
    "AMGN", "GILD", "VRTX", "REGN", "ISRG", "MDT", "SYK", "ZTS", "BDX", "CI",
    # Consumer
    "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "COST", "TGT",
    "PG", "KO", "PEP", "PM", "MO", "CL", "EL", "GIS", "K", "KHC",
    # Industrial
    "CAT", "DE", "UNP", "UPS", "RTX", "HON", "BA", "LMT", "GE", "MMM",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Communication
    "GOOG", "DIS", "NFLX", "CMCSA", "VZ", "T", "TMUS", "CHTR",
]


class StockDataClient:
    """Client for fetching stock data using yfinance."""

    def __init__(self):
        """Initialize the stock data client."""
        pass

    def get_stock_universe(
        self,
        exchanges: List[str],
        min_market_cap: int,
        excluded_sectors: List[str],
    ) -> List[str]:
        """
        Get list of stock symbols to analyze.

        Since yfinance doesn't have a screener, we use a predefined list
        of major US stocks. Filtering by market cap and sector happens
        when fetching individual stock data.

        Args:
            exchanges: List of exchanges (not used, kept for API compatibility).
            min_market_cap: Minimum market cap (filtering done in get_stock_data).
            excluded_sectors: Sectors to exclude (filtering done in get_stock_data).

        Returns:
            List of stock symbols.
        """
        logger.info(f"Using predefined stock universe of {len(STOCK_UNIVERSE)} stocks")
        return STOCK_UNIVERSE.copy()

    def get_stock_data(
        self,
        symbol: str,
        min_market_cap: int = 0,
        excluded_sectors: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch all financial data for a stock.

        Args:
            symbol: Stock ticker symbol.
            min_market_cap: Minimum market cap filter.
            excluded_sectors: Sectors to exclude.

        Returns:
            Dict with stock data, or None if data unavailable or filtered out.
        """
        if excluded_sectors is None:
            excluded_sectors = []

        for attempt in range(MAX_RETRIES):
            try:
                # Apply backoff delay on retries
                if attempt > 0:
                    backoff = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    logger.info(f"Retry attempt {attempt + 1}, waiting {backoff}s")
                    time.sleep(backoff)

                logger.debug(f"Fetching data for {symbol}")
                ticker = yf.Ticker(symbol)

                # Get company info
                info = ticker.info
                if not info or info.get("regularMarketPrice") is None:
                    logger.warning(f"No info data for {symbol}")
                    return None

                # Check market cap filter
                market_cap = info.get("marketCap", 0) or 0
                if min_market_cap > 0 and market_cap < min_market_cap:
                    logger.debug(
                        f"Skipping {symbol}: market cap ${market_cap:,} below minimum"
                    )
                    return None

                # Check sector filter
                sector = info.get("sector", "")
                if sector in excluded_sectors:
                    logger.debug(f"Skipping {symbol}: sector '{sector}' is excluded")
                    return None

                # Get financial statements
                income_stmt = ticker.income_stmt
                balance_sheet = ticker.balance_sheet

                # Extract EBIT (Operating Income)
                ebit = None
                if income_stmt is not None and not income_stmt.empty:
                    if "Operating Income" in income_stmt.index:
                        # Get most recent value (first column)
                        ebit = income_stmt.loc["Operating Income"].iloc[0]
                    elif "EBIT" in income_stmt.index:
                        ebit = income_stmt.loc["EBIT"].iloc[0]

                if ebit is None:
                    logger.warning(f"No operating income data for {symbol}")
                    return None

                # Extract Total Assets
                total_assets = None
                if balance_sheet is not None and not balance_sheet.empty:
                    if "Total Assets" in balance_sheet.index:
                        total_assets = balance_sheet.loc["Total Assets"].iloc[0]

                if total_assets is None:
                    logger.warning(f"No total assets data for {symbol}")
                    return None

                # Extract Current Liabilities
                current_liabilities = None
                if balance_sheet is not None and not balance_sheet.empty:
                    if "Current Liabilities" in balance_sheet.index:
                        current_liabilities = balance_sheet.loc[
                            "Current Liabilities"
                        ].iloc[0]

                if current_liabilities is None:
                    logger.warning(f"No current liabilities data for {symbol}")
                    return None

                # Get Enterprise Value
                enterprise_value = info.get("enterpriseValue")
                if enterprise_value is None:
                    logger.warning(f"No enterprise value data for {symbol}")
                    return None

                # Build result
                return {
                    "symbol": symbol,
                    "company_name": info.get("shortName", info.get("longName", symbol)),
                    "price": info.get(
                        "currentPrice", info.get("regularMarketPrice", 0)
                    ),
                    "ebit": float(ebit),
                    "enterprise_value": float(enterprise_value),
                    "total_assets": float(total_assets),
                    "current_liabilities": float(current_liabilities),
                    "market_cap": market_cap,
                    "sector": sector,
                }

            except Exception as e:
                logger.warning(
                    f"Error fetching data for {symbol}, "
                    f"attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Max retries exceeded for {symbol}")
                    return None

        return None
