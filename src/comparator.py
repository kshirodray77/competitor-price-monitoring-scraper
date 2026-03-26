"""Price comparison engine: diffs current vs. previous prices and decides alerts."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.scraper import ScrapeResult
from src.database import PriceDatabase

logger = logging.getLogger("price_tracker.comparator")


@dataclass
class PriceChange:
    """Represents a detected price change for a single product."""

    product: str
    url: str
    old_price: float
    new_price: float
    absolute_change: float
    percent_change: float
    direction: str  # "up", "down", or "unchanged"
    history: list[dict] = field(default_factory=list)

    @property
    def trend_indicator(self) -> str:
        """Return a visual trend indicator."""
        if self.direction == "down":
            return "📉"
        elif self.direction == "up":
            return "📈"
        return "➡️"

    @property
    def sparkline(self) -> str:
        """Generate a simple text sparkline from price history."""
        if not self.history:
            return ""

        prices = [h["price"] for h in self.history]
        if len(prices) < 2:
            return "▅"

        min_p, max_p = min(prices), max(prices)
        spread = max_p - min_p

        if spread == 0:
            return "▅" * len(prices)

        bars = " ▁▂▃▄▅▆▇"
        return "".join(
            bars[int((p - min_p) / spread * (len(bars) - 1))] for p in prices
        )


class PriceComparator:
    """
    Compares freshly scraped prices against stored history.

    Determines which products have changed beyond their configured
    thresholds and should trigger an alert.
    """

    def __init__(self, database: PriceDatabase):
        self.db = database

    def compare(
        self,
        scrape_results: list[ScrapeResult],
        product_configs: list[dict],
    ) -> list[PriceChange]:
        """
        Compare scraped prices against stored history.

        For each successfully scraped product:
        1. Save the new price to the database.
        2. Compare against the previously stored price.
        3. If the change exceeds the threshold, include it in the results.

        Args:
            scrape_results: Results from the scraper.
            product_configs: Product configurations with threshold settings.

        Returns:
            A list of PriceChange objects for products that exceed thresholds.
        """
        # Build a config lookup by product name
        config_map = {p["name"]: p for p in product_configs}
        changes: list[PriceChange] = []

        for result in scrape_results:
            if not result.success or result.price is None:
                logger.debug("Skipping %s (scrape failed)", result.product)
                continue

            # Get previous price before saving the new one
            previous = self.db.get_latest_price(result.product)

            # Save new price
            self.db.save_price(
                product=result.product,
                url=result.url,
                price=result.price,
            )

            # First-time scrape — no comparison to make
            if previous is None:
                logger.info(
                    "First scrape for %s: $%.2f (no comparison)",
                    result.product,
                    result.price,
                )
                continue

            old_price = previous["price"]
            new_price = result.price

            # Calculate change
            abs_change = new_price - old_price
            pct_change = (abs_change / old_price * 100) if old_price != 0 else 0.0

            if abs_change > 0:
                direction = "up"
            elif abs_change < 0:
                direction = "down"
            else:
                direction = "unchanged"

            # Check against thresholds
            config = config_map.get(result.product, {})
            threshold_pct = config.get("alert_threshold_pct", 5.0)
            threshold_abs = config.get("alert_threshold_abs")

            should_alert = False
            if abs(pct_change) >= threshold_pct:
                should_alert = True
            if threshold_abs is not None and abs(abs_change) >= threshold_abs:
                should_alert = True

            if should_alert:
                history = self.db.get_price_history(result.product, days=7)
                change = PriceChange(
                    product=result.product,
                    url=result.url,
                    old_price=old_price,
                    new_price=new_price,
                    absolute_change=abs_change,
                    percent_change=pct_change,
                    direction=direction,
                    history=history,
                )
                changes.append(change)
                logger.info(
                    "Alert: %s %s $%.2f → $%.2f (%+.1f%%)",
                    change.trend_indicator,
                    result.product,
                    old_price,
                    new_price,
                    pct_change,
                )
            else:
                logger.debug(
                    "No alert for %s: $%.2f → $%.2f (%+.1f%%, threshold: %.1f%%)",
                    result.product,
                    old_price,
                    new_price,
                    pct_change,
                    threshold_pct,
                )

        logger.info(
            "Comparison complete: %d price changes detected", len(changes)
        )
        return changes
