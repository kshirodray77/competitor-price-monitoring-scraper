"""SMTP email alerter: composes and sends HTML price alert digests."""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from urllib.parse import urlparse

from src.comparator import PriceChange

logger = logging.getLogger("price_tracker.alerter")


class EmailAlerter:
    """
    Composes and sends HTML email digests for price changes.

    Connects to an SMTP server with TLS and sends a formatted
    daily digest to configured recipients.
    """

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: str = "",
        sender_password: str = "",
        recipients: Optional[list[str]] = None,
        use_tls: bool = True,
        subject_prefix: str = "🏷️ Price Alert",
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipients = recipients or []
        self.use_tls = use_tls
        self.subject_prefix = subject_prefix

    def send_alert(self, changes: list[PriceChange]) -> bool:
        """
        Send a price alert email for the given changes.

        Args:
            changes: List of PriceChange objects to include in the digest.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if not changes:
            logger.info("No price changes to report — skipping email.")
            return False

        if not self.recipients:
            logger.warning("No recipients configured — skipping email.")
            return False

        subject = self._build_subject(changes)
        html_body = self._build_html(changes)
        text_body = self._build_plaintext(changes)

        msg = MIMEMultipart("alternative")
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject

        # Attach both plain text and HTML (email clients prefer HTML)
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email, self.recipients, msg.as_string()
                )
            logger.info(
                "Alert email sent to %d recipients: %s",
                len(self.recipients),
                ", ".join(self.recipients),
            )
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed. Check your email credentials. "
                "For Gmail, use an App Password: "
                "https://support.google.com/accounts/answer/185833"
            )
            return False
        except smtplib.SMTPException as exc:
            logger.error("SMTP error sending alert: %s", exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error sending alert: %s", exc)
            return False

    def _build_subject(self, changes: list[PriceChange]) -> str:
        """Build the email subject line."""
        date_str = datetime.now().strftime("%b %d, %Y")
        drops = sum(1 for c in changes if c.direction == "down")
        increases = sum(1 for c in changes if c.direction == "up")

        parts = []
        if drops:
            parts.append(f"{drops} drop{'s' if drops > 1 else ''}")
        if increases:
            parts.append(f"{increases} increase{'s' if increases > 1 else ''}")

        summary = ", ".join(parts) if parts else f"{len(changes)} changes"
        return f"{self.subject_prefix}: {summary} — {date_str}"

    def _build_html(self, changes: list[PriceChange]) -> str:
        """Build an HTML email body with styled product cards."""
        date_str = datetime.now().strftime("%B %d, %Y")
        cards_html = "\n".join(self._render_card(c) for c in changes)

        return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:
  -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:24px;">

  <!-- Header -->
  <div style="background:#18181b;color:white;padding:24px 28px;
    border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:20px;font-weight:600;">
      {self.subject_prefix}
    </h1>
    <p style="margin:8px 0 0;font-size:14px;color:#a1a1aa;">
      {date_str} &middot; {len(changes)} product{'s' if len(changes) != 1 else ''} changed
    </p>
  </div>

  <!-- Product Cards -->
  <div style="background:white;padding:4px 0;border-radius:0 0 12px 12px;
    border:1px solid #e4e4e7;border-top:none;">
    {cards_html}
  </div>

  <!-- Footer -->
  <p style="text-align:center;font-size:12px;color:#a1a1aa;margin-top:20px;">
    Sent by Price Tracker &middot;
    <a href="#" style="color:#a1a1aa;">Unsubscribe</a>
  </p>

</div>
</body>
</html>"""

    def _render_card(self, change: PriceChange) -> str:
        """Render a single product card in HTML."""
        # Color coding
        if change.direction == "down":
            badge_bg, badge_color, badge_text = "#dcfce7", "#166534", "Price Drop"
            arrow = "↓"
        elif change.direction == "up":
            badge_bg, badge_color, badge_text = "#fee2e2", "#991b1b", "Price Increase"
            arrow = "↑"
        else:
            badge_bg, badge_color, badge_text = "#f4f4f5", "#52525b", "No Change"
            arrow = "→"

        source = urlparse(change.url).netloc
        sparkline = change.sparkline

        return f"""\
    <div style="padding:20px 28px;border-bottom:1px solid #f4f4f5;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <span style="background:{badge_bg};color:{badge_color};
            padding:2px 8px;border-radius:4px;font-size:11px;
            font-weight:600;text-transform:uppercase;">{badge_text}</span>
        </div>
      </div>
      <h2 style="margin:12px 0 4px;font-size:16px;font-weight:600;color:#18181b;">
        {change.trend_indicator} {change.product}
      </h2>
      <p style="margin:0;font-size:28px;font-weight:700;color:#18181b;">
        ${change.old_price:,.2f}
        <span style="color:#a1a1aa;font-size:18px;font-weight:400;">{arrow}</span>
        ${change.new_price:,.2f}
        <span style="font-size:14px;font-weight:500;color:{badge_color};
          margin-left:8px;">({change.percent_change:+.1f}%)</span>
      </p>
      <p style="margin:8px 0 0;font-size:13px;color:#71717a;">
        7-day: {sparkline} &middot; Source:
        <a href="{change.url}" style="color:#3b82f6;text-decoration:none;">
          {source}</a>
      </p>
    </div>"""

    def _build_plaintext(self, changes: list[PriceChange]) -> str:
        """Build a plain-text fallback for email clients that don't support HTML."""
        date_str = datetime.now().strftime("%B %d, %Y")
        lines = [
            f"Price Alert — {date_str}",
            f"{len(changes)} price change(s) detected",
            "=" * 50,
            "",
        ]

        for change in changes:
            source = urlparse(change.url).netloc
            lines.extend([
                f"{change.trend_indicator} {change.product}",
                f"   ${change.old_price:,.2f} → ${change.new_price:,.2f} "
                f"({change.percent_change:+.1f}%)",
                f"   7-day: {change.sparkline}",
                f"   Source: {source}",
                f"   URL: {change.url}",
                "-" * 50,
            ])

        lines.append("\nSent by Price Tracker")
        return "\n".join(lines)
