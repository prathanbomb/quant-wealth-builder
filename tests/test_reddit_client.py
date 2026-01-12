"""Unit tests for Reddit client module."""

import pytest
from unittest.mock import MagicMock, patch
import requests

from src.reddit_client import RedditClient


class TestRedditClientInit:
    """Tests for RedditClient initialization."""

    def test_init(self):
        """RedditClient should initialize without errors."""
        client = RedditClient()
        assert client is not None
        assert client.disable_ssl_verification is False

    def test_init_with_ssl_disabled(self):
        """RedditClient should accept disable_ssl_verification parameter."""
        client = RedditClient(disable_ssl_verification=True)
        assert client is not None
        assert client.disable_ssl_verification is True

    def test_init_with_ssl_enabled(self):
        """RedditClient should work with SSL explicitly enabled."""
        client = RedditClient(disable_ssl_verification=False)
        assert client is not None
        assert client.disable_ssl_verification is False
        assert client.cert_bundle is not None


class TestFetchSentimentData:
    """Tests for fetch_sentiment_data method."""

    @patch("src.reddit_client.requests.get")
    def test_returns_reddit_data(self, mock_get):
        """fetch_sentiment_data should return Reddit sentiment data."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "ticker": "NVDA",
                "no_of_comments": 150,
                "sentiment": "Bullish",
                "sentiment_score": 0.15,
            },
            {
                "ticker": "AAPL",
                "no_of_comments": 75,
                "sentiment": "Bullish",
                "sentiment_score": 0.12,
            },
        ]
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is not None
        assert len(result) == 2
        assert result[0]["ticker"] == "NVDA"
        assert result[0]["no_of_comments"] == 150
        assert result[0]["sentiment"] == "Bullish"
        assert result[0]["sentiment_score"] == 0.15

    @patch("src.reddit_client.requests.get")
    def test_returns_data_with_date_parameter(self, mock_get):
        """fetch_sentiment_data should include date parameter when provided."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "ticker": "GME",
                "no_of_comments": 200,
                "sentiment": "Bearish",
                "sentiment_score": -0.10,
            }
        ]
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data(date="01-15-2025")

        # Verify the URL includes the date parameter
        assert mock_get.called
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.tradestie.com/v1/apps/reddit?date=01-15-2025"
        assert call_args[1]["timeout"] == 30
        assert result is not None
        assert len(result) == 1

    @patch("src.reddit_client.requests.get")
    def test_returns_none_on_json_parse_error(self, mock_get):
        """fetch_sentiment_data should return None on JSON parse error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None

    @patch("src.reddit_client.requests.get")
    def test_returns_none_on_empty_response(self, mock_get):
        """fetch_sentiment_data should return None on empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None

    @patch("src.reddit_client.requests.get")
    def test_returns_none_on_non_list_response(self, mock_get):
        """fetch_sentiment_data should return None on non-list response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid format"}
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_returns_none_on_http_4xx_error(self, mock_sleep, mock_get):
        """fetch_sentiment_data should return None on HTTP 4xx error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        # Should not retry on 4xx errors (other than 429)
        assert mock_sleep.call_count == 0

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_returns_none_on_http_5xx_error(self, mock_sleep, mock_get):
        """fetch_sentiment_data should retry on HTTP 5xx error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        # Should retry on 5xx errors
        assert mock_sleep.call_count == 2  # 3 attempts means 2 sleeps between them

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_handles_rate_limit_429(self, mock_sleep, mock_get):
        """fetch_sentiment_data should handle 429 rate limit with 60s wait."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        # Should wait 60 seconds on 429
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert 60 in sleep_calls

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_retries_on_timeout(self, mock_sleep, mock_get):
        """fetch_sentiment_data should retry on timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        # Should retry with exponential backoff
        assert mock_sleep.call_count == 2  # 3 attempts means 2 sleeps between them
        # Verify exponential backoff: 1s, 2s
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [1.0, 2.0]

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_retries_on_connection_error(self, mock_sleep, mock_get):
        """fetch_sentiment_data should retry on connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        assert mock_sleep.call_count == 2  # 3 attempts means 2 sleeps between them

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_succeeds_on_second_attempt(self, mock_sleep, mock_get):
        """fetch_sentiment_data should succeed on retry after initial failure."""
        # First call fails, second succeeds
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise requests.exceptions.Timeout("Timeout")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "ticker": "TSLA",
                    "no_of_comments": 300,
                    "sentiment": "Bullish",
                    "sentiment_score": 0.20,
                }
            ]
            return mock_response

        mock_get.side_effect = side_effect

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is not None
        assert len(result) == 1
        assert result[0]["ticker"] == "TSLA"
        assert mock_sleep.call_count == 1  # Only one retry

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_returns_none_after_max_retries(self, mock_sleep, mock_get):
        """fetch_sentiment_data should return None after max retries."""
        mock_get.side_effect = requests.exceptions.Timeout("Always timeout")

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        assert mock_get.call_count == 3  # MAX_RETRIES

    @patch("src.reddit_client.requests.get")
    def test_filters_items_with_missing_fields(self, mock_get):
        """fetch_sentiment_data should filter items with missing required fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "ticker": "NVDA",
                "no_of_comments": 150,
                "sentiment": "Bullish",
                "sentiment_score": 0.15,
            },
            {
                # Missing sentiment_score
                "ticker": "AAPL",
                "no_of_comments": 75,
                "sentiment": "Bullish",
            },
            {
                "ticker": "TSLA",
                "no_of_comments": 300,
                "sentiment": "Bullish",
                "sentiment_score": 0.20,
            },
        ]
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is not None
        # Should only return valid items (2 out of 3)
        assert len(result) == 2
        assert result[0]["ticker"] == "NVDA"
        assert result[1]["ticker"] == "TSLA"

    @patch("src.reddit_client.requests.get")
    def test_returns_none_when_all_items_invalid(self, mock_get):
        """fetch_sentiment_data should return None when all items are invalid."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"ticker": "INVALID1"},  # Missing all required fields
            {"no_of_comments": 100},  # Missing ticker, sentiment, score
        ]
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_handles_request_exception(self, mock_sleep, mock_get):
        """fetch_sentiment_data should handle generic RequestException."""
        mock_get.side_effect = requests.exceptions.RequestException("Generic error")

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        assert mock_sleep.call_count == 2  # 3 attempts means 2 sleeps between them

    @patch("src.reddit_client.requests.get")
    @patch("src.reddit_client.time.sleep")
    def test_handles_unexpected_exception(self, mock_sleep, mock_get):
        """fetch_sentiment_data should handle unexpected exceptions."""
        mock_get.side_effect = Exception("Unexpected error")

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is None
        assert mock_sleep.call_count == 2  # 3 attempts means 2 sleeps between them

    @patch("src.reddit_client.requests.get")
    def test_uses_certifi_bundle_by_default(self, mock_get):
        """fetch_sentiment_data should use certifi bundle for SSL verification by default."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "ticker": "NVDA",
                "no_of_comments": 150,
                "sentiment": "Bullish",
                "sentiment_score": 0.15,
            }
        ]
        mock_get.return_value = mock_response

        client = RedditClient()
        result = client.fetch_sentiment_data()

        assert result is not None
        # Verify requests.get was called with certifi bundle
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        assert "verify" in call_kwargs
        # Should use certifi bundle (not False, not True)
        assert call_kwargs["verify"] is not False
        assert isinstance(call_kwargs["verify"], str)

    @patch("src.reddit_client.requests.get")
    def test_disables_ssl_when_configured(self, mock_get):
        """fetch_sentiment_data should disable SSL verification when configured."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "ticker": "NVDA",
                "no_of_comments": 150,
                "sentiment": "Bullish",
                "sentiment_score": 0.15,
            }
        ]
        mock_get.return_value = mock_response

        client = RedditClient(disable_ssl_verification=True)
        result = client.fetch_sentiment_data()

        assert result is not None
        # Verify requests.get was called with verify=False
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("verify") is False
