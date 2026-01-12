"""Stock data client module using yfinance."""

import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd
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


def _safe_get_value(
    df: Optional[pd.DataFrame],
    row_name: str,
    col_idx: int = 0,
) -> Optional[float]:
    """
    Safely extract a value from a DataFrame.

    Args:
        df: DataFrame to extract from (can be None or empty).
        row_name: Index/row name to look up.
        col_idx: Column index (0 = most recent, 1 = previous year).

    Returns:
        Float value if found, None otherwise.
    """
    if df is None or df.empty:
        return None
    if row_name not in df.index:
        return None
    if col_idx >= len(df.columns):
        return None
    try:
        value = df.loc[row_name].iloc[col_idx]
        if pd.isna(value):
            return None
        return float(value)
    except (IndexError, KeyError, TypeError):
        return None


def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """
    Safely divide two numbers.

    Args:
        numerator: The numerator (can be None).
        denominator: The denominator (can be None or zero).

    Returns:
        Result of division, or None if invalid.
    """
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


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

        Fetches comprehensive financial data needed for multiple screening formulas:
        - Magic Formula: EBIT, Enterprise Value, Total Assets, Current Liabilities
        - Piotroski F-Score: YoY comparisons, cash flow, margins
        - Graham Number: EPS, Book Value Per Share
        - Acquirer's Multiple: EV, EBIT (same as Magic Formula)
        - Altman Z-Score: Working Capital, Retained Earnings, Revenue, Liabilities

        Args:
            symbol: Stock ticker symbol.
            min_market_cap: Minimum market cap filter.
            excluded_sectors: Sectors to exclude.

        Returns:
            Dict with stock data, or None if core data unavailable or filtered out.
            Optional fields for advanced formulas may be None if not available.
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
                cashflow = ticker.cashflow

                # === Core fields (required for Magic Formula) ===

                # Extract EBIT (Operating Income)
                ebit = _safe_get_value(income_stmt, "Operating Income", 0)
                if ebit is None:
                    ebit = _safe_get_value(income_stmt, "EBIT", 0)

                if ebit is None:
                    logger.warning(f"No operating income data for {symbol}")
                    return None

                # Extract Total Assets (current year)
                total_assets = _safe_get_value(balance_sheet, "Total Assets", 0)

                if total_assets is None:
                    logger.warning(f"No total assets data for {symbol}")
                    return None

                # Extract Current Liabilities
                current_liabilities = _safe_get_value(
                    balance_sheet, "Current Liabilities", 0
                )

                if current_liabilities is None:
                    logger.warning(f"No current liabilities data for {symbol}")
                    return None

                # Get Enterprise Value
                enterprise_value = info.get("enterpriseValue")
                if enterprise_value is None:
                    logger.warning(f"No enterprise value data for {symbol}")
                    return None

                # === Extended fields for Piotroski F-Score ===

                # Net Income
                net_income = _safe_get_value(income_stmt, "Net Income", 0)

                # Operating Cash Flow
                operating_cash_flow = _safe_get_value(
                    cashflow, "Operating Cash Flow", 0
                )
                if operating_cash_flow is None:
                    operating_cash_flow = _safe_get_value(
                        cashflow, "Cash Flow From Continuing Operating Activities", 0
                    )

                # Total Assets (previous year) for ROA comparison
                total_assets_prev = _safe_get_value(balance_sheet, "Total Assets", 1)

                # ROA current and previous
                roa = _safe_divide(net_income, total_assets)
                roa_prev = None
                if total_assets_prev is not None:
                    net_income_prev = _safe_get_value(income_stmt, "Net Income", 1)
                    roa_prev = _safe_divide(net_income_prev, total_assets_prev)

                # Long-term Debt
                long_term_debt = _safe_get_value(balance_sheet, "Long Term Debt", 0)
                long_term_debt_prev = _safe_get_value(balance_sheet, "Long Term Debt", 1)

                # Current Assets
                current_assets = _safe_get_value(balance_sheet, "Current Assets", 0)
                current_assets_prev = _safe_get_value(balance_sheet, "Current Assets", 1)

                # Current Liabilities (previous year)
                current_liabilities_prev = _safe_get_value(
                    balance_sheet, "Current Liabilities", 1
                )

                # Current Ratio
                current_ratio = _safe_divide(current_assets, current_liabilities)
                current_ratio_prev = _safe_divide(
                    current_assets_prev, current_liabilities_prev
                )

                # Shares Outstanding
                shares_outstanding = info.get("sharesOutstanding")
                shares_outstanding_prev = None  # yfinance doesn't provide historical

                # Gross Profit and Revenue for margins
                gross_profit = _safe_get_value(income_stmt, "Gross Profit", 0)
                gross_profit_prev = _safe_get_value(income_stmt, "Gross Profit", 1)
                revenue = _safe_get_value(income_stmt, "Total Revenue", 0)
                revenue_prev = _safe_get_value(income_stmt, "Total Revenue", 1)

                # Gross Margin
                gross_margin = _safe_divide(gross_profit, revenue)
                gross_margin_prev = _safe_divide(gross_profit_prev, revenue_prev)

                # Asset Turnover
                asset_turnover = _safe_divide(revenue, total_assets)
                asset_turnover_prev = _safe_divide(revenue_prev, total_assets_prev)

                # === Extended fields for Graham Number ===

                # EPS (trailing twelve months)
                eps = info.get("trailingEps")

                # Book Value Per Share
                book_value_per_share = info.get("bookValue")

                # === Extended fields for Altman Z-Score ===

                # Working Capital
                working_capital = None
                if current_assets is not None and current_liabilities is not None:
                    working_capital = current_assets - current_liabilities

                # Retained Earnings
                retained_earnings = _safe_get_value(
                    balance_sheet, "Retained Earnings", 0
                )

                # Total Liabilities
                total_liabilities = _safe_get_value(
                    balance_sheet, "Total Liabilities Net Minority Interest", 0
                )
                if total_liabilities is None:
                    total_liabilities = _safe_get_value(
                        balance_sheet, "Total Liabilities", 0
                    )

                # Build result with all fields
                return {
                    # Identification
                    "symbol": symbol,
                    "company_name": info.get("shortName", info.get("longName", symbol)),
                    "sector": sector,
                    # Price & Valuation
                    "price": info.get(
                        "currentPrice", info.get("regularMarketPrice", 0)
                    ),
                    "market_cap": market_cap,
                    "enterprise_value": float(enterprise_value),
                    # Core Income Statement (required)
                    "ebit": float(ebit),
                    # Core Balance Sheet (required)
                    "total_assets": float(total_assets),
                    "current_liabilities": float(current_liabilities),
                    # Extended Income Statement
                    "net_income": net_income,
                    "revenue": revenue,
                    "gross_profit": gross_profit,
                    "revenue_prev": revenue_prev,
                    "gross_profit_prev": gross_profit_prev,
                    # Extended Balance Sheet (current year)
                    "current_assets": current_assets,
                    "total_liabilities": total_liabilities,
                    "long_term_debt": long_term_debt,
                    "retained_earnings": retained_earnings,
                    "shares_outstanding": shares_outstanding,
                    # Extended Balance Sheet (previous year)
                    "total_assets_prev": total_assets_prev,
                    "long_term_debt_prev": long_term_debt_prev,
                    "current_liabilities_prev": current_liabilities_prev,
                    "shares_outstanding_prev": shares_outstanding_prev,
                    # Cash Flow
                    "operating_cash_flow": operating_cash_flow,
                    # Per-Share Metrics
                    "eps": eps,
                    "book_value_per_share": book_value_per_share,
                    # Derived Ratios
                    "working_capital": working_capital,
                    "current_ratio": current_ratio,
                    "current_ratio_prev": current_ratio_prev,
                    "roa": roa,
                    "roa_prev": roa_prev,
                    "gross_margin": gross_margin,
                    "gross_margin_prev": gross_margin_prev,
                    "asset_turnover": asset_turnover,
                    "asset_turnover_prev": asset_turnover_prev,
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
