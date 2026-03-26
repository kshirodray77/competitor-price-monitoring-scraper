"""Tests for the CLI entry point and pipeline orchestration."""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.main import load_config, parse_args


class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_default_args(self):
        """Should use default config path and no flags."""
        with patch("sys.argv", ["prog"]):
            args = parse_args()
            assert args.config == "config/config.yaml"
            assert args.dry_run is False
            assert args.verbose is False
            assert args.products is None

    def test_dry_run_flag(self):
        """Should parse --dry-run flag."""
        with patch("sys.argv", ["prog", "--dry-run"]):
            args = parse_args()
            assert args.dry_run is True

    def test_verbose_flag(self):
        """Should parse --verbose flag."""
        with patch("sys.argv", ["prog", "--verbose"]):
            args = parse_args()
            assert args.verbose is True

    def test_custom_config(self):
        """Should parse --config with custom path."""
        with patch("sys.argv", ["prog", "--config", "custom.yaml"]):
            args = parse_args()
            assert args.config == "custom.yaml"

    def test_product_filter(self):
        """Should parse --products with multiple names."""
        with patch("sys.argv", ["prog", "--products", "iPad Air", "Sony XM5"]):
            args = parse_args()
            assert args.products == ["iPad Air", "Sony XM5"]

    def test_all_flags_combined(self):
        """Should handle all flags together."""
        with patch("sys.argv", [
            "prog", "--dry-run", "--verbose",
            "--config", "test.yaml",
            "--products", "Widget"
        ]):
            args = parse_args()
            assert args.dry_run is True
            assert args.verbose is True
            assert args.config == "test.yaml"
            assert args.products == ["Widget"]


class TestLoadConfig:
    """Tests for config loading."""

    def test_missing_config_exits(self):
        """Should exit with error if config file is missing."""
        with pytest.raises(SystemExit):
            load_config("/nonexistent/config.yaml")

    def test_load_valid_config(self, tmp_path):
        """Should load a valid YAML config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
scraper:
  timeout: 15
  delay_range: [2, 5]
email:
  smtp_server: smtp.test.com
  smtp_port: 587
  sender_email: test@test.com
  sender_password: secret
  recipients:
    - team@test.com
products:
  - name: Test Product
    url: https://example.com
    selector: span.price
""")
        config = load_config(str(config_file))
        assert config["scraper"]["timeout"] == 15
        assert config["email"]["smtp_server"] == "smtp.test.com"
        assert len(config["products"]) == 1

    def test_env_override(self, tmp_path):
        """Should allow .env to override email settings."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
products:
  - name: Test
    url: https://example.com
    selector: span.price
""")
        with patch.dict(os.environ, {
            "SMTP_SERVER": "smtp.override.com",
            "SENDER_EMAIL": "override@test.com",
        }):
            config = load_config(str(config_file))
            assert config["email"]["smtp_server"] == "smtp.override.com"
            assert config["email"]["sender_email"] == "override@test.com"
