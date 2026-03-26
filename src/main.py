"""CLI entry point: orchestrates scrape → compare → alert pipeline."""

import argparse
import sys
import logging
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.scraper import PriceScraper
from src.database import PriceDatabase
from src.comparator import PriceComparator
from src.alerter import EmailAlerter
from src.utils import setup_logging

logger = logging.getLogger("price_tracker.main")

DEFAULT_CONFIG = "config/config.yaml"


def load_config(config_path: str) -> dict:
    """
    Load and validate the YAML configuration file.

    Falls back to environment variables for email credentials
    if they aren't set in the config file.
    """
    path = Path(config_path)
    if not path.exists():
        print(f"Error: Config file not found: {path}")
        print(f"Copy config/config.example.yaml to {path} and fill in your values.")
        sys.exit(1)

    with open(path) as f:
        config = yaml.safe_load(f)

    # Allow .env overrides for sensitive values
    load_dotenv()
    import os

    email_cfg = config.get("email", {})
    email_cfg.setdefault("smtp_server", os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    email_cfg.setdefault("smtp_port", int(os.getenv("SMTP_PORT", "587")))
    email_cfg.setdefault("sender_email", os.getenv("SENDER_EMAIL", ""))
    email_cfg.setdefault("sender_password", os.getenv("SENDER_PASSWORD", ""))

    env_recipients = os.getenv("RECIPIENTS")
    if env_recipients and "recipients" not in email_cfg:
        email_cfg["recipients"] = [r.strip() for r in env_recipients.split(",")]

    config["email"] = email_cfg
    return config


def run_pipeline(config: dict, dry_run: bool = False, product_filter: list[str] = None):
    """
    Execute the full scrape → compare → alert pipeline.

    Args:
        config: Parsed configuration dictionary.
        dry_run: If True, scrape and compare but don't send emails.
        product_filter: If set, only process products whose names are in this list.
    """
    # ── Setup ────────────────────────────────────────────────
    scraper_cfg = config.get("scraper", {})
    email_cfg = config.get("email", {})
    db_cfg = config.get("database", {})
    products = config.get("products", [])

    if not products:
        logger.error("No products configured. Add products to config.yaml.")
        sys.exit(1)

    # Optional filter
    if product_filter:
        filter_set = set(product_filter)
        products = [p for p in products if p["name"] in filter_set]
        if not products:
            logger.error("No matching products found for filter: %s", product_filter)
            sys.exit(1)

    logger.info("=" * 60)
    logger.info("Price Tracker — starting pipeline")
    logger.info("Products to scrape: %d", len(products))
    logger.info("Dry run: %s", dry_run)
    logger.info("=" * 60)

    # ── Step 1: Scrape ───────────────────────────────────────
    logger.info("Step 1/3: Scraping product prices...")
    with PriceScraper(
        timeout=scraper_cfg.get("timeout", 10),
        delay_range=tuple(scraper_cfg.get("delay_range", [1, 3])),
        max_retries=scraper_cfg.get("max_retries", 3),
    ) as scraper:
        results = scraper.scrape_all(products)

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    if failed:
        logger.warning(
            "Failed to scrape %d product(s): %s",
            len(failed),
            ", ".join(r.product for r in failed),
        )

    if not successful:
        logger.error("All scrapes failed. Exiting.")
        sys.exit(1)

    # ── Step 2: Compare ──────────────────────────────────────
    logger.info("Step 2/3: Comparing prices against history...")
    db = PriceDatabase(db_path=db_cfg.get("path", "data/prices.db"))
    comparator = PriceComparator(database=db)
    changes = comparator.compare(results, products)

    # Periodic cleanup
    db.cleanup_old_records(keep_days=90)

    # ── Step 3: Alert ────────────────────────────────────────
    if dry_run:
        logger.info("Step 3/3: Dry run — skipping email.")
        if changes:
            logger.info("Would have sent alert for %d product(s):", len(changes))
            for c in changes:
                logger.info(
                    "  %s %s: $%.2f → $%.2f (%+.1f%%)",
                    c.trend_indicator, c.product,
                    c.old_price, c.new_price, c.percent_change,
                )
        else:
            logger.info("No price changes exceeded thresholds.")
    else:
        logger.info("Step 3/3: Sending email alert...")
        alerter = EmailAlerter(
            smtp_server=email_cfg.get("smtp_server", "smtp.gmail.com"),
            smtp_port=email_cfg.get("smtp_port", 587),
            sender_email=email_cfg.get("sender_email", ""),
            sender_password=email_cfg.get("sender_password", ""),
            recipients=email_cfg.get("recipients", []),
            use_tls=email_cfg.get("use_tls", True),
            subject_prefix=email_cfg.get("subject_prefix", "🏷️ Price Alert"),
        )
        alerter.send_alert(changes)

    # ── Summary ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Pipeline complete.")
    logger.info(
        "  Scraped: %d/%d  |  Changes: %d  |  Alerts: %s",
        len(successful), len(results), len(changes),
        "sent" if (changes and not dry_run) else "none",
    )
    logger.info("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Competitor Price Tracker — scrape, compare, alert.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python -m src.main                          # Full run
  python -m src.main --dry-run                # Scrape only, no email
  python -m src.main --verbose                # Debug logging
  python -m src.main --products "iPad Air"    # Filter products
        """,
    )
    parser.add_argument(
        "--config", default=DEFAULT_CONFIG,
        help=f"Path to config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Scrape and compare, but don't send emails",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--products", nargs="+",
        help="Only scrape specific products (by name)",
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Load config
    config = load_config(args.config)

    # Setup logging
    log_cfg = config.get("logging", {})
    level = "DEBUG" if args.verbose else log_cfg.get("level", "INFO")
    setup_logging(
        level=level,
        log_file=log_cfg.get("file"),
        max_bytes=log_cfg.get("max_bytes", 5_242_880),
        backup_count=log_cfg.get("backup_count", 3),
    )

    # Run
    run_pipeline(
        config=config,
        dry_run=args.dry_run,
        product_filter=args.products,
    )


if __name__ == "__main__":
    main()
