"""Unit tests for Discord notifier module."""

import pytest
from unittest.mock import MagicMock, patch

import requests

from src.discord_notifier import DiscordNotifier, EMBED_COLOR


@pytest.fixture
def notifier():
    """Create a Discord notifier instance."""
    return DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test/token")


@pytest.fixture
def sample_stocks():
    """Create sample stock data for testing."""
    return [
        {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "price": 229.50,
            "magic_score": 15,
            "earnings_yield": 0.085,
            "roc": 0.452,
        },
        {
            "symbol": "MSFT",
            "company_name": "Microsoft Corporation",
            "price": 415.25,
            "magic_score": 18,
            "earnings_yield": 0.072,
            "roc": 0.385,
        },
        {
            "symbol": "GOOGL",
            "company_name": "Alphabet Inc.",
            "price": 175.80,
            "magic_score": 22,
            "earnings_yield": 0.065,
            "roc": 0.310,
        },
    ]


class TestDiscordNotifierInit:
    """Tests for DiscordNotifier initialization."""

    def test_init_sets_webhook_url(self):
        """Should store the webhook URL."""
        url = "https://discord.com/api/webhooks/123/abc"
        notifier = DiscordNotifier(webhook_url=url)
        assert notifier.webhook_url == url


class TestFormatStockField:
    """Tests for _format_stock_field method."""

    def test_format_stock_field_structure(self, notifier):
        """Should return dict with name, value, inline keys."""
        stock = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "price": 229.50,
            "magic_score": 15,
            "earnings_yield": 0.085,
            "roc": 0.452,
        }

        result = notifier._format_stock_field(stock, rank=1)

        assert "name" in result
        assert "value" in result
        assert "inline" in result
        assert result["inline"] is False

    def test_format_stock_field_name_includes_rank_and_symbol(self, notifier):
        """Should include rank and symbol in field name."""
        stock = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "price": 229.50,
            "magic_score": 15,
            "earnings_yield": 0.085,
            "roc": 0.452,
        }

        result = notifier._format_stock_field(stock, rank=1)

        assert "1." in result["name"]
        assert "AAPL" in result["name"]
        assert "Apple Inc." in result["name"]

    def test_format_stock_field_gold_medal_for_rank_1(self, notifier):
        """Should use gold medal emoji for rank 1."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 100,
                 "magic_score": 10, "earnings_yield": 0.1, "roc": 0.2}

        result = notifier._format_stock_field(stock, rank=1)

        assert "🥇" in result["name"]

    def test_format_stock_field_silver_medal_for_rank_2(self, notifier):
        """Should use silver medal emoji for rank 2."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 100,
                 "magic_score": 10, "earnings_yield": 0.1, "roc": 0.2}

        result = notifier._format_stock_field(stock, rank=2)

        assert "🥈" in result["name"]

    def test_format_stock_field_bronze_medal_for_rank_3(self, notifier):
        """Should use bronze medal emoji for rank 3."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 100,
                 "magic_score": 10, "earnings_yield": 0.1, "roc": 0.2}

        result = notifier._format_stock_field(stock, rank=3)

        assert "🥉" in result["name"]

    def test_format_stock_field_generic_medal_for_rank_4_plus(self, notifier):
        """Should use generic medal emoji for rank 4+."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 100,
                 "magic_score": 10, "earnings_yield": 0.1, "roc": 0.2}

        result = notifier._format_stock_field(stock, rank=4)

        assert "🏅" in result["name"]

    def test_format_stock_field_price_formatting(self, notifier):
        """Should format price with 2 decimals and comma separators."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 1234.567,
                 "magic_score": 10, "earnings_yield": 0.1, "roc": 0.2}

        result = notifier._format_stock_field(stock, rank=1)

        assert "$1,234.57" in result["value"]

    def test_format_stock_field_percentage_formatting(self, notifier):
        """Should format earnings yield and ROC as percentages."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 100,
                 "magic_score": 10, "earnings_yield": 0.085, "roc": 0.452}

        result = notifier._format_stock_field(stock, rank=1)

        assert "8.5%" in result["value"]
        assert "45.2%" in result["value"]

    def test_format_stock_field_includes_magic_score(self, notifier):
        """Should include magic score in value."""
        stock = {"symbol": "TEST", "company_name": "Test", "price": 100,
                 "magic_score": 15, "earnings_yield": 0.1, "roc": 0.2}

        result = notifier._format_stock_field(stock, rank=1)

        assert "Score: 15" in result["value"]

    def test_format_stock_field_handles_missing_data(self, notifier):
        """Should handle missing data gracefully."""
        stock = {"symbol": "TEST"}  # Minimal data

        result = notifier._format_stock_field(stock, rank=1)

        assert "TEST" in result["name"]
        assert "$0.00" in result["value"]


class TestSendMagicFormulaAlert:
    """Tests for send_magic_formula_alert method."""

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_success_200(self, mock_post, notifier, sample_stocks):
        """Should return True on 200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        assert result is True

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_success_204(self, mock_post, notifier, sample_stocks):
        """Should return True on 204 response (Discord sometimes returns this)."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        result = notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        assert result is True

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_failure_4xx(self, mock_post, notifier, sample_stocks):
        """Should return False on 4xx response."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        result = notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        assert result is False

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_failure_5xx(self, mock_post, notifier, sample_stocks):
        """Should return False on 5xx response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        assert result is False

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_handles_request_exception(self, mock_post, notifier, sample_stocks):
        """Should return False on request exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        result = notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        assert result is False

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_payload_structure(self, mock_post, notifier, sample_stocks):
        """Should send correct payload structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        # Get the JSON payload sent
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs.get("json")

        assert "embeds" in payload
        assert len(payload["embeds"]) == 1

        embed = payload["embeds"][0]
        assert "title" in embed
        assert "description" in embed
        assert "fields" in embed
        assert "footer" in embed
        assert embed["color"] == EMBED_COLOR

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_includes_month_year(self, mock_post, notifier, sample_stocks):
        """Should include month/year in description."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier.send_magic_formula_alert(sample_stocks, "February 2025")

        payload = mock_post.call_args.kwargs.get("json")
        description = payload["embeds"][0]["description"]

        assert "February 2025" in description

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_includes_disclaimer(self, mock_post, notifier, sample_stocks):
        """Should include disclaimer in footer."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        payload = mock_post.call_args.kwargs.get("json")
        footer = payload["embeds"][0]["footer"]["text"]

        assert "Disclaimer" in footer
        assert "DYOR" in footer

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_correct_number_of_fields(self, mock_post, notifier, sample_stocks):
        """Should have one field per stock."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        payload = mock_post.call_args.kwargs.get("json")
        fields = payload["embeds"][0]["fields"]

        assert len(fields) == len(sample_stocks)

    @patch("src.discord_notifier.requests.post")
    def test_send_alert_uses_webhook_url(self, mock_post, notifier, sample_stocks):
        """Should POST to the configured webhook URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier.send_magic_formula_alert(sample_stocks, "January 2025")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.args[0] == notifier.webhook_url
