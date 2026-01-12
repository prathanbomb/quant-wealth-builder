"""Altman Z-Score calculation module.

Implements Edward Altman's Z-Score model for predicting bankruptcy risk.
The Z-Score combines 5 financial ratios to assess a company's financial health.

Formula:
    Z = 1.2×(Working Capital / Total Assets)
      + 1.4×(Retained Earnings / Total Assets)
      + 3.3×(EBIT / Total Assets)
      + 0.6×(Market Cap / Total Liabilities)
      + 1.0×(Revenue / Total Assets)

Risk Zones:
    Z > 2.99: Safe Zone (low bankruptcy risk)
    1.81 < Z < 2.99: Grey Zone (moderate risk)
    Z < 1.81: Distress Zone (high bankruptcy risk)

This implementation only ranks companies in the Safe Zone for investment purposes.
"""

from typing import Optional

import pandas as pd


# Zone thresholds
SAFE_ZONE_THRESHOLD = 2.99
GREY_ZONE_THRESHOLD = 1.81


def _is_valid(value: Optional[float]) -> bool:
    """Check if a value is valid (not None and not NaN)."""
    if value is None:
        return False
    try:
        return not pd.isna(value)
    except (TypeError, ValueError):
        return True


def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safely divide two numbers, returning None for invalid inputs."""
    if not _is_valid(numerator) or not _is_valid(denominator):
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def calculate_zscore(
    working_capital: Optional[float],
    retained_earnings: Optional[float],
    ebit: Optional[float],
    market_cap: Optional[float],
    total_liabilities: Optional[float],
    revenue: Optional[float],
    total_assets: Optional[float],
) -> Optional[float]:
    """
    Calculate the Altman Z-Score.

    The Z-Score combines 5 financial ratios with specific weights:
    - 1.2 × Working Capital / Total Assets (liquidity)
    - 1.4 × Retained Earnings / Total Assets (cumulative profitability)
    - 3.3 × EBIT / Total Assets (operating efficiency)
    - 0.6 × Market Cap / Total Liabilities (solvency/leverage)
    - 1.0 × Revenue / Total Assets (asset turnover)

    Args:
        working_capital: Current Assets - Current Liabilities.
        retained_earnings: Cumulative retained earnings.
        ebit: Earnings Before Interest and Taxes (Operating Income).
        market_cap: Market capitalization.
        total_liabilities: Total liabilities.
        revenue: Total revenue.
        total_assets: Total assets.

    Returns:
        Z-Score value, or None if insufficient data for calculation.
        Returns None if total_assets is zero (would cause division by zero).
    """
    # Total Assets is the common denominator for most ratios
    if not _is_valid(total_assets) or total_assets == 0:
        return None

    # Calculate each component
    score = 0.0
    components_count = 0

    # Component 1: 1.2 × Working Capital / Total Assets
    wc_ratio = _safe_divide(working_capital, total_assets)
    if wc_ratio is not None:
        score += 1.2 * wc_ratio
        components_count += 1

    # Component 2: 1.4 × Retained Earnings / Total Assets
    re_ratio = _safe_divide(retained_earnings, total_assets)
    if re_ratio is not None:
        score += 1.4 * re_ratio
        components_count += 1

    # Component 3: 3.3 × EBIT / Total Assets
    ebit_ratio = _safe_divide(ebit, total_assets)
    if ebit_ratio is not None:
        score += 3.3 * ebit_ratio
        components_count += 1

    # Component 4: 0.6 × Market Cap / Total Liabilities
    solvency_ratio = _safe_divide(market_cap, total_liabilities)
    if solvency_ratio is not None:
        score += 0.6 * solvency_ratio
        components_count += 1

    # Component 5: 1.0 × Revenue / Total Assets
    turnover_ratio = _safe_divide(revenue, total_assets)
    if turnover_ratio is not None:
        score += 1.0 * turnover_ratio
        components_count += 1

    # Require at least 4 out of 5 components for a valid score
    if components_count < 4:
        return None

    return score


def get_risk_zone(zscore: Optional[float]) -> str:
    """
    Get the risk zone category for a Z-Score.

    Args:
        zscore: The calculated Z-Score.

    Returns:
        "Safe" if Z > 2.99 (low bankruptcy risk)
        "Grey" if 1.81 < Z < 2.99 (moderate risk)
        "Distress" if Z < 1.81 (high bankruptcy risk)
        "Unknown" if zscore is None
    """
    if zscore is None:
        return "Unknown"

    if zscore > SAFE_ZONE_THRESHOLD:
        return "Safe"
    elif zscore > GREY_ZONE_THRESHOLD:
        return "Grey"
    else:
        return "Distress"


def calculate_zscore_from_dict(data: dict) -> tuple[Optional[float], str]:
    """
    Calculate Z-Score and risk zone from a stock data dictionary.

    Convenience function that extracts fields from a stock data dict.

    Args:
        data: Stock data dictionary from StockDataClient.

    Returns:
        Tuple of (zscore, risk_zone).
        risk_zone is one of: "Safe", "Grey", "Distress", "Unknown"
    """
    zscore = calculate_zscore(
        working_capital=data.get("working_capital"),
        retained_earnings=data.get("retained_earnings"),
        ebit=data.get("ebit"),
        market_cap=data.get("market_cap"),
        total_liabilities=data.get("total_liabilities"),
        revenue=data.get("revenue"),
        total_assets=data.get("total_assets"),
    )
    risk_zone = get_risk_zone(zscore)
    return zscore, risk_zone


def rank_by_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks by Z-Score descending (higher is safer).

    Only stocks in the Safe Zone (Z > 2.99) are included in the ranking.
    Grey and Distress zone stocks are excluded as they represent higher risk.

    Args:
        df: DataFrame with stock data including all required financial metrics.

    Returns:
        DataFrame with added columns:
        - zscore: The calculated Altman Z-Score
        - risk_zone: Risk zone category ("Safe", "Grey", "Distress")
        - rank_zscore: Rank by Z-Score (1 = safest)
        Sorted by zscore descending (safest first).
        Stocks not in Safe Zone are excluded.
    """
    result = df.copy()

    # Calculate Z-Score and risk zone for each row
    result["zscore"] = None
    result["risk_zone"] = "Unknown"

    for idx, row in result.iterrows():
        zscore = calculate_zscore(
            working_capital=row.get("working_capital"),
            retained_earnings=row.get("retained_earnings"),
            ebit=row.get("ebit"),
            market_cap=row.get("market_cap"),
            total_liabilities=row.get("total_liabilities"),
            revenue=row.get("revenue"),
            total_assets=row.get("total_assets"),
        )
        risk_zone = get_risk_zone(zscore)

        result.at[idx, "zscore"] = zscore
        result.at[idx, "risk_zone"] = risk_zone

    # Filter to only Safe Zone stocks
    result = result[result["risk_zone"] == "Safe"]

    if result.empty:
        return result

    # Rank by Z-Score descending (higher = safer)
    result["rank_zscore"] = result["zscore"].rank(
        ascending=False, method="first"
    ).astype(int)

    # Sort by Z-Score descending (safest first)
    result = result.sort_values("zscore", ascending=False).reset_index(drop=True)

    return result


def get_top_zscore_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get the top N stocks by Altman Z-Score (safest financial health).

    Returns the stocks with highest Z-Scores from the Safe Zone.

    Args:
        df: DataFrame sorted by zscore (from rank_by_zscore).
        n: Number of top stocks to return (default: 5).

    Returns:
        DataFrame containing the top N safest stocks by Z-Score.
        Returns fewer than n if fewer Safe Zone stocks are available.
    """
    return df.head(n).copy()
