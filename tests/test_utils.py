"""Tests for utility functions."""

import pytest
from src.utils import parse_price, get_random_headers


class TestParsePrice:
    """Unit tests for the price parser."""

    def test_standard_usd(self):
        assert parse_price("$299.99") == 299.99

    def test_with_commas(self):
        assert parse_price("$1,299.99") == 1299.99

    def test_currency_symbol_euro(self):
        assert parse_price("€49.50") == 49.50

    def test_currency_symbol_rupee(self):
        assert parse_price("₹12,499.00") == 12499.00

    def test_currency_code_prefix(self):
        assert parse_price("USD 29.50") == 29.50

    def test_price_with_label(self):
        assert parse_price("Price: 499") == 499.0

    def test_whole_number(self):
        assert parse_price("$100") == 100.0

    def test_empty_string(self):
        assert parse_price("") is None

    def test_none_input(self):
        assert parse_price(None) is None

    def test_no_number(self):
        assert parse_price("Out of Stock") is None

    def test_whitespace(self):
        assert parse_price("  $  349.99  ") == 349.99

    def test_gbp_symbol(self):
        assert parse_price("£199.99") == 199.99

    def test_yen_symbol(self):
        assert parse_price("¥2500") == 2500.0

    def test_large_price(self):
        assert parse_price("$12,345,678.90") == 12345678.90


class TestGetRandomHeaders:
    """Tests for HTTP header generation."""

    def test_returns_dict(self):
        headers = get_random_headers()
        assert isinstance(headers, dict)

    def test_has_user_agent(self):
        headers = get_random_headers()
        assert "User-Agent" in headers
        assert len(headers["User-Agent"]) > 20

    def test_has_accept(self):
        headers = get_random_headers()
        assert "Accept" in headers

    def test_rotation(self):
        """Should not always return the same User-Agent."""
        agents = {get_random_headers()["User-Agent"] for _ in range(50)}
        assert len(agents) > 1
