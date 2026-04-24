from __future__ import annotations

import logging

from .auto_report import render_auto_report
from .config import load_settings
from .sheets import load_worksheet
from .telegram import send_message


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def main() -> None:
    settings = load_settings()

    logging.info("Loading Google Sheet %s", settings.google_sheet_id)
    raw_df = load_worksheet(
        settings.google_sheet_id,
        settings.google_worksheet_name,
        settings.google_service_account_file,
    )

    logging.info("Building report")
    message = render_auto_report(raw_df, settings.report_title, settings.report_date)

    if settings.dry_run:
        logging.info("DRY_RUN is enabled; Telegram message will not be sent")
        print(message)
        return

    logging.info("Sending report to Telegram chat %s", settings.telegram_chat_id)
    send_message(settings.telegram_bot_token, settings.telegram_chat_id, message)
    logging.info("Report sent successfully")
