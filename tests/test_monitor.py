"""
test_monitor.py — Unit tests for the Server Health Check Bot.

Tests cover threshold-based alerting logic, API health check handling,
ping behaviour, and the alert cooldown system. All external calls are
mocked so no real network or system access is needed.
"""

import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_cooldown():
    """Reset the alert cooldown tracker before every test."""
    from alerts import reset_cooldown

    reset_cooldown()
    yield
    reset_cooldown()


# ─────────────────────────────────────────────────────
# CPU threshold tests
# ─────────────────────────────────────────────────────


@patch("monitor.send_alert")
@patch("monitor.psutil")
def test_cpu_below_threshold_no_alert(mock_psutil, mock_alert):
    """No alert should fire when CPU is below the threshold."""
    mock_psutil.cpu_percent.return_value = 50.0

    from monitor import check_cpu

    result = check_cpu()

    assert result == 50.0
    mock_alert.assert_not_called()


@patch("monitor.send_alert")
@patch("monitor.psutil")
def test_cpu_above_threshold_triggers_alert(mock_psutil, mock_alert):
    """An alert should fire when CPU exceeds the threshold."""
    mock_psutil.cpu_percent.return_value = 95.0

    from monitor import check_cpu

    result = check_cpu()

    assert result == 95.0
    mock_alert.assert_called_once()
    call_args = mock_alert.call_args
    assert "95.0%" in call_args[0][0]


# ─────────────────────────────────────────────────────
# Memory threshold tests
# ─────────────────────────────────────────────────────


@patch("monitor.send_alert")
@patch("monitor.psutil")
def test_memory_below_threshold_no_alert(mock_psutil, mock_alert):
    """No alert should fire when memory is below the threshold."""
    mem = MagicMock()
    mem.percent = 60.0
    mem.used = 4 * 1024**2
    mem.total = 8 * 1024**2
    mock_psutil.virtual_memory.return_value = mem

    from monitor import check_memory

    result = check_memory()

    assert result == 60.0
    mock_alert.assert_not_called()


@patch("monitor.send_alert")
@patch("monitor.psutil")
def test_memory_above_threshold_triggers_alert(mock_psutil, mock_alert):
    """An alert should fire when memory exceeds the threshold."""
    mem = MagicMock()
    mem.percent = 92.0
    mem.used = 7 * 1024**2
    mem.total = 8 * 1024**2
    mock_psutil.virtual_memory.return_value = mem

    from monitor import check_memory

    result = check_memory()

    assert result == 92.0
    mock_alert.assert_called_once()
    assert "92.0%" in mock_alert.call_args[0][0]


# ─────────────────────────────────────────────────────
# Disk threshold tests
# ─────────────────────────────────────────────────────


@patch("monitor.send_alert")
@patch("monitor.psutil")
def test_disk_below_threshold_no_alert(mock_psutil, mock_alert):
    """No alert should fire when disk usage is below the threshold."""
    disk = MagicMock()
    disk.percent = 70.0
    disk.used = 50 * 1024**3
    disk.total = 100 * 1024**3
    mock_psutil.disk_usage.return_value = disk

    from monitor import check_disk

    result = check_disk("/")

    assert result == 70.0
    mock_alert.assert_not_called()


@patch("monitor.send_alert")
@patch("monitor.psutil")
def test_disk_above_threshold_triggers_alert(mock_psutil, mock_alert):
    """An alert should fire when disk usage exceeds the threshold."""
    disk = MagicMock()
    disk.percent = 95.0
    disk.used = 95 * 1024**3
    disk.total = 100 * 1024**3
    mock_psutil.disk_usage.return_value = disk

    from monitor import check_disk

    result = check_disk("/")

    assert result == 95.0
    mock_alert.assert_called_once()
    assert "95.0%" in mock_alert.call_args[0][0]


# ─────────────────────────────────────────────────────
# Endpoint health check tests
# ─────────────────────────────────────────────────────


@patch("monitor.send_alert")
@patch("monitor.requests")
def test_endpoint_healthy(mock_requests, mock_alert):
    """A 200 response should be treated as healthy — no alert."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    from monitor import check_endpoint

    result = check_endpoint("https://example.com/health")

    assert result is True
    mock_alert.assert_not_called()


@patch("monitor.send_alert")
@patch("monitor.requests")
def test_endpoint_unhealthy_status(mock_requests, mock_alert):
    """A non-200 response should trigger an alert."""
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_requests.get.return_value = mock_response

    from monitor import check_endpoint

    result = check_endpoint("https://example.com/health")

    assert result is False
    mock_alert.assert_called_once()
    assert "503" in mock_alert.call_args[0][0]


@patch("monitor.send_alert")
@patch("monitor.requests")
def test_endpoint_connection_error(mock_requests, mock_alert):
    """A connection error should trigger an alert."""
    import requests as real_requests

    mock_requests.get.side_effect = real_requests.ConnectionError("refused")
    mock_requests.ConnectionError = real_requests.ConnectionError
    mock_requests.Timeout = real_requests.Timeout
    mock_requests.RequestException = real_requests.RequestException

    from monitor import check_endpoint

    result = check_endpoint("https://example.com/health")

    assert result is False
    mock_alert.assert_called_once()


# ─────────────────────────────────────────────────────
# Ping tests
# ─────────────────────────────────────────────────────


@patch("monitor.send_alert")
@patch("monitor.subprocess")
def test_ping_success(mock_subprocess, mock_alert):
    """A successful ping should not trigger an alert."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_subprocess.run.return_value = mock_result
    mock_subprocess.PIPE = subprocess.PIPE

    from monitor import ping_server

    result = ping_server("8.8.8.8")

    assert result is True
    mock_alert.assert_not_called()


@patch("monitor.send_alert")
@patch("monitor.subprocess")
def test_ping_failure(mock_subprocess, mock_alert):
    """A failed ping should trigger an alert."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_subprocess.run.return_value = mock_result
    mock_subprocess.PIPE = subprocess.PIPE

    from monitor import ping_server

    result = ping_server("192.168.255.255")

    assert result is False
    mock_alert.assert_called_once()


# ─────────────────────────────────────────────────────
# Cooldown tests
# ─────────────────────────────────────────────────────


def test_cooldown_suppresses_duplicate_alerts():
    """Alerts with the same key within the cooldown window should be suppressed."""
    from alerts import _can_send, reset_cooldown

    reset_cooldown()

    assert _can_send("test_key") is True   # first call → allowed
    assert _can_send("test_key") is False  # immediate repeat → blocked


@patch("alerts.ALERT_COOLDOWN_SECONDS", 0)
def test_cooldown_allows_after_expiry():
    """Alerts should be allowed again after the cooldown window expires."""
    from alerts import _can_send, reset_cooldown

    reset_cooldown()

    assert _can_send("test_key") is True
    time.sleep(0.1)
    assert _can_send("test_key") is True  # cooldown = 0 → immediately allowed
