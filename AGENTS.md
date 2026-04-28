# Agent Notes

## Project Snapshot

PhotoZoom Analytics is a small Python CLI app that reads Google Sheets data, builds a Telegram-friendly daily analytics report, and sends it to Telegram. The active package lives under `src/photozoom_analytics`.

Main runtime flow:

1. `photozoom_analytics.app:main` loads settings and send state.
2. `sheets.load_worksheet` reads one worksheet or all worksheets from Google Sheets.
3. `auto_report.render_auto_report` builds the current Telegram Markdown report.
4. `telegram.send_message` sends the message through Telegram Bot API.

## Common Commands

Set `PYTHONPATH=src` when running from the repo without installing the package.

```bash
PYTHONPATH=src python -m photozoom_analytics
DRY_RUN=true PYTHONPATH=src python -m photozoom_analytics
REPORT_DATE=2026-04-22 PYTHONPATH=src python -m photozoom_analytics
FORCE_SEND=true PYTHONPATH=src python -m photozoom_analytics
```

Install locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

There is no test suite configured yet. For verification, prefer `DRY_RUN=true` with a specific `REPORT_DATE` when credentials and sheet access are available.

## Important Files

- `src/photozoom_analytics/app.py` - orchestration, schedule checks, state file reads/writes, Telegram delivery.
- `src/photozoom_analytics/config.py` - `.env` parsing, trading point config, delivery validation.
- `src/photozoom_analytics/sheets.py` - Google Sheets access through `gspread`; supports `*`, `all`, and `все` to load every worksheet.
- `src/photozoom_analytics/auto_report.py` - active domain-specific report for worksheets named `Продажи` and `ЗП`.
- `src/photozoom_analytics/analysis.py` and `src/photozoom_analytics/report.py` - older/general metric report path; currently not used by `app.py`.
- `trading-points.example.json` - example multi-point config.
- `scripts/run_daily_report.sh` and `cron/photozoom-analytics.cron` - deployment helpers.
- `DEPLOYMENT_RU.md` - Russian deployment guide.

## Configuration And Local State

Secrets and local production data are intentionally local:

- `.env`
- `service-account.json`
- `trading-points.json`
- `.photozoom-report-state.json`
- `report.log`

Do not commit secrets or real trading point credentials. `trading-points.example.json` is safe to edit as documentation/example config.

Key env vars:

- `GOOGLE_SHEET_ID`, `GOOGLE_WORKSHEET_NAME`, `GOOGLE_SERVICE_ACCOUNT_FILE`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `REPORT_TIMEZONE`, `REPORT_SEND_TIME`, `REPORT_DATE`
- `DRY_RUN`, `FORCE_SEND`
- `TRADING_POINTS_FILE` or `TRADING_POINTS_JSON`
- `REPORT_STATE_FILE`

For multiple trading points, each point may define its own sheet, worksheet, report title, timezone, send time, and optional Telegram chat id. Point names must be unique because send state is keyed by `TradingPoint.name`.

## Report Assumptions

The active `auto_report` logic expects data from all worksheets and filters by worksheet names:

- `Продажи`: date is read from `column_1`, which comes from a blank first header cell in Google Sheets.
- `ЗП`: date is read from `Дата`; daily revenue is summed from `Касса`.

Dates are accepted in `%d.%m.%y`, `%d.%m.%Y`, and `%Y-%m-%d` formats, with a pandas fallback using day-first parsing.

Product names and unit costs are hardcoded in `auto_report.py` through `PRODUCT_COLUMNS` and `PRODUCT_UNIT_COSTS`. Keep edits there conservative because Google Sheet column spelling matters, including case, spaces, and duplicate names.

Telegram formatting uses Markdown escaping helpers. If report text changes, check that `*`, `_`, `` ` ``, `[`, and backslashes remain escaped where user-controlled text is inserted.

## Coding Preferences

- Keep the project dependency-light; current runtime deps are `gspread`, `google-auth`, `pandas`, `python-dotenv`, and `requests`.
- Follow the existing simple module style: dataclasses for config/metrics, small helper functions, explicit runtime errors for configuration problems.
- Preserve Python 3.9 compatibility.
- Use structured JSON parsing for trading point config and avoid ad hoc parsing.
- Avoid touching local secret/state files unless the user explicitly asks.

