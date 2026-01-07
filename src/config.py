"""Configuration module for Magic Formula DCA Bot."""

import os
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


# Environment variables
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

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
    }
