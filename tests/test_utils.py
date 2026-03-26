"""Tests for utility functions."""

import logging
import os
import pytest
from unittest.mock import patch

from src.utils import parse_price, get_random_headers, retry, setup_logging, random_delay


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


class TestRetryDecorator:
    """Tests for the exponential backoff retry decorator."""

    @patch("src.utils.time.sleep")
    def test_succeeds_on_first_try(self, mock_sleep):
        """Should not retry if function succeeds immediately."""
        @retry(max_retries=3, base_delay=0.01)
        def always_works():
            return "ok"

        assert always_works() == "ok"
        mock_sleep.assert_not_called()

    @patch("src.utils.time.sleep")
    def test_retries_then_succeeds(self, mock_sleep):
        """Should retry and return result once function succeeds."""
        call_count = 0

        @retry(max_retries=3, base_delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary failure")
            return "recovered"

        assert fails_twice() == "recovered"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.utils.time.sleep")
    def test_raises_after_all_retries(self, mock_sleep):
        """Should raise the last exception after exhausting retries."""
        @retry(max_retries=2, base_delay=0.01)
        def always_fails():
            raise ValueError("permanent failure")

        with pytest.raises(ValueError, match="permanent failure"):
            always_fails()
        assert mock_sleep.call_count == 1


class TestSetupLogging:
    """Tests for logging configuration."""

    def test_console_only(self):
        """Should create logger with console handler."""
        logger = setup_logging(level="DEBUG")
        assert logger.name == "price_tracker"
        assert logger.level == logging.DEBUG
        # Clean up handlers to avoid pollution
        logger.handlers.clear()

    def test_with_file_handler(self, tmp_path):
        """Should create logger with both console and file handler."""
        log_file = str(tmp_path / "test.log")
        logger = setup_logging(level="INFO", log_file=log_file)
        assert any(
            hasattr(h, "baseFilename") for h in logger.handlers
        )
        logger.handlers.clear()

    def test_log_file_directory_created(self, tmp_path):
        """Should create parent directories for the log file."""
        log_file = str(tmp_path / "subdir" / "deep" / "test.log")
        logger = setup_logging(log_file=log_file)
        assert os.path.exists(os.path.dirname(log_file))
        logger.handlers.clear()


class TestRandomDelay:
    """Tests for the delay helper."""

    @patch("src.utils.time.sleep")
    def test_calls_sleep(self, mock_sleep):
        """Should call time.sleep with a value in range."""
        random_delay((0.1, 0.2))
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0.1 <= delay <= 0.2

    @patch("src.utils.time.sleep")
    def test_default_range(self, mock_sleep):
        """Should use default range (1.0, 3.0)."""
        random_delay()
        delay = mock_sleep.call_args[0][0]
        assert 1.0 <= delay <= 3.0
