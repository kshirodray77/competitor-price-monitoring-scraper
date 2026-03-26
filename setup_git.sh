#!/bin/bash
# ============================================================
# Competitor Price Monitoring Scraper — Git History Builder
# ============================================================
# Creates a realistic commit history with 15 incremental commits.
#
# USAGE:
#   1. cd into the project folder
#   2. Run: bash setup_git.sh
#   3. Then push:
#      git remote add origin https://github.com/kshirodray77/competitor-price-monitoring-scraper.git
#      git push -u origin main
# ============================================================

set -e

# ── Initialize repo ──────────────────────────────────────────
git init
git branch -M main

git config user.name "Kshirod"
git config user.email "ray.kshirod@gmail.com"

echo "🚀 Building commit history (15 commits)..."

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 1: Foundation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Commit 1 ─────────────────────────────────────────────────
git add .gitignore LICENSE
git commit -m "chore: initialize repository with license and gitignore

- Add MIT license
- Add .gitignore for Python, venv, IDE, and project-specific files"

echo "  ✓  1/15  repo init"

# ── Commit 2 ─────────────────────────────────────────────────
git add requirements.txt setup.py .env.example
git commit -m "chore: add project dependencies and package config

- Add requirements.txt with requests, beautifulsoup4, lxml, PyYAML
- Add setup.py with console_scripts entry point
- Add .env.example for SMTP credential overrides"

echo "  ✓  2/15  dependencies"

# ── Commit 3 ─────────────────────────────────────────────────
git add config/config.example.yaml
git commit -m "feat: add YAML configuration system

- Add example config with scraper, email, and product settings
- Support per-product CSS selectors with fallback selectors
- Configurable alert thresholds (percentage and absolute)
- Document all config keys with inline comments"

echo "  ✓  3/15  configuration"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 2: Core modules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Commit 4 ─────────────────────────────────────────────────
git add src/__init__.py src/utils.py
git commit -m "feat: add utility module with user-agent rotation and retry logic

- Implement rotating User-Agent pool (5 browser profiles)
- Add @retry decorator with exponential backoff and jitter
- Add parse_price() supporting multiple currency formats
- Add rotating file handler logger with configurable verbosity
- Add random_delay() helper for polite rate limiting"

echo "  ✓  4/15  utilities"

# ── Commit 5 ─────────────────────────────────────────────────
git add src/database.py
git commit -m "feat: add SQLite database layer for price history

- Create prices table with product, url, price, currency, timestamp
- Add composite index on (product, scraped_at) for fast lookups
- Implement CRUD: save_price, get_latest, get_previous, get_history
- Add cleanup_old_records() with configurable retention (90 days)
- Support custom currency codes (default: USD)"

echo "  ✓  5/15  database"

# ── Commit 6 ─────────────────────────────────────────────────
git add src/scraper.py
git commit -m "feat: implement BeautifulSoup scraper with fallback selectors

- Add PriceScraper class with configurable timeout and delay
- Parse HTML using lxml backend for performance
- Try primary CSS selector, then iterate fallback selectors
- Return structured ScrapeResult dataclass per product
- Integrate @retry for transient HTTP failures
- Support context manager protocol for session cleanup"

echo "  ✓  6/15  scraper"

# ── Commit 7 ─────────────────────────────────────────────────
git add src/comparator.py
git commit -m "feat: add price comparison engine with threshold alerts

- Diff scraped prices against stored history
- Support both percentage and absolute change thresholds
- Generate PriceChange objects with direction and trend metadata
- Add sparkline text chart from 7-day price history
- Skip failed scrapes gracefully, log first-time products"

echo "  ✓  7/15  comparator"

# ── Commit 8 ─────────────────────────────────────────────────
git add src/alerter.py
git commit -m "feat: add SMTP alerter with HTML email digest

- Compose HTML email with styled product cards and badges
- Include sparkline trend + source domain per product
- Add plaintext fallback for non-HTML email clients
- Support TLS encryption and Gmail App Password auth
- Handle SMTP auth errors with actionable error messages
- Dynamic subject: summarize drops and increases"

echo "  ✓  8/15  alerter"

# ── Commit 9 ─────────────────────────────────────────────────
git add src/main.py
git commit -m "feat: add CLI entry point to orchestrate the pipeline

- Wire scrape -> compare -> alert into a single run
- Add --dry-run flag to test without sending emails
- Add --verbose flag for debug-level logging
- Add --products filter to target specific items
- Load config from YAML with .env fallback for secrets
- Print run summary: scraped/total, changes, alerts sent"

echo "  ✓  9/15  CLI"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3: Testing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Commit 10 ────────────────────────────────────────────────
git add tests/__init__.py tests/test_utils.py tests/test_database.py
git commit -m "test: add unit tests for utils and database modules

- test_utils: 16 price parser cases (USD, EUR, INR, commas, edge
  cases), header rotation randomness verification
- test_database: save/retrieve, latest vs previous, history range,
  cleanup retention, currency support, row ID verification"

echo "  ✓ 10/15  tests (utils + db)"

# ── Commit 11 ────────────────────────────────────────────────
git add tests/test_scraper.py tests/test_comparator.py tests/test_alerter.py
git commit -m "test: add unit tests for scraper, comparator, and alerter

- test_scraper: mock HTML fixtures (Amazon, BestBuy style),
  fallback selector matching, HTTP error handling
- test_comparator: threshold logic, first-scrape skip,
  percentage vs absolute triggers, failed scrape filtering
- test_alerter: HTML/plaintext composition, subject line,
  SMTP mock send, auth failure, multi-product digest"

echo "  ✓ 11/15  tests (scraper + comparator + alerter)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4: Polish & DevOps
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Commit 12 ────────────────────────────────────────────────
git add pyproject.toml Makefile
git commit -m "chore: add Makefile and pyproject.toml for dev workflow

- Add Makefile with targets: test, coverage, lint, format, run, clean
- Add pyproject.toml with black, pytest, and coverage config
- Set minimum coverage threshold to 80%
- Set black line-length to 100"

echo "  ✓ 12/15  dev tooling"

# ── Commit 13 ────────────────────────────────────────────────
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for automated testing

- Run pytest on push and PR to main
- Test matrix: Python 3.9, 3.10, 3.11, 3.12
- Cache pip dependencies for faster CI runs
- Upload coverage report as artifact on 3.12"

echo "  ✓ 13/15  CI pipeline"

# ── Commit 14 ────────────────────────────────────────────────
git add CONTRIBUTING.md
git commit -m "docs: add contributing guide

- Document dev setup with virtualenv instructions
- Explain conventional commit convention
- Add instructions for adding new e-commerce sites
- Describe PR process and code style expectations"

echo "  ✓ 14/15  contributing guide"

# ── Commit 15 ────────────────────────────────────────────────
git add README.md
git commit -m "docs: add comprehensive README with architecture and usage

- Add project overview, feature list, and tech stack table
- Add ASCII architecture diagram
- Document quick start, CLI flags, and cron scheduling
- Add config reference table and sample email output
- Add project structure tree and test instructions"

echo "  ✓ 15/15  README"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "✅ All 15 commits created!"
echo ""
echo "📋 Commit log:"
git log --oneline
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NEXT STEPS — run these two commands:"
echo ""
echo "  git remote add origin https://github.com/kshirodray77/competitor-price-monitoring-scraper.git"
echo "  git push -u origin main"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
