"""CLI entry point for the Weatherman application."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from calculations import WeatherCalculator
from data_models import ReadingsByMonth
from file_parser import DirectoryParser, WeatherDataParser
from report_generator import ConsoleReportGenerator
from report_service import ReportResult, WeatherReportService

ReportCall = Callable[[], ReportResult]


def parse_year_month_argument(value: str) -> tuple[int, int]:
    """Parses a 'YYYY/M' string into an integer tuple of (year, month)."""
    try:
        year_text, month_text = value.split("/")
        return int(year_text), int(month_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY/M, got {value!r}") from exc


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

    reports = [
        ("-e", int, "YEAR", "Yearly extremes report"),
        ("-a", parse_year_month_argument, "YEAR/MONTH", "Monthly averages report"),
        ("-c", parse_year_month_argument, "YEAR/MONTH", "Daily bar chart report"),
    ]

    for flag, arg_type, metavar, help_text in reports:
        parser.add_argument(flag, type=arg_type, metavar=metavar, help=help_text)

    return parser


def _requested_report_calls(
    args: argparse.Namespace, report_service: WeatherReportService
) -> list[ReportCall]:
    """Builds one no-argument call per requested report, in a fixed order."""
    possible_reports: list[tuple[Any, ReportCall]] = [
        (args.e, lambda: report_service.yearly_report(args.e)),
        (args.a, lambda: report_service.monthly_report(*args.a)),
        (args.c, lambda: report_service.daily_report(*args.c, args.combined)),
    ]

    return [call for requested, call in possible_reports if requested is not None]


def build_requested_reports(
    args: argparse.Namespace, readings_by_month: ReadingsByMonth
) -> tuple[list[str], Optional[str]]:
    """Computes and renders every report the user asked for, in a fixed order."""
    report_service = WeatherReportService(
        WeatherCalculator(readings_by_month), ConsoleReportGenerator()
    )
    sections: list[str] = []

    for produce_report in _requested_report_calls(args, report_service):
        text, error = produce_report()
        if error:
            return sections, error
        sections.append(text)

    return sections, None


def main(argv: list[str] | None = None) -> int:
    """Orchestrates the lifecycle of parsing data, calculating metrics, and printing reports."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if not any((args.e, args.a, args.c)):
        parser.error("at least one of -e, -a, -c is required")

    sections: list[str] = []
    error_message: str | None = None

    try:
        directory_parser = DirectoryParser(WeatherDataParser())
        readings_by_month = directory_parser.process_directory(args.directory)
    except (NotADirectoryError, FileNotFoundError) as exc:
        error_message = str(exc)
    else:
        sections, error_message = build_requested_reports(args, readings_by_month)

    if error_message is not None:
        print(f"Error: {error_message}", file=sys.stderr)
        exit_code = 1
    else:
        print("\n\n".join(sections))
        exit_code = 0

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(1)
