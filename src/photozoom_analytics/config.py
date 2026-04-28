from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class TradingPoint:
    name: str
    google_sheet_id: str
    google_worksheet_name: str
    report_title: str
    timezone: str
    send_time: str
    telegram_chat_id: str | None


@dataclass(frozen=True)
class Settings:
    google_service_account_file: Path
    telegram_bot_token: str
    telegram_chat_id: str
    date_column: str
    revenue_column: str
    cost_column: str
    orders_column: str
    conversions_column: str
    visits_column: str
    report_date: date | None
    dry_run: bool
    force_send: bool
    state_file: Path
    trading_points: tuple[TradingPoint, ...]


def load_settings() -> Settings:
    load_dotenv()
    dry_run = _parse_bool(os.getenv("DRY_RUN", "false"))
    default_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    trading_points = _load_trading_points(default_chat_id)
    _validate_trading_point_names(trading_points)
    if not dry_run:
        _validate_delivery_settings(trading_points)

    return Settings(
        google_service_account_file=Path(
            os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "./service-account.json")
        ),
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN") if not dry_run else "",
        telegram_chat_id=default_chat_id,
        date_column=os.getenv("DATE_COLUMN", "date"),
        revenue_column=os.getenv("REVENUE_COLUMN", "revenue"),
        cost_column=os.getenv("COST_COLUMN", "cost"),
        orders_column=os.getenv("ORDERS_COLUMN", "orders"),
        conversions_column=os.getenv("CONVERSIONS_COLUMN", "conversions"),
        visits_column=os.getenv("VISITS_COLUMN", "visits"),
        report_date=_parse_optional_date(os.getenv("REPORT_DATE", "")),
        dry_run=dry_run,
        force_send=_parse_bool(os.getenv("FORCE_SEND", "false")),
        state_file=Path(
            os.getenv("REPORT_STATE_FILE", ".photozoom-report-state.json")
        ),
        trading_points=trading_points,
    )


def _validate_delivery_settings(trading_points: tuple[TradingPoint, ...]) -> None:
    _required("TELEGRAM_BOT_TOKEN")
    missing_chat_ids = [
        point.name for point in trading_points if not point.telegram_chat_id
    ]
    if missing_chat_ids:
        names = ", ".join(missing_chat_ids)
        raise RuntimeError(f"Missing Telegram chat id for trading points: {names}")


def _validate_trading_point_names(trading_points: tuple[TradingPoint, ...]) -> None:
    names = [point.name for point in trading_points]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        names_text = ", ".join(duplicate_names)
        raise RuntimeError(f"Trading point names must be unique: {names_text}")


def _load_trading_points(default_chat_id: str) -> tuple[TradingPoint, ...]:
    raw_config = os.getenv("TRADING_POINTS_JSON", "").strip()
    config_file = os.getenv("TRADING_POINTS_FILE", "").strip()

    if raw_config and config_file:
        raise RuntimeError(
            "Use either TRADING_POINTS_JSON or TRADING_POINTS_FILE, not both"
        )

    if config_file:
        raw_config = Path(config_file).read_text(encoding="utf-8")

    if raw_config:
        try:
            data = json.loads(raw_config)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid trading points JSON: {exc}") from exc

        if not isinstance(data, list):
            raise RuntimeError("Trading points config must be a JSON array")

        points = [_parse_trading_point(item, default_chat_id) for item in data]
        if not points:
            raise RuntimeError("Trading points config must contain at least one point")
        return tuple(points)

    return (
        TradingPoint(
            name=os.getenv("TRADING_POINT_NAME", "Default"),
            google_sheet_id=_required("GOOGLE_SHEET_ID"),
            google_worksheet_name=os.getenv("GOOGLE_WORKSHEET_NAME", "*"),
            report_title=os.getenv("REPORT_TITLE", "Ракета Челябинск"),
            timezone=os.getenv("REPORT_TIMEZONE", "Asia/Yekaterinburg"),
            send_time=os.getenv("REPORT_SEND_TIME", "22:00"),
            telegram_chat_id=default_chat_id or None,
        ),
    )


def _parse_trading_point(item: object, default_chat_id: str) -> TradingPoint:
    if not isinstance(item, dict):
        raise RuntimeError("Each trading point must be a JSON object")

    name = _required_item(item, "name")
    return TradingPoint(
        name=name,
        google_sheet_id=_required_item(item, "google_sheet_id"),
        google_worksheet_name=str(item.get("google_worksheet_name", "*")),
        report_title=str(item.get("report_title", name)),
        timezone=str(item.get("timezone", "Asia/Yekaterinburg")),
        send_time=str(item.get("send_time", "22:00")),
        telegram_chat_id=str(item.get("telegram_chat_id") or default_chat_id or ""),
    )


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _required_item(item: dict[str, object], name: str) -> str:
    value = item.get(name)
    if value is None or str(value).strip() == "":
        raise RuntimeError(f"Missing required trading point field: {name}")
    return str(value)


def _parse_optional_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}
