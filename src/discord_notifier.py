"""Discord webhook notification module."""

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Discord embed colors
EMBED_COLOR = 3447003  # Blue for Magic Formula
PIOTROSKI_COLOR = 3066993  # Green for F-Score
GRAHAM_COLOR = 15105570  # Orange for Graham Number
ACQUIRER_COLOR = 10181038  # Purple for Acquirer's Multiple
ALTMAN_COLOR = 2326507  # Red for Z-Score

# Emoji for risk zone indicators
SAFE_EMOJI = "🟢"
GREY_EMOJI = "🟡"
DISTRESS_EMOJI = "🔴"


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

    def _format_piotroski_field(self, stock: Dict[str, Any], rank: int) -> Dict[str, str]:
        """
        Format a Piotroski F-Score stock as a Discord embed field.

        Args:
            stock: Stock data dictionary with fscore and other keys.
            rank: Display rank (1-indexed).

        Returns:
            Dict with 'name' and 'value' keys for Discord embed field.
        """
        symbol = stock.get("symbol", "N/A")
        company_name = stock.get("company_name", "Unknown")
        price = stock.get("price", 0)
        fscore = stock.get("fscore", 0)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, "🏅")

        return {
            "name": f"{medal} {rank}. {symbol} - {company_name}",
            "value": f"💰 Price: ${price:,.2f} | 📊 F-Score: {int(fscore)}/9",
            "inline": False,
        }

    def _format_graham_field(self, stock: Dict[str, Any], rank: int) -> Dict[str, str]:
        """
        Format a Graham Number stock as a Discord embed field.

        Args:
            stock: Stock data dictionary with graham_number, margin_of_safety.
            rank: Display rank (1-indexed).

        Returns:
            Dict with 'name' and 'value' keys for Discord embed field.
        """
        symbol = stock.get("symbol", "N/A")
        company_name = stock.get("company_name", "Unknown")
        price = stock.get("price", 0)
        graham_number = stock.get("graham_number", 0)
        margin = stock.get("margin_of_safety", 0)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, "🏅")

        margin_str = f"+{margin:.1f}%" if margin > 0 else f"{margin:.1f}%"

        return {
            "name": f"{medal} {rank}. {symbol} - {company_name}",
            "value": (
                f"💰 Price: ${price:,.2f} | 💎 Fair Value: ${graham_number:,.2f}\n"
                f"📉 Margin: {margin_str}"
            ),
            "inline": False,
        }

    def _format_acquirer_field(self, stock: Dict[str, Any], rank: int) -> Dict[str, str]:
        """
        Format an Acquirer's Multiple stock as a Discord embed field.

        Args:
            stock: Stock data dictionary with acquirer_multiple.
            rank: Display rank (1-indexed).

        Returns:
            Dict with 'name' and 'value' keys for Discord embed field.
        """
        symbol = stock.get("symbol", "N/A")
        company_name = stock.get("company_name", "Unknown")
        price = stock.get("price", 0)
        multiple = stock.get("acquirer_multiple", 0)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, "🏅")

        return {
            "name": f"{medal} {rank}. {symbol} - {company_name}",
            "value": f"💰 Price: ${price:,.2f} | 🏷️ EV/EBIT: {multiple:.2f}x",
            "inline": False,
        }

    def _format_altman_field(self, stock: Dict[str, Any], rank: int) -> Dict[str, str]:
        """
        Format an Altman Z-Score stock as a Discord embed field.

        Args:
            stock: Stock data dictionary with zscore, risk_zone.
            rank: Display rank (1-indexed).

        Returns:
            Dict with 'name' and 'value' keys for Discord embed field.
        """
        symbol = stock.get("symbol", "N/A")
        company_name = stock.get("company_name", "Unknown")
        price = stock.get("price", 0)
        zscore = stock.get("zscore", 0)
        risk_zone = stock.get("risk_zone", "Unknown")

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        medal = medals.get(rank, "🏅")

        # Risk zone emoji
        zone_emoji = {
            "Safe": SAFE_EMOJI,
            "Grey": GREY_EMOJI,
            "Distress": DISTRESS_EMOJI,
            "Unknown": "⚪",
        }.get(risk_zone, "⚪")

        return {
            "name": f"{medal} {rank}. {symbol} - {company_name}",
            "value": f"💰 Price: ${price:,.2f} | 🛡️ Z-Score: {zscore:.2f} {zone_emoji}",
            "inline": False,
        }

    def _build_formula_embed(
        self,
        formula_name: str,
        title: str,
        description: str,
        color: int,
        stocks: List[Dict[str, Any]],
        formatter_fn,
    ) -> Dict[str, Any]:
        """
        Build a Discord embed for a single formula.

        Args:
            formula_name: Name of the formula (for logging).
            title: Embed title.
            description: Embed description.
            color: Embed color.
            stocks: List of stock dictionaries.
            formatter_fn: Function to format stock fields.

        Returns:
            Complete Discord embed dictionary.
        """
        fields = [
            formatter_fn(stock, rank)
            for rank, stock in enumerate(stocks, start=1)
        ] if stocks else []

        return {
            "title": title,
            "description": description,
            "color": color,
            "fields": fields,
        }

    def send_multi_formula_alert(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        month_year: str,
        enabled_formulas: List[str],
    ) -> bool:
        """
        Send unified alert with all formula results to Discord.

        Creates separate embed sections for each enabled formula.
        Splits into multiple messages if content exceeds Discord limits.

        Args:
            results: Dictionary mapping formula names to their top stocks lists.
                Keys: "magic_formula", "piotroski", "graham", "acquirer", "altman"
            month_year: Display string for month/year (e.g., "January 2025").
            enabled_formulas: List of formula names that were enabled.

        Returns:
            True if all messages sent successfully, False otherwise.
        """
        # Build all embeds
        all_embeds = []

        # Magic Formula embed
        if "magic_formula" in enabled_formulas and "magic_formula" in results:
            stocks = results["magic_formula"]
            if stocks:
                embed = self._build_formula_embed(
                    formula_name="Magic Formula",
                    title="📊 Magic Formula",
                    description=f"Top {len(stocks)} stocks ranked by Magic Formula "
                                "(Earnings Yield + Return on Capital)",
                    color=EMBED_COLOR,
                    stocks=stocks,
                    formatter_fn=self._format_stock_field,
                )
                all_embeds.append(embed)

        # Piotroski F-Score embed
        if "piotroski" in enabled_formulas and "piotroski" in results:
            stocks = results["piotroski"]
            if stocks:
                embed = self._build_formula_embed(
                    formula_name="Piotroski F-Score",
                    title="📈 Piotroski F-Score",
                    description=f"Top {len(stocks)} stocks by fundamental strength "
                                "(9-point profitability, leverage, and efficiency score)",
                    color=PIOTROSKI_COLOR,
                    stocks=stocks,
                    formatter_fn=self._format_piotroski_field,
                )
                all_embeds.append(embed)

        # Graham Number embed
        if "graham" in enabled_formulas and "graham" in results:
            stocks = results["graham"]
            if stocks:
                embed = self._build_formula_embed(
                    formula_name="Graham Number",
                    title="💎 Graham Number",
                    description=f"Top {len(stocks)} most undervalued stocks "
                                "(intrinsic value vs current price)",
                    color=GRAHAM_COLOR,
                    stocks=stocks,
                    formatter_fn=self._format_graham_field,
                )
                all_embeds.append(embed)

        # Acquirer's Multiple embed
        if "acquirer" in enabled_formulas and "acquirer" in results:
            stocks = results["acquirer"]
            if stocks:
                embed = self._build_formula_embed(
                    formula_name="Acquirer's Multiple",
                    title="🏷️ Acquirer's Multiple",
                    description=f"Top {len(stocks)} cheapest stocks by EV/EBIT "
                                "(deep value metric)",
                    color=ACQUIRER_COLOR,
                    stocks=stocks,
                    formatter_fn=self._format_acquirer_field,
                )
                all_embeds.append(embed)

        # Altman Z-Score embed
        if "altman" in enabled_formulas and "altman" in results:
            stocks = results["altman"]
            if stocks:
                embed = self._build_formula_embed(
                    formula_name="Altman Z-Score",
                    title="🛡️ Altman Z-Score",
                    description=f"Top {len(stocks)} financially strongest stocks "
                                "(Safe Zone only - low bankruptcy risk)",
                    color=ALTMAN_COLOR,
                    stocks=stocks,
                    formatter_fn=self._format_altman_field,
                )
                all_embeds.append(embed)

        if not all_embeds:
            logger.warning("No formula results to send")
            return False

        # Add disclaimer to last embed
        all_embeds[-1]["footer"] = {
            "text": (
                "⚠️ Disclaimer: Automated analysis based on financial "
                "statements. Please do your own research (DYOR)."
            )
        }

        # Discord has a limit of 10 embeds per message and 6000 chars total
        # Split into multiple messages if needed
        EMBEDS_PER_MESSAGE = 10
        messages = []
        for i in range(0, len(all_embeds), EMBEDS_PER_MESSAGE):
            message_embeds = all_embeds[i:i + EMBEDS_PER_MESSAGE]

            # Add header to first message
            if i == 0:
                message_embeds.insert(0, {
                    "title": f"🤖 Multi-Formula Stock Screener - {month_year}",
                    "description": f"**Stock picks for {month_year}**\n\n"
                                  f"Analyzed by {len(enabled_formulas)} formula(s)",
                    "color": EMBED_COLOR,
                })

            messages.append(message_embeds)

        # Send all messages
        all_success = True
        for i, embeds in enumerate(messages, start=1):
            payload = {"embeds": embeds}

            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30,
                )

                if response.status_code in (200, 204):
                    logger.info(f"Discord notification {i}/{len(messages)} sent successfully")
                else:
                    logger.error(
                        f"Discord webhook {i}/{len(messages)} failed with status "
                        f"{response.status_code}: {response.text}"
                    )
                    all_success = False

            except requests.exceptions.RequestException as e:
                logger.error(f"Discord webhook request {i}/{len(messages)} failed: {e}")
                all_success = False

        return all_success
