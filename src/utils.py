"""Shared utilities: user agents, retry logic, logging, price parsing."""

import logging
import random
import re
import time
import functools
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# ── User-Agent Rotation ─────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def get_random_headers() -> dict:
    """Return HTTP headers with a randomly selected User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


# ── Retry Decorator ─────────────────────────────────────────────

def retry(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds before the first retry.
        backoff_factor: Multiplier applied to the delay after each failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        jitter = random.uniform(0, delay * 0.5)
                        wait = delay + jitter
                        logger.warning(
                            "Attempt %d/%d for %s failed: %s — retrying in %.1fs",
                            attempt,
                            max_retries,
                            func.__name__,
                            exc,
                            wait,
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            "All %d attempts for %s failed. Last error: %s",
                            max_retries,
                            func.__name__,
                            exc,
                        )
            raise last_exception  # type: ignore[misc]

        return wrapper
    return decorator


# ── Price Parsing ────────────────────────────────────────────────

def parse_price(raw_text: str) -> Optional[float]:
    """
    Extract a numeric price from messy text.

    Handles formats like:
        "$1,299.99", "USD 29.50", "Price: 499", "₹12,499.00"

    Returns:
        The price as a float, or None if parsing fails.
    """
    if not raw_text:
        return None

    # Strip whitespace and common currency symbols/words
    cleaned = raw_text.strip()
    cleaned = re.sub(r"[₹$€£¥]", "", cleaned)
    cleaned = re.sub(r"\b(USD|EUR|GBP|INR|JPY)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    # Match a number pattern (with optional commas and decimal)
    match = re.search(r"[\d,]+\.?\d*", cleaned)
    if not match:
        return None

    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return None


# ── Logging Setup ────────────────────────────────────────────────

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 5_242_880,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configure the root logger with console + optional rotating file handler.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        log_file: Path to the log file. If None, logs to console only.
        max_bytes: Max log file size before rotation.
        backup_count: Number of rotated backup files to keep.

    Returns:
        The configured root logger.
    """
    logger = logging.getLogger("price_tracker")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ── Delay Helper ─────────────────────────────────────────────────

def random_delay(delay_range: tuple[float, float] = (1.0, 3.0)) -> None:
    """Sleep for a random duration within the given range."""
    time.sleep(random.uniform(*delay_range))
