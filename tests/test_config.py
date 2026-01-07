"""Unit tests for configuration module."""

import pytest
from unittest.mock import patch

from src import config
from src.config import ConfigurationError, validate_config, get_config


class TestConstants:
    """Tests for configuration constants."""

    def test_min_market_cap_default(self):
        """MIN_MARKET_CAP should be $100 Million."""
        assert config.MIN_MARKET_CAP == 100_000_000

    def test_excluded_sectors_default(self):
        """EXCLUDED_SECTORS should contain Financial Services and Utilities."""
        assert "Financial Services" in config.EXCLUDED_SECTORS
        assert "Utilities" in config.EXCLUDED_SECTORS
        assert len(config.EXCLUDED_SECTORS) == 2

    def test_target_exchanges_default(self):
        """TARGET_EXCHANGES should contain NYSE and NASDAQ."""
        assert "NYSE" in config.TARGET_EXCHANGES
        assert "NASDAQ" in config.TARGET_EXCHANGES
        assert len(config.TARGET_EXCHANGES) == 2

    def test_api_delay_seconds_default(self):
        """API_DELAY_SECONDS should be 0.5 seconds."""
        assert config.API_DELAY_SECONDS == 0.5

    def test_top_n_stocks_default(self):
        """TOP_N_STOCKS should be 5."""
        assert config.TOP_N_STOCKS == 5


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_config_success(self):
        """validate_config should not raise when all env vars are set."""
        with patch.object(config, "DISCORD_WEBHOOK_URL", "https://discord.com/webhook"):
            validate_config()

    def test_validate_config_missing_discord_webhook(self):
        """validate_config should raise ConfigurationError when DISCORD_WEBHOOK_URL is missing."""
        with patch.object(config, "DISCORD_WEBHOOK_URL", ""):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_config()
            assert "DISCORD_WEBHOOK_URL" in str(exc_info.value)


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_returns_dict(self):
        """get_config should return a dictionary."""
        result = get_config()
        assert isinstance(result, dict)

    def test_get_config_contains_all_keys(self):
        """get_config should contain all expected configuration keys."""
        result = get_config()
        expected_keys = [
            "discord_webhook_url",
            "min_market_cap",
            "excluded_sectors",
            "target_exchanges",
            "api_delay_seconds",
            "top_n_stocks",
        ]
        for key in expected_keys:
            assert key in result

    def test_get_config_values_match_module_vars(self):
        """get_config values should match module-level variables."""
        with patch.object(config, "DISCORD_WEBHOOK_URL", "test_url"):
            result = get_config()
            assert result["discord_webhook_url"] == "test_url"
            assert result["min_market_cap"] == config.MIN_MARKET_CAP
            assert result["excluded_sectors"] == config.EXCLUDED_SECTORS
            assert result["target_exchanges"] == config.TARGET_EXCHANGES
            assert result["api_delay_seconds"] == config.API_DELAY_SECONDS
            assert result["top_n_stocks"] == config.TOP_N_STOCKS
