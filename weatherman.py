"""CLI entry point for the Weatherman application."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable

from calculations import WeatherCalculator
from data_models import ReadingsByMonth
from file_parser import WeatherDataParser
from readings_loader import WeatherReadingsLoader
from report_generator import ConsoleReportGenerator
from report_service import ReportResult, WeatherReportService

ReportCall = Callable[[], ReportResult]


def parse_year_month_argument(raw_year_month: str) -> tuple[int, int]:
    """Parses a 'YYYY/M' string into an integer tuple of (year, month)."""
    try:
        year_text, month_text = raw_year_month.split("/")
        return int(year_text), int(month_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"expected YYYY/M, got {raw_year_month!r}"
        ) from exc


class _RecordReportRequestAction(argparse.Action):
    """Argparse action that records every -e/-a/-c occurrence in one shared
    list, in the exact order and repetition they were typed on the command
    line.
    """

    def __call__(self, parser, namespace, values, _option_string=None):
        requested_reports = getattr(namespace, self.dest, None)
        if requested_reports is None:
            requested_reports = []
            setattr(namespace, self.dest, requested_reports)

        requested_reports.append((self.const, values))


def build_argument_parser() -> argparse.ArgumentParser:
    """Constructs the command-line interface argument parser."""
    parser = argparse.ArgumentParser(
        prog="weatherman.py",
        description="Generate reports from historical weather data files.",
    )

    parser.add_argument(
        "directory", type=Path, help="Directory containing weather .txt files"
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Render -c as one combined bar per day (bonus report) instead of two bars",
    )

    report_argument_specs = [
        ("-e", int, "YEAR", "Yearly extremes report", "yearly"),
        (
            "-a",
            parse_year_month_argument,
            "YEAR/MONTH",
            "Monthly averages report",
            "monthly",
        ),
        (
            "-c",
            parse_year_month_argument,
            "YEAR/MONTH",
            "Daily bar chart report",
            "daily",
        ),
    ]

    for flag, arg_type, metavar, help_text, report_kind in report_argument_specs:
        parser.add_argument(
            flag,
            type=arg_type,
            metavar=metavar,
            help=help_text,
            action=_RecordReportRequestAction,
            dest="requested_reports",
            const=report_kind,
        )

    return parser


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


def _format_report_result(report_result: ReportResult) -> str:
    """Renders one report's outcome as printable text: its report text if
    it succeeded, or an 'Error: ...' line if it didn't."""
    report_text, error_message = report_result

    return report_text if error_message is None else f"Error: {error_message}"


def main(argv: list[str] | None = None) -> int:
    """Orchestrates the lifecycle of parsing data, calculating metrics, and printing reports."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if not args.requested_reports:
        parser.error("at least one of -e, -a, -c is required")

    report_results: list[ReportResult] = []
    directory_error_message: str | None = None

    try:
        readings_loader = WeatherReadingsLoader(WeatherDataParser())
        readings_by_month = readings_loader.load_directory(args.directory)
    except (NotADirectoryError, FileNotFoundError) as exc:
        directory_error_message = str(exc)
    else:
        report_results = build_requested_reports(args, readings_by_month)

    if directory_error_message is not None:
        print(f"Error: {directory_error_message}", file=sys.stderr)
        exit_code = 1
    else:
        output_lines = [_format_report_result(result) for result in report_results]
        any_report_failed = any(error is not None for _, error in report_results)
        print("\n\n".join(output_lines))
        exit_code = 1 if any_report_failed else 0

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(1)
