.PHONY: install test lint run dry-run clean help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

install-dev: ## Install dev dependencies (includes test tools)
	pip install -e ".[dev]"

test: ## Run test suite
	python -m pytest tests/ -v

coverage: ## Run tests with coverage report
	python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint: ## Run linting checks
	python -m flake8 src/ tests/ --max-line-length=100 --ignore=E501
	python -m black src/ tests/ --check

format: ## Auto-format code with black
	python -m black src/ tests/

run: ## Run the price tracker
	python -m src.main

dry-run: ## Run without sending emails
	python -m src.main --dry-run

verbose: ## Run with debug logging
	python -m src.main --verbose

clean: ## Remove generated files
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf *.egg-info dist build
	find . -name "*.pyc" -delete
