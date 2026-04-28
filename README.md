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
GOOGLE_WORKSHEET_NAME=*
GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=-100...
REPORT_TIMEZONE=Asia/Yekaterinburg
REPORT_SEND_TIME=22:00
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

To force delivery for all configured trading points regardless of schedule:

```bash
FORCE_SEND=true PYTHONPATH=src python -m photozoom_analytics
```

## Multiple Trading Points

Each trading point can read its own Google Sheet and use its own local delivery schedule. Copy the example config:

```bash
cp trading-points.example.json trading-points.json
```

Set the file in `.env`:

```bash
TRADING_POINTS_FILE=./trading-points.json
```

Example point:

```json
{
  "name": "PhotoZoom Москва",
  "google_sheet_id": "google_sheet_id_for_moscow",
  "google_worksheet_name": "*",
  "report_title": "PhotoZoom Москва",
  "timezone": "Europe/Moscow",
  "send_time": "22:00"
}
```

Optional `telegram_chat_id` can be set per point. If it is omitted, the global `TELEGRAM_CHAT_ID` is used.

The app stores successful scheduled sends in `.photozoom-report-state.json`, so repeated cron runs will not send duplicates for the same local date.

## Cron Example

For multiple time zones, run the app every 2 hours and let it decide which trading points are due:

```cron
0 */2 * * * cd "/Users/aduvarov/Documents/PhotoZoom Analytics" && PYTHONPATH=src .venv/bin/python -m photozoom_analytics >> report.log 2>&1
```

Alternatively, install the package in editable mode with `pip install -e .` and run `.venv/bin/photozoom-analytics`.

## Deployment Options

Recommended production options:

- VPS with `cron` for the simplest setup.
- Google Cloud Run plus Cloud Scheduler for managed infrastructure.
- GitHub Actions scheduled workflow for repository-based automation.

For the first production version, VPS plus cron is enough.
