"""Formats computed results into the report strings printed to the console."""

from __future__ import annotations

import calendar
from datetime import date
from typing import List

from constants import ANSI_BLUE, ANSI_RED, ANSI_RESET
from data_models import DailyExtreme, MonthlyAverages, YearlyExtremes


def format_month_and_day(reading_date: date) -> str:
    """Render e.g. 'June 23' without relying on platform-specific strftime flags."""
    return f"{reading_date.strftime('%B')} {reading_date.day}"


def format_month_and_year_header(year: int, month: int) -> str:
    return f"{calendar.month_name[month]} {year}"


def _colored_bar(color: str, length: int) -> str:
    """Build one colored run of '+' characters for a single bar-chart segment."""
    return f"{color}{'+' * length}{ANSI_RESET}"


def _format_extreme_line(label: str, value_text: str, extreme_date: date) -> str:
    """Build one 'Label: value on Month Day' line, used by render_yearly_extremes."""
    return f"{label}: {value_text} on {format_month_and_day(extreme_date)}"


def _format_bar_line(label: str, color: str, temp: int) -> str:
    """Build one 'DD [bar] NNC' line, used by render_daily_bar_charts."""
    return f"{label} {_colored_bar(color, temp)} {temp:02d}C"


def render_yearly_extremes(result: YearlyExtremes) -> str:
    return "\n".join(
        [
            _format_extreme_line(
                "Highest", f"{result.highest_temp:02d}C", result.highest_temp_date
            ),
            _format_extreme_line(
                "Lowest", f"{result.lowest_temp:02d}C", result.lowest_temp_date
            ),
            _format_extreme_line(
                "Humidity", f"{result.most_humid_value}%", result.most_humid_date
            ),
        ]
    )


def render_monthly_averages(result: MonthlyAverages) -> str:
    return "\n".join(
        [
            f"Highest Average: {result.avg_highest_temp:.0f}C",
            f"Lowest Average: {result.avg_lowest_temp:.0f}C",
            f"Average Mean Humidity: {result.avg_mean_humidity:.0f}%",
        ]
    )


def render_separate_temperature_bars(
    year: int, month: int, days: List[DailyExtreme]
) -> str:
    """Two bars per day: red for the day's high, blue for the day's low."""
    lines = [format_month_and_year_header(year, month)]
    for day_extreme in days:
        label = f"{day_extreme.day:02d}"
        if day_extreme.max_temp is not None:
            lines.append(_format_bar_line(label, ANSI_RED, day_extreme.max_temp))
        if day_extreme.min_temp is not None:
            lines.append(_format_bar_line(label, ANSI_BLUE, day_extreme.min_temp))
    return "\n".join(lines)


def render_combined_temperature_bars(
    year: int, month: int, days: List[DailyExtreme]
) -> str:
    """Bonus report: one bar per day - blue segment (low) then red segment (high)."""
    lines = [format_month_and_year_header(year, month)]
    for day_extreme in days:
        if day_extreme.min_temp is None or day_extreme.max_temp is None:
            continue
        label = f"{day_extreme.day:02d}"
        bar = _colored_bar(ANSI_BLUE, day_extreme.min_temp) + _colored_bar(
            ANSI_RED, day_extreme.max_temp
        )
        lines.append(
            f"{label} {bar} {day_extreme.min_temp:02d}C - {day_extreme.max_temp:02d}C"
        )
    return "\n".join(lines)
