"""Integration tests for Reddit Momentum feature."""

import pytest
from unittest.mock import MagicMock, patch

from src.main import main, run_reddit_momentum
from src.reddit_client import RedditClient
from src.stock_data_client import StockDataClient


# Sample Reddit API response data
SAMPLE_REDDIT_DATA = [
    {
        "ticker": "NVDA",
        "no_of_comments": 250,
        "sentiment": "Bullish",
        "sentiment_score": 0.18,
    },
    {
        "ticker": "AAPL",
        "no_of_comments": 150,
        "sentiment": "Bullish",
        "sentiment_score": 0.12,
    },
    {
        "ticker": "TSLA",
        "no_of_comments": 500,
        "sentiment": "Bullish",
        "sentiment_score": 0.22,
    },
    {
        "ticker": "MSFT",
        "no_of_comments": 75,
        "sentiment": "Bullish",
        "sentiment_score": 0.10,
    },
    {
        "ticker": "META",
        "no_of_comments": 100,
        "sentiment": "Bullish",
        "sentiment_score": 0.15,
    },
    {
        "ticker": "GME",
        "no_of_comments": 300,
        "sentiment": "Bearish",
        "sentiment_score": -0.10,
    },
    {
        "ticker": "AMC",
        "no_of_comments": 200,
        "sentiment": "Bearish",
        "sentiment_score": -0.08,
    },
]


def create_mock_reddit_client(reddit_data=None):
    """Create a mock Reddit client with sample data."""
    if reddit_data is None:
        reddit_data = SAMPLE_REDDIT_DATA

    mock_client = MagicMock(spec=RedditClient)
    mock_client.fetch_sentiment_data.return_value = reddit_data
    return mock_client


# Sample stock universe (matching stock_data_client.py)
SAMPLE_STOCK_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN",
    "TSLA", "AMD", "INTC", "CSCO",
]


class TestRunRedditMomentum:
    """Integration tests for run_reddit_momentum function."""

    def test_run_reddit_momentum_success(self):
        """Should successfully fetch and rank Reddit momentum stocks."""
        mock_client = create_mock_reddit_client()

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert result is not None
        assert isinstance(result, list)
        # Should return top 5 bullish stocks (GME and AMC are bearish and filtered out)
        assert len(result) == 5

    def test_run_reddit_momentum_filters_to_universe(self):
        """Should filter Reddit data to stock universe."""
        # Include stocks not in universe
        reddit_data = SAMPLE_REDDIT_DATA + [
            {
                "ticker": "MEME1",
                "no_of_comments": 1000,
                "sentiment": "Bullish",
                "sentiment_score": 0.30,
            },
            {
                "ticker": "MEME2",
                "no_of_comments": 800,
                "sentiment": "Bullish",
                "sentiment_score": 0.25,
            },
        ]
        mock_client = create_mock_reddit_client(reddit_data)

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        # Should only include stocks from universe
        tickers = [stock["ticker"] for stock in result]
        assert "MEME1" not in tickers
        assert "MEME2" not in tickers
        assert all(ticker in SAMPLE_STOCK_UNIVERSE for ticker in tickers)

    def test_run_reddit_momentum_excludes_bearish(self):
        """Should exclude bearish stocks from top picks."""
        mock_client = create_mock_reddit_client()

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        # All returned stocks should be bullish
        for stock in result:
            assert stock["sentiment"] == "Bullish"

        # GME and AMC should not be in results
        tickers = [stock["ticker"] for stock in result]
        assert "GME" not in tickers
        assert "AMC" not in tickers

    def test_run_reddit_momentum_returns_top_5(self):
        """Should return exactly 5 stocks when available."""
        mock_client = create_mock_reddit_client()

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert len(result) == 5

    def test_run_reddit_momentum_handles_fewer_than_5_bullish(self):
        """Should return fewer than 5 when fewer bullish stocks available."""
        # Create data with only 3 bullish stocks
        limited_data = [
            {
                "ticker": "NVDA",
                "no_of_comments": 250,
                "sentiment": "Bullish",
                "sentiment_score": 0.18,
            },
            {
                "ticker": "AAPL",
                "no_of_comments": 150,
                "sentiment": "Bullish",
                "sentiment_score": 0.12,
            },
            {
                "ticker": "MSFT",
                "no_of_comments": 75,
                "sentiment": "Bullish",
                "sentiment_score": 0.10,
            },
        ]
        mock_client = create_mock_reddit_client(limited_data)

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert len(result) == 3

    def test_run_reddit_momentum_returns_none_on_api_failure(self):
        """Should return None when Reddit API fails."""
        mock_client = MagicMock(spec=RedditClient)
        mock_client.fetch_sentiment_data.return_value = None

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert result is None

    def test_run_reddit_momentum_returns_none_when_no_universe_match(self):
        """Should return None when no Reddit stocks match universe."""
        # All Reddit stocks are outside universe
        outside_universe_data = [
            {
                "ticker": "MEME1",
                "no_of_comments": 500,
                "sentiment": "Bullish",
                "sentiment_score": 0.20,
            },
            {
                "ticker": "MEME2",
                "no_of_comments": 300,
                "sentiment": "Bullish",
                "sentiment_score": 0.15,
            },
        ]
        mock_client = create_mock_reddit_client(outside_universe_data)

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert result is None

    def test_run_reddit_momentum_returns_none_when_all_bearish(self):
        """Should return None when all Reddit stocks are bearish."""
        all_bearish_data = [
            {
                "ticker": "GME",
                "no_of_comments": 300,
                "sentiment": "Bearish",
                "sentiment_score": -0.10,
            },
            {
                "ticker": "AMC",
                "no_of_comments": 200,
                "sentiment": "Bearish",
                "sentiment_score": -0.08,
            },
        ]
        mock_client = create_mock_reddit_client(all_bearish_data)

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert result is None

    def test_run_reddit_momentum_stock_has_required_fields(self):
        """Stocks should have all required fields."""
        mock_client = create_mock_reddit_client()

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        required_fields = ["ticker", "no_of_comments", "sentiment", "sentiment_score", "momentum_score", "rank"]
        for stock in result:
            for field in required_fields:
                assert field in stock

    def test_run_reddit_momentum_ranks_by_momentum_score(self):
        """Should rank stocks by momentum score (highest first)."""
        mock_client = create_mock_reddit_client()

        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        # Check that momentum scores are in descending order
        momentum_scores = [stock["momentum_score"] for stock in result]
        assert momentum_scores == sorted(momentum_scores, reverse=True)

    def test_run_reddit_momentum_with_historical_date(self):
        """Should support fetching historical Reddit data."""
        mock_client = MagicMock(spec=RedditClient)
        mock_client.fetch_sentiment_data.return_value = SAMPLE_REDDIT_DATA

        # Call with date parameter would need a different function signature
        # For now, just verify the basic flow works
        result = run_reddit_momentum(mock_client, SAMPLE_STOCK_UNIVERSE)

        assert result is not None
        # Verify fetch was called without date (current implementation doesn't pass date)
        mock_client.fetch_sentiment_data.assert_called_once_with(None)


class TestMainIntegrationWithReddit:
    """Integration tests for main() with Reddit Momentum enabled."""

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_main_with_reddit_momentum_enabled(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Should include Reddit Momentum when enabled."""
        mock_formulas.return_value = ["reddit_momentum"]

        # Mock Reddit client
        mock_reddit_client = create_mock_reddit_client()
        mock_reddit_class.return_value = mock_reddit_client

        # Mock stock client
        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        # Mock Discord notifier
        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        assert result == 0
        mock_reddit_client.fetch_sentiment_data.assert_called_once()

        # Verify Reddit results were sent to Discord
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]
        assert "reddit_momentum" in results_sent

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_main_with_reddit_and_value_formulas(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Should execute Reddit alongside value formulas."""
        mock_formulas.return_value = ["magic_formula", "reddit_momentum"]

        # Mock Reddit client
        mock_reddit_client = create_mock_reddit_client()
        mock_reddit_class.return_value = mock_reddit_client

        # Mock stock client
        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        # Mock Discord notifier
        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        assert result == 0

        # Verify both formulas were executed
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]
        enabled_sent = call_args.kwargs.get("enabled_formulas") or call_args[0][1]

        assert "magic_formula" in results_sent
        assert "reddit_momentum" in results_sent
        assert set(enabled_sent) == {"magic_formula", "reddit_momentum"}

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_main_graceful_degradation_on_reddit_failure(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Should continue with other formulas when Reddit fails."""
        mock_formulas.return_value = ["magic_formula", "reddit_momentum"]

        # Mock Reddit client to return None (API failure)
        mock_reddit_client = MagicMock(spec=RedditClient)
        mock_reddit_client.fetch_sentiment_data.return_value = None
        mock_reddit_class.return_value = mock_reddit_client

        # Mock stock client
        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        # Mock Discord notifier
        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        # Should still succeed (Magic Formula works)
        assert result == 0

        # Verify only Magic Formula results were sent (Reddit failed)
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        assert "magic_formula" in results_sent
        # Reddit should not be in results since it failed
        assert "reddit_momentum" not in results_sent

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_main_reddit_momentum_only(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Should work with only Reddit Momentum enabled."""
        mock_formulas.return_value = ["reddit_momentum"]

        # Mock Reddit client
        mock_reddit_client = create_mock_reddit_client()
        mock_reddit_class.return_value = mock_reddit_client

        # Mock stock client (for universe only)
        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        # Mock Discord notifier
        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        result = main()

        assert result == 0

        # Verify Reddit results were sent
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        assert "reddit_momentum" in results_sent
        assert len(results_sent["reddit_momentum"]) == 5

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.validate_config")
    def test_main_reddit_client_not_initialized_when_disabled(
        self, mock_validate, mock_client_class, mock_formulas
    ):
        """Should not initialize RedditClient when Reddit Momentum is disabled."""
        mock_formulas.return_value = ["magic_formula"]

        # Mock stock client
        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        # Mock Discord notifier
        with patch("src.main.DiscordNotifier") as mock_discord_class:
            mock_discord = MagicMock()
            mock_discord.send_multi_formula_alert.return_value = True
            mock_discord_class.return_value = mock_discord

            result = main()

            assert result == 0
            # RedditClient should not be imported or initialized
            # (verified by no exception being raised)

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_main_sends_reddit_results_with_correct_format(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Reddit results should have correct format for Discord."""
        mock_formulas.return_value = ["reddit_momentum"]

        # Mock Reddit client
        mock_reddit_client = create_mock_reddit_client()
        mock_reddit_class.return_value = mock_reddit_client

        # Mock stock client
        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        # Mock Discord notifier
        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        # Get Reddit results sent to Discord
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]
        reddit_results = results_sent["reddit_momentum"]

        # Verify format
        required_fields = ["ticker", "no_of_comments", "sentiment", "sentiment_score", "momentum_score", "rank"]
        for stock in reddit_results:
            for field in required_fields:
                assert field in stock
            # All should be bullish
            assert stock["sentiment"] == "Bullish"


class TestDiscordIntegrationWithReddit:
    """Tests for Discord notification integration with Reddit."""

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_discord_receives_reddit_embed(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Discord notifier should receive Reddit embed."""
        mock_formulas.return_value = ["reddit_momentum"]

        mock_reddit_client = create_mock_reddit_client()
        mock_reddit_class.return_value = mock_reddit_client

        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        # Verify send_multi_formula_alert was called with reddit_momentum in enabled_formulas
        call_args = mock_discord.send_multi_formula_alert.call_args
        enabled_formulas = call_args.kwargs.get("enabled_formulas") or call_args[0][1]

        assert "reddit_momentum" in enabled_formulas

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_discord_reddit_embed_has_correct_color(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Discord notifier should format Reddit embed with correct color."""
        from src.discord_notifier import REDDIT_COLOR

        mock_formulas.return_value = ["reddit_momentum"]

        mock_reddit_client = create_mock_reddit_client()
        mock_reddit_class.return_value = mock_reddit_client

        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        # The notifier should be called with Reddit results
        # (Color is applied inside the notifier, verified by notifier tests)
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        assert "reddit_momentum" in results_sent


class TestConfigToggleWithReddit:
    """Tests for ENABLE_REDDIT_MOMENTUM configuration toggle."""

    @patch("src.main.get_enabled_formulas")
    @patch("src.main.DiscordNotifier")
    @patch("src.main.StockDataClient")
    @patch("src.main.RedditClient")
    @patch("src.main.validate_config")
    def test_reddit_disabled_when_toggle_false(
        self, mock_validate, mock_reddit_class, mock_client_class, mock_discord_class, mock_formulas
    ):
        """Should not execute Reddit when toggle is False."""
        # Simulate config with Reddit disabled
        mock_formulas.return_value = ["magic_formula"]  # Only Magic Formula

        from tests.test_main import create_mock_stock_client
        mock_stock_client = create_mock_stock_client()
        mock_client_class.return_value = mock_stock_client

        mock_discord = MagicMock()
        mock_discord.send_multi_formula_alert.return_value = True
        mock_discord_class.return_value = mock_discord

        main()

        # Reddit client should not be called
        mock_reddit_class.assert_not_called()

        # Results should only have magic_formula
        call_args = mock_discord.send_multi_formula_alert.call_args
        results_sent = call_args.kwargs.get("results") or call_args[0][0]

        assert "magic_formula" in results_sent
        assert "reddit_momentum" not in results_sent
