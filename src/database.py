"""SQLite database for storing price history."""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("price_tracker.database")


class PriceDatabase:
    """Manages SQLite storage for product price history."""

    def __init__(self, db_path: str = "data/prices.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("Database initialized at %s", self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Create a new connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create the prices table if it doesn't exist."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    product     TEXT    NOT NULL,
                    url         TEXT    NOT NULL,
                    price       REAL    NOT NULL,
                    currency    TEXT    DEFAULT 'USD',
                    scraped_at  TEXT    NOT NULL,
                    created_at  TEXT    DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_product_time
                ON prices (product, scraped_at DESC)
            """)
            conn.commit()

    def save_price(
        self,
        product: str,
        url: str,
        price: float,
        currency: str = "USD",
        scraped_at: Optional[str] = None,
    ) -> int:
        """
        Insert a new price record.

        Args:
            product: Product name.
            url: Source URL.
            price: Scraped price value.
            currency: Currency code (default: USD).
            scraped_at: ISO timestamp. If None, uses current time.

        Returns:
            The row ID of the inserted record.
        """
        if scraped_at is None:
            scraped_at = datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO prices (product, url, price, currency, scraped_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (product, url, price, currency, scraped_at),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.debug(
                "Saved price: %s = %.2f %s (row %d)", product, price, currency, row_id
            )
            return row_id

    def get_latest_price(self, product: str) -> Optional[dict]:
        """
        Get the most recent price record for a product.

        Returns:
            A dict with keys (product, url, price, currency, scraped_at)
            or None if no record exists.
        """
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT product, url, price, currency, scraped_at
                FROM prices
                WHERE product = ?
                ORDER BY scraped_at DESC
                LIMIT 1
                """,
                (product,),
            ).fetchone()
            return dict(row) if row else None

    def get_previous_price(self, product: str) -> Optional[dict]:
        """
        Get the second-most-recent price record (the one before today's scrape).

        This is used for comparison: latest vs. previous.
        """
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT product, url, price, currency, scraped_at
                FROM prices
                WHERE product = ?
                ORDER BY scraped_at DESC
                LIMIT 1 OFFSET 1
                """,
                (product,),
            ).fetchone()
            return dict(row) if row else None

    def get_price_history(self, product: str, days: int = 7) -> list[dict]:
        """
        Get price history for a product over the last N days.

        Returns:
            A list of dicts ordered oldest → newest.
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT product, price, scraped_at
                FROM prices
                WHERE product = ? AND scraped_at >= ?
                ORDER BY scraped_at ASC
                """,
                (product, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_products(self) -> list[str]:
        """Return a list of all unique product names in the database."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT product FROM prices ORDER BY product"
            ).fetchall()
            return [r["product"] for r in rows]

    def cleanup_old_records(self, keep_days: int = 90) -> int:
        """
        Delete records older than `keep_days`.

        Returns:
            Number of deleted rows.
        """
        cutoff = (datetime.utcnow() - timedelta(days=keep_days)).isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM prices WHERE scraped_at < ?", (cutoff,)
            )
            conn.commit()
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info("Cleaned up %d records older than %d days", deleted, keep_days)
            return deleted
