"""Unit tests for stock data client module."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from src.stock_data_client import (
    StockDataClient,
    STOCK_UNIVERSE,
    _safe_get_value,
    _safe_divide,
)


class TestStockUniverse:
    """Tests for stock universe constant."""

    def test_stock_universe_not_empty(self):
        """STOCK_UNIVERSE should contain stocks."""
        assert len(STOCK_UNIVERSE) > 0

    def test_stock_universe_contains_major_stocks(self):
        """STOCK_UNIVERSE should contain major US stocks."""
        assert "AAPL" in STOCK_UNIVERSE
        assert "MSFT" in STOCK_UNIVERSE
        assert "GOOGL" in STOCK_UNIVERSE


class TestStockDataClientInit:
    """Tests for StockDataClient initialization."""

    def test_init(self):
        """StockDataClient should initialize without errors."""
        client = StockDataClient()
        assert client is not None


class TestGetStockUniverse:
    """Tests for get_stock_universe method."""

    def test_returns_list(self):
        """get_stock_universe should return a list."""
        client = StockDataClient()
        result = client.get_stock_universe(
            exchanges=["NYSE", "NASDAQ"],
            min_market_cap=100_000_000,
            excluded_sectors=["Financial Services"],
        )
        assert isinstance(result, list)

    def test_returns_stock_universe(self):
        """get_stock_universe should return the predefined universe."""
        client = StockDataClient()
        result = client.get_stock_universe(
            exchanges=["NYSE", "NASDAQ"],
            min_market_cap=100_000_000,
            excluded_sectors=[],
        )
        assert result == STOCK_UNIVERSE


class TestGetStockData:
    """Tests for get_stock_data method."""

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_returns_stock_data(self, mock_sleep, mock_ticker_class):
        """get_stock_data should return stock data dict."""
        # Setup mock ticker
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        # Mock info
        mock_ticker.info = {
            "shortName": "Apple Inc.",
            "currentPrice": 150.0,
            "marketCap": 3000000000000,
            "enterpriseValue": 2900000000000,
            "sector": "Technology",
            "regularMarketPrice": 150.0,
        }

        # Mock income statement
        mock_income = pd.DataFrame(
            {"2024-09-30": [100000000000]},
            index=["Operating Income"],
        )
        mock_ticker.income_stmt = mock_income

        # Mock balance sheet
        mock_balance = pd.DataFrame(
            {
                "2024-09-30": [350000000000, 150000000000],
            },
            index=["Total Assets", "Current Liabilities"],
        )
        mock_ticker.balance_sheet = mock_balance

        client = StockDataClient()
        result = client.get_stock_data("AAPL")

        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["company_name"] == "Apple Inc."
        assert result["price"] == 150.0
        assert result["ebit"] == 100000000000
        assert result["enterprise_value"] == 2900000000000
        assert result["total_assets"] == 350000000000
        assert result["current_liabilities"] == 150000000000

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_returns_none_when_no_info(self, mock_sleep, mock_ticker_class):
        """get_stock_data should return None when ticker info is empty."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {}

        client = StockDataClient()
        result = client.get_stock_data("INVALID")

        assert result is None

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_filters_by_market_cap(self, mock_sleep, mock_ticker_class):
        """get_stock_data should filter by market cap."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        mock_ticker.info = {
            "shortName": "Small Corp",
            "currentPrice": 10.0,
            "marketCap": 50000000,  # Below 100M threshold
            "enterpriseValue": 45000000,
            "sector": "Technology",
            "regularMarketPrice": 10.0,
        }

        client = StockDataClient()
        result = client.get_stock_data("SMALL", min_market_cap=100_000_000)

        assert result is None

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_filters_by_sector(self, mock_sleep, mock_ticker_class):
        """get_stock_data should filter by excluded sectors."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        mock_ticker.info = {
            "shortName": "Big Bank",
            "currentPrice": 100.0,
            "marketCap": 500000000000,
            "enterpriseValue": 450000000000,
            "sector": "Financial Services",
            "regularMarketPrice": 100.0,
        }

        client = StockDataClient()
        result = client.get_stock_data(
            "BANK",
            excluded_sectors=["Financial Services"],
        )

        assert result is None

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_returns_none_when_no_operating_income(self, mock_sleep, mock_ticker_class):
        """get_stock_data should return None when operating income is missing."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        mock_ticker.info = {
            "shortName": "Test Corp",
            "currentPrice": 100.0,
            "marketCap": 500000000000,
            "enterpriseValue": 450000000000,
            "sector": "Technology",
            "regularMarketPrice": 100.0,
        }

        # Empty income statement
        mock_ticker.income_stmt = pd.DataFrame()

        client = StockDataClient()
        result = client.get_stock_data("TEST")

        assert result is None

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_returns_none_when_no_enterprise_value(self, mock_sleep, mock_ticker_class):
        """get_stock_data should return None when enterprise value is missing."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        mock_ticker.info = {
            "shortName": "Test Corp",
            "currentPrice": 100.0,
            "marketCap": 500000000000,
            "enterpriseValue": None,  # Missing
            "sector": "Technology",
            "regularMarketPrice": 100.0,
        }

        mock_income = pd.DataFrame(
            {"2024-09-30": [100000000000]},
            index=["Operating Income"],
        )
        mock_ticker.income_stmt = mock_income

        mock_balance = pd.DataFrame(
            {"2024-09-30": [350000000000, 150000000000]},
            index=["Total Assets", "Current Liabilities"],
        )
        mock_ticker.balance_sheet = mock_balance

        client = StockDataClient()
        result = client.get_stock_data("TEST")

        assert result is None

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_retries_on_exception(self, mock_sleep, mock_ticker_class):
        """get_stock_data should retry on exception."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        # First call raises exception, second succeeds
        call_count = [0]

        def side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Network error")
            return {
                "shortName": "Apple Inc.",
                "currentPrice": 150.0,
                "marketCap": 3000000000000,
                "enterpriseValue": 2900000000000,
                "sector": "Technology",
                "regularMarketPrice": 150.0,
            }

        type(mock_ticker).info = property(lambda self: side_effect())

        mock_income = pd.DataFrame(
            {"2024-09-30": [100000000000]},
            index=["Operating Income"],
        )
        mock_ticker.income_stmt = mock_income

        mock_balance = pd.DataFrame(
            {"2024-09-30": [350000000000, 150000000000]},
            index=["Total Assets", "Current Liabilities"],
        )
        mock_ticker.balance_sheet = mock_balance

        client = StockDataClient()
        result = client.get_stock_data("AAPL")

        assert result is not None
        assert result["symbol"] == "AAPL"

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_returns_none_after_max_retries(self, mock_sleep, mock_ticker_class):
        """get_stock_data should return None after max retries."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        # Always raise exception
        type(mock_ticker).info = property(
            lambda self: (_ for _ in ()).throw(Exception("Network error"))
        )

        client = StockDataClient()
        result = client.get_stock_data("AAPL")

        assert result is None

    @patch("src.stock_data_client.yf.Ticker")
    @patch("src.stock_data_client.time.sleep")
    def test_returns_extended_fields(self, mock_sleep, mock_ticker_class):
        """get_stock_data should return extended fields for advanced formulas."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        # Mock info with extended fields
        mock_ticker.info = {
            "shortName": "Apple Inc.",
            "currentPrice": 150.0,
            "marketCap": 3000000000000,
            "enterpriseValue": 2900000000000,
            "sector": "Technology",
            "regularMarketPrice": 150.0,
            "trailingEps": 6.05,
            "bookValue": 4.25,
            "sharesOutstanding": 15500000000,
        }

        # Mock income statement with current and previous year
        mock_income = pd.DataFrame(
            {
                "2024-09-30": [100000000000, 95000000000, 170000000000, 380000000000],
                "2023-09-30": [90000000000, 85000000000, 160000000000, 360000000000],
            },
            index=["Operating Income", "Net Income", "Gross Profit", "Total Revenue"],
        )
        mock_ticker.income_stmt = mock_income

        # Mock balance sheet with current and previous year
        mock_balance = pd.DataFrame(
            {
                "2024-09-30": [350000000000, 150000000000, 130000000000, 280000000000,
                              100000000000, 50000000000],
                "2023-09-30": [340000000000, 140000000000, 125000000000, 270000000000,
                              95000000000, 45000000000],
            },
            index=["Total Assets", "Current Liabilities", "Current Assets",
                   "Total Liabilities Net Minority Interest", "Long Term Debt",
                   "Retained Earnings"],
        )
        mock_ticker.balance_sheet = mock_balance

        # Mock cash flow statement
        mock_cashflow = pd.DataFrame(
            {"2024-09-30": [110000000000]},
            index=["Operating Cash Flow"],
        )
        mock_ticker.cashflow = mock_cashflow

        client = StockDataClient()
        result = client.get_stock_data("AAPL")

        # Check core fields
        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["ebit"] == 100000000000
        assert result["total_assets"] == 350000000000
        assert result["current_liabilities"] == 150000000000
        assert result["enterprise_value"] == 2900000000000

        # Check extended fields for Piotroski
        assert result["net_income"] == 95000000000
        assert result["operating_cash_flow"] == 110000000000
        assert result["total_assets_prev"] == 340000000000
        assert result["long_term_debt"] == 100000000000
        assert result["long_term_debt_prev"] == 95000000000
        assert result["current_assets"] == 130000000000
        assert result["current_liabilities_prev"] == 140000000000
        assert result["gross_profit"] == 170000000000
        assert result["gross_profit_prev"] == 160000000000
        assert result["revenue"] == 380000000000
        assert result["revenue_prev"] == 360000000000

        # Check derived ratios
        assert result["roa"] is not None
        assert result["roa_prev"] is not None
        assert result["current_ratio"] is not None
        assert result["current_ratio_prev"] is not None
        assert result["gross_margin"] is not None
        assert result["gross_margin_prev"] is not None
        assert result["asset_turnover"] is not None
        assert result["asset_turnover_prev"] is not None
        assert result["working_capital"] == 130000000000 - 150000000000  # -20B

        # Check Graham Number fields
        assert result["eps"] == 6.05
        assert result["book_value_per_share"] == 4.25

        # Check Altman Z-Score fields
        assert result["retained_earnings"] == 50000000000
        assert result["total_liabilities"] == 280000000000


class TestSafeGetValue:
    """Tests for _safe_get_value helper function."""

    def test_returns_value_from_dataframe(self):
        """_safe_get_value should return value when present."""
        df = pd.DataFrame(
            {"2024": [100, 200], "2023": [90, 180]},
            index=["Revenue", "Assets"],
        )
        assert _safe_get_value(df, "Revenue", 0) == 100
        assert _safe_get_value(df, "Revenue", 1) == 90
        assert _safe_get_value(df, "Assets", 0) == 200

    def test_returns_none_for_none_dataframe(self):
        """_safe_get_value should return None for None DataFrame."""
        assert _safe_get_value(None, "Revenue", 0) is None

    def test_returns_none_for_empty_dataframe(self):
        """_safe_get_value should return None for empty DataFrame."""
        df = pd.DataFrame()
        assert _safe_get_value(df, "Revenue", 0) is None

    def test_returns_none_for_missing_row(self):
        """_safe_get_value should return None for missing row."""
        df = pd.DataFrame({"2024": [100]}, index=["Revenue"])
        assert _safe_get_value(df, "NonExistent", 0) is None

    def test_returns_none_for_invalid_column_index(self):
        """_safe_get_value should return None for invalid column index."""
        df = pd.DataFrame({"2024": [100]}, index=["Revenue"])
        assert _safe_get_value(df, "Revenue", 5) is None

    def test_returns_none_for_nan_value(self):
        """_safe_get_value should return None for NaN values."""
        df = pd.DataFrame({"2024": [float("nan")]}, index=["Revenue"])
        assert _safe_get_value(df, "Revenue", 0) is None


class TestSafeDivide:
    """Tests for _safe_divide helper function."""

    def test_divides_valid_numbers(self):
        """_safe_divide should divide valid numbers."""
        assert _safe_divide(100, 50) == 2.0
        assert _safe_divide(10, 3) == pytest.approx(3.333, rel=0.01)

    def test_returns_none_for_none_numerator(self):
        """_safe_divide should return None for None numerator."""
        assert _safe_divide(None, 50) is None

    def test_returns_none_for_none_denominator(self):
        """_safe_divide should return None for None denominator."""
        assert _safe_divide(100, None) is None

    def test_returns_none_for_zero_denominator(self):
        """_safe_divide should return None for zero denominator."""
        assert _safe_divide(100, 0) is None

    def test_handles_negative_numbers(self):
        """_safe_divide should handle negative numbers."""
        assert _safe_divide(-100, 50) == -2.0
        assert _safe_divide(100, -50) == -2.0
