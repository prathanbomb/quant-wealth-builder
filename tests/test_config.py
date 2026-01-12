"""Unit tests for configuration module."""

import pytest
from unittest.mock import patch

from src import config
from src.config import (
    ConfigurationError,
    validate_config,
    get_config,
    get_enabled_formulas,
    _parse_bool_env,
)


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
            assert result["top_n_stocks"] == config.TOP_N_STOCKS

    def test_get_config_contains_formula_toggles(self):
        """get_config should contain all formula toggle keys."""
        result = get_config()
        formula_keys = [
            "enable_magic_formula",
            "enable_piotroski",
            "enable_graham",
            "enable_acquirer",
            "enable_altman",
        ]
        for key in formula_keys:
            assert key in result


class TestParseBoolEnv:
    """Tests for _parse_bool_env helper function."""

    def test_parse_bool_env_true_values(self):
        """_parse_bool_env should return True for 'true', '1', 'yes'."""
        with patch.dict("os.environ", {"TEST_VAR": "true"}):
            assert _parse_bool_env("TEST_VAR") is True
        with patch.dict("os.environ", {"TEST_VAR": "TRUE"}):
            assert _parse_bool_env("TEST_VAR") is True
        with patch.dict("os.environ", {"TEST_VAR": "1"}):
            assert _parse_bool_env("TEST_VAR") is True
        with patch.dict("os.environ", {"TEST_VAR": "yes"}):
            assert _parse_bool_env("TEST_VAR") is True
        with patch.dict("os.environ", {"TEST_VAR": "YES"}):
            assert _parse_bool_env("TEST_VAR") is True

    def test_parse_bool_env_false_values(self):
        """_parse_bool_env should return False for 'false', '0', 'no'."""
        with patch.dict("os.environ", {"TEST_VAR": "false"}):
            assert _parse_bool_env("TEST_VAR") is False
        with patch.dict("os.environ", {"TEST_VAR": "FALSE"}):
            assert _parse_bool_env("TEST_VAR") is False
        with patch.dict("os.environ", {"TEST_VAR": "0"}):
            assert _parse_bool_env("TEST_VAR") is False
        with patch.dict("os.environ", {"TEST_VAR": "no"}):
            assert _parse_bool_env("TEST_VAR") is False

    def test_parse_bool_env_default_when_not_set(self):
        """_parse_bool_env should return default when env var not set."""
        with patch.dict("os.environ", {}, clear=True):
            assert _parse_bool_env("NONEXISTENT_VAR", default=True) is True
            assert _parse_bool_env("NONEXISTENT_VAR", default=False) is False

    def test_parse_bool_env_default_when_empty(self):
        """_parse_bool_env should return default when env var is empty."""
        with patch.dict("os.environ", {"TEST_VAR": ""}):
            assert _parse_bool_env("TEST_VAR", default=True) is True
            assert _parse_bool_env("TEST_VAR", default=False) is False

    def test_parse_bool_env_strips_whitespace(self):
        """_parse_bool_env should strip whitespace from values."""
        with patch.dict("os.environ", {"TEST_VAR": "  true  "}):
            assert _parse_bool_env("TEST_VAR") is True


class TestFormulaToggles:
    """Tests for formula toggle configuration."""

    def test_formula_toggles_default_to_true(self):
        """All formula toggles should default to True."""
        assert config.ENABLE_MAGIC_FORMULA is True
        assert config.ENABLE_PIOTROSKI is True
        assert config.ENABLE_GRAHAM is True
        assert config.ENABLE_ACQUIRER is True
        assert config.ENABLE_ALTMAN is True


class TestGetEnabledFormulas:
    """Tests for get_enabled_formulas function."""

    def test_get_enabled_formulas_all_enabled(self):
        """get_enabled_formulas returns all formulas when all are enabled."""
        with patch.object(config, "ENABLE_MAGIC_FORMULA", True), \
             patch.object(config, "ENABLE_PIOTROSKI", True), \
             patch.object(config, "ENABLE_GRAHAM", True), \
             patch.object(config, "ENABLE_ACQUIRER", True), \
             patch.object(config, "ENABLE_ALTMAN", True):
            result = get_enabled_formulas()
            assert "magic_formula" in result
            assert "piotroski" in result
            assert "graham" in result
            assert "acquirer" in result
            assert "altman" in result
            assert len(result) == 5

    def test_get_enabled_formulas_none_enabled(self):
        """get_enabled_formulas returns empty list when all are disabled."""
        with patch.object(config, "ENABLE_MAGIC_FORMULA", False), \
             patch.object(config, "ENABLE_PIOTROSKI", False), \
             patch.object(config, "ENABLE_GRAHAM", False), \
             patch.object(config, "ENABLE_ACQUIRER", False), \
             patch.object(config, "ENABLE_ALTMAN", False):
            result = get_enabled_formulas()
            assert result == []

    def test_get_enabled_formulas_partial_enabled(self):
        """get_enabled_formulas returns only enabled formulas."""
        with patch.object(config, "ENABLE_MAGIC_FORMULA", True), \
             patch.object(config, "ENABLE_PIOTROSKI", False), \
             patch.object(config, "ENABLE_GRAHAM", True), \
             patch.object(config, "ENABLE_ACQUIRER", False), \
             patch.object(config, "ENABLE_ALTMAN", True):
            result = get_enabled_formulas()
            assert "magic_formula" in result
            assert "piotroski" not in result
            assert "graham" in result
            assert "acquirer" not in result
            assert "altman" in result
            assert len(result) == 3

    def test_get_enabled_formulas_order(self):
        """get_enabled_formulas returns formulas in consistent order."""
        with patch.object(config, "ENABLE_MAGIC_FORMULA", True), \
             patch.object(config, "ENABLE_PIOTROSKI", True), \
             patch.object(config, "ENABLE_GRAHAM", True), \
             patch.object(config, "ENABLE_ACQUIRER", True), \
             patch.object(config, "ENABLE_ALTMAN", True):
            result = get_enabled_formulas()
            expected_order = ["magic_formula", "piotroski", "graham", "acquirer", "altman"]
            assert result == expected_order
