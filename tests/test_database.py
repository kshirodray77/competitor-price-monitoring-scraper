"""Tests for the SQLite database module."""

import os
import pytest
from datetime import datetime, timedelta

from src.database import PriceDatabase


class TestPriceDatabase:
    """Unit tests for price history database operations."""

    def setup_method(self):
        """Create a fresh in-memory-like temp database for each test."""
        self.db_path = "/tmp/test_prices.db"
        self.db = PriceDatabase(db_path=self.db_path)

    def teardown_method(self):
        """Clean up the test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_retrieve_price(self):
        """Should save a price and retrieve it as the latest."""
        self.db.save_price("Widget X", "https://example.com/x", 29.99)
        latest = self.db.get_latest_price("Widget X")

        assert latest is not None
        assert latest["product"] == "Widget X"
        assert latest["price"] == 29.99
        assert latest["url"] == "https://example.com/x"

    def test_latest_returns_most_recent(self):
        """Should return the most recently saved price."""
        self.db.save_price("Widget X", "https://example.com/x", 29.99,
                           scraped_at="2026-03-23T08:00:00")
        self.db.save_price("Widget X", "https://example.com/x", 24.99,
                           scraped_at="2026-03-24T08:00:00")
        self.db.save_price("Widget X", "https://example.com/x", 27.50,
                           scraped_at="2026-03-25T08:00:00")

        latest = self.db.get_latest_price("Widget X")
        assert latest["price"] == 27.50

    def test_previous_price(self):
        """Should return the second-most-recent price."""
        self.db.save_price("Widget X", "https://example.com/x", 29.99,
                           scraped_at="2026-03-23T08:00:00")
        self.db.save_price("Widget X", "https://example.com/x", 24.99,
                           scraped_at="2026-03-24T08:00:00")

        previous = self.db.get_previous_price("Widget X")
        assert previous is not None
        assert previous["price"] == 29.99

    def test_previous_price_none_on_first_entry(self):
        """Should return None when there's only one record."""
        self.db.save_price("Widget X", "https://example.com/x", 29.99)

        previous = self.db.get_previous_price("Widget X")
        assert previous is None

    def test_no_price_returns_none(self):
        """Should return None for a product with no records."""
        latest = self.db.get_latest_price("Nonexistent")
        assert latest is None

    def test_price_history(self):
        """Should return history within the specified day range."""
        now = datetime.utcnow()
        for i in range(10):
            ts = (now - timedelta(days=i)).isoformat()
            self.db.save_price("Widget X", "https://example.com/x",
                               100.0 - i, scraped_at=ts)

        history = self.db.get_price_history("Widget X", days=7)
        assert len(history) <= 8  # 7 days + today
        assert all(h["product"] == "Widget X" for h in history)
        # Should be oldest → newest
        prices = [h["price"] for h in history]
        assert prices == sorted(prices)

    def test_get_all_products(self):
        """Should return unique product names."""
        self.db.save_price("Alpha", "https://example.com/a", 10.0)
        self.db.save_price("Beta", "https://example.com/b", 20.0)
        self.db.save_price("Alpha", "https://example.com/a", 11.0)

        products = self.db.get_all_products()
        assert products == ["Alpha", "Beta"]

    def test_cleanup_old_records(self):
        """Should delete records older than the specified number of days."""
        now = datetime.utcnow()

        # Insert an old record (100 days ago)
        old_ts = (now - timedelta(days=100)).isoformat()
        self.db.save_price("Widget X", "https://example.com/x", 50.0,
                           scraped_at=old_ts)

        # Insert a recent record
        self.db.save_price("Widget X", "https://example.com/x", 45.0,
                           scraped_at=now.isoformat())

        deleted = self.db.cleanup_old_records(keep_days=90)
        assert deleted == 1

        # Recent record should still be there
        latest = self.db.get_latest_price("Widget X")
        assert latest["price"] == 45.0

    def test_save_returns_row_id(self):
        """save_price should return the auto-incremented row ID."""
        id1 = self.db.save_price("A", "https://example.com/a", 10.0)
        id2 = self.db.save_price("B", "https://example.com/b", 20.0)
        assert id1 == 1
        assert id2 == 2

    def test_currency_default(self):
        """Default currency should be USD."""
        self.db.save_price("Widget X", "https://example.com/x", 29.99)
        latest = self.db.get_latest_price("Widget X")
        assert latest["currency"] == "USD"

    def test_custom_currency(self):
        """Should store a custom currency code."""
        self.db.save_price("Widget X", "https://example.com/x", 2499.0,
                           currency="INR")
        latest = self.db.get_latest_price("Widget X")
        assert latest["currency"] == "INR"
