"""Portfolio Optimizer API client module.

Implements portfolio analysis and optimization using the Portfolio Optimizer Web API:
https://api.portfoliooptimizer.io/

Provides:
- Risk metrics: volatility, Sharpe ratio, diversification ratio
- Portfolio construction: maximum Sharpe ratio, minimum variance, equal risk contributions
"""

import logging
import time
from typing import Any, Dict, List, Optional

import certifi
import requests

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

# Portfolio Optimizer API endpoints
API_BASE_URL = "https://api.portfoliooptimizer.io/v1"


class PortfolioOptimizerClient:
    """Client for Portfolio Optimizer API."""

    def __init__(self, disable_ssl_verification: bool = False):
        """
        Initialize the Portfolio Optimizer client.

        Args:
            disable_ssl_verification: If True, disable SSL verification (NOT recommended
                for production). Use only for testing/diagnosis. Default: False.
        """
        self.disable_ssl_verification = disable_ssl_verification
        if disable_ssl_verification:
            logger.warning(
                "SSL verification DISABLED - This is insecure and should only be "
                "used for testing! DO NOT use in production."
            )
        self.cert_bundle = certifi.where()

    def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Make a POST request to Portfolio Optimizer API with retry logic.

        Args:
            endpoint: API endpoint path (e.g., "/portfolios/analyzer/volatility")
            payload: Request payload for the API

        Returns:
            API response as dict, or None if request fails after all retries.
        """
        url = f"{API_BASE_URL}{endpoint}"

        for attempt in range(MAX_RETRIES):
            try:
                # Apply backoff delay on retries
                if attempt > 0:
                    backoff = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    logger.info(f"Retry attempt {attempt + 1}, waiting {backoff}s")
                    time.sleep(backoff)

                logger.debug(f"POST request to {url}")

                # Make API request with SSL verification handling
                verify_param = False if self.disable_ssl_verification else self.cert_bundle
                response = requests.post(
                    url,
                    json=payload,
                    timeout=30,
                    verify=verify_param,
                    headers={"Content-Type": "application/json"}
                )

                # Check for rate limiting (HTTP 429)
                if response.status_code == 429:
                    logger.warning("Portfolio Optimizer API rate limit exceeded (429)")
                    if attempt < MAX_RETRIES - 1:
                        logger.info("Waiting 60 seconds before retry...")
                        time.sleep(60)
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limit")
                        return None

                # Check for server errors (5xx) - should retry
                if 500 <= response.status_code < 600:
                    logger.warning(
                        f"Portfolio Optimizer API returned server error {response.status_code}, "
                        f"attempt {attempt + 1}/{MAX_RETRIES}"
                    )
                    if attempt == MAX_RETRIES - 1:
                        logger.error("Max retries exceeded for server error")
                        return None
                    continue

                # Check for client errors (4xx except 429) - don't retry
                if 400 <= response.status_code < 500:
                    logger.error(
                        f"Portfolio Optimizer API returned client error {response.status_code}: "
                        f"{response.text}"
                    )
                    return None

                # Parse JSON response
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None

                logger.debug(f"Successfully received response from {endpoint}")
                return data

            except requests.exceptions.Timeout as e:
                logger.warning(
                    f"Portfolio Optimizer API request timed out, "
                    f"attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries exceeded for timeout")
                    return None

            except requests.exceptions.SSLError as e:
                logger.error(f"SSL Certificate verification failed: {e}")
                logger.warning("The API server's SSL certificate may be invalid")
                logger.info(
                    "To bypass SSL verification for testing, set DISABLE_SSL_VERIFICATION=true "
                    "in your .env file (NOT recommended for production)"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("SSL verification failed after all retries")
                    return None

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Portfolio Optimizer API request failed, "
                    f"attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries exceeded for request")
                    return None

            except Exception as e:
                logger.error(
                    f"Unexpected error calling Portfolio Optimizer API, "
                    f"attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries exceeded for unexpected error")
                    return None

        return None

    def analyze_volatility(
        self,
        assets: List[str],
        weights: List[float],
        covariance_matrix: List[List[float]],
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate portfolio volatility (standard deviation of returns).

        Volatility measures the riskiness of a portfolio - higher volatility
        means larger price swings and greater risk.

        Args:
            assets: List of stock symbols (e.g., ["AAPL", "MSFT"])
            weights: Portfolio weights (must sum to 1.0)
            covariance_matrix: NxN covariance matrix of asset returns

        Returns:
            Dict with portfolio volatility, or None on failure:
            {
                "portfolioVolatility": float  # Annualized volatility
            }
        """
        # Build assets list for API
        assets_list = [{"assetId": symbol} for symbol in assets]

        # Build weights list for API
        weights_list = [
            {"assetId": symbol, "weight": weight}
            for symbol, weight in zip(assets, weights)
        ]

        # Build covariance matrix for API (flatten to list of dicts)
        cov_matrix = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                cov_matrix.append({
                    "asset1": asset1,
                    "asset2": asset2,
                    "value": covariance_matrix[i][j]
                })

        payload = {
            "assets": assets_list,
            "portfolio": {"weights": weights_list},
            "marketData": {"covarianceMatrix": cov_matrix}
        }

        logger.info(f"Calculating portfolio volatility for {len(assets)} assets")
        result = self._make_request("/portfolios/analyzer/volatility", payload)

        if result and "portfolioVolatility" in result:
            logger.info(f"Portfolio volatility: {result['portfolioVolatility']:.4f}")
            return result

        logger.warning("Failed to calculate portfolio volatility")
        return None

    def analyze_sharpe_ratio(
        self,
        assets: List[str],
        weights: List[float],
        covariance_matrix: List[List[float]],
        expected_returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate portfolio Sharpe ratio (risk-adjusted return).

        Sharpe ratio measures excess return per unit of risk. Higher is better.
        Typically: <1 = poor, 1-2 = good, 2-3 = very good, >3 = excellent.

        Args:
            assets: List of stock symbols
            weights: Portfolio weights (must sum to 1.0)
            covariance_matrix: NxN covariance matrix of asset returns
            expected_returns: Expected annual returns for each asset
            risk_free_rate: Risk-free rate (default: 2% or 0.02)

        Returns:
            Dict with Sharpe ratio, or None on failure:
            {
                "sharpeRatio": float  # Risk-adjusted return metric
            }
        """
        # Build assets list for API
        assets_list = [{"assetId": symbol} for symbol in assets]

        # Build weights list for API
        weights_list = [
            {"assetId": symbol, "weight": weight}
            for symbol, weight in zip(assets, weights)
        ]

        # Build expected returns list for API
        returns_list = [
            {"assetId": symbol, "expectedReturn": ret}
            for symbol, ret in zip(assets, expected_returns)
        ]

        # Build covariance matrix for API
        cov_matrix = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                cov_matrix.append({
                    "asset1": asset1,
                    "asset2": asset2,
                    "value": covariance_matrix[i][j]
                })

        payload = {
            "assets": assets_list,
            "portfolio": {"weights": weights_list},
            "marketData": {
                "expectedReturns": returns_list,
                "covarianceMatrix": cov_matrix
            }
        }

        logger.info(f"Calculating Sharpe ratio for {len(assets)} assets")
        result = self._make_request("/portfolios/analyzer/sharpe-ratio", payload)

        if result and "sharpeRatio" in result:
            logger.info(f"Sharpe ratio: {result['sharpeRatio']:.4f}")
            return result

        logger.warning("Failed to calculate Sharpe ratio")
        return None

    def analyze_diversification_ratio(
        self,
        assets: List[str],
        weights: List[float],
        covariance_matrix: List[List[float]],
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate portfolio diversification ratio.

        Diversification ratio measures how much a portfolio benefits from
        diversification. Values > 1.0 indicate the portfolio is more
        diversified than a simple weighted average of individual assets.

        Args:
            assets: List of stock symbols
            weights: Portfolio weights (must sum to 1.0)
            covariance_matrix: NxN covariance matrix of asset returns

        Returns:
            Dict with diversification ratio, or None on failure:
            {
                "diversificationRatio": float  # Diversification benefit
            }
        """
        # Build assets list for API
        assets_list = [{"assetId": symbol} for symbol in assets]

        # Build weights list for API
        weights_list = [
            {"assetId": symbol, "weight": weight}
            for symbol, weight in zip(assets, weights)
        ]

        # Build covariance matrix for API
        cov_matrix = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                cov_matrix.append({
                    "asset1": asset1,
                    "asset2": asset2,
                    "value": covariance_matrix[i][j]
                })

        payload = {
            "assets": assets_list,
            "portfolio": {"weights": weights_list},
            "marketData": {"covarianceMatrix": cov_matrix}
        }

        logger.info(f"Calculating diversification ratio for {len(assets)} assets")
        result = self._make_request("/portfolios/analyzer/diversification-ratio", payload)

        if result and "diversificationRatio" in result:
            logger.info(f"Diversification ratio: {result['diversificationRatio']:.4f}")
            return result

        logger.warning("Failed to calculate diversification ratio")
        return None

    def maximize_sharpe_ratio(
        self,
        assets: List[str],
        covariance_matrix: List[List[float]],
        expected_returns: List[float],
        risk_free_rate: float = 0.02,
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate optimal portfolio weights for maximum Sharpe ratio.

        Finds the portfolio allocation that maximizes risk-adjusted returns.
        This is the tangency portfolio when combined with the risk-free asset.

        Args:
            assets: List of stock symbols
            covariance_matrix: NxN covariance matrix of asset returns
            expected_returns: Expected annual returns for each asset
            risk_free_rate: Risk-free rate (default: 2% or 0.02)

        Returns:
            Dict with optimal weights, or None on failure:
            {
                "optimalWeights": {"AAPL": 0.30, "MSFT": 0.25, ...},
                "sharpeRatio": float,
                "expectedReturn": float,
                "volatility": float
            }
        """
        # Build assets list for API
        assets_list = [{"assetId": symbol} for symbol in assets]

        # Build expected returns list for API
        returns_list = [
            {"assetId": symbol, "expectedReturn": ret}
            for symbol, ret in zip(assets, expected_returns)
        ]

        # Build covariance matrix for API
        cov_matrix = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                cov_matrix.append({
                    "asset1": asset1,
                    "asset2": asset2,
                    "value": covariance_matrix[i][j]
                })

        payload = {
            "assets": assets_list,
            "optimization": {
                "objective": "maximizeSharpeRatio",
                "riskFreeRate": risk_free_rate
            },
            "constraints": {
                "weights": {"type": "allLong"}
            },
            "marketData": {
                "expectedReturns": returns_list,
                "covarianceMatrix": cov_matrix
            }
        }

        logger.info(f"Calculating maximum Sharpe ratio portfolio for {len(assets)} assets")
        result = self._make_request("/portfolios/maximizer/sharpe-ratio", payload)

        if result and "optimalWeights" in result:
            # Extract weights into a simpler format
            weights = result.get("optimalWeights", {})
            if isinstance(weights, list):
                # Convert list format to dict format
                weights_dict = {w["assetId"]: w["weight"] for w in weights}
                result["optimalWeights"] = weights_dict

            logger.info(f"Maximum Sharpe ratio portfolio optimized")
            return result

        logger.warning("Failed to calculate maximum Sharpe ratio portfolio")
        return None

    def minimize_variance(
        self,
        assets: List[str],
        covariance_matrix: List[List[float]],
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate optimal portfolio weights for minimum variance.

        Finds the portfolio allocation with the lowest possible volatility.
        This is the most conservative portfolio on the efficient frontier.

        Args:
            assets: List of stock symbols
            covariance_matrix: NxN covariance matrix of asset returns

        Returns:
            Dict with optimal weights, or None on failure:
            {
                "optimalWeights": {"AAPL": 0.25, "MSFT": 0.30, ...},
                "volatility": float
            }
        """
        # Build assets list for API
        assets_list = [{"assetId": symbol} for symbol in assets]

        # Build covariance matrix for API
        cov_matrix = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                cov_matrix.append({
                    "asset1": asset1,
                    "asset2": asset2,
                    "value": covariance_matrix[i][j]
                })

        payload = {
            "assets": assets_list,
            "optimization": {
                "objective": "minimizeVariance"
            },
            "constraints": {
                "weights": {"type": "allLong"}
            },
            "marketData": {
                "covarianceMatrix": cov_matrix
            }
        }

        logger.info(f"Calculating minimum variance portfolio for {len(assets)} assets")
        result = self._make_request("/portfolios/minimizer/variance", payload)

        if result and "optimalWeights" in result:
            # Extract weights into a simpler format
            weights = result.get("optimalWeights", {})
            if isinstance(weights, list):
                # Convert list format to dict format
                weights_dict = {w["assetId"]: w["weight"] for w in weights}
                result["optimalWeights"] = weights_dict

            logger.info(f"Minimum variance portfolio optimized")
            return result

        logger.warning("Failed to calculate minimum variance portfolio")
        return None

    def equalize_risk_contributions(
        self,
        assets: List[str],
        covariance_matrix: List[List[float]],
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate optimal portfolio weights for equal risk contributions.

        Also known as risk parity. Each asset contributes the same amount
        of risk to the portfolio, regardless of its volatility or correlation.

        Args:
            assets: List of stock symbols
            covariance_matrix: NxN covariance matrix of asset returns

        Returns:
            Dict with optimal weights, or None on failure:
            {
                "optimalWeights": {"AAPL": 0.20, "MSFT": 0.25, ...},
                "volatility": float
            }
        """
        # Build assets list for API
        assets_list = [{"assetId": symbol} for symbol in assets]

        # Build covariance matrix for API
        cov_matrix = []
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                cov_matrix.append({
                    "asset1": asset1,
                    "asset2": asset2,
                    "value": covariance_matrix[i][j]
                })

        payload = {
            "assets": assets_list,
            "optimization": {
                "objective": "equalizeRiskContributions"
            },
            "constraints": {
                "weights": {"type": "allLong"}
            },
            "marketData": {
                "covarianceMatrix": cov_matrix
            }
        }

        logger.info(f"Calculating equal risk contributions portfolio for {len(assets)} assets")
        result = self._make_request("/portfolios/equalizer/risk-contributions", payload)

        if result and "optimalWeights" in result:
            # Extract weights into a simpler format
            weights = result.get("optimalWeights", {})
            if isinstance(weights, list):
                # Convert list format to dict format
                weights_dict = {w["assetId"]: w["weight"] for w in weights}
                result["optimalWeights"] = weights_dict

            logger.info(f"Equal risk contributions portfolio optimized")
            return result

        logger.warning("Failed to calculate equal risk contributions portfolio")
        return None
