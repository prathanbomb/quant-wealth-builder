"""Configuration module for Magic Formula DCA Bot."""

import os
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


def _parse_bool_env(key: str, default: bool = True) -> bool:
    """Parse a boolean environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        True if value is 'true', '1', or 'yes' (case-insensitive).
        False if value is 'false', '0', or 'no'.
        Default if not set or empty.
    """
    value = os.getenv(key, "").lower().strip()
    if not value:
        return default
    return value in ("true", "1", "yes")


# Environment variables
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

# Formula toggles - each formula can be enabled/disabled independently
ENABLE_MAGIC_FORMULA: bool = _parse_bool_env("ENABLE_MAGIC_FORMULA", True)
ENABLE_PIOTROSKI: bool = _parse_bool_env("ENABLE_PIOTROSKI", True)
ENABLE_GRAHAM: bool = _parse_bool_env("ENABLE_GRAHAM", True)
ENABLE_ACQUIRER: bool = _parse_bool_env("ENABLE_ACQUIRER", True)
ENABLE_ALTMAN: bool = _parse_bool_env("ENABLE_ALTMAN", True)

# Constants
MIN_MARKET_CAP: int = 100_000_000  # $100 Million USD
EXCLUDED_SECTORS: List[str] = ["Financial Services", "Utilities"]
TARGET_EXCHANGES: List[str] = ["NYSE", "NASDAQ"]
TOP_N_STOCKS: int = 5  # Number of top stocks to select


def validate_config() -> None:
    """
    Validate that all required configuration values are present.

    Raises:
        ConfigurationError: If any required configuration is missing.
    """
    missing = []

    if not DISCORD_WEBHOOK_URL:
        missing.append("DISCORD_WEBHOOK_URL")

    if missing:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please set them in your .env file or environment."
        )


def get_enabled_formulas() -> List[str]:
    """
    Get list of enabled formula names.

    Returns:
        List of formula names that are currently enabled.
    """
    formulas = []
    if ENABLE_MAGIC_FORMULA:
        formulas.append("magic_formula")
    if ENABLE_PIOTROSKI:
        formulas.append("piotroski")
    if ENABLE_GRAHAM:
        formulas.append("graham")
    if ENABLE_ACQUIRER:
        formulas.append("acquirer")
    if ENABLE_ALTMAN:
        formulas.append("altman")
    return formulas


def get_config() -> dict:
    """
    Get all configuration values as a dictionary.

    Returns:
        dict: Configuration values.
    """
    return {
        "discord_webhook_url": DISCORD_WEBHOOK_URL,
        "min_market_cap": MIN_MARKET_CAP,
        "excluded_sectors": EXCLUDED_SECTORS,
        "target_exchanges": TARGET_EXCHANGES,
        "top_n_stocks": TOP_N_STOCKS,
        "enable_magic_formula": ENABLE_MAGIC_FORMULA,
        "enable_piotroski": ENABLE_PIOTROSKI,
        "enable_graham": ENABLE_GRAHAM,
        "enable_acquirer": ENABLE_ACQUIRER,
        "enable_altman": ENABLE_ALTMAN,
    }
