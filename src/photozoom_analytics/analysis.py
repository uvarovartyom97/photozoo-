from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from .config import Settings


@dataclass(frozen=True)
class ReportMetrics:
    report_date: date
    rows_count: int
    revenue: float
    cost: float
    profit: float
    orders: int
    visits: int
    conversions: int
    conversion_rate: float | None
    average_order_value: float | None
    revenue_delta_pct: float | None
    profit_delta_pct: float | None
    revenue_7d_avg: float | None
    profit_7d_avg: float | None


def build_metrics(raw_df: pd.DataFrame, settings: Settings) -> ReportMetrics:
    required_columns = [
        settings.date_column,
        settings.revenue_column,
        settings.cost_column,
        settings.orders_column,
        settings.conversions_column,
        settings.visits_column,
    ]
    missing_columns = [column for column in required_columns if column not in raw_df]
    if missing_columns:
        raise ValueError(f"Missing columns in Google Sheet: {', '.join(missing_columns)}")

    df = raw_df.copy()
    df[settings.date_column] = pd.to_datetime(
        df[settings.date_column],
        errors="coerce",
        dayfirst=False,
    ).dt.date

    for column in required_columns[1:]:
        df[column] = df[column].apply(_parse_number)

    df = df.dropna(subset=[settings.date_column])
    if df.empty:
        raise ValueError("No rows with a valid date found in Google Sheet")

    report_date = settings.report_date or max(df[settings.date_column])
    current = df[df[settings.date_column] == report_date]
    previous_date = report_date - timedelta(days=1)
    previous = df[df[settings.date_column] == previous_date]
    week_start = report_date - timedelta(days=7)
    last_week = df[
        (df[settings.date_column] >= week_start)
        & (df[settings.date_column] < report_date)
    ]

    revenue = float(current[settings.revenue_column].sum())
    cost = float(current[settings.cost_column].sum())
    profit = revenue - cost
    orders = int(current[settings.orders_column].sum())
    visits = int(current[settings.visits_column].sum())
    conversions = int(current[settings.conversions_column].sum())

    previous_revenue = float(previous[settings.revenue_column].sum())
    previous_profit = previous_revenue - float(previous[settings.cost_column].sum())

    return ReportMetrics(
        report_date=report_date,
        rows_count=len(current),
        revenue=revenue,
        cost=cost,
        profit=profit,
        orders=orders,
        visits=visits,
        conversions=conversions,
        conversion_rate=_safe_ratio(conversions, visits),
        average_order_value=_safe_ratio(revenue, orders),
        revenue_delta_pct=_pct_delta(revenue, previous_revenue),
        profit_delta_pct=_pct_delta(profit, previous_profit),
        revenue_7d_avg=_daily_average(
            last_week,
            settings.date_column,
            settings.revenue_column,
        ),
        profit_7d_avg=_daily_profit_average(
            last_week,
            settings.date_column,
            settings.revenue_column,
            settings.cost_column,
        ),
    )


def _parse_number(value: object) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).strip().replace(" ", "").replace(",", ".")
    if normalized in {"", "-", "None"}:
        return 0.0
    return float(normalized)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _pct_delta(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / previous


def _daily_average(df: pd.DataFrame, date_column: str, value_column: str) -> float | None:
    if df.empty:
        return None
    daily = df.groupby(date_column)[value_column].sum()
    if daily.empty:
        return None
    return float(daily.mean())


def _daily_profit_average(
    df: pd.DataFrame,
    date_column: str,
    revenue_column: str,
    cost_column: str,
) -> float | None:
    if df.empty:
        return None
    daily = df.groupby(date_column)[[revenue_column, cost_column]].sum()
    if daily.empty:
        return None
    profit = daily[revenue_column] - daily[cost_column]
    return float(profit.mean())
