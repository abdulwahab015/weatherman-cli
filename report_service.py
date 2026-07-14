"""Combines calculation and rendering into complete report text or an error message."""

from __future__ import annotations

from typing import Callable, Optional, TypeVar

from calculations import WeatherCalculator
from report_generator import ConsoleReportGenerator

ReportResult = tuple[Optional[str], Optional[str]]

CalculationResult = TypeVar("CalculationResult")


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

    def _build_report(
        self,
        compute: Callable[[], Optional[CalculationResult]],
        render: Callable[[CalculationResult], str],
        not_found_message: str,
    ) -> ReportResult:
        """Runs compute(); renders the result if found, otherwise reports why not.

        Shared by yearly_report/monthly_report/daily_report below, since all
        three follow the same shape and only differ in which calculation to
        run, how to render it, and what "not found" means for that report.
        """
        result = compute()
        text = render(result) if result is not None else None
        error = None if result is not None else not_found_message

        return text, error

    def yearly_report(self, year: int) -> ReportResult:
        """Returns (rendered_text, error_message) - exactly one of the two is None."""
        return self._build_report(
            lambda: self.calculator.calculate_yearly_extremes(year),
            self.reporter.render_yearly_extremes,
            f"No readings found for year {year}",
        )

    def monthly_report(self, year: int, month: int) -> ReportResult:
        return self._build_report(
            lambda: self.calculator.calculate_monthly_averages(year, month),
            self.reporter.render_monthly_averages,
            f"No readings found for {year}-{month:02d}",
        )

    def daily_report(self, year: int, month: int, combined: bool) -> ReportResult:
        render_chart = (
            self.reporter.render_combined_temperature_bars
            if combined
            else self.reporter.render_separate_temperature_bars
        )

        return self._build_report(
            lambda: self.calculator.calculate_daily_extremes(year, month),
            lambda days: render_chart(year, month, days),
            f"No readings found for {year}-{month:02d}",
        )
