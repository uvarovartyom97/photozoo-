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
    "Расходник (пачка бумаги)",
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
    "Цветные магниты",
    "Брелки",
    "Фотосессия",
    "КОЛЛАЖ А5",
]

PRODUCT_UNIT_COSTS = {
    "Магнит 7х10": 19.0,
    "Рамка 15х20": 175.0,
    "Ел.Игрушка": 135.0,
    "Фото 15х20": 3.0,
    "Кружка": 70.0,
    "Расходник (пачка бумаги)": 550.0,
    "фото за 100": 1.0,
    "эл.фото": 1.0,
    "Фото 10х15": 1.5,
    "Фото А4": 6.0,
    "Магнит 10х15": 54.0,
    "Подарочные магниты": 19.0,
    "Брелки": 28.0,
    "Брел0ки": 28.0,
    "Рамка А4": 245.0,
    "Водная": 210.0,
    "Стикеры": 6.0,
    "Полароид": 1.0,
    "Деревянная рамка": 98.0,
    "Фотобудка": 2.0,
    "Коллаж А4(БЕЗ РАМКИ )": 6.0,
    "фото за 200": 1.0,
    "эл.фото за 300": 1.0,
    "Цветные магниты": 23.0,
    "Фотосессия": 1200.0,
    "КОЛЛАЖ А5": 3.0,
}


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
        f"*Дата:* `{_format_report_date(report_date) if report_date else 'н/д'}`",
    ]

    sales = _sales_section(df, report_date)
    if sales:
        lines.extend(sales)

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
        return ["", "За выбранную дату строк продаж нет."]

    totals = _product_totals(current)
    unit_costs = _product_unit_costs(df)
    revenue = _daily_revenue(df, report_date)
    product_columns = _sales_product_columns(sheet)
    rows = []
    for name in product_columns:
        quantity = totals.get(name, 0.0)
        cost = quantity * unit_costs.get(name, 0.0)
        if quantity > 0:
            rows.append((name, quantity, cost, _safe_percent(cost, revenue)))

    total_cost = sum(row[2] for row in rows)
    zero_count = len(product_columns) - len(rows)

    lines = [
        "",
        f"Выручка: `{_rubles(revenue)}`",
        f"Себестоимость: `{_rubles(total_cost)}`",
        f"Доля от выручки: `{_percent_or_na(_safe_percent(total_cost, revenue))}`",
        "",
        "*Проданные позиции:*",
    ]
    if not rows:
        lines.append("Проданных позиций за выбранную дату нет.")
    for index, (name, quantity, cost, revenue_pct) in enumerate(rows, start=1):
        lines.extend(
            [
                f"{index}. *{_escape(name)}*",
                f"   Кол-во: `{_whole(quantity)}`",
                f"   Себестоимость: `{_rubles(cost)}`",
                f"   Доля выручки: `{_percent_or_na(revenue_pct)}`",
                "",
            ]
        )
    lines.append(f"Позиций без продаж: `{zero_count}`")
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
    for column in set(PRODUCT_COLUMNS) | set(PRODUCT_UNIT_COSTS):
        if column in df:
            totals[column] = _sum(df, column)
    return totals


def _sales_product_columns(sheet: pd.DataFrame) -> list[str]:
    product_names = set(PRODUCT_COLUMNS) | set(PRODUCT_UNIT_COSTS)
    return [column for column in sheet.columns if column in product_names]


def _product_unit_costs(_df: pd.DataFrame) -> dict[str, float]:
    return PRODUCT_UNIT_COSTS.copy()


def _daily_revenue(df: pd.DataFrame, report_date: date) -> float:
    salary = df[df["worksheet"] == "ЗП"].copy()
    if salary.empty or "Дата" not in salary:
        return 0.0

    salary["_date"] = _parse_dates(salary["Дата"])
    return _sum(salary[salary["_date"] == report_date], "Касса")


def _sum(df: pd.DataFrame, column: str) -> float:
    if column not in df:
        return 0.0
    return float(df[column].apply(_parse_number).sum())


def _safe_percent(value: float, total: float) -> float | None:
    if total == 0:
        return None
    return value / total * 100


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


def _rubles(value: float) -> str:
    return f"{_whole(value)}руб."


def _percent_or_na(value: float | None) -> str:
    if value is None:
        return "н/д"
    return f"{value:.2f}%".replace(".", ",")


def _format_report_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("`", "\\`")
        .replace("[", "\\[")
    )
