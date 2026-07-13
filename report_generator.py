"""Generates formatted console reports from weather data calculations."""

from __future__ import annotations

import calendar
from datetime import date

from constants import ANSI_BLUE, ANSI_RED, ANSI_RESET
from data_models import DailyExtreme, MonthlyAverages, YearlyExtremes


class ConsoleReportGenerator:
    """Formats calculation results into standard text reports for the console."""

    def _format_month_day(self, value: date) -> str:
        """Formats a date as 'Month Day' (e.g., 'June 23')."""
        return f"{value.strftime('%B')} {value.day}"

    def _format_month_year(self, year: int, month: int) -> str:
        """Formats a header as 'Month Year' (e.g., 'March 2011')."""
        return f"{calendar.month_name[month]} {year}"

    def _build_colored_bar(self, color: str, length: int) -> str:
        """Generates a colored sequence of plus signs for charts."""
        safe_length = max(0, length)

        return f"{color}{'+' * safe_length}{ANSI_RESET}"

    def render_yearly_extremes(self, result: YearlyExtremes) -> str:
        """Renders whichever of the three metrics are actually available."""
        metrics = [
            (result.highest_temp, "Highest", "{:02d}C", result.highest_temp_date),
            (result.lowest_temp, "Lowest", "{:02d}C", result.lowest_temp_date),
            (result.most_humid_value, "Humidity", "{}%", result.most_humid_date),
        ]

        lines = [
            f"{label}: {value_format.format(value)} on "
            f"{self._format_month_day(extreme_date)}"
            for value, label, value_format, extreme_date in metrics
            if value is not None
        ]

        return "\n".join(lines)

    def render_monthly_averages(self, result: MonthlyAverages) -> str:
        """Renders whichever averages are actually available."""
        metrics = [
            (result.avg_highest_temp, "Highest Average", "{:.0f}C"),
            (result.avg_lowest_temp, "Lowest Average", "{:.0f}C"),
            (result.avg_mean_humidity, "Average Mean Humidity", "{:.0f}%"),
        ]

        lines = [
            f"{label}: {value_format.format(value)}"
            for value, label, value_format in metrics
            if value is not None
        ]

        return "\n".join(lines)

    def _separate_bar_line(
        self, day_extreme: DailyExtreme, temp: int, color: str
    ) -> str:
        """Renders one 'DD [bar] NNC' line for a single high or low temperature."""
        label = f"{day_extreme.day:02d}"
        bar = self._build_colored_bar(color, temp)

        return f"{label} {bar} {temp:02d}C"

    def render_separate_temperature_bars(
        self, year: int, month: int, days: list[DailyExtreme]
    ) -> str:
        """Renders two individual colored bars (high and low) per day for a specific month."""
        header = [self._format_month_year(year, month)]

        bar_lines = [
            self._separate_bar_line(day_extreme, temp, color)
            for day_extreme in days
            for temp, color in (
                (day_extreme.max_temp, ANSI_RED),
                (day_extreme.min_temp, ANSI_BLUE),
            )
            if temp is not None
        ]

        return "\n".join(header + bar_lines)

    def _combined_bar_line(self, day_extreme: DailyExtreme) -> str:
        """Renders one 'DD [bar] lowC - highC' line for a single day."""
        label = f"{day_extreme.day:02d}"
        blue_segment = self._build_colored_bar(ANSI_BLUE, day_extreme.min_temp)
        red_segment = self._build_colored_bar(ANSI_RED, day_extreme.max_temp)

        return (
            f"{label} {blue_segment}{red_segment} "
            f"{day_extreme.min_temp:02d}C - {day_extreme.max_temp:02d}C"
        )

    def render_combined_temperature_bars(
        self, year: int, month: int, days: list[DailyExtreme]
    ) -> str:
        """Renders a single unified bar (low and high) per day for a specific month."""
        header = [self._format_month_year(year, month)]

        bar_lines = [
            self._combined_bar_line(day_extreme)
            for day_extreme in days
            if day_extreme.min_temp is not None and day_extreme.max_temp is not None
        ]

        return "\n".join(header + bar_lines)
