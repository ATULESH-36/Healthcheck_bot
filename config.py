"""
config.py — Configuration module for the Server Health Check Bot.

Loads environment variables from a .env file and exposes all
configuration constants used across the project.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ──────────────────────────────────────────────
# System-metric thresholds (percentage)
# ──────────────────────────────────────────────
CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", "80"))
MEMORY_THRESHOLD: float = float(os.getenv("MEMORY_THRESHOLD", "85"))
DISK_THRESHOLD: float = float(os.getenv("DISK_THRESHOLD", "90"))

# ──────────────────────────────────────────────
# Target servers / endpoints to monitor
# ──────────────────────────────────────────────
PING_HOST: str = os.getenv("PING_HOST", "8.8.8.8")
HEALTH_CHECK_URL: str = os.getenv("HEALTH_CHECK_URL", "https://example.com/health")

# ──────────────────────────────────────────────
# Slack configuration
# ──────────────────────────────────────────────
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

# ──────────────────────────────────────────────
# Email (SMTP) configuration
# ──────────────────────────────────────────────
SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER: str = os.getenv("EMAIL_RECEIVER", "")

# ──────────────────────────────────────────────
# Alert cooldown (seconds)
# ──────────────────────────────────────────────
ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "600"))

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOG_FILE: str = os.getenv("LOG_FILE", "health.log")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
