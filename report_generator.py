"""Generates formatted console reports from weather data calculations."""

from __future__ import annotations

import calendar
from datetime import date

from constants import ANSI_BLUE, ANSI_RED, ANSI_RESET
from data_models import DailyExtreme, MonthlyAverages, YearlyExtremes


class ConsoleReportGenerator:
    """Formats calculation results into standard text reports for the console."""

    def _format_month_day(self, reading_date: date) -> str:
        """Formats a date as 'Month Day' (e.g., 'June 23')."""
        return f"{reading_date.strftime('%B')} {reading_date.day}"

    def _format_month_year(self, year: int, month: int) -> str:
        """Formats a header as 'Month Year' (e.g., 'March 2011')."""
        return f"{calendar.month_name[month]} {year}"

    def _build_colored_bar(self, color: str, length: int) -> str:
        """Generates a colored sequence of plus signs for charts."""
        # Ensure length is not negative to prevent string multiplication bugs
        safe_length = max(0, length)
        return f"{color}{'+' * safe_length}{ANSI_RESET}"

    def render_yearly_extremes(self, result: YearlyExtremes) -> str:
        """Renders whichever of the three metrics are actually available."""
        lines = []

        if result.highest_temp is not None:
            lines.append(
                f"Highest: {result.highest_temp:02d}C on "
                f"{self._format_month_day(result.highest_temp_date)}"
            )

        if result.lowest_temp is not None:
            lines.append(
                f"Lowest: {result.lowest_temp:02d}C on "
                f"{self._format_month_day(result.lowest_temp_date)}"
            )

        if result.most_humid_value is not None:
            lines.append(
                f"Humidity: {result.most_humid_value}% on "
                f"{self._format_month_day(result.most_humid_date)}"
            )

        return "\n".join(lines)

    def render_monthly_averages(self, result: MonthlyAverages) -> str:
        """Renders whichever averages are actually available."""
        lines = []

        if result.avg_highest_temp is not None:
            lines.append(f"Highest Average: {result.avg_highest_temp:.0f}C")

        if result.avg_lowest_temp is not None:
            lines.append(f"Lowest Average: {result.avg_lowest_temp:.0f}C")

        if result.avg_mean_humidity is not None:
            lines.append(f"Average Mean Humidity: {result.avg_mean_humidity:.0f}%")

        return "\n".join(lines)

    def render_separate_temperature_bars(
        self, year: int, month: int, days: list[DailyExtreme]
    ) -> str:
        """Renders two individual colored bars (high and low) per day for a specific month."""
        lines = [self._format_month_year(year, month)]

        for day_extreme in days:
            label = f"{day_extreme.day:02d}"

            if day_extreme.max_temp is not None:
                red_bar = self._build_colored_bar(ANSI_RED, day_extreme.max_temp)
                lines.append(f"{label} {red_bar} {day_extreme.max_temp:02d}C")

            if day_extreme.min_temp is not None:
                blue_bar = self._build_colored_bar(ANSI_BLUE, day_extreme.min_temp)
                lines.append(f"{label} {blue_bar} {day_extreme.min_temp:02d}C")

        return "\n".join(lines)

    def render_combined_temperature_bars(
        self, year: int, month: int, days: list[DailyExtreme]
    ) -> str:
        """Renders a single unified bar (low and high) per day for a specific month."""
        lines = [self._format_month_year(year, month)]

        for day_extreme in days:
            if day_extreme.min_temp is None or day_extreme.max_temp is None:
                continue

            label = f"{day_extreme.day:02d}"
            blue_segment = self._build_colored_bar(ANSI_BLUE, day_extreme.min_temp)
            red_segment = self._build_colored_bar(ANSI_RED, day_extreme.max_temp)

            lines.append(
                f"{label} {blue_segment}{red_segment} {day_extreme.min_temp:02d}C - {day_extreme.max_temp:02d}C"
            )

        return "\n".join(lines)
