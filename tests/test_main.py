"""Integration tests for main orchestrator module."""

import pytest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.main import main, run, fetch_stock_data
from src.stock_data_client import StockDataClient


# Sample fixture data for mocking
SAMPLE_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN"]

SAMPLE_STOCK_DATA = {
    "AAPL": {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "price": 229.00,
        "ebit": 120000000000,
        "enterprise_value": 3100000000000,
        "total_assets": 350000000000,
        "current_liabilities": 150000000000,
        "market_cap": 3000000000000,
        "sector": "Technology",
    },
    "MSFT": {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "price": 415.00,
        "ebit": 90000000000,
        "enterprise_value": 2900000000000,
        "total_assets": 400000000000,
        "current_liabilities": 100000000000,
        "market_cap": 2800000000000,
        "sector": "Technology",
    },
    "GOOGL": {
        "symbol": "GOOGL",
        "company_name": "Alphabet Inc.",
        "price": 175.00,
        "ebit": 75000000000,
        "enterprise_value": 1750000000000,
        "total_assets": 380000000000,
        "current_liabilities": 80000000000,
        "market_cap": 1800000000000,
        "sector": "Technology",
    },
    "META": {
        "symbol": "META",
        "company_name": "Meta Platforms Inc.",
        "price": 550.00,
        "ebit": 45000000000,
        "enterprise_value": 1150000000000,
        "total_assets": 200000000000,
        "current_liabilities": 50000000000,
        "market_cap": 1200000000000,
        "sector": "Technology",
    },
    "NVDA": {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "price": 480.00,
        "ebit": 35000000000,
        "enterprise_value": 1050000000000,
        "total_assets": 65000000000,
        "current_liabilities": 10000000000,
        "market_cap": 1100000000000,
        "sector": "Technology",
    },
    "AMZN": {
        "symbol": "AMZN",
        "company_name": "Amazon.com Inc.",
        "price": 185.00,
        "ebit": 25000000000,
        "enterprise_value": 1600000000000,
        "total_assets": 500000000000,
        "current_liabilities": 200000000000,
        "market_cap": 1500000000000,
        "sector": "Consumer Cyclical",
    },
}


def create_mock_stock_client():
    """Create a mock stock data client with sample data."""
    mock_client = MagicMock(spec=StockDataClient)

    mock_client.get_stock_universe.return_value = SAMPLE_SYMBOLS

    def mock_get_stock_data(symbol, min_market_cap=0, excluded_sectors=None):
        return SAMPLE_STOCK_DATA.get(symbol)

    mock_client.get_stock_data.side_effect = mock_get_stock_data

    return mock_client


class TestFetchStockData:
    """Tests for fetch_stock_data function."""

    def test_fetch_stock_data_returns_dataframe(self):
        """Should return a pandas DataFrame."""
        mock_client = create_mock_stock_client()

        result = fetch_stock_data(mock_client, SAMPLE_SYMBOLS)

        assert isinstance(result, pd.DataFrame)

    def test_fetch_stock_data_correct_columns(self):
        """Should have all required columns."""
        mock_client = create_mock_stock_client()

        result = fetch_stock_data(mock_client, SAMPLE_SYMBOLS)

        expected_columns = [
            "symbol", "company_name", "price", "ebit",
            "enterprise_value", "total_assets", "current_liabilities"
        ]
        for col in expected_columns:
            assert col in result.columns

    def test_fetch_stock_data_correct_row_count(self):
        """Should return data for all stocks with valid data."""
        mock_client = create_mock_stock_client()

        result = fetch_stock_data(mock_client, SAMPLE_SYMBOLS)

        assert len(result) == len(SAMPLE_SYMBOLS)

    def test_fetch_stock_data_skips_none_data(self):
        """Should skip stocks when get_stock_data returns None."""
        mock_client = create_mock_stock_client()
        # Make AAPL return None
        mock_client.get_stock_data.side_effect = lambda s, **kwargs: None if s == "AAPL" else SAMPLE_STOCK_DATA.get(s)

        result = fetch_stock_data(mock_client, SAMPLE_SYMBOLS)

        assert "AAPL" not in result["symbol"].values
        assert len(result) == len(SAMPLE_SYMBOLS) - 1


class TestMainIntegration:
    """Integration tests for main function."""

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_success_full_pipeline(self, mock_validate, mock_client_class, mock_discord_class):
        """Should complete full pipeline and return 0 on success."""
        # Setup mocks
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_magic_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        # Run
        result = main()

        # Verify
        assert result == 0
        mock_discord.send_magic_formula_alert.assert_called_once()

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_sends_top_5_stocks(self, mock_validate, mock_client_class, mock_discord_class):
        """Should send exactly 5 stocks to Discord."""
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_magic_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        # Get the stocks sent to Discord
        call_args = mock_discord.send_magic_formula_alert.call_args
        stocks_sent = call_args.kwargs.get("stocks") or call_args[0][0]

        assert len(stocks_sent) == 5

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_stocks_have_required_fields(self, mock_validate, mock_client_class, mock_discord_class):
        """Stocks sent to Discord should have all required fields."""
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_magic_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        call_args = mock_discord.send_magic_formula_alert.call_args
        stocks_sent = call_args.kwargs.get("stocks") or call_args[0][0]

        required_fields = ["symbol", "company_name", "price", "earnings_yield", "roc", "magic_score"]
        for stock in stocks_sent:
            for field in required_fields:
                assert field in stock

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_on_discord_failure(self, mock_validate, mock_client_class, mock_discord_class):
        """Should return 1 when Discord notification fails."""
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_magic_formula_alert.return_value = False
        mock_discord_class.return_value = mock_discord

        result = main()

        assert result == 1

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_on_empty_universe(self, mock_validate, mock_client_class, mock_discord_class):
        """Should return 1 when stock universe is empty."""
        mock_client = MagicMock(spec=StockDataClient)
        mock_client.get_stock_universe.return_value = []
        mock_client_class.return_value = mock_client

        result = main()

        assert result == 1

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_handles_fewer_than_5_stocks(self, mock_validate, mock_client_class, mock_discord_class):
        """Should handle case with fewer than 5 valid stocks."""
        # Only 3 stocks in universe
        limited_symbols = SAMPLE_SYMBOLS[:3]

        mock_client = create_mock_stock_client()
        mock_client.get_stock_universe.return_value = limited_symbols
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_magic_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        # Should still succeed
        assert result == 0

        # Should send only 3 stocks
        call_args = mock_discord.send_magic_formula_alert.call_args
        stocks_sent = call_args.kwargs.get("stocks") or call_args[0][0]
        assert len(stocks_sent) == 3

    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_on_config_error(self, mock_validate, mock_client_class):
        """Should return 1 when configuration validation fails."""
        from src.config import ConfigurationError
        mock_validate.side_effect = ConfigurationError("Missing webhook")

        result = main()

        assert result == 1

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_handles_all_stocks_missing_data(self, mock_validate, mock_client_class, mock_discord_class):
        """Should return 1 when all stocks have missing data."""
        mock_client = MagicMock(spec=StockDataClient)
        mock_client.get_stock_universe.return_value = SAMPLE_SYMBOLS
        # All get_stock_data returns None
        mock_client.get_stock_data.return_value = None
        mock_client_class.return_value = mock_client

        result = main()

        assert result == 1

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_catches_unhandled_exceptions(self, mock_validate, mock_client_class, mock_discord_class):
        """Should catch unhandled exceptions and return 1."""
        mock_client_class.side_effect = RuntimeError("Unexpected error")

        result = main()

        assert result == 1

    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_stocks_sorted_by_magic_score(self, mock_validate, mock_client_class, mock_discord_class):
        """Stocks should be sorted by magic score (lowest first)."""
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_magic_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        call_args = mock_discord.send_magic_formula_alert.call_args
        stocks_sent = call_args.kwargs.get("stocks") or call_args[0][0]

        # Verify stocks are sorted by magic_score ascending
        magic_scores = [s["magic_score"] for s in stocks_sent]
        assert magic_scores == sorted(magic_scores)
