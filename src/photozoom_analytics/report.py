from __future__ import annotations

from .analysis import ReportMetrics


def render_report(title: str, metrics: ReportMetrics) -> str:
    lines = [
        f"*{_escape_markdown(title)}*",
        f"Отчет за `{metrics.report_date.isoformat()}`",
        "",
        "*Ключевые показатели*",
        f"- Строк за день: `{metrics.rows_count}`",
        f"- Выручка: `{_money(metrics.revenue)}`",
        f"- Расходы: `{_money(metrics.cost)}`",
        f"- Прибыль: `{_money(metrics.profit)}`",
        f"- Заказы: `{metrics.orders}`",
        f"- Визиты: `{metrics.visits}`",
        f"- Конверсии: `{metrics.conversions}`",
        f"- CR: `{_percent(metrics.conversion_rate)}`",
        f"- Средний чек: `{_money_or_na(metrics.average_order_value)}`",
        "",
        "*Динамика*",
        f"- Выручка к предыдущему дню: `{_signed_percent(metrics.revenue_delta_pct)}`",
        f"- Прибыль к предыдущему дню: `{_signed_percent(metrics.profit_delta_pct)}`",
        f"- Средняя выручка за 7 дней: `{_money_or_na(metrics.revenue_7d_avg)}`",
        f"- Средняя прибыль за 7 дней: `{_money_or_na(metrics.profit_7d_avg)}`",
    ]
    return "\n".join(lines)


def _money(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


def _money_or_na(value: float | None) -> str:
    if value is None:
        return "н/д"
    return _money(value)


def _percent(value: float | None) -> str:
    if value is None:
        return "н/д"
    return f"{value * 100:.2f}%"


def _signed_percent(value: float | None) -> str:
    if value is None:
        return "н/д"
    return f"{value * 100:+.2f}%"


def _escape_markdown(value: str) -> str:
    replacements = {
        "\\": "\\\\",
        "*": "\\*",
        "_": "\\_",
        "`": "\\`",
        "[": "\\[",
    }
    escaped = value
    for old, new in replacements.items():
        escaped = escaped.replace(old, new)
    return escaped
