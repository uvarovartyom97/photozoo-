from __future__ import annotations

from pathlib import Path

import gspread
import pandas as pd


def load_worksheet(
    sheet_id: str,
    worksheet_name: str,
    service_account_file: Path,
) -> pd.DataFrame:
    if not service_account_file.exists():
        raise FileNotFoundError(
            f"Google service account file not found: {service_account_file}"
        )

    client = gspread.service_account(filename=str(service_account_file))
    spreadsheet = client.open_by_key(sheet_id)

    if worksheet_name.strip().lower() in {"*", "all", "все"}:
        frames = []
        for worksheet in spreadsheet.worksheets():
            frame = _worksheet_to_frame(worksheet)
            if not frame.empty:
                frame.insert(0, "worksheet", worksheet.title)
                frames.append(frame)

        if not frames:
            return pd.DataFrame()

        return pd.concat(frames, ignore_index=True, sort=False)

    worksheet = spreadsheet.worksheet(worksheet_name)
    return _worksheet_to_frame(worksheet)


def _worksheet_to_frame(worksheet: gspread.Worksheet) -> pd.DataFrame:
    values = worksheet.get_all_values()

    if not values:
        return pd.DataFrame()

    headers = _unique_headers(values[0])
    rows = values[1:]
    if not rows:
        return pd.DataFrame(columns=headers)

    return pd.DataFrame(rows, columns=headers)


def _unique_headers(headers: list[str]) -> list[str]:
    result = []
    counts: dict[str, int] = {}

    for index, header in enumerate(headers, start=1):
        name = header.strip() or f"column_{index}"
        count = counts.get(name, 0)
        counts[name] = count + 1
        if count:
            result.append(f"{name}_{count + 1}")
        else:
            result.append(name)

    return result
