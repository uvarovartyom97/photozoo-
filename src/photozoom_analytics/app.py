from __future__ import annotations

import json
import logging
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from .auto_report import render_auto_report
from .config import Settings, TradingPoint, load_settings
from .sheets import load_worksheet
from .telegram import send_message


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def main() -> None:
    settings = load_settings()

    state = _load_state(settings.state_file)
    sent_count = 0

    for point in settings.trading_points:
        if not _should_send(point, settings, state):
            continue

        _send_point_report(point, settings)
        sent_count += 1

        if not settings.dry_run and settings.report_date is None:
            _mark_sent(point, settings, state)

    if sent_count == 0:
        logging.info("No trading points are due for report delivery")


def _send_point_report(point: TradingPoint, settings: Settings) -> None:
    chat_id = point.telegram_chat_id or settings.telegram_chat_id
    if not chat_id and not settings.dry_run:
        raise RuntimeError(
            f"Telegram chat id is not configured for trading point: {point.name}"
        )

    logging.info("Loading Google Sheet %s for %s", point.google_sheet_id, point.name)
    raw_df = load_worksheet(
        point.google_sheet_id,
        point.google_worksheet_name,
        settings.google_service_account_file,
    )

    logging.info("Building report for %s", point.name)
    message = render_auto_report(raw_df, point.report_title, settings.report_date)

    if settings.dry_run:
        logging.info("DRY_RUN is enabled; Telegram message will not be sent")
        print(message)
        return

    logging.info("Sending %s report to Telegram chat %s", point.name, chat_id)
    send_message(settings.telegram_bot_token, chat_id, message)
    logging.info("Report for %s sent successfully", point.name)


def _should_send(
    point: TradingPoint,
    settings: Settings,
    state: dict[str, dict[str, str]],
) -> bool:
    if settings.report_date is not None or settings.force_send:
        return True

    local_now = datetime.now(ZoneInfo(point.timezone))
    send_time = _parse_send_time(point.send_time)
    today_key = local_now.date().isoformat()

    if local_now.time() < send_time:
        logging.info(
            "%s is not due yet: local time is %s, send time is %s",
            point.name,
            local_now.strftime("%H:%M"),
            point.send_time,
        )
        return False

    point_state = state.get(point.name, {})
    if (
        isinstance(point_state, dict)
        and point_state.get("last_sent_date") == today_key
    ):
        logging.info("%s report was already sent for %s", point.name, today_key)
        return False

    return True


def _parse_send_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise RuntimeError(f"Invalid send_time {value!r}; expected HH:MM") from exc


def _load_state(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid report state file: {path}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid report state file format: {path}")

    return data


def _mark_sent(
    point: TradingPoint,
    settings: Settings,
    state: dict[str, dict[str, str]],
) -> None:
    local_now = datetime.now(ZoneInfo(point.timezone))
    state[point.name] = {
        "last_sent_date": local_now.date().isoformat(),
        "last_sent_at": local_now.isoformat(),
    }
    settings.state_file.parent.mkdir(parents=True, exist_ok=True)
    settings.state_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
