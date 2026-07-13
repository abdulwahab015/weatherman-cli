"""Combines calculation and rendering into complete report text or an error message."""

from __future__ import annotations

from typing import Optional

from calculations import WeatherCalculator
from report_generator import ConsoleReportGenerator

ReportResult = tuple[Optional[str], Optional[str]]


class WeatherReportService:
    """Produces rendered report text for one report type, or a not-found message.

    Each method assumes the caller has already decided this report was
    requested - no re-validation of that decision happens here.
    """

    def __init__(
        self, calculator: WeatherCalculator, reporter: ConsoleReportGenerator
    ) -> None:
        self.calculator = calculator
        self.reporter = reporter

    def yearly_report(self, year: int) -> ReportResult:
        """Returns (rendered_text, error_message) - exactly one of the two is None."""
        result = self.calculator.calculate_yearly_extremes(year)
        text: Optional[str] = None
        error: Optional[str] = None

        if result is None:
            error = f"No readings found for year {year}"
        else:
            text = self.reporter.render_yearly_extremes(result)

        return text, error

    def monthly_report(self, year: int, month: int) -> ReportResult:
        result = self.calculator.calculate_monthly_averages(year, month)
        text: Optional[str] = None
        error: Optional[str] = None

        if result is None:
            error = f"No readings found for {year}-{month:02d}"
        else:
            text = self.reporter.render_monthly_averages(result)

        return text, error

    def daily_report(self, year: int, month: int, combined: bool) -> ReportResult:
        result = self.calculator.calculate_daily_extremes(year, month)
        text: Optional[str] = None
        error: Optional[str] = None

        if result is None:
            error = f"No readings found for {year}-{month:02d}"
        else:
            render = (
                self.reporter.render_combined_temperature_bars
                if combined
                else self.reporter.render_separate_temperature_bars
            )
            text = render(year, month, result)

        return text, error
