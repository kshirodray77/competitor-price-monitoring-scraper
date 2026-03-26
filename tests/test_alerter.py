"""Tests for the email alerter module."""

import pytest
from unittest.mock import patch, MagicMock

from src.alerter import EmailAlerter
from src.comparator import PriceChange


class TestEmailAlerter:
    """Unit tests for email composition and sending."""

    def setup_method(self):
        self.alerter = EmailAlerter(
            smtp_server="smtp.test.com",
            smtp_port=587,
            sender_email="test@test.com",
            sender_password="secret",
            recipients=["team@test.com"],
        )

    def _make_change(self, direction="down", pct=-15.0):
        return PriceChange(
            product="Sony WH-1000XM5",
            url="https://www.example.com/product/sony",
            old_price=349.99,
            new_price=299.99 if direction == "down" else 399.99,
            absolute_change=-50.0 if direction == "down" else 50.0,
            percent_change=pct,
            direction=direction,
            history=[
                {"price": 349.99, "scraped_at": "2026-03-22"},
                {"price": 339.99, "scraped_at": "2026-03-23"},
                {"price": 299.99, "scraped_at": "2026-03-24"},
            ],
        )

    def test_subject_line_with_drops(self):
        """Subject line should mention price drops."""
        changes = [self._make_change(direction="down")]
        subject = self.alerter._build_subject(changes)
        assert "1 drop" in subject
        assert "Price Alert" in subject

    def test_subject_line_with_increases(self):
        """Subject line should mention price increases."""
        changes = [self._make_change(direction="up", pct=15.0)]
        subject = self.alerter._build_subject(changes)
        assert "1 increase" in subject

    def test_html_body_contains_product(self):
        """HTML body should contain the product name and prices."""
        changes = [self._make_change()]
        html = self.alerter._build_html(changes)
        assert "Sony WH-1000XM5" in html
        assert "$349.99" in html
        assert "$299.99" in html
        assert "Price Drop" in html

    def test_html_body_contains_source_domain(self):
        """HTML body should show the source domain."""
        changes = [self._make_change()]
        html = self.alerter._build_html(changes)
        assert "www.example.com" in html

    def test_plaintext_fallback(self):
        """Plain text body should be a readable fallback."""
        changes = [self._make_change()]
        text = self.alerter._build_plaintext(changes)
        assert "Sony WH-1000XM5" in text
        assert "349.99" in text
        assert "299.99" in text

    def test_no_changes_skips_email(self):
        """Should not send email when there are no changes."""
        result = self.alerter.send_alert([])
        assert result is False

    def test_no_recipients_skips_email(self):
        """Should not send email when no recipients are configured."""
        self.alerter.recipients = []
        changes = [self._make_change()]
        result = self.alerter.send_alert(changes)
        assert result is False

    @patch("smtplib.SMTP")
    def test_successful_email_send(self, mock_smtp_class):
        """Should return True when email is sent successfully."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        changes = [self._make_change()]
        result = self.alerter.send_alert(changes)
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "secret")
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_smtp_auth_failure(self, mock_smtp_class):
        """Should handle SMTP auth failure gracefully."""
        import smtplib

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad creds")
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        changes = [self._make_change()]
        result = self.alerter.send_alert(changes)
        assert result is False

    def test_multiple_changes_in_digest(self):
        """Email should include all changes in a single digest."""
        changes = [
            self._make_change(direction="down", pct=-14.3),
            PriceChange(
                product="iPad Air",
                url="https://www.example.com/product/ipad",
                old_price=599.0, new_price=649.0,
                absolute_change=50.0, percent_change=8.3,
                direction="up", history=[],
            ),
        ]
        html = self.alerter._build_html(changes)
        assert "Sony WH-1000XM5" in html
        assert "iPad Air" in html
        assert "2 products changed" in html
