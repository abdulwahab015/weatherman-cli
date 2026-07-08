import calendar
from datetime import date

from data_models import DailyExtremes, MonthlyAverages, YearlyExtremes

RED = "\033[31m"
BLUE = "\033[34m"
RESET = "\033[0m"


def _month_day(value: date) -> str:
    """Render e.g. 'June 23' without relying on platform-specific strftime flags."""
    return f"{value.strftime('%B')} {value.day}"


def render_yearly_extremes(result: YearlyExtremes) -> str:
    return "\n".join(
        [
            f"Highest: {result['highest_temp']:02d}C on "
            f"{_month_day(result['highest_temp_date'])}",
            f"Lowest: {result['lowest_temp']:02d}C on "
            f"{_month_day(result['lowest_temp_date'])}",
            f"Humidity: {result['most_humid_value']}% on "
            f"{_month_day(result['most_humid_date'])}",
        ]
    )


def render_monthly_averages(result: MonthlyAverages) -> str:
    return "\n".join(
        [
            f"Highest Average: {result['avg_highest_temp']:.0f}C",
            f"Lowest Average: {result['avg_lowest_temp']:.0f}C",
            f"Average Mean Humidity: {result['avg_mean_humidity']:.0f}%",
        ]
    )


def render_daily_bar_charts(year: int, month: int, days: list[DailyExtremes]) -> str:
    """Two bars per day: red for the day's high, blue for the day's low."""
    lines = [f"{calendar.month_name[month]} {year}"]
    for entry in days:
        label = f"{entry['day']:02d}"
        max_temp = entry["max_temp"]
        min_temp = entry["min_temp"]
        if max_temp is not None:
            lines.append(f"{label} {RED}{'+' * max_temp}{RESET} {max_temp:02d}C")
        if min_temp is not None:
            lines.append(f"{label} {BLUE}{'+' * min_temp}{RESET} {min_temp:02d}C")
    return "\n".join(lines)


def render_daily_bar_chart_combined(
    year: int, month: int, days: list[DailyExtremes]
) -> str:
    """Bonus report: one bar per day - blue segment (low) then red segment (high)."""
    lines = [f"{calendar.month_name[month]} {year}"]
    for entry in days:
        max_temp = entry["max_temp"]
        min_temp = entry["min_temp"]
        if max_temp is None or min_temp is None:
            continue
        label = f"{entry['day']:02d}"
        bar = f"{BLUE}{'+' * min_temp}{RESET}{RED}{'+' * max_temp}{RESET}"
        lines.append(f"{label} {bar} {min_temp:02d}C - {max_temp:02d}C")
    return "\n".join(lines)
