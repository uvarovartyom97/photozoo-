from __future__ import annotations

import re
from datetime import date, datetime

import pandas as pd


PRODUCT_COLUMNS = [
    "Магнит 7х10",
    "Рамка 15х20",
    "Ел.Игрушка",
    "Фото 15х20",
    "Кружка",
    "фото за 100",
    "эл.фото",
    "Фото 10х15",
    "Фото А4",
    "Магнит 10х15",
    "Подарочные магниты",
    "Брелки",
    "Рамка А4",
    "Водная",
    "Стикеры",
    "Полароид",
    "Деревянная рамка",
    "Фотобудка",
    "Коллаж А4(БЕЗ РАМКИ )",
    "фото за 200",
    "эл.фото за 300",
    "Брел0ки",
    "Фотосессия",
    "КОЛЛАЖ А5",
]


def render_auto_report(
    df: pd.DataFrame,
    title: str,
    requested_date: date | None = None,
) -> str:
    if df.empty:
        return f"*{_escape(title)}*\n\nДанных в таблице не найдено."

    report_date = requested_date or _latest_report_date(df)
    lines = [
        f"*{_escape(title)}*",
        f"Отчет за `{report_date.isoformat() if report_date else 'н/д'}`",
        "",
    ]

    salary = _salary_section(df, report_date)
    if salary:
        lines.extend(salary)
        lines.append("")

    sales = _sales_section(df, report_date)
    if sales:
        lines.extend(sales)
        lines.append("")

    extra_sales = _extra_sales_section(df)
    if extra_sales:
        lines.extend(extra_sales)

    return "\n".join(lines).strip()


def _salary_section(df: pd.DataFrame, report_date: date | None) -> list[str]:
    sheet = df[df["worksheet"] == "ЗП"].copy()
    if sheet.empty or report_date is None or "Дата" not in sheet:
        return []

    sheet["_date"] = _parse_dates(sheet["Дата"])
    current = sheet[sheet["_date"] == report_date]
    if current.empty:
        return ["*ЗП и касса*", "- За выбранную дату строк нет."]

    cash = _sum(current, "Касса")
    payroll = _sum(current, "Зарплата+премия")
    staff = ", ".join(str(value) for value in current.get("ФИО", pd.Series()).dropna() if str(value).strip())

    return [
        "*ЗП и касса*",
        f"- Касса: `{_money(cash)}`",
        f"- Наличные: `{_money(_sum(current, 'Наличные'))}`",
        f"- Б/Н: `{_money(_sum(current, 'Б/Н'))}`",
        f"- Перевод: `{_money(_sum(current, 'Перевод'))}`",
        f"- Дети: `{_whole(_sum(current, 'Дети'))}`",
        f"- Кадры: `{_whole(_sum(current, 'Кадры'))}`",
        f"- Зарплата + премия: `{_money(payroll)}`",
        f"- Остаток после ЗП: `{_money(cash - payroll)}`",
        f"- Сотрудники: `{_escape(staff) if staff else 'н/д'}`",
    ]


def _sales_section(df: pd.DataFrame, report_date: date | None) -> list[str]:
    sheet = df[df["worksheet"] == "Продажи"].copy()
    if sheet.empty or report_date is None or "column_1" not in sheet:
        return []

    sheet["_date"] = _parse_dates(sheet["column_1"])
    current = sheet[sheet["_date"] == report_date]
    if current.empty:
        return ["*Продажи по товарам*", "- За выбранную дату строк нет."]

    totals = _product_totals(current)
    total_units = sum(totals.values())
    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:7]

    lines = [
        "*Продажи по товарам*",
        f"- Всего единиц: `{_whole(total_units)}`",
    ]
    for name, value in top:
        if value:
            lines.append(f"- {_escape(name)}: `{_whole(value)}`")
    return lines


def _extra_sales_section(df: pd.DataFrame) -> list[str]:
    sheet = df[df["worksheet"] == "таблица продаж"].copy()
    if sheet.empty:
        return []

    totals = _product_totals(sheet)
    total_units = sum(totals.values())
    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:7]

    lines = [
        "*Таблица продаж без дат*",
        f"- Всего единиц: `{_whole(total_units)}`",
    ]
    for name, value in top:
        if value:
            lines.append(f"- {_escape(name)}: `{_whole(value)}`")
    return lines


def _latest_report_date(df: pd.DataFrame) -> date | None:
    today = date.today()
    dates: list[date] = []

    salary = df[df["worksheet"] == "ЗП"].copy()
    if not salary.empty and "Дата" in salary:
        salary["_date"] = _parse_dates(salary["Дата"])
        for _, row in salary.iterrows():
            row_date = row["_date"]
            if row_date and row_date <= today and _salary_row_has_data(row):
                dates.append(row_date)

    sales = df[df["worksheet"] == "Продажи"].copy()
    if not sales.empty and "column_1" in sales:
        sales["_date"] = _parse_dates(sales["column_1"])
        for _, row in sales.iterrows():
            row_date = row["_date"]
            totals = _product_totals(pd.DataFrame([row]))
            if row_date and row_date <= today and sum(totals.values()) > 0:
                dates.append(row_date)

    return max(dates) if dates else None


def _parse_dates(values: pd.Series) -> pd.Series:
    return values.apply(_parse_date)


def _parse_date(value: object) -> date | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%d.%m.%y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return parsed.date()


def _salary_row_has_data(row: pd.Series) -> bool:
    for column in ("Касса", "Наличные", "Б/Н", "Перевод", "Дети", "Кадры"):
        if _parse_number(row.get(column, 0)) > 0:
            return True
    return False


def _product_totals(df: pd.DataFrame) -> dict[str, float]:
    totals = {}
    for column in PRODUCT_COLUMNS:
        if column in df:
            totals[column] = _sum(df, column)
    return totals


def _sum(df: pd.DataFrame, column: str) -> float:
    if column not in df:
        return 0.0
    return float(df[column].apply(_parse_number).sum())


def _parse_number(value: object) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace(" ", "").replace(",", ".")
    if not text:
        return 0.0

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    return float(match.group(0))


def _money(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


def _whole(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("`", "\\`")
        .replace("[", "\\[")
    )
