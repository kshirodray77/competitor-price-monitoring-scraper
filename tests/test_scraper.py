"""Tests for the web scraper module."""

import pytest
from unittest.mock import patch, MagicMock
from src.scraper import PriceScraper, ScrapeResult


# ── HTML Fixtures ────────────────────────────────────────────────

MOCK_HTML_AMAZON = """
<html>
<body>
  <div id="product">
    <h1>Sony WH-1000XM5</h1>
    <span class="a-price">
      <span class="a-offscreen">$299.99</span>
    </span>
  </div>
</body>
</html>
"""

MOCK_HTML_BESTBUY = """
<html>
<body>
  <div class="product-info">
    <h1>Apple iPad Air</h1>
    <div class="product-price">
      <span class="current">$599.00</span>
    </div>
  </div>
</body>
</html>
"""

MOCK_HTML_NO_PRICE = """
<html>
<body>
  <div id="product">
    <h1>Out of Stock Product</h1>
    <span class="out-of-stock">Currently Unavailable</span>
  </div>
</body>
</html>
"""

MOCK_HTML_MULTIPLE_PRICES = """
<html>
<body>
  <div class="product">
    <span class="was-price">$499.99</span>
    <span class="sale-price">$349.99</span>
  </div>
</body>
</html>
"""


# ── Scraper Tests ────────────────────────────────────────────────

class TestPriceScraper:
    """Unit tests for the PriceScraper class."""

    def setup_method(self):
        self.scraper = PriceScraper(timeout=5, delay_range=(0, 0), max_retries=1)

    def teardown_method(self):
        self.scraper.close()

    @patch.object(PriceScraper, "_fetch_page")
    def test_scrape_amazon_style_price(self, mock_fetch):
        """Should extract price from Amazon-style nested span."""
        mock_fetch.return_value = MOCK_HTML_AMAZON
        result = self.scraper.scrape_product(
            name="Sony WH-1000XM5",
            url="https://www.example.com/product/1",
            selector="span.a-price > span.a-offscreen",
        )
        assert result.success is True
        assert result.price == 299.99
        assert result.product == "Sony WH-1000XM5"

    @patch.object(PriceScraper, "_fetch_page")
    def test_scrape_bestbuy_style_price(self, mock_fetch):
        """Should extract price from Best Buy-style product page."""
        mock_fetch.return_value = MOCK_HTML_BESTBUY
        result = self.scraper.scrape_product(
            name="iPad Air",
            url="https://www.example.com/product/2",
            selector="div.product-price span.current",
        )
        assert result.success is True
        assert result.price == 599.00

    @patch.object(PriceScraper, "_fetch_page")
    def test_scrape_no_price_found(self, mock_fetch):
        """Should return failure when no price element matches."""
        mock_fetch.return_value = MOCK_HTML_NO_PRICE
        result = self.scraper.scrape_product(
            name="Ghost Product",
            url="https://www.example.com/product/3",
            selector="span.price",
        )
        assert result.success is False
        assert result.price is None
        assert result.error is not None

    @patch.object(PriceScraper, "_fetch_page")
    def test_fallback_selector(self, mock_fetch):
        """Should use fallback selector when primary fails."""
        mock_fetch.return_value = MOCK_HTML_MULTIPLE_PRICES
        result = self.scraper.scrape_product(
            name="Sale Item",
            url="https://www.example.com/product/4",
            selector="span.nonexistent",
            fallback_selectors=["span.sale-price"],
        )
        assert result.success is True
        assert result.price == 349.99

    @patch.object(PriceScraper, "_fetch_page")
    def test_scrape_http_error(self, mock_fetch):
        """Should handle HTTP errors gracefully."""
        from requests.exceptions import HTTPError

        mock_fetch.side_effect = HTTPError("404 Not Found")
        result = self.scraper.scrape_product(
            name="Missing Product",
            url="https://www.example.com/product/404",
            selector="span.price",
        )
        assert result.success is False
        assert "404" in result.error

    @patch.object(PriceScraper, "_fetch_page")
    def test_scrape_all_with_delay(self, mock_fetch):
        """Should scrape multiple products and return all results."""
        mock_fetch.return_value = MOCK_HTML_AMAZON
        products = [
            {
                "name": "Product A",
                "url": "https://example.com/a",
                "selector": "span.a-price > span.a-offscreen",
            },
            {
                "name": "Product B",
                "url": "https://example.com/b",
                "selector": "span.a-price > span.a-offscreen",
            },
        ]
        results = self.scraper.scrape_all(products)
        assert len(results) == 2
        assert all(r.success for r in results)


class TestScrapeResult:
    """Tests for the ScrapeResult dataclass."""

    def test_successful_result(self):
        r = ScrapeResult(
            product="Test", url="https://example.com", price=29.99,
            raw_text="$29.99", success=True,
        )
        assert r.success is True
        assert r.error is None

    def test_failed_result(self):
        r = ScrapeResult(
            product="Test", url="https://example.com", price=None,
            raw_text=None, success=False, error="timeout",
        )
        assert r.success is False
        assert r.error == "timeout"
