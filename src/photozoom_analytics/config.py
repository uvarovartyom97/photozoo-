from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    google_sheet_id: str
    google_worksheet_name: str
    google_service_account_file: Path
    telegram_bot_token: str
    telegram_chat_id: str
    report_title: str
    date_column: str
    revenue_column: str
    cost_column: str
    orders_column: str
    conversions_column: str
    visits_column: str
    report_date: date | None
    dry_run: bool


def load_settings() -> Settings:
    load_dotenv()
    dry_run = _parse_bool(os.getenv("DRY_RUN", "false"))

    return Settings(
        google_sheet_id=_required("GOOGLE_SHEET_ID"),
        google_worksheet_name=os.getenv("GOOGLE_WORKSHEET_NAME", "*"),
        google_service_account_file=Path(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "./service-account.json")
        ),
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN") if not dry_run else "",
        telegram_chat_id=_required("TELEGRAM_CHAT_ID") if not dry_run else "",
        report_title=os.getenv("REPORT_TITLE", "Daily PhotoZoom Analytics"),
        date_column=os.getenv("DATE_COLUMN", "date"),
        revenue_column=os.getenv("REVENUE_COLUMN", "revenue"),
        cost_column=os.getenv("COST_COLUMN", "cost"),
        orders_column=os.getenv("ORDERS_COLUMN", "orders"),
        conversions_column=os.getenv("CONVERSIONS_COLUMN", "conversions"),
        visits_column=os.getenv("VISITS_COLUMN", "visits"),
        report_date=_parse_optional_date(os.getenv("REPORT_DATE", "")),
        dry_run=dry_run,
    )


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_optional_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}
