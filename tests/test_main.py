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
        # Magic Formula
        "ebit": 120000000000,
        "enterprise_value": 3100000000000,
        "total_assets": 350000000000,
        "current_liabilities": 150000000000,
        # Piotroski F-Score
        "net_income": 100000000000,
        "net_income_prev": 95000000000,
        "operating_cash_flow": 110000000000,
        "roa": 0.30,
        "roa_prev": 0.28,
        "gross_margin": 0.40,
        "gross_margin_prev": 0.38,
        "asset_turnover": 0.60,
        "asset_turnover_prev": 0.58,
        "total_assets_prev": 330000000000,
        "long_term_debt": 80000000000,
        "long_term_debt_prev": 85000000000,
        "current_ratio": 2.5,
        "current_ratio_prev": 2.3,
        "shares_outstanding": 15000000000,
        "shares_outstanding_prev": 15500000000,
        # Graham Number
        "eps": 6.50,
        "book_value_per_share": 25.00,
        # Altman Z-Score
        "working_capital": 200000000000,
        "retained_earnings": 250000000000,
        "market_cap": 3000000000000,
        "total_liabilities": 200000000000,
        "revenue": 380000000000,
        # Other
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
        "net_income": 75000000000,
        "net_income_prev": 70000000000,
        "operating_cash_flow": 80000000000,
        "roa": 0.20,
        "roa_prev": 0.18,
        "gross_margin": 0.65,
        "gross_margin_prev": 0.63,
        "asset_turnover": 0.45,
        "asset_turnover_prev": 0.43,
        "total_assets_prev": 380000000000,
        "long_term_debt": 50000000000,
        "long_term_debt_prev": 55000000000,
        "current_ratio": 3.5,
        "current_ratio_prev": 3.3,
        "shares_outstanding": 7500000000,
        "shares_outstanding_prev": 7600000000,
        "eps": 10.00,
        "book_value_per_share": 30.00,
        "working_capital": 300000000000,
        "retained_earnings": 200000000000,
        "market_cap": 2800000000000,
        "total_liabilities": 150000000000,
        "revenue": 200000000000,
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
        "net_income": 60000000000,
        "net_income_prev": 58000000000,
        "operating_cash_flow": 65000000000,
        "roa": 0.16,
        "roa_prev": 0.15,
        "gross_margin": 0.55,
        "gross_margin_prev": 0.54,
        "asset_turnover": 0.50,
        "asset_turnover_prev": 0.48,
        "total_assets_prev": 360000000000,
        "long_term_debt": 20000000000,
        "long_term_debt_prev": 25000000000,
        "current_ratio": 2.8,
        "current_ratio_prev": 2.6,
        "shares_outstanding": 12000000000,
        "shares_outstanding_prev": 12500000000,
        "eps": 5.00,
        "book_value_per_share": 28.00,
        "working_capital": 300000000000,
        "retained_earnings": 180000000000,
        "market_cap": 1800000000000,
        "total_liabilities": 100000000000,
        "revenue": 280000000000,
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
        "net_income": 35000000000,
        "net_income_prev": 30000000000,
        "operating_cash_flow": 40000000000,
        "roa": 0.18,
        "roa_prev": 0.15,
        "gross_margin": 0.80,
        "gross_margin_prev": 0.78,
        "asset_turnover": 0.55,
        "asset_turnover_prev": 0.52,
        "total_assets_prev": 190000000000,
        "long_term_debt": 10000000000,
        "long_term_debt_prev": 12000000000,
        "current_ratio": 2.0,
        "current_ratio_prev": 1.8,
        "shares_outstanding": 2500000000,
        "shares_outstanding_prev": 2600000000,
        "eps": 14.00,
        "book_value_per_share": 55.00,
        "working_capital": 150000000000,
        "retained_earnings": 120000000000,
        "market_cap": 1200000000000,
        "total_liabilities": 80000000000,
        "revenue": 110000000000,
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
        "net_income": 25000000000,
        "net_income_prev": 20000000000,
        "operating_cash_flow": 28000000000,
        "roa": 0.40,
        "roa_prev": 0.35,
        "gross_margin": 0.70,
        "gross_margin_prev": 0.68,
        "asset_turnover": 0.80,
        "asset_turnover_prev": 0.75,
        "total_assets_prev": 55000000000,
        "long_term_debt": 5000000000,
        "long_term_debt_prev": 7000000000,
        "current_ratio": 4.0,
        "current_ratio_prev": 3.8,
        "shares_outstanding": 2500000000,
        "shares_outstanding_prev": 2600000000,
        "eps": 10.00,
        "book_value_per_share": 22.00,
        "working_capital": 55000000000,
        "retained_earnings": 45000000000,
        "market_cap": 1100000000000,
        "total_liabilities": 15000000000,
        "revenue": 50000000000,
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
        "net_income": 15000000000,
        "net_income_prev": 10000000000,
        "operating_cash_flow": 20000000000,
        "roa": 0.03,
        "roa_prev": 0.02,
        "gross_margin": 0.45,
        "gross_margin_prev": 0.43,
        "asset_turnover": 0.60,
        "asset_turnover_prev": 0.58,
        "total_assets_prev": 480000000000,
        "long_term_debt": 60000000000,
        "long_term_debt_prev": 65000000000,
        "current_ratio": 1.0,
        "current_ratio_prev": 0.9,
        "shares_outstanding": 10000000000,
        "shares_outstanding_prev": 10500000000,
        "eps": 1.50,
        "book_value_per_share": 18.00,
        "working_capital": 300000000000,
        "retained_earnings": 80000000000,
        "market_cap": 1500000000000,
        "total_liabilities": 300000000000,
        "revenue": 500000000000,
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

        # Check for basic required columns
        basic_columns = ["symbol", "company_name", "price"]
        for col in basic_columns:
            assert col in result.columns

        # Check for Magic Formula columns
        mf_columns = ["ebit", "enterprise_value", "total_assets", "current_liabilities"]
        for col in mf_columns:
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

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_success_full_pipeline(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should complete full pipeline and return 0 on success."""
        # Setup mocks
        mock_formulas.return_value = ["magic_formula"]
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        # Run
        result = main()

        # Verify
        assert result == 0
        mock_discord.send_multi_formula_alert.assert_called_once()

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_sends_top_5_stocks(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should send exactly 5 stocks to Discord."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        # Get the results sent to Discord
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        # Check Magic Formula results
        assert "magic_formula" in results_sent
        assert len(results_sent["magic_formula"]) == 5

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_stocks_have_required_fields(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Stocks sent to Discord should have all required fields."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        required_fields = ["symbol", "company_name", "price", "earnings_yield", "roc", "magic_score"]
        for stock in results_sent["magic_formula"]:
            for field in required_fields:
                assert field in stock

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_on_discord_failure(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should return 1 when Discord notification fails."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = False
        mock_discord_class.return_value = mock_discord

        result = main()

        assert result == 1

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_on_empty_universe(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should return 1 when stock universe is empty."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client = MagicMock(spec=StockDataClient)
        mock_client.get_stock_universe.return_value = []
        mock_client_class.return_value = mock_client

        result = main()

        assert result == 1

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_handles_fewer_than_5_stocks(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should handle case with fewer than 5 valid stocks."""
        mock_formulas.return_value = ["magic_formula"]
        # Only 3 stocks in universe
        limited_symbols = SAMPLE_SYMBOLS[:3]

        mock_client = create_mock_stock_client()
        mock_client.get_stock_universe.return_value = limited_symbols
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        # Should still succeed
        assert result == 0

        # Should send only 3 stocks
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]
        assert len(results_sent["magic_formula"]) == 3

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_on_config_error(self, mock_validate, mock_client_class, mock_formulas):
        """Should return 1 when configuration validation fails."""
        from src.config import ConfigurationError
        mock_formulas.return_value = ["magic_formula"]
        mock_validate.side_effect = ConfigurationError("Missing webhook")

        result = main()

        assert result == 1

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_handles_all_stocks_missing_data(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should return 1 when all stocks have missing data."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client = MagicMock(spec=StockDataClient)
        mock_client.get_stock_universe.return_value = SAMPLE_SYMBOLS
        # All get_stock_data returns None
        mock_client.get_stock_data.return_value = None
        mock_client_class.return_value = mock_client

        result = main()

        assert result == 1

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_catches_unhandled_exceptions(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should catch unhandled exceptions and return 1."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client_class.side_effect = RuntimeError("Unexpected error")

        result = main()

        assert result == 1

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_stocks_sorted_by_magic_score(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Stocks should be sorted by magic score (lowest first)."""
        mock_formulas.return_value = ["magic_formula"]
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        # Verify stocks are sorted by magic_score ascending
        magic_scores = [s["magic_score"] for s in results_sent["magic_formula"]]
        assert magic_scores == sorted(magic_scores)

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_returns_1_when_no_formulas_enabled(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should return 1 when no formulas are enabled."""
        mock_formulas.return_value = []

        result = main()

        assert result == 1

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_executes_multiple_formulas(self, mock_validate, mock_client_class, mock_discord_class, mock_formulas):
        """Should execute multiple enabled formulas."""
        mock_formulas.return_value = ["magic_formula", "acquirer"]
        mock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        assert result == 0

        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]
        enabled_sent = call_args.kwargs.get("enabled_formulas") or call_args[0][1]

        # Should have results for both formulas
        assert "magic_formula" in results_sent
        assert "acquirer" in results_sent
        assert set(enabled_sent) == {"magic_formula", "acquirer"}
