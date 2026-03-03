"""
dashboard.py — Rich terminal dashboard for the Server Health Check Bot.

Displays a beautiful, color-coded dashboard in the terminal showing
real-time system health metrics and check results.

Usage::

    python dashboard.py              # Single run
    python dashboard.py --live       # Auto-refresh every 5 seconds
"""

import argparse
import platform
import subprocess
import sys
import time
from datetime import datetime

import psutil
import requests
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config import (
    CPU_THRESHOLD,
    DISK_THRESHOLD,
    HEALTH_CHECK_URL,
    MEMORY_THRESHOLD,
    PING_HOST,
)
from logger import get_logger

logger = get_logger("dashboard")
console = Console()

# ──────────────────────────────────────────────
# Metric collection helpers
# ──────────────────────────────────────────────

def _status_icon(ok: bool) -> str:
    """Return a colored status icon."""
    return "[bold green][OK][/]" if ok else "[bold red][!!][/]"


def _bar(percent: float, width: int = 25) -> Text:
    """Build a colored progress bar as a Rich Text object."""
    filled = int(percent / 100 * width)
    empty = width - filled

    if percent > 90:
        color = "bold red"
    elif percent > 75:
        color = "bold yellow"
    else:
        color = "bold green"

    bar_text = Text()
    bar_text.append("#" * filled, style=color)
    bar_text.append("-" * empty, style="dim")
    bar_text.append(f" {percent:.1f}%", style=color)
    return bar_text


def _collect_metrics() -> dict:
    """Collect all health-check metrics and return a report dict."""
    # CPU
    cpu = psutil.cpu_percent(interval=1)

    # Memory
    mem = psutil.virtual_memory()

    # Disk
    disk_path = "C:\\" if platform.system().lower() == "windows" else "/"
    disk = psutil.disk_usage(disk_path)

    # Ping
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        ping_result = subprocess.run(
            ["ping", count_flag, "1", PING_HOST],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5,
        )
        ping_ok = ping_result.returncode == 0
    except Exception:
        ping_ok = False

    # HTTP endpoint
    try:
        resp = requests.get(HEALTH_CHECK_URL, timeout=5)
        endpoint_ok = resp.status_code == 200
        endpoint_status = resp.status_code
    except Exception:
        endpoint_ok = False
        endpoint_status = "ERR"

    return {
        "cpu": cpu,
        "mem_percent": mem.percent,
        "mem_used_gb": mem.used / (1024 ** 3),
        "mem_total_gb": mem.total / (1024 ** 3),
        "disk_percent": disk.percent,
        "disk_used_gb": disk.used / (1024 ** 3),
        "disk_total_gb": disk.total / (1024 ** 3),
        "disk_path": disk_path,
        "ping_ok": ping_ok,
        "ping_host": PING_HOST,
        "endpoint_ok": endpoint_ok,
        "endpoint_status": endpoint_status,
        "endpoint_url": HEALTH_CHECK_URL,
    }


# ──────────────────────────────────────────────
# Dashboard panels
# ──────────────────────────────────────────────

def _header() -> Panel:
    """Render the dashboard header."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(
        Text("[+] SERVER HEALTH DASHBOARD [+]", style="bold cyan", justify="center")
    )
    grid.add_row(
        Text(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            style="dim", justify="center",
        )
    )
    return Panel(grid, style="bright_blue", padding=(1, 2))


def _system_metrics_panel(m: dict) -> Panel:
    """Render the system metrics panel (CPU / Memory / Disk)."""
    table = Table(show_header=True, header_style="bold magenta", expand=True,
                  box=None, padding=(0, 2))
    table.add_column("Metric", style="bold white", min_width=10)
    table.add_column("Usage", min_width=35)
    table.add_column("Threshold", justify="center", min_width=10)
    table.add_column("Status", justify="center", min_width=8)

    # CPU
    cpu_ok = m["cpu"] <= CPU_THRESHOLD
    table.add_row(
        "CPU", _bar(m["cpu"]),
        f"{CPU_THRESHOLD:.0f}%",
        _status_icon(cpu_ok),
    )

    # Memory
    mem_ok = m["mem_percent"] <= MEMORY_THRESHOLD
    mem_detail = Text()
    mem_detail.append_text(_bar(m["mem_percent"]))
    mem_detail.append(f"  ({m['mem_used_gb']:.1f} / {m['mem_total_gb']:.1f} GB)", style="dim")
    table.add_row(
        "Memory", mem_detail,
        f"{MEMORY_THRESHOLD:.0f}%",
        _status_icon(mem_ok),
    )

    # Disk
    disk_ok = m["disk_percent"] <= DISK_THRESHOLD
    disk_detail = Text()
    disk_detail.append_text(_bar(m["disk_percent"]))
    disk_detail.append(f"  ({m['disk_used_gb']:.1f} / {m['disk_total_gb']:.1f} GB)", style="dim")
    table.add_row(
        f"Disk ({m['disk_path']})", disk_detail,
        f"{DISK_THRESHOLD:.0f}%",
        _status_icon(disk_ok),
    )

    return Panel(table, title="[bold white]System Metrics[/]", border_style="cyan",
                 padding=(1, 1))


def _network_panel(m: dict) -> Panel:
    """Render the network checks panel (Ping / Endpoint)."""
    table = Table(show_header=True, header_style="bold magenta", expand=True,
                  box=None, padding=(0, 2))
    table.add_column("Check", style="bold white", min_width=12)
    table.add_column("Target", min_width=30)
    table.add_column("Result", justify="center", min_width=12)
    table.add_column("Status", justify="center", min_width=8)

    # Ping
    ping_result = "[bold green]Reachable[/]" if m["ping_ok"] else "[bold red]Unreachable[/]"
    table.add_row("Ping", m["ping_host"], ping_result, _status_icon(m["ping_ok"]))

    # Endpoint
    if m["endpoint_ok"]:
        ep_result = f"[bold green]200 OK[/]"
    else:
        ep_result = f"[bold red]{m['endpoint_status']}[/]"
    table.add_row("HTTP", m["endpoint_url"], ep_result, _status_icon(m["endpoint_ok"]))

    return Panel(table, title="[bold white]Network Checks[/]", border_style="cyan",
                 padding=(1, 1))


def _summary_panel(m: dict) -> Panel:
    """Render an overall health summary."""
    checks = [
        ("CPU",      m["cpu"] <= CPU_THRESHOLD),
        ("Memory",   m["mem_percent"] <= MEMORY_THRESHOLD),
        ("Disk",     m["disk_percent"] <= DISK_THRESHOLD),
        ("Ping",     m["ping_ok"]),
        ("Endpoint", m["endpoint_ok"]),
    ]
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)

    if passed == total:
        summary_style = "bold green"
        summary_text = f"ALL SYSTEMS HEALTHY  ({passed}/{total} checks passed)"
        border = "green"
    elif passed >= 3:
        summary_style = "bold yellow"
        summary_text = f"WARNINGS DETECTED  ({passed}/{total} checks passed)"
        border = "yellow"
    else:
        summary_style = "bold red"
        summary_text = f"CRITICAL ISSUES  ({passed}/{total} checks passed)"
        border = "red"

    detail_parts = []
    for name, ok in checks:
        icon = "[OK]" if ok else "[!!]"
        color = "green" if ok else "red"
        detail_parts.append(f"[{color}]{icon}[/] {name}")

    markup_str = f"\n  [{summary_style}]{summary_text}[/]\n\n  " + "   ".join(detail_parts) + "\n"
    content = Text.from_markup(markup_str)

    return Panel(content, title="[bold white]Overall Health[/]", border_style=border,
                 padding=(0, 1))


def build_dashboard() -> Layout:
    """Assemble the full dashboard layout."""
    m = _collect_metrics()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="body"),
        Layout(name="summary", size=6),
    )
    layout["body"].split_column(
        Layout(name="metrics", size=8),
        Layout(name="network", size=7),
    )

    layout["header"].update(_header())
    layout["metrics"].update(_system_metrics_panel(m))
    layout["network"].update(_network_panel(m))
    layout["summary"].update(_summary_panel(m))

    return layout


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Server Health Dashboard")
    parser.add_argument("--live", action="store_true",
                        help="Auto-refresh the dashboard every 5 seconds")
    parser.add_argument("--interval", type=int, default=5,
                        help="Refresh interval in seconds (default: 5)")
    args = parser.parse_args()

    if args.live:
        console.clear()
        try:
            with Live(build_dashboard(), console=console, refresh_per_second=0.5,
                       screen=True) as live:
                while True:
                    time.sleep(args.interval)
                    live.update(build_dashboard())
        except KeyboardInterrupt:
            console.print("\n[dim]Dashboard stopped.[/dim]")
    else:
        console.clear()
        console.print(build_dashboard())


if __name__ == "__main__":
    main()
