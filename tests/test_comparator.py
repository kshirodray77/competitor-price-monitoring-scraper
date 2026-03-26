"""Tests for the price comparison engine."""

import pytest
from unittest.mock import MagicMock

from src.scraper import ScrapeResult
from src.comparator import PriceComparator, PriceChange


class TestPriceComparator:
    """Unit tests for price comparison logic."""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.comparator = PriceComparator(database=self.mock_db)

    def _make_result(self, name="Test Product", price=100.0, success=True):
        return ScrapeResult(
            product=name, url="https://example.com/p", price=price,
            raw_text=f"${price}", success=success,
        )

    def test_first_scrape_no_alert(self):
        """First time seeing a product — save but no alert."""
        self.mock_db.get_latest_price.return_value = None
        self.mock_db.get_price_history.return_value = []

        results = [self._make_result(price=299.99)]
        configs = [{"name": "Test Product", "alert_threshold_pct": 5.0}]

        changes = self.comparator.compare(results, configs)
        assert len(changes) == 0
        self.mock_db.save_price.assert_called_once()

    def test_price_drop_triggers_alert(self):
        """A >5% price drop should trigger an alert."""
        self.mock_db.get_latest_price.return_value = {
            "product": "Test Product", "url": "https://example.com/p",
            "price": 100.0, "currency": "USD",
            "scraped_at": "2026-03-24T08:00:00",
        }
        self.mock_db.get_price_history.return_value = [
            {"product": "Test Product", "price": 100.0, "scraped_at": "2026-03-24"},
        ]

        results = [self._make_result(price=89.99)]  # ~10% drop
        configs = [{"name": "Test Product", "alert_threshold_pct": 5.0}]

        changes = self.comparator.compare(results, configs)
        assert len(changes) == 1
        assert changes[0].direction == "down"
        assert changes[0].percent_change == pytest.approx(-10.01, abs=0.1)

    def test_price_increase_triggers_alert(self):
        """A >5% price increase should trigger an alert."""
        self.mock_db.get_latest_price.return_value = {
            "product": "Test Product", "url": "https://example.com/p",
            "price": 100.0, "currency": "USD",
            "scraped_at": "2026-03-24T08:00:00",
        }
        self.mock_db.get_price_history.return_value = []

        results = [self._make_result(price=115.0)]  # 15% increase
        configs = [{"name": "Test Product", "alert_threshold_pct": 5.0}]

        changes = self.comparator.compare(results, configs)
        assert len(changes) == 1
        assert changes[0].direction == "up"
        assert changes[0].percent_change == pytest.approx(15.0, abs=0.1)

    def test_small_change_no_alert(self):
        """A change below threshold should NOT trigger an alert."""
        self.mock_db.get_latest_price.return_value = {
            "product": "Test Product", "url": "https://example.com/p",
            "price": 100.0, "currency": "USD",
            "scraped_at": "2026-03-24T08:00:00",
        }

        results = [self._make_result(price=98.0)]  # Only 2% drop
        configs = [{"name": "Test Product", "alert_threshold_pct": 5.0}]

        changes = self.comparator.compare(results, configs)
        assert len(changes) == 0

    def test_absolute_threshold_triggers_alert(self):
        """An absolute threshold should also trigger alerts."""
        self.mock_db.get_latest_price.return_value = {
            "product": "Test Product", "url": "https://example.com/p",
            "price": 1000.0, "currency": "USD",
            "scraped_at": "2026-03-24T08:00:00",
        }
        self.mock_db.get_price_history.return_value = []

        results = [self._make_result(price=975.0)]  # $25 drop (only 2.5%)
        configs = [{
            "name": "Test Product",
            "alert_threshold_pct": 5.0,
            "alert_threshold_abs": 20.0,  # $20 absolute threshold
        }]

        changes = self.comparator.compare(results, configs)
        assert len(changes) == 1  # Triggered by absolute threshold

    def test_failed_scrape_skipped(self):
        """Failed scrapes should be silently skipped."""
        results = [self._make_result(success=False, price=None)]
        configs = [{"name": "Test Product", "alert_threshold_pct": 5.0}]

        changes = self.comparator.compare(results, configs)
        assert len(changes) == 0
        self.mock_db.save_price.assert_not_called()


class TestPriceChange:
    """Tests for the PriceChange dataclass."""

    def test_trend_indicator_down(self):
        change = PriceChange(
            product="X", url="", old_price=100, new_price=80,
            absolute_change=-20, percent_change=-20.0, direction="down",
        )
        assert change.trend_indicator == "📉"

    def test_trend_indicator_up(self):
        change = PriceChange(
            product="X", url="", old_price=100, new_price=120,
            absolute_change=20, percent_change=20.0, direction="up",
        )
        assert change.trend_indicator == "📈"

    def test_sparkline_generation(self):
        change = PriceChange(
            product="X", url="", old_price=100, new_price=80,
            absolute_change=-20, percent_change=-20.0, direction="down",
            history=[
                {"price": 100, "scraped_at": "2026-03-19"},
                {"price": 95, "scraped_at": "2026-03-20"},
                {"price": 90, "scraped_at": "2026-03-21"},
                {"price": 85, "scraped_at": "2026-03-22"},
                {"price": 80, "scraped_at": "2026-03-23"},
            ],
        )
        sparkline = change.sparkline
        assert len(sparkline) == 5
        # First char should be tallest, last shortest
        assert sparkline[0] == "▇"
        assert sparkline[-1] == " "

    def test_sparkline_flat(self):
        change = PriceChange(
            product="X", url="", old_price=100, new_price=100,
            absolute_change=0, percent_change=0, direction="unchanged",
            history=[
                {"price": 50, "scraped_at": "2026-03-22"},
                {"price": 50, "scraped_at": "2026-03-23"},
            ],
        )
        assert change.sparkline == "▅▅"
