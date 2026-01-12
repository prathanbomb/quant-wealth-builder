"""Acquirer's Multiple calculation module.

Implements Tobias Carlisle's Acquirer's Multiple, a deep value investing metric.
The Acquirer's Multiple measures how cheap a company is based on its enterprise value
relative to its operating income.

Formula:
    Acquirer's Multiple = Enterprise Value / Operating Income (EBIT)

Lower values indicate cheaper stocks (better value). This metric is preferred by
deep value investors because it considers:
- Enterprise Value (includes debt, excludes cash) rather than market cap
- Operating Income (EBIT) rather than net income (excludes interest/tax effects)

Interpretation:
- < 5x: Very cheap (deep value opportunity)
- 5-10x: Reasonably priced
- > 10x: Expensive
- < 0: Invalid (negative EBIT means losing money)
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


def calculate_acquirer_multiple(enterprise_value: Optional[float], operating_income: Optional[float]) -> Optional[float]:
    """
    Calculate the Acquirer's Multiple.

    Acquirer's Multiple = Enterprise Value / Operating Income (EBIT)

    Args:
        enterprise_value: Enterprise Value (market cap + debt - cash).
        operating_income: Operating Income (EBIT).

    Returns:
        Acquirer's Multiple value, or None if inputs are invalid.
        Returns None if EBIT is zero or negative.
        Returns None if Enterprise Value is negative.
    """
    if not _is_valid(enterprise_value) or not _is_valid(operating_income):
        return None

    # Negative EBIT means the company is losing money
    # Zero EBIT would cause division by zero
    if operating_income <= 0:
        return None

    # Negative EV doesn't make economic sense
    # (though technically possible, usually indicates data issues)
    if enterprise_value < 0:
        return None

    try:
        multiple = enterprise_value / operating_income
        return multiple
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def calculate_acquirer_from_dict(data: dict) -> Optional[float]:
    """
    Calculate Acquirer's Multiple from a stock data dictionary.

    Convenience function that extracts fields from a stock data dict.

    Args:
        data: Stock data dictionary from StockDataClient.
            Must contain 'enterprise_value' and 'ebit' keys.

    Returns:
        Acquirer's Multiple value, or None if calculation failed.
    """
    enterprise_value = data.get("enterprise_value")
    operating_income = data.get("ebit")

    return calculate_acquirer_multiple(enterprise_value, operating_income)


def rank_by_acquirer_multiple(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks by Acquirer's Multiple ascending.

    Stocks with lower Acquirer's Multiple are cheaper and ranked higher.
    Only stocks with valid multiples are included.

    Args:
        df: DataFrame with stock data including enterprise_value and ebit.

    Returns:
        DataFrame with added columns:
        - acquirer_multiple: The calculated Acquirer's Multiple
        - rank_acquirer: Rank by multiple (1 = cheapest)
        Sorted by acquirer_multiple ascending (cheapest first).
        Stocks with invalid data are excluded.
    """
    result = df.copy()

    # Calculate Acquirer's Multiple for each row
    result["acquirer_multiple"] = result.apply(
        lambda row: calculate_acquirer_multiple(
            enterprise_value=row.get("enterprise_value"),
            operating_income=row.get("ebit"),
        ),
        axis=1,
    )

    # Filter out stocks with no valid Acquirer's Multiple
    result = result.dropna(subset=["acquirer_multiple"])

    if result.empty:
        return result

    # Rank by Acquirer's Multiple ascending (lower = better value)
    result["rank_acquirer"] = result["acquirer_multiple"].rank(
        ascending=True, method="first"
    ).astype(int)

    # Sort by Acquirer's Multiple ascending (cheapest first)
    result = result.sort_values("acquirer_multiple", ascending=True).reset_index(drop=True)

    return result


def get_top_acquirer_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get the top N stocks by Acquirer's Multiple (cheapest stocks).

    Returns the stocks with lowest Acquirer's Multiple (best value).

    Args:
        df: DataFrame sorted by acquirer_multiple (from rank_by_acquirer_multiple).
        n: Number of top stocks to return (default: 5).

    Returns:
        DataFrame containing the top N cheapest stocks by Acquirer's Multiple.
    """
    return df.head(n).copy()
