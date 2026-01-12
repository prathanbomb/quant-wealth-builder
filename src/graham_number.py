"""Graham Number calculation module.

Implements Benjamin Graham's intrinsic value formula for finding undervalued stocks.
The Graham Number is a conservative valuation metric that combines earnings per share
(EPS) and book value per share (BVPS) to estimate a stock's fair value.

Formula:
    Graham Number = sqrt(22.5 * EPS * BVPS)

The multiplier 22.5 comes from:
- 15x P/E ratio (Graham's recommended maximum)
- 1.5x P/B ratio (Graham's recommended maximum)
- 15 * 1.5 = 22.5

Margin of Safety indicates how much below intrinsic value a stock is trading:
    Margin % = (Graham Number - Current Price) / Graham Number * 100%

A positive margin indicates the stock is trading below its Graham Number (undervalued).
"""

from typing import Optional

import pandas as pd


def _is_valid(value: Optional[float]) -> bool:
    """Check if a value is valid (not None and not NaN)."""
    if value is None:
        return False
    try:
        return not pd.isna(value)
    except (TypeError, ValueError):
        return True


def calculate_graham_number(eps: Optional[float], book_value_per_share: Optional[float]) -> Optional[float]:
    """
    Calculate the Graham Number (intrinsic value).

    Graham Number = sqrt(22.5 * EPS * BVPS)

    Args:
        eps: Earnings per share (trailing twelve months).
        book_value_per_share: Book value per share.

    Returns:
        Graham Number value, or None if inputs are invalid.
        Returns None if EPS or BVPS is negative or zero.
    """
    if not _is_valid(eps) or not _is_valid(book_value_per_share):
        return None

    # Graham Number requires positive EPS and BVPS
    # Negative earnings means the company is losing money
    # Negative book value means liabilities exceed assets
    if eps <= 0:
        return None
    if book_value_per_share <= 0:
        return None

    try:
        graham_number = (22.5 * eps * book_value_per_share) ** 0.5
        return graham_number
    except (ValueError, TypeError, OverflowError):
        return None


def calculate_margin_of_safety(graham_number: Optional[float], current_price: Optional[float]) -> Optional[float]:
    """
    Calculate the margin of safety as a percentage.

    Margin % = (Graham Number - Current Price) / Graham Number * 100%

    A positive margin indicates the stock is trading below intrinsic value (undervalued).
    A negative margin indicates the stock is trading above intrinsic value (overvalued).

    Args:
        graham_number: The calculated Graham Number.
        current_price: Current stock price.

    Returns:
        Margin of safety as a percentage (e.g., 33.5 means 33.5%).
        Returns None if inputs are invalid or if Graham Number is zero.
    """
    if not _is_valid(graham_number) or not _is_valid(current_price):
        return None

    if graham_number == 0:
        return None

    margin = (graham_number - current_price) / graham_number * 100
    return margin


def calculate_graham_from_dict(data: dict) -> tuple[Optional[float], Optional[float]]:
    """
    Calculate Graham Number and margin of safety from a stock data dictionary.

    Convenience function that extracts fields from a stock data dict.

    Args:
        data: Stock data dictionary from StockDataClient.
            Must contain 'eps', 'book_value_per_share', and 'price' keys.

    Returns:
        Tuple of (graham_number, margin_of_safety).
        Either value can be None if calculation failed.
    """
    eps = data.get("eps")
    book_value_per_share = data.get("book_value_per_share")
    price = data.get("price")

    graham = calculate_graham_number(eps, book_value_per_share)
    margin = calculate_margin_of_safety(graham, price)

    return graham, margin


def rank_by_margin_of_safety(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks by margin of safety descending.

    Stocks with higher margin of safety are more undervalued and ranked higher.
    Only stocks with valid Graham Numbers are included.

    Args:
        df: DataFrame with stock data including eps, book_value_per_share, and price.

    Returns:
        DataFrame with added columns:
        - graham_number: The calculated Graham Number
        - margin_of_safety: Margin percentage (positive = undervalued)
        - rank_graham: Rank by margin of safety (1 = most undervalued)
        Sorted by margin_of_safety descending (most undervalued first).
        Stocks with invalid data are excluded.
    """
    result = df.copy()

    # Calculate Graham Number and margin of safety for each row
    result["graham_number"] = None
    result["margin_of_safety"] = None

    for idx, row in result.iterrows():
        eps = row.get("eps")
        bvps = row.get("book_value_per_share")
        price = row.get("price")

        graham = calculate_graham_number(eps, bvps)
        margin = calculate_margin_of_safety(graham, price)

        result.at[idx, "graham_number"] = graham
        result.at[idx, "margin_of_safety"] = margin

    # Filter out stocks with no valid margin of safety
    result = result.dropna(subset=["margin_of_safety"])

    if result.empty:
        return result

    # Rank by margin of safety descending (higher margin = better value)
    result["rank_graham"] = result["margin_of_safety"].rank(
        ascending=False, method="first"
    ).astype(int)

    # Sort by margin of safety descending (most undervalued first)
    result = result.sort_values("margin_of_safety", ascending=False).reset_index(drop=True)

    return result


def get_top_graham_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get the top N stocks by Graham Number margin of safety.

    Returns the most undervalued stocks based on the Graham Number.

    Args:
        df: DataFrame sorted by margin_of_safety (from rank_by_margin_of_safety).
        n: Number of top stocks to return (default: 5).

    Returns:
        DataFrame containing the top N most undervalued stocks.
    """
    return df.head(n).copy()
