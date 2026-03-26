# Contributing to Competitor Price Monitoring Scraper

Thanks for considering contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/kshirodray77/competitor-price-monitoring-scraper.git
cd competitor-price-monitoring-scraper

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run a specific test file
python -m pytest tests/test_scraper.py -v
```

## Code Style

This project uses [Black](https://github.com/psf/black) for code formatting:

```bash
# Check formatting
make lint

# Auto-format
make format
```

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `test:` — Adding or updating tests
- `chore:` — Maintenance tasks
- `refactor:` — Code restructuring without behavior change

## Adding a New E-commerce Site

1. Find the CSS selector for the price element on the product page
2. Add a new entry in `config/config.yaml` under `products:`
3. Test with `python -m src.main --dry-run --products "Your Product"`
4. If the site uses JavaScript rendering, note it in the PR — we may need Playwright

## Pull Request Process

1. Fork the repo and create a feature branch from `main`
2. Write tests for any new functionality
3. Make sure all tests pass: `make test`
4. Update documentation if needed
5. Submit a PR with a clear description of the changes
