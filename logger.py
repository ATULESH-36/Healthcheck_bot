"""
logger.py — Centralized logging configuration for the Health Check Bot.

Provides a pre-configured logger that writes timestamped entries to a
rotating log file (health.log) and to the console.
"""

import logging
from logging.handlers import RotatingFileHandler

from config import LOG_FILE, LOG_LEVEL

# ──────────────────────────────────────────────
# Formatter shared by all handlers
# ──────────────────────────────────────────────
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

# ──────────────────────────────────────────────
# File handler — rotates at 5 MB, keeps 3 backups
# ──────────────────────────────────────────────
_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(_formatter)

# ──────────────────────────────────────────────
# Console handler
# ──────────────────────────────────────────────
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)


def get_logger(name: str = "health_bot") -> logging.Logger:
    """Return a logger configured with file and console handlers.

    Args:
        name: Logger name (defaults to ``health_bot``).

    Returns:
        A ``logging.Logger`` instance ready to use.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)

    return logger
