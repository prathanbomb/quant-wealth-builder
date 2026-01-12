"""Reddit sentiment data client module using Tradestie API."""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

# Tradestie Reddit API endpoint
API_URL = "https://api.tradestie.com/v1/apps/reddit"


class RedditClient:
    """Client for fetching Reddit sentiment data from Tradestie API."""

    def __init__(self):
        """Initialize the Reddit client."""
        pass

    def fetch_sentiment_data(
        self,
        date: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch Reddit sentiment data from Tradestie API.

        The API returns top 50 stocks discussed on Reddit's Wallstreetbets,
        including ticker, comment count, sentiment (Bullish/Bearish), and
        sentiment score.

        Args:
            date: Optional date in MM-DD-YYYY format (e.g., "11-02-2025").
                  If None, fetches the latest available data.

        Returns:
            List of dictionaries with keys:
            - ticker: Stock symbol (str)
            - no_of_comments: Discussion volume (int)
            - sentiment: "Bullish" or "Bearish" (str)
            - sentiment_score: Sentiment value (float)
            Returns None if API fails after all retries.
        """
        # Build URL with optional date parameter
        url = API_URL
        if date:
            url = f"{API_URL}?date={date}"

        for attempt in range(MAX_RETRIES):
            try:
                # Apply backoff delay on retries
                if attempt > 0:
                    backoff = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    logger.info(f"Retry attempt {attempt + 1}, waiting {backoff}s")
                    time.sleep(backoff)

                logger.debug(f"Fetching Reddit sentiment data from {url}")

                # Make API request
                response = requests.get(url, timeout=30)

                # Check for rate limiting (HTTP 429)
                if response.status_code == 429:
                    logger.warning("Reddit API rate limit exceeded (429)")
                    # Wait 60 seconds and retry once
                    if attempt < MAX_RETRIES - 1:
                        logger.info("Waiting 60 seconds before retry...")
                        time.sleep(60)
                        continue
                    else:
                        logger.error("Max retries exceeded for rate limit")
                        return None

                # Check for other HTTP errors
                if response.status_code >= 400:
                    logger.error(
                        f"Reddit API returned error {response.status_code}: {response.text}"
                    )
                    return None

                # Parse JSON response
                try:
                    data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None

                # Validate response is a list
                if not isinstance(data, list):
                    logger.error(f"Expected list response, got {type(data).__name__}")
                    return None

                # Validate response is not empty
                if not data:
                    logger.warning("Reddit API returned empty response")
                    return None

                # Validate each item has required fields
                required_fields = {"ticker", "no_of_comments", "sentiment", "sentiment_score"}
                valid_items = []

                for item in data:
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dict item: {item}")
                        continue

                    if not required_fields.issubset(item.keys()):
                        logger.warning(
                            f"Skipping item with missing fields: {item.get('ticker', 'unknown')}"
                        )
                        continue

                    valid_items.append(item)

                if not valid_items:
                    logger.warning("No valid items in Reddit API response")
                    return None

                logger.info(
                    f"Successfully fetched Reddit data for {len(valid_items)} stocks"
                )
                return valid_items

            except requests.exceptions.Timeout as e:
                logger.warning(
                    f"Reddit API request timed out, attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries exceeded for timeout")
                    return None

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Reddit API request failed, attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries exceeded for request")
                    return None

            except Exception as e:
                logger.error(
                    f"Unexpected error fetching Reddit data, attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
                if attempt == MAX_RETRIES - 1:
                    logger.error("Max retries exceeded for unexpected error")
                    return None

        return None
