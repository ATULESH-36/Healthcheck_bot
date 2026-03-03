"""
monitor.py — Core monitoring module for the Server Health Check Bot.

Collects system metrics, pings a server, checks HTTP endpoint health,
compares results against thresholds, and dispatches alerts.

Usage (standalone)::

    python monitor.py

Schedule via Cron::

    */5 * * * * /usr/bin/python3 /path/to/monitor.py
"""

import platform
import subprocess
import sys

import psutil
import requests

from alerts import send_alert
from config import (
    CPU_THRESHOLD,
    DISK_THRESHOLD,
    HEALTH_CHECK_URL,
    MEMORY_THRESHOLD,
    PING_HOST,
)
from logger import get_logger

logger = get_logger("monitor")


# ──────────────────────────────────────────────
# System metric checks
# ──────────────────────────────────────────────
def check_cpu() -> float:
    """Check current CPU usage and alert if it exceeds the threshold.

    Returns:
        Current CPU usage percentage.
    """
    usage = psutil.cpu_percent(interval=1)
    logger.info("CPU usage: %.1f%% (threshold: %.1f%%)", usage, CPU_THRESHOLD)

    if usage > CPU_THRESHOLD:
        send_alert(
            f"🔴 *CPU usage critical:* {usage:.1f}% (threshold: {CPU_THRESHOLD}%)",
            alert_key="cpu_high",
        )
    return usage


def check_memory() -> float:
    """Check current memory usage and alert if it exceeds the threshold.

    Returns:
        Current memory usage percentage.
    """
    mem = psutil.virtual_memory()
    usage = mem.percent
    logger.info("Memory usage: %.1f%% (threshold: %.1f%%)", usage, MEMORY_THRESHOLD)

    if usage > MEMORY_THRESHOLD:
        send_alert(
            f"🔴 *Memory usage critical:* {usage:.1f}% "
            f"(used {mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB, "
            f"threshold: {MEMORY_THRESHOLD}%)",
            alert_key="memory_high",
        )
    return usage


def check_disk(path: str = "/") -> float:
    """Check current disk usage and alert if it exceeds the threshold.

    Args:
        path: Mount point / drive to check (defaults to ``/``).

    Returns:
        Current disk usage percentage.
    """
    disk = psutil.disk_usage(path)
    usage = disk.percent
    logger.info("Disk usage (%s): %.1f%% (threshold: %.1f%%)", path, usage, DISK_THRESHOLD)

    if usage > DISK_THRESHOLD:
        send_alert(
            f"🔴 *Disk usage critical ({path}):* {usage:.1f}% "
            f"(used {disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB, "
            f"threshold: {DISK_THRESHOLD}%)",
            alert_key="disk_high",
        )
    return usage


# ──────────────────────────────────────────────
# Network checks
# ──────────────────────────────────────────────
def ping_server(host: str = PING_HOST) -> bool:
    """Ping a server to verify network connectivity.

    Uses the platform-appropriate flag (``-n`` on Windows, ``-c`` on Unix).

    Args:
        host: Hostname or IP address to ping.

    Returns:
        ``True`` if the ping succeeds, ``False`` otherwise.
    """
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"

    try:
        result = subprocess.run(
            ["ping", count_flag, "1", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        success = result.returncode == 0

        if success:
            logger.info("Ping to %s: SUCCESS", host)
        else:
            logger.warning("Ping to %s: FAILED", host)
            send_alert(
                f"🔴 *Server unreachable:* Ping to `{host}` failed.",
                alert_key="ping_fail",
            )
        return success

    except subprocess.TimeoutExpired:
        logger.error("Ping to %s timed out.", host)
        send_alert(
            f"🔴 *Server unreachable:* Ping to `{host}` timed out.",
            alert_key="ping_fail",
        )
        return False

    except OSError as exc:
        logger.error("Ping command failed: %s", exc)
        send_alert(
            f"🔴 *Ping error:* Could not execute ping to `{host}` — {exc}",
            alert_key="ping_fail",
        )
        return False


def check_endpoint(url: str = HEALTH_CHECK_URL) -> bool:
    """Check whether an HTTP endpoint returns a 200 OK response.

    Args:
        url: The URL to check.

    Returns:
        ``True`` if the endpoint responds with status 200, ``False`` otherwise.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logger.info("Endpoint %s: HEALTHY (200 OK)", url)
            return True

        logger.warning(
            "Endpoint %s: UNHEALTHY (status %d)", url, response.status_code
        )
        send_alert(
            f"🔴 *Endpoint unhealthy:* `{url}` returned status {response.status_code}.",
            alert_key="endpoint_unhealthy",
        )
        return False

    except requests.ConnectionError:
        logger.error("Endpoint %s: CONNECTION REFUSED", url)
        send_alert(
            f"🔴 *Endpoint down:* Could not connect to `{url}`.",
            alert_key="endpoint_unhealthy",
        )
        return False

    except requests.Timeout:
        logger.error("Endpoint %s: TIMED OUT", url)
        send_alert(
            f"🔴 *Endpoint timeout:* `{url}` did not respond within 10 s.",
            alert_key="endpoint_unhealthy",
        )
        return False

    except requests.RequestException as exc:
        logger.error("Endpoint check failed for %s: %s", url, exc)
        send_alert(
            f"🔴 *Endpoint error:* `{url}` — {exc}",
            alert_key="endpoint_unhealthy",
        )
        return False


# ──────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────
def run_health_check() -> dict:
    """Run all health checks and return a summary report.

    Returns:
        A dictionary with keys for each check and their results.
    """
    logger.info("=" * 60)
    logger.info("Starting health check run")
    logger.info("=" * 60)

    # Determine disk path based on platform
    disk_path = "C:\\" if platform.system().lower() == "windows" else "/"

    report = {
        "cpu_percent": check_cpu(),
        "memory_percent": check_memory(),
        "disk_percent": check_disk(path=disk_path),
        "ping_ok": ping_server(),
        "endpoint_ok": check_endpoint(),
    }

    logger.info("Health check complete: %s", report)
    logger.info("=" * 60)
    return report


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    try:
        run_health_check()
    except KeyboardInterrupt:
        logger.info("Health check interrupted by user.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        logger.critical("Unhandled exception during health check: %s", exc, exc_info=True)
        send_alert(
            f"🔴 *Health Bot crashed:* {exc}",
            alert_key="bot_crash",
        )
        sys.exit(1)
