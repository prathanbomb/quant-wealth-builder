"""Reddit Momentum Formula calculation module.

Implements momentum ranking based on Reddit sentiment data:
- Sentiment Score: How positive/negative discussions are
- Discussion Volume: How much the stock is being discussed
"""

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_momentum_score(sentiment_score: float, no_of_comments: int) -> float:
    """
    Calculate combined momentum score from sentiment and volume.

    Formula: sentiment_score * 1000 + log(no_of_comments + 1)

    The sentiment_score is the primary factor (multiplied by 1000 to ensure
    it dominates). Discussion volume is a secondary factor using logarithmic
    scaling to prevent spam from overwhelming genuine sentiment.

    Args:
        sentiment_score: Sentiment value from API (typically 0.0 to 1.0).
        no_of_comments: Number of Reddit comments.

    Returns:
        Combined momentum score (higher = better).
    """
    # Sentiment is primary (0-1 range becomes 0-1000)
    sentiment_component = sentiment_score * 1000

    # Logarithmic comment scaling prevents spam from dominating
    # log(comments + 1) gives diminishing returns
    volume_component = np.log(no_of_comments + 1)

    return sentiment_component + volume_component


def filter_by_stock_universe(
    reddit_data: List[Dict[str, Any]],
    stock_universe: List[str],
) -> pd.DataFrame:
    """
    Filter Reddit data to only include stocks in the given universe.

    Args:
        reddit_data: Raw data from Reddit API (list of dicts).
        stock_universe: List of valid stock symbols.

    Returns:
        DataFrame with columns:
        - ticker
        - no_of_comments
        - sentiment
        - sentiment_score
    """
    # Convert stock universe to set for O(1) lookup
    universe_set = set(symbol.upper() for symbol in stock_universe)

    filtered_data = []
    excluded_count = 0

    for item in reddit_data:
        ticker = item.get("ticker", "").upper()

        if ticker in universe_set:
            filtered_data.append({
                "ticker": ticker,
                "no_of_comments": item["no_of_comments"],
                "sentiment": item["sentiment"],
                "sentiment_score": item["sentiment_score"],
            })
        else:
            excluded_count += 1
            logger.debug(f"Excluded {ticker} - not in stock universe")

    logger.info(
        f"Filtered Reddit data: {len(filtered_data)} matches, "
        f"{excluded_count} excluded from universe"
    )

    return pd.DataFrame(filtered_data)


def rank_by_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks by Reddit momentum score.

    Args:
        df: DataFrame with Reddit sentiment data (from filter_by_stock_universe).

    Returns:
        DataFrame with additional columns:
        - momentum_score: Combined score
        - rank: Ranking (1 = best)
        Sorted by momentum_score descending.
    """
    if df.empty:
        logger.warning("Cannot rank empty DataFrame")
        return df

    result = df.copy()

    # Calculate momentum score for each stock
    result["momentum_score"] = result.apply(
        lambda row: calculate_momentum_score(
            row["sentiment_score"],
            row["no_of_comments"]
        ),
        axis=1
    )

    # Rank by momentum score (descending - highest score gets rank 1)
    result["rank"] = result["momentum_score"].rank(
        ascending=False, method="first"
    ).astype(int)

    # Sort by momentum score descending (best stocks first)
    result = result.sort_values("momentum_score", ascending=False).reset_index(drop=True)

    logger.info(f"Ranked {len(result)} stocks by momentum score")

    return result


def get_top_momentum_picks(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get top N stocks from ranked momentum DataFrame.

    Filters out bearish stocks before selecting top picks. Only stocks
    with "Bullish" sentiment are eligible for top picks.

    Args:
        df: Ranked DataFrame from rank_by_momentum.
        n: Number of top stocks to return (default: 5).

    Returns:
        DataFrame with top N bullish stocks by momentum score.
    """
    if df.empty:
        logger.warning("Cannot get top picks from empty DataFrame")
        return df

    # Filter to only bullish stocks
    bullish_df = df[df["sentiment"] == "Bullish"].copy()

    if bullish_df.empty:
        logger.warning("No bullish stocks found in Reddit data")
        return pd.DataFrame()

    # Sort by momentum score descending to ensure we get actual top N
    bullish_df = bullish_df.sort_values("momentum_score", ascending=False)

    # Get top N stocks
    top_picks = bullish_df.head(n).copy()

    logger.info(
        f"Selected top {len(top_picks)} bullish stocks from {len(bullish_df)} bullish candidates"
    )

    return top_picks
