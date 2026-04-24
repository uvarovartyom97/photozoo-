# PhotoZoom Analytics

Daily Google Sheets analytics report sender for a private Telegram channel.

## What It Does

The script:

1. Reads data from a Google Sheet.
2. Calculates daily metrics.
3. Builds a Telegram-friendly report.
4. Sends the report to a private Telegram channel.

## Expected Google Sheet Columns

By default the script expects these columns:

| Column | Meaning |
| --- | --- |
| `date` | Date in `YYYY-MM-DD` format |
| `revenue` | Revenue |
| `cost` | Cost |
| `orders` | Orders count |
| `conversions` | Conversions count |
| `visits` | Visits count |

Column names can be changed in `.env`.

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Fill in `.env`:

```bash
GOOGLE_SHEET_ID=...
GOOGLE_WORKSHEET_NAME=Sheet1
GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=-100...
```

For a safe preview without Telegram delivery, set:

```bash
DRY_RUN=true
```

## Google Sheets Access

1. Create a Google Cloud project.
2. Enable Google Sheets API.
3. Create a service account.
4. Download its JSON key as `service-account.json`.
5. Share the Google Sheet with the service account email.

## Telegram Access

1. Create a bot via `@BotFather`.
2. Add the bot to the private channel as an administrator.
3. Get the private channel `chat_id`.
4. Put `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` into `.env`.

## Run Manually

```bash
PYTHONPATH=src python -m photozoom_analytics
```

Preview without sending to Telegram:

```bash
DRY_RUN=true PYTHONPATH=src python -m photozoom_analytics
```

To build a report for a specific date:

```bash
REPORT_DATE=2026-04-22 PYTHONPATH=src python -m photozoom_analytics
```

## Daily Cron Example

This example runs the report every day at 09:00 server time:

```cron
0 9 * * * cd "/Users/aduvarov/Documents/PhotoZoom Analytics" && PYTHONPATH=src .venv/bin/python -m photozoom_analytics >> report.log 2>&1
```

Alternatively, install the package in editable mode with `pip install -e .` and run `.venv/bin/photozoom-analytics`.

## Deployment Options

Recommended production options:

- VPS with `cron` for the simplest setup.
- Google Cloud Run plus Cloud Scheduler for managed infrastructure.
- GitHub Actions scheduled workflow for repository-based automation.

For the first production version, VPS plus cron is enough.
