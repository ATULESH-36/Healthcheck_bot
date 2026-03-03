"""
alerts.py — Alerting module for the Server Health Check Bot.

Provides functions to send Slack and email notifications with a
built-in cooldown system to prevent alert spamming.
"""

import json
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

import requests

from config import (
    ALERT_COOLDOWN_SECONDS,
    EMAIL_PASSWORD,
    EMAIL_RECEIVER,
    EMAIL_SENDER,
    SLACK_WEBHOOK_URL,
    SMTP_PORT,
    SMTP_SERVER,
)
from logger import get_logger

logger = get_logger("alerts")

# ──────────────────────────────────────────────
# Cooldown tracker  {alert_key: last_sent_epoch}
# ──────────────────────────────────────────────
_cooldown_tracker: Dict[str, float] = {}


def _can_send(alert_key: str) -> bool:
    """Check whether an alert is allowed based on the cooldown window.

    Args:
        alert_key: A unique identifier for the alert type
                   (e.g. ``"cpu_high"``, ``"disk_high"``).

    Returns:
        ``True`` if enough time has elapsed since the last alert with
        the same key, ``False`` otherwise.
    """
    now = time.time()
    last_sent = _cooldown_tracker.get(alert_key, 0.0)

    if now - last_sent < ALERT_COOLDOWN_SECONDS:
        logger.info(
            "Alert '%s' suppressed (cooldown active, %ds remaining).",
            alert_key,
            int(ALERT_COOLDOWN_SECONDS - (now - last_sent)),
        )
        return False

    _cooldown_tracker[alert_key] = now
    return True


def reset_cooldown() -> None:
    """Reset the cooldown tracker — useful for testing."""
    _cooldown_tracker.clear()


# ──────────────────────────────────────────────
# Slack alert
# ──────────────────────────────────────────────
def send_slack_alert(message: str, alert_key: str = "general") -> bool:
    """Post a message to a Slack channel via Incoming Webhook.

    Args:
        message:   The alert text to send.
        alert_key: Unique key used for cooldown tracking.

    Returns:
        ``True`` if the message was sent successfully, ``False`` otherwise.
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured — skipping Slack alert.")
        return False

    if not _can_send(f"slack_{alert_key}"):
        return False

    try:
        payload = {"text": f":rotating_light: *Health Check Alert*\n{message}"}
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            logger.info("Slack alert sent: %s", message)
            return True

        logger.error(
            "Slack API returned status %d: %s",
            response.status_code,
            response.text,
        )
        return False

    except requests.RequestException as exc:
        logger.error("Failed to send Slack alert: %s", exc)
        return False


# ──────────────────────────────────────────────
# Email alert
# ──────────────────────────────────────────────
def send_email_alert(subject: str, body: str, alert_key: str = "general") -> bool:
    """Send an email alert via SMTP with TLS.

    Args:
        subject:   Email subject line.
        body:      Email body (plain text).
        alert_key: Unique key used for cooldown tracking.

    Returns:
        ``True`` if the email was sent successfully, ``False`` otherwise.
    """
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        logger.warning("Email credentials not fully configured — skipping email alert.")
        return False

    if not _can_send(f"email_{alert_key}"):
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        logger.info("Email alert sent: %s", subject)
        return True

    except smtplib.SMTPException as exc:
        logger.error("Failed to send email alert: %s", exc)
        return False

    except OSError as exc:
        logger.error("Network error while sending email: %s", exc)
        return False


# ──────────────────────────────────────────────
# Convenience dispatcher
# ──────────────────────────────────────────────
def send_alert(message: str, alert_key: str = "general") -> None:
    """Send an alert via Slack and email (as backup).

    Attempts Slack first; if that fails, falls back to email.

    Args:
        message:   Alert message body.
        alert_key: Unique key used for cooldown tracking.
    """
    slack_ok = send_slack_alert(message, alert_key=alert_key)

    if not slack_ok:
        logger.info("Falling back to email alert for key '%s'.", alert_key)
        send_email_alert(
            subject=f"[Health Bot] {alert_key.upper()} Alert",
            body=message,
            alert_key=alert_key,
        )
