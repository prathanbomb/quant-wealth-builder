"""Piotroski F-Score calculation module.

Implements Joseph Piotroski's F-Score, a 9-point scoring system that measures
the financial strength of a company based on profitability, leverage, liquidity,
and operating efficiency signals.

Score interpretation:
- 8-9: Strong financial position
- 5-7: Average financial position
- 0-4: Weak financial position
"""

from typing import Optional, Union

import pandas as pd


def _is_valid(value: Optional[Union[float, int]]) -> bool:
    """Check if a value is valid (not None and not NaN)."""
    if value is None:
        return False
    try:
        return not pd.isna(value)
    except (TypeError, ValueError):
        return True


def _score_positive_roa(net_income: Optional[float], total_assets: Optional[float]) -> int:
    """
    Score 1: Positive Return on Assets.

    Awards 1 point if ROA (Net Income / Total Assets) > 0.

    Args:
        net_income: Net income for current year.
        total_assets: Total assets for current year.

    Returns:
        1 if ROA is positive, 0 otherwise.
    """
    if not _is_valid(net_income) or not _is_valid(total_assets) or total_assets == 0:
        return 0
    return 1 if (net_income / total_assets) > 0 else 0


def _score_positive_cfo(operating_cash_flow: Optional[float]) -> int:
    """
    Score 2: Positive Operating Cash Flow.

    Awards 1 point if operating cash flow is positive.

    Args:
        operating_cash_flow: Operating cash flow for current year.

    Returns:
        1 if positive, 0 otherwise.
    """
    if not _is_valid(operating_cash_flow):
        return 0
    return 1 if operating_cash_flow > 0 else 0


def _score_roa_improvement(
    roa_current: Optional[float],
    roa_previous: Optional[float],
) -> int:
    """
    Score 3: ROA Improvement Year-over-Year.

    Awards 1 point if ROA increased from previous year.

    Args:
        roa_current: Current year ROA.
        roa_previous: Previous year ROA.

    Returns:
        1 if ROA improved, 0 otherwise.
    """
    if not _is_valid(roa_current) or not _is_valid(roa_previous):
        return 0
    return 1 if roa_current > roa_previous else 0


def _score_accruals(
    operating_cash_flow: Optional[float],
    net_income: Optional[float],
) -> int:
    """
    Score 4: Quality of Earnings (Accruals).

    Awards 1 point if operating cash flow exceeds net income.
    This indicates earnings quality - cash flow should support reported income.

    Args:
        operating_cash_flow: Operating cash flow for current year.
        net_income: Net income for current year.

    Returns:
        1 if CFO > Net Income, 0 otherwise.
    """
    if not _is_valid(operating_cash_flow) or not _is_valid(net_income):
        return 0
    return 1 if operating_cash_flow > net_income else 0


def _score_decreased_leverage(
    long_term_debt: Optional[float],
    long_term_debt_prev: Optional[float],
    total_assets: Optional[float],
    total_assets_prev: Optional[float],
) -> int:
    """
    Score 5: Decreased Long-term Debt Ratio.

    Awards 1 point if long-term debt ratio (LT Debt / Total Assets) decreased.

    Args:
        long_term_debt: Current year long-term debt.
        long_term_debt_prev: Previous year long-term debt.
        total_assets: Current year total assets.
        total_assets_prev: Previous year total assets.

    Returns:
        1 if leverage decreased, 0 otherwise.
    """
    # Handle missing data - if no asset data, assume no change (0 points)
    if not _is_valid(total_assets) or total_assets == 0:
        return 0
    if not _is_valid(total_assets_prev) or total_assets_prev == 0:
        return 0

    # Treat None/NaN debt as zero debt
    debt_current = long_term_debt if _is_valid(long_term_debt) else 0
    debt_prev = long_term_debt_prev if _is_valid(long_term_debt_prev) else 0

    ratio_current = debt_current / total_assets
    ratio_prev = debt_prev / total_assets_prev

    return 1 if ratio_current < ratio_prev else 0


def _score_improved_liquidity(
    current_ratio: Optional[float],
    current_ratio_prev: Optional[float],
) -> int:
    """
    Score 6: Improved Current Ratio (Liquidity).

    Awards 1 point if current ratio increased from previous year.

    Args:
        current_ratio: Current year current ratio.
        current_ratio_prev: Previous year current ratio.

    Returns:
        1 if liquidity improved, 0 otherwise.
    """
    if not _is_valid(current_ratio) or not _is_valid(current_ratio_prev):
        return 0
    return 1 if current_ratio > current_ratio_prev else 0


def _score_no_dilution(
    shares_outstanding: Optional[float],
    shares_outstanding_prev: Optional[float],
) -> int:
    """
    Score 7: No New Shares Issued (No Dilution).

    Awards 1 point if shares outstanding did not increase.

    Args:
        shares_outstanding: Current year shares outstanding.
        shares_outstanding_prev: Previous year shares outstanding.

    Returns:
        1 if no dilution, 0 otherwise.
    """
    # If we don't have current year data, we can't determine dilution
    if not _is_valid(shares_outstanding):
        return 0
    # yfinance doesn't provide historical shares, so we give benefit of doubt
    if not _is_valid(shares_outstanding_prev):
        # No historical data available - award point (benefit of doubt)
        return 1
    return 1 if shares_outstanding <= shares_outstanding_prev else 0


def _score_improved_margin(
    gross_margin: Optional[float],
    gross_margin_prev: Optional[float],
) -> int:
    """
    Score 8: Improved Gross Margin.

    Awards 1 point if gross margin increased from previous year.

    Args:
        gross_margin: Current year gross margin.
        gross_margin_prev: Previous year gross margin.

    Returns:
        1 if margin improved, 0 otherwise.
    """
    if not _is_valid(gross_margin) or not _is_valid(gross_margin_prev):
        return 0
    return 1 if gross_margin > gross_margin_prev else 0


def _score_improved_turnover(
    asset_turnover: Optional[float],
    asset_turnover_prev: Optional[float],
) -> int:
    """
    Score 9: Improved Asset Turnover.

    Awards 1 point if asset turnover increased from previous year.

    Args:
        asset_turnover: Current year asset turnover.
        asset_turnover_prev: Previous year asset turnover.

    Returns:
        1 if turnover improved, 0 otherwise.
    """
    if not _is_valid(asset_turnover) or not _is_valid(asset_turnover_prev):
        return 0
    return 1 if asset_turnover > asset_turnover_prev else 0


def calculate_fscore(
    net_income: Optional[float],
    total_assets: Optional[float],
    operating_cash_flow: Optional[float],
    roa: Optional[float],
    roa_prev: Optional[float],
    long_term_debt: Optional[float],
    long_term_debt_prev: Optional[float],
    total_assets_prev: Optional[float],
    current_ratio: Optional[float],
    current_ratio_prev: Optional[float],
    shares_outstanding: Optional[float],
    shares_outstanding_prev: Optional[float],
    gross_margin: Optional[float],
    gross_margin_prev: Optional[float],
    asset_turnover: Optional[float],
    asset_turnover_prev: Optional[float],
) -> Optional[int]:
    """
    Calculate the Piotroski F-Score (0-9).

    The F-Score is composed of 9 binary signals:
    - Profitability (4 points): Positive ROA, Positive CFO, ROA improvement, Accruals
    - Leverage/Liquidity (3 points): Decreased leverage, Improved liquidity, No dilution
    - Operating Efficiency (2 points): Improved margin, Improved turnover

    Args:
        net_income: Net income for current year.
        total_assets: Total assets for current year.
        operating_cash_flow: Operating cash flow for current year.
        roa: Return on assets for current year.
        roa_prev: Return on assets for previous year.
        long_term_debt: Long-term debt for current year.
        long_term_debt_prev: Long-term debt for previous year.
        total_assets_prev: Total assets for previous year.
        current_ratio: Current ratio for current year.
        current_ratio_prev: Current ratio for previous year.
        shares_outstanding: Shares outstanding for current year.
        shares_outstanding_prev: Shares outstanding for previous year.
        gross_margin: Gross margin for current year.
        gross_margin_prev: Gross margin for previous year.
        asset_turnover: Asset turnover for current year.
        asset_turnover_prev: Asset turnover for previous year.

    Returns:
        F-Score (0-9), or None if insufficient data for calculation.
    """
    # Require at least some basic data to calculate a score
    if not _is_valid(net_income) and not _is_valid(operating_cash_flow):
        return None
    if not _is_valid(total_assets):
        return None

    # Calculate each component
    score = 0

    # Profitability signals (4 points)
    score += _score_positive_roa(net_income, total_assets)
    score += _score_positive_cfo(operating_cash_flow)
    score += _score_roa_improvement(roa, roa_prev)
    score += _score_accruals(operating_cash_flow, net_income)

    # Leverage/Liquidity signals (3 points)
    score += _score_decreased_leverage(
        long_term_debt, long_term_debt_prev, total_assets, total_assets_prev
    )
    score += _score_improved_liquidity(current_ratio, current_ratio_prev)
    score += _score_no_dilution(shares_outstanding, shares_outstanding_prev)

    # Operating Efficiency signals (2 points)
    score += _score_improved_margin(gross_margin, gross_margin_prev)
    score += _score_improved_turnover(asset_turnover, asset_turnover_prev)

    return score


def calculate_fscore_from_dict(data: dict) -> Optional[int]:
    """
    Calculate F-Score from a stock data dictionary.

    Convenience function that extracts fields from a stock data dict
    and calls calculate_fscore.

    Args:
        data: Stock data dictionary from StockDataClient.

    Returns:
        F-Score (0-9), or None if insufficient data.
    """
    return calculate_fscore(
        net_income=data.get("net_income"),
        total_assets=data.get("total_assets"),
        operating_cash_flow=data.get("operating_cash_flow"),
        roa=data.get("roa"),
        roa_prev=data.get("roa_prev"),
        long_term_debt=data.get("long_term_debt"),
        long_term_debt_prev=data.get("long_term_debt_prev"),
        total_assets_prev=data.get("total_assets_prev"),
        current_ratio=data.get("current_ratio"),
        current_ratio_prev=data.get("current_ratio_prev"),
        shares_outstanding=data.get("shares_outstanding"),
        shares_outstanding_prev=data.get("shares_outstanding_prev"),
        gross_margin=data.get("gross_margin"),
        gross_margin_prev=data.get("gross_margin_prev"),
        asset_turnover=data.get("asset_turnover"),
        asset_turnover_prev=data.get("asset_turnover_prev"),
    )


def rank_by_fscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks by Piotroski F-Score.

    Calculates F-Score for each stock and ranks them in descending order
    (higher score = better).

    Args:
        df: DataFrame with stock data including fields needed for F-Score.

    Returns:
        DataFrame with added columns:
        - fscore: The calculated F-Score (0-9)
        - rank_fscore: Rank by F-Score (1 = highest score)
        Sorted by fscore descending (best stocks first).
        Stocks with None fscore are excluded.
    """
    result = df.copy()

    # Calculate F-Score for each row
    result["fscore"] = result.apply(
        lambda row: calculate_fscore(
            net_income=row.get("net_income"),
            total_assets=row.get("total_assets"),
            operating_cash_flow=row.get("operating_cash_flow"),
            roa=row.get("roa"),
            roa_prev=row.get("roa_prev"),
            long_term_debt=row.get("long_term_debt"),
            long_term_debt_prev=row.get("long_term_debt_prev"),
            total_assets_prev=row.get("total_assets_prev"),
            current_ratio=row.get("current_ratio"),
            current_ratio_prev=row.get("current_ratio_prev"),
            shares_outstanding=row.get("shares_outstanding"),
            shares_outstanding_prev=row.get("shares_outstanding_prev"),
            gross_margin=row.get("gross_margin"),
            gross_margin_prev=row.get("gross_margin_prev"),
            asset_turnover=row.get("asset_turnover"),
            asset_turnover_prev=row.get("asset_turnover_prev"),
        ),
        axis=1,
    )

    # Filter out stocks with no valid F-Score
    result = result.dropna(subset=["fscore"])

    if result.empty:
        return result

    # Rank by F-Score (descending - highest gets rank 1)
    # Using method='first' to handle ties deterministically
    result["rank_fscore"] = result["fscore"].rank(
        ascending=False, method="first"
    ).astype(int)

    # Sort by F-Score descending (best stocks first)
    result = result.sort_values("fscore", ascending=False).reset_index(drop=True)

    return result


def get_top_fscore_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get the top N stocks by Piotroski F-Score.

    Args:
        df: DataFrame sorted by fscore (from rank_by_fscore).
        n: Number of top stocks to return (default: 5).

    Returns:
        DataFrame containing the top N stocks with highest F-Scores.
    """
    return df.head(n).copy()
