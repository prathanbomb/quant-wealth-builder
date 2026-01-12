"""Portfolio data utilities module.

Provides functions for fetching historical price data and computing
covariance matrices for portfolio analysis.
"""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Number of trading days per year (for annualization)
TRADING_DAYS_PER_YEAR = 252


def fetch_historical_returns(
    symbols: List[str],
    period: str = "1y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Fetch historical price data and compute daily returns.

    Uses yfinance to download historical OHLCV data, then computes
    daily percentage returns for each symbol.

    Args:
        symbols: List of stock symbols (e.g., ["AAPL", "MSFT"])
        period: yfinance period parameter (default: "1y" for 1 year)
                Options: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
        interval: yfinance interval parameter (default: "1d" for daily)
                  Options: "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"

    Returns:
        DataFrame with daily returns for each symbol, indexed by date.
        Returns None if fetch fails or no valid data is found.

    Example:
        >>> returns = fetch_historical_returns(["AAPL", "MSFT"], period="1y")
        >>> print(returns.head())
                AAPL      MSFT
        Date
        2023-01-03  0.0125  0.0080
        2023-01-04 -0.0050 -0.0030
    """
    if not symbols:
        logger.warning("Empty symbols list provided")
        return None

    if len(symbols) == 0:
        logger.warning("No symbols to fetch")
        return None

    logger.info(f"Fetching historical returns for {len(symbols)} symbols: {symbols}")

    try:
        # Download historical data using yfinance
        logger.debug(f"Downloading data with period={period}, interval={interval}")

        # yfinance can handle multiple symbols at once
        # We'll fetch them together and then extract the 'Close' prices
        data = yf.download(
            " ".join(symbols),
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False  # Get raw prices, not auto-adjusted
        )

        if data.empty:
            logger.warning(f"No data returned for symbols: {symbols}")
            return None

        # Extract close prices
        # For single symbol, yfinance returns a Series
        # For multiple symbols, it returns a DataFrame with MultiIndex columns
        if "Close" in data.columns:
            close_prices = data["Close"]
        else:
            # Single symbol case - data itself is the prices
            close_prices = data

        # Handle single symbol - convert to DataFrame
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.to_frame()

        # Drop any columns with all NaN values
        close_prices = close_prices.dropna(axis=1, how="all")

        if close_prices.empty:
            logger.warning("All price data is NaN")
            return None

        # Check which symbols we actually got data for
        available_symbols = list(close_prices.columns)
        missing_symbols = set(symbols) - set(available_symbols)

        if missing_symbols:
            logger.warning(f"Could not fetch data for symbols: {missing_symbols}")
            if not available_symbols:
                logger.error("No valid data available")
                return None

        # Forward fill missing values (common in yfinance data)
        close_prices = close_prices.ffill()

        # Compute daily returns: (P_t / P_{t-1}) - 1
        returns = close_prices.pct_change().dropna()

        if returns.empty:
            logger.warning("No returns data after calculation")
            return None

        logger.info(
            f"Successfully computed returns for {len(available_symbols)} symbols, "
            f"{len(returns)} trading days"
        )

        return returns

    except Exception as e:
        logger.error(f"Failed to fetch historical returns: {e}")
        return None


def compute_covariance_matrix(
    returns_df: pd.DataFrame,
    annualize: bool = True
) -> np.ndarray:
    """
    Compute covariance matrix from returns DataFrame.

    The covariance matrix measures how assets move together.
    Positive values = assets move together
    Negative values = assets move in opposite directions
    Values near zero = assets are uncorrelated

    Args:
        returns_df: DataFrame with daily returns (columns = assets, rows = dates)
        annualize: If True, annualize the covariance matrix (multiply by 252 trading days)
                   Default: True

    Returns:
        NxN covariance matrix as numpy array, where N is the number of assets.

    Example:
        >>> returns = pd.DataFrame({
        ...     "AAPL": [0.01, 0.02, -0.01],
        ...     "MSFT": [0.015, 0.01, 0.02]
        ... })
        >>> cov = compute_covariance_matrix(returns)
        >>> print(cov.shape)
        (2, 2)
    """
    if returns_df.empty:
        logger.warning("Cannot compute covariance from empty DataFrame")
        return np.array([])

    n_assets = returns_df.shape[1]

    if n_assets == 0:
        logger.warning("No columns in returns DataFrame")
        return np.array([])

    logger.debug(f"Computing covariance matrix for {n_assets} assets")

    # Compute sample covariance matrix
    # pandas .cov() calculates the sample covariance by default
    cov_matrix = returns_df.cov()

    # Annualize: multiply by number of trading days
    # Daily covariance * 252 = annualized covariance
    if annualize:
        cov_matrix = cov_matrix * TRADING_DAYS_PER_YEAR
        logger.debug("Annualized covariance matrix (x252)")

    # Convert to numpy array
    cov_array = cov_matrix.to_numpy()

    logger.debug(f"Covariance matrix shape: {cov_array.shape}")

    return cov_array


def compute_expected_returns(
    returns_df: pd.DataFrame,
    annualize: bool = True
) -> np.ndarray:
    """
    Compute expected (mean) returns from returns DataFrame.

    Args:
        returns_df: DataFrame with daily returns
        annualize: If True, annualize the returns (multiply by 252)
                   Default: True

    Returns:
        1D numpy array of expected returns, one per asset.
    """
    if returns_df.empty:
        logger.warning("Cannot compute expected returns from empty DataFrame")
        return np.array([])

    # Compute mean daily return for each asset
    mean_returns = returns_df.mean()

    # Annualize: multiply by number of trading days
    if annualize:
        mean_returns = mean_returns * TRADING_DAYS_PER_YEAR
        logger.debug("Annualized expected returns (x252)")

    logger.debug(f"Expected returns: {mean_returns.tolist()}")

    return mean_returns.to_numpy()
