"""Discord webhook notification module."""

import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

# Discord embed color (blue)
EMBED_COLOR = 3447003


class DiscordNotifier:
    """Client for sending notifications via Discord webhooks."""

    def __init__(self, webhook_url: str):
        """
        Initialize the Discord notifier.

        Args:
            webhook_url: Discord webhook URL for sending messages.
        """
        self.webhook_url = webhook_url

    def _format_stock_field(self, stock: Dict[str, Any], rank: int) -> Dict[str, str]:
        """
        Format a single stock as a Discord embed field.

        Args:
            stock: Stock data dictionary with keys:
                - symbol: Stock ticker
                - company_name: Full company name
                - price: Current stock price
                - magic_score: Combined ranking score
                - earnings_yield: Earnings yield as decimal
                - roc: Return on capital as decimal
            rank: Display rank (1-indexed).

        Returns:
            Dict with 'name' and 'value' keys for Discord embed field.
        """
        symbol = stock.get("symbol", "N/A")
        company_name = stock.get("company_name", "Unknown")
        price = stock.get("price", 0)
        magic_score = stock.get("magic_score", 0)
        earnings_yield = stock.get("earnings_yield", 0)
        roc = stock.get("roc", 0)

        # Medal emojis for top 3
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, "🏅")

        # Format percentages
        ey_pct = earnings_yield * 100 if earnings_yield else 0
        roc_pct = roc * 100 if roc else 0

        return {
            "name": f"{medal} {rank}. {symbol} - {company_name}",
            "value": (
                f"💰 Price: ${price:,.2f} | 📊 Score: {magic_score}\n"
                f"E.Yield: {ey_pct:.1f}% | ROC: {roc_pct:.1f}%"
            ),
            "inline": False,
        }

    def send_magic_formula_alert(
        self,
        stocks: List[Dict[str, Any]],
        month_year: str,
    ) -> bool:
        """
        Send Magic Formula alert to Discord channel.

        Args:
            stocks: List of stock dictionaries (top picks).
            month_year: Display string for month/year (e.g., "January 2025").

        Returns:
            True if message sent successfully, False otherwise.
        """
        # Build embed fields for each stock
        fields = [
            self._format_stock_field(stock, rank)
            for rank, stock in enumerate(stocks, start=1)
        ]

        # Build Discord webhook payload
        payload = {
            "embeds": [
                {
                    "title": "🤖 Magic Formula DCA Alert",
                    "description": f"**Monthly stock picks for {month_year}**\n\n"
                    f"Top {len(stocks)} stocks ranked by Magic Formula "
                    f"(Earnings Yield + Return on Capital)",
                    "color": EMBED_COLOR,
                    "fields": fields,
                    "footer": {
                        "text": (
                            "⚠️ Disclaimer: Automated analysis based on financial "
                            "statements. Please do your own research (DYOR)."
                        )
                    },
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30,
            )

            if response.status_code in (200, 204):
                logger.info("Discord notification sent successfully")
                return True
            else:
                logger.error(
                    f"Discord webhook failed with status {response.status_code}: "
                    f"{response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Discord webhook request failed: {e}")
            return False
