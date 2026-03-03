# 🩺 Server Health Check Bot

A production-ready, modular Python bot that continuously monitors server health
metrics and sends real-time alerts via **Slack** and **Email** when configurable
thresholds are breached.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Slack Webhook Setup](#-slack-webhook-setup)
- [Cron Job Setup](#-cron-job-setup)
- [Running Tests](#-running-tests)
- [Example Alert Messages](#-example-alert-messages)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| **CPU Monitoring** | Alerts when CPU usage exceeds threshold (default 80 %) |
| **Memory Monitoring** | Alerts when memory usage exceeds threshold (default 85 %) |
| **Disk Monitoring** | Alerts when disk usage exceeds threshold (default 90 %) |
| **Ping Check** | Verifies server reachability via ICMP ping |
| **HTTP Health Check** | Validates API endpoints return HTTP 200 |
| **Slack Alerts** | Sends rich alerts to a Slack channel via Incoming Webhook |
| **Email Alerts** | Fallback email alerting over SMTP / TLS |
| **Cooldown System** | Prevents alert spamming (default 10-minute window) |
| **Rotating Log File** | Logs all activity to `health.log` with automatic rotation |
| **Cron Ready** | Designed to be scheduled via cron for automated monitoring |

---

## 🏗 Architecture

```
┌────────────────────────────────────────────────┐
│                  monitor.py                    │
│  (orchestrates all health checks)              │
│                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ CPU      │ │ Memory   │ │ Disk     │       │
│  │ Check    │ │ Check    │ │ Check    │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │             │            │              │
│  ┌──────────┐ ┌──────────────┐                 │
│  │ Ping     │ │ HTTP         │                 │
│  │ Check    │ │ Endpoint     │                 │
│  └────┬─────┘ └──────┬───────┘                 │
│       │               │                        │
│       └───────┬───────┘                        │
│               ▼                                │
│  ┌─────────────────────────┐                   │
│  │      alerts.py          │                   │
│  │  ┌───────┐ ┌─────────┐  │                   │
│  │  │ Slack │ │ Email   │  │                   │
│  │  └───────┘ └─────────┘  │                   │
│  │  ┌──────────────────┐   │                   │
│  │  │ Cooldown Tracker │   │                   │
│  │  └──────────────────┘   │                   │
│  └─────────────────────────┘                   │
│                                                │
│  ┌─────────────┐  ┌──────────────┐             │
│  │ config.py   │  │ logger.py    │             │
│  │ (.env)      │  │ (health.log) │             │
│  └─────────────┘  └──────────────┘             │
└────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
health-monitor-bot/
├── monitor.py          # Core monitoring logic & entry point
├── alerts.py           # Slack & Email alerting with cooldown
├── config.py           # Environment variable loading & thresholds
├── logger.py           # Centralized logging configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── README.md           # This file
└── tests/
    └── test_monitor.py # Unit tests (pytest)
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/health-monitor-bot.git
cd health-monitor-bot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values (Slack webhook URL, email credentials, etc.)
```

### 5. Run the bot manually

```bash
python monitor.py
```

---

## ⚙️ Configuration

All configuration is managed through environment variables (loaded from `.env`).

| Variable | Default | Description |
|---|---|---|
| `CPU_THRESHOLD` | `80` | CPU usage alert threshold (%) |
| `MEMORY_THRESHOLD` | `85` | Memory usage alert threshold (%) |
| `DISK_THRESHOLD` | `90` | Disk usage alert threshold (%) |
| `PING_HOST` | `8.8.8.8` | Host to ping for uptime check |
| `HEALTH_CHECK_URL` | `https://example.com/health` | HTTP endpoint to monitor |
| `SLACK_WEBHOOK_URL` | *(empty)* | Slack Incoming Webhook URL |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP server address |
| `SMTP_PORT` | `587` | SMTP server port |
| `EMAIL_SENDER` | *(empty)* | Sender email address |
| `EMAIL_PASSWORD` | *(empty)* | Sender email password / app password |
| `EMAIL_RECEIVER` | *(empty)* | Recipient email address |
| `ALERT_COOLDOWN_SECONDS` | `600` | Minimum seconds between duplicate alerts |
| `LOG_FILE` | `health.log` | Log output file path |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🔔 Slack Webhook Setup

1. Go to [Slack API: Incoming Webhooks](https://api.slack.com/messaging/webhooks).
2. Click **Create your Slack app** → select workspace.
3. Under **Incoming Webhooks**, toggle **Activate** to On.
4. Click **Add New Webhook to Workspace** and choose a channel.
5. Copy the **Webhook URL** and paste it into your `.env` file:

```
SLACK_WEBHOOK_URL=https://***REMOVED***/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

---

## ⏰ Cron Job Setup

Schedule the bot to run every **5 minutes** using cron (Linux / macOS):

```bash
crontab -e
```

Add the following line:

```cron
*/5 * * * * /path/to/venv/bin/python /path/to/monitor.py >> /var/log/health-bot-cron.log 2>&1
```

### Windows Task Scheduler

1. Open **Task Scheduler** → Create Basic Task.
2. Set the trigger to repeat every 5 minutes.
3. Set the action to run:
   - **Program**: `C:\path\to\venv\Scripts\python.exe`
   - **Arguments**: `C:\path\to\monitor.py`

---

## 🧪 Running Tests

```bash
pytest tests/test_monitor.py -v
```

All tests use **mocks** — no real network or system calls are made.

---

## 📨 Example Alert Messages

### Slack Alert

```
🚨 Health Check Alert
🔴 CPU usage critical: 92.3% (threshold: 80%)
```

### Email Alert

```
Subject: [Health Bot] CPU_HIGH Alert

🔴 CPU usage critical: 92.3% (threshold: 80%)
```

### Log Entry

```
2026-03-03 23:30:00 | WARNING  | monitor | CPU usage: 92.3% (threshold: 80.0%)
2026-03-03 23:30:00 | INFO     | alerts  | Slack alert sent: ...
```

---

## 📄 License

This project is released under the [MIT License](LICENSE).
