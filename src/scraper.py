"""Web scraper: fetches product pages and extracts prices with BeautifulSoup."""

import logging
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.utils import get_random_headers, parse_price, random_delay, retry

logger = logging.getLogger("price_tracker.scraper")


@dataclass
class ScrapeResult:
    """Result of a single product scrape."""

    product: str
    url: str
    price: Optional[float]
    raw_text: Optional[str]
    success: bool
    error: Optional[str] = None


class PriceScraper:
    """
    Scrapes product prices from e-commerce sites.

    Uses rotating user agents, configurable delays, and retry logic
    to avoid detection and handle transient failures.
    """

    def __init__(
        self,
        timeout: int = 10,
        delay_range: tuple[float, float] = (1.0, 3.0),
        max_retries: int = 3,
    ):
        self.timeout = timeout
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.session = requests.Session()

    def scrape_product(
        self,
        name: str,
        url: str,
        selector: str,
        fallback_selectors: Optional[list[str]] = None,
    ) -> ScrapeResult:
        """
        Scrape a single product's price.

        Args:
            name: Human-readable product name.
            url: Full URL of the product page.
            selector: Primary CSS selector for the price element.
            fallback_selectors: Backup selectors to try if primary fails.

        Returns:
            A ScrapeResult with the extracted price or error details.
        """
        logger.info("Scraping: %s (%s)", name, url)

        try:
            html = self._fetch_page(url)
            price, raw_text = self._extract_price(html, selector, fallback_selectors)

            if price is not None:
                logger.info("  ✓ %s: $%.2f", name, price)
                return ScrapeResult(
                    product=name, url=url, price=price, raw_text=raw_text, success=True
                )
            else:
                msg = f"Price element not found with selector '{selector}'"
                logger.warning("  ✗ %s: %s", name, msg)
                return ScrapeResult(
                    product=name, url=url, price=None, raw_text=raw_text,
                    success=False, error=msg,
                )

        except requests.RequestException as exc:
            logger.error("  ✗ %s: HTTP error — %s", name, exc)
            return ScrapeResult(
                product=name, url=url, price=None, raw_text=None,
                success=False, error=str(exc),
            )
        except Exception as exc:
            logger.error("  ✗ %s: Unexpected error — %s", name, exc)
            return ScrapeResult(
                product=name, url=url, price=None, raw_text=None,
                success=False, error=str(exc),
            )

    def scrape_all(self, products: list[dict]) -> list[ScrapeResult]:
        """
        Scrape a list of products with delays between requests.

        Args:
            products: List of product configs, each with keys:
                name, url, selector, and optionally fallback_selectors.

        Returns:
            A list of ScrapeResult objects.
        """
        results = []
        for i, product in enumerate(products):
            if i > 0:
                random_delay(self.delay_range)

            result = self.scrape_product(
                name=product["name"],
                url=product["url"],
                selector=product["selector"],
                fallback_selectors=product.get("fallback_selectors"),
            )
            results.append(result)

        successful = sum(1 for r in results if r.success)
        logger.info(
            "Scraping complete: %d/%d products successful", successful, len(results)
        )
        return results

    @retry(max_retries=3, base_delay=2.0)
    def _fetch_page(self, url: str) -> str:
        """
        Fetch a product page's HTML content.

        Uses rotating headers and respects timeouts.
        Decorated with @retry for automatic exponential backoff.
        """
        headers = get_random_headers()
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        logger.debug("  Fetched %s — %d bytes", url, len(response.text))
        return response.text

    def _extract_price(
        self,
        html: str,
        selector: str,
        fallback_selectors: Optional[list[str]] = None,
    ) -> tuple[Optional[float], Optional[str]]:
        """
        Extract a price from HTML using CSS selectors.

        Tries the primary selector first, then falls back to alternatives.

        Returns:
            A tuple of (parsed_price, raw_text_found).
        """
        soup = BeautifulSoup(html, "lxml")

        # Try primary selector
        element = soup.select_one(selector)
        if element:
            raw = element.get_text(strip=True)
            price = parse_price(raw)
            if price is not None:
                return price, raw
            logger.debug("  Primary selector matched but price parse failed: '%s'", raw)

        # Try fallback selectors
        if fallback_selectors:
            for fb_selector in fallback_selectors:
                element = soup.select_one(fb_selector)
                if element:
                    raw = element.get_text(strip=True)
                    price = parse_price(raw)
                    if price is not None:
                        logger.debug("  Fallback selector '%s' matched", fb_selector)
                        return price, raw

        return None, None

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
