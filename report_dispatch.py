"""Builds and runs the report calls the user requested via the CLI."""

from __future__ import annotations

import argparse
from typing import Any, Callable

from calculations import WeatherCalculator
from data_models import ReadingsByMonth
from report_generator import ConsoleReportGenerator
from report_service import ReportResult, WeatherReportService

ReportCall = Callable[[], ReportResult]


def _yearly_call(
    report_service: WeatherReportService, year: int, combined: bool
) -> ReportCall:
    return lambda: report_service.yearly_report(year)


def _monthly_call(
    report_service: WeatherReportService, year_month: tuple[int, int], combined: bool
) -> ReportCall:
    year, month = year_month
    return lambda: report_service.monthly_report(year, month)


def _daily_call(
    report_service: WeatherReportService, year_month: tuple[int, int], combined: bool
) -> ReportCall:
    year, month = year_month
    return lambda: report_service.daily_report(year, month, combined)


_REPORT_CALL_BUILDERS: dict[
    str, Callable[[WeatherReportService, Any, bool], ReportCall]
] = {
    "yearly": _yearly_call,
    "monthly": _monthly_call,
    "daily": _daily_call,
}


def _requested_report_calls(
    args: argparse.Namespace, report_service: WeatherReportService
) -> list[ReportCall]:
    """Builds one no-argument call per requested report, in the exact order
    and repetition the user typed -e/-a/-c on the command line."""
    return [
        _REPORT_CALL_BUILDERS[report_kind](
            report_service, report_argument, args.combined
        )
        for report_kind, report_argument in args.requested_reports
    ]


def build_requested_reports(
    args: argparse.Namespace, readings_by_month: ReadingsByMonth
) -> list[ReportResult]:
    """Computes every report the user asked for, in the order requested."""
    report_service = WeatherReportService(
        WeatherCalculator(readings_by_month), ConsoleReportGenerator()
    )

    return [
        produce_report()
        for produce_report in _requested_report_calls(args, report_service)
    ]
