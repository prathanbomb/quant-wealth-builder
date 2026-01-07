"""Magic Formula calculation module.

Implements Joel Greenblatt's Magic Formula ranking algorithm:
- Earnings Yield: EBIT / Enterprise Value (the "Cheap" metric)
- Return on Capital: EBIT / Capital Employed (the "Good" metric)
"""

from typing import Optional

import pandas as pd


def calculate_earnings_yield(ebit: float, enterprise_value: float) -> Optional[float]:
    """
    Calculate Earnings Yield = EBIT / Enterprise Value.

    Earnings Yield measures how cheap a stock is relative to its earnings power.
    Higher values indicate the company is more undervalued.

    Args:
        ebit: Earnings Before Interest and Taxes (operating income).
        enterprise_value: Total enterprise value of the company.

    Returns:
        Earnings yield as a decimal (e.g., 0.08 for 8%), or None if
        enterprise_value is zero or negative.
    """
    if enterprise_value <= 0:
        return None

    return ebit / enterprise_value


def calculate_roc(
    ebit: float,
    total_assets: float,
    current_liabilities: float,
) -> Optional[float]:
    """
    Calculate Return on Capital = EBIT / Capital Employed.

    Return on Capital measures how efficiently a company uses its capital
    to generate profits. Higher values indicate better capital efficiency.

    Uses the simplified formula: Capital Employed = Total Assets - Current Liabilities
    This approximates (Net Working Capital + Net Fixed Assets).

    Args:
        ebit: Earnings Before Interest and Taxes (operating income).
        total_assets: Total assets from balance sheet.
        current_liabilities: Current liabilities from balance sheet.

    Returns:
        Return on capital as a decimal (e.g., 0.25 for 25%), or None if
        capital employed is zero or negative.
    """
    capital_employed = total_assets - current_liabilities

    if capital_employed <= 0:
        return None

    return ebit / capital_employed


def rank_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks using the Magic Formula algorithm.

    Adds ranking columns and calculates the combined Magic Score.
    Lower Magic Score = better stock (combines high earnings yield + high ROC).

    Args:
        df: DataFrame with 'earnings_yield' and 'roc' columns.

    Returns:
        DataFrame with added columns:
        - rank_ey: Earnings Yield rank (1 = highest yield)
        - rank_roc: ROC rank (1 = highest ROC)
        - magic_score: Combined score (rank_ey + rank_roc)
        Sorted by magic_score ascending (best stocks first).
    """
    result = df.copy()

    # Rank by earnings yield (descending - highest gets rank 1)
    # Using method='first' to handle ties deterministically
    result["rank_ey"] = result["earnings_yield"].rank(
        ascending=False, method="first"
    ).astype(int)

    # Rank by ROC (descending - highest gets rank 1)
    result["rank_roc"] = result["roc"].rank(
        ascending=False, method="first"
    ).astype(int)

    # Calculate Magic Score (lower is better)
    result["magic_score"] = result["rank_ey"] + result["rank_roc"]

    # Sort by magic_score ascending (best stocks first)
    result = result.sort_values("magic_score", ascending=True).reset_index(drop=True)

    return result


def get_top_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get the top N stocks from a ranked DataFrame.

    Args:
        df: DataFrame sorted by magic_score (from rank_stocks).
        n: Number of top stocks to return (default: 5).

    Returns:
        DataFrame containing the top N stocks with lowest magic scores.
    """
    return df.head(n).copy()
