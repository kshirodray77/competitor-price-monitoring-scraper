# 🕷️ Competitor Price Tracker

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready web scraper that monitors competitor product prices on e-commerce sites and sends daily email alerts when prices change. Built with Python, BeautifulSoup, and SMTP.

![Price Tracker Demo](docs/screenshots/demo.png)

---

## Features

- **Multi-site scraping** — Monitor products across Amazon, Best Buy, Walmart, and custom sites
- **Intelligent price detection** — CSS selector-based extraction with fallback strategies
- **Price change alerts** — Configurable thresholds (percentage or absolute) for email notifications
- **Historical tracking** — SQLite database stores full price history with timestamps
- **Beautiful email reports** — HTML-formatted daily digests with price trends (↑↓→)
- **Rate limiting & stealth** — Rotating user agents, request delays, and robots.txt compliance
- **Retry logic** — Exponential backoff on failed requests with configurable max retries
- **Structured logging** — Rotating log files with configurable verbosity
- **Dry run mode** — Test scraping without sending emails
- **CLI interface** — Run manually or schedule via cron/Task Scheduler

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Cron Job /  │────▶│  Scraper Engine   │────▶│  Price Comparator │
│  Scheduler   │     │  (BeautifulSoup)  │     │  (diff engine)    │
└─────────────┘     └──────────────────┘     └────────┬─────────┘
                           │                           │
                    ┌──────▼──────┐            ┌───────▼────────┐
                    │  E-commerce  │            │   SQLite DB    │
                    │  Sites (HTTP)│            │  (price history)│
                    └─────────────┘            └───────┬────────┘
                                                       │
                                               ┌───────▼────────┐
                                               │  SMTP Alerter   │
                                               │  (email digest)  │
                                               └───────┬────────┘
                                                       │
                                               ┌───────▼────────┐
                                               │  Team Inbox     │
                                               └────────────────┘
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/kshirodray77/competitor-price-monitoring-scraper.git
cd competitor-price-monitoring-scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` with your SMTP credentials and target products:

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"   # Use Gmail App Password
  recipients:
    - "team-lead@company.com"

products:
  - name: "Sony WH-1000XM5"
    url: "https://www.example.com/product/sony-wh1000xm5"
    selector: "span.price"
    alert_threshold_pct: 5.0
```

### 3. Run

```bash
# Single run (scrape + compare + alert)
python -m src.main

# Dry run (scrape only, no emails)
python -m src.main --dry-run

# Verbose logging
python -m src.main --verbose

# Run for specific products only
python -m src.main --products "Sony WH-1000XM5" "iPad Air"
```

### 4. Schedule (optional)

**Linux/macOS (cron):**
```bash
# Run daily at 8:00 AM
crontab -e
0 8 * * * cd /path/to/price-tracker && /path/to/venv/bin/python -m src.main >> logs/cron.log 2>&1
```

**Windows (Task Scheduler):**
```powershell
schtasks /create /tn "PriceTracker" /tr "python -m src.main" /sc daily /st 08:00
```

## Configuration Reference

See [`config/config.example.yaml`](config/config.example.yaml) for the full configuration file with comments.

| Key | Description | Default |
|-----|-------------|---------|
| `scraper.delay_range` | Random delay between requests (seconds) | `[1, 3]` |
| `scraper.max_retries` | Max retry attempts per URL | `3` |
| `scraper.timeout` | Request timeout (seconds) | `10` |
| `email.smtp_server` | SMTP server hostname | `smtp.gmail.com` |
| `email.smtp_port` | SMTP server port | `587` |
| `products[].alert_threshold_pct` | Min % change to trigger alert | `5.0` |
| `products[].alert_threshold_abs` | Min absolute $ change to trigger | `null` |

## Project Structure

```
price-tracker/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point & orchestrator
│   ├── scraper.py           # HTTP fetching + BeautifulSoup parsing
│   ├── comparator.py        # Price diff engine + threshold logic
│   ├── alerter.py           # SMTP email composer + sender
│   ├── database.py          # SQLite ORM for price history
│   └── utils.py             # User agents, retry, logging helpers
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py      # Scraper unit tests with mock HTML
│   ├── test_comparator.py   # Comparison logic tests
│   ├── test_alerter.py      # Email formatting tests
│   └── test_database.py     # Database CRUD tests
├── config/
│   ├── config.example.yaml  # Template configuration
│   └── config.yaml          # Your local config (git-ignored)
├── data/
│   └── prices.db            # SQLite database (git-ignored)
├── logs/                    # Log files (git-ignored)
├── docs/
│   └── screenshots/
├── requirements.txt
├── setup.py
├── .gitignore
├── .env.example
├── LICENSE
└── README.md
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_scraper.py -v
```

## Sample Email Alert

The daily digest email includes:

- **Summary header** with date and count of price changes
- **Product cards** showing old price → new price with % change
- **Trend indicators** (🔴 price increase, 🟢 price decrease, ⚪ no change)
- **7-day sparkline** text chart for each product

```
Subject: 🏷️ Price Alert: 3 changes detected — Mar 25, 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📉 Sony WH-1000XM5
   $349.99 → $299.99 (-14.3%)
   7-day: ▁▂▃▅▇▅▃
   Source: amazon.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Scraping | `requests` + `BeautifulSoup4` | HTTP fetching + HTML parsing |
| Storage | `SQLite3` | Price history database |
| Email | `smtplib` + `email.mime` | SMTP alert delivery |
| Config | `PyYAML` | Configuration management |
| CLI | `argparse` | Command-line interface |
| Testing | `pytest` + `unittest.mock` | Unit & integration tests |
| Scheduling | System cron / Task Scheduler | Daily automation |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/add-walmart-support`)
3. Run tests (`python -m pytest tests/ -v`)
4. Commit your changes (`git commit -m 'Add Walmart price selector'`)
5. Push to the branch (`git push origin feature/add-walmart-support`)
6. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with Python 🐍 | BeautifulSoup 🍜 | SMTP 📧
</p>
