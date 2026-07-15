"""Shared CLI, dispatch, and orchestration helpers for the Weatherman application."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from calculations import WeatherCalculator
from data_models import ReadingsByMonth
from file_parser import WeatherDataParser
from report_generator import ConsoleReportGenerator

ReportResult = tuple[Optional[str], Optional[str]]
ReportCall = Callable[[], ReportResult]
CalculationResult = TypeVar("CalculationResult")


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


class CliArgumentParser:
    """Builds the command-line argument parser for the Weatherman CLI."""

    @staticmethod
    def parse_year_month(raw_year_month: str) -> tuple[int, int]:
        """Parses a 'YYYY/M' string into an integer tuple of (year, month)."""
        try:
            year_text, month_text = raw_year_month.split("/")
            return int(year_text), int(month_text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"expected YYYY/M, got {raw_year_month!r}"
            ) from exc

    def build(self) -> argparse.ArgumentParser:
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
                self.parse_year_month,
                "YEAR/MONTH",
                "Monthly averages report",
                "monthly",
            ),
            (
                "-c",
                self.parse_year_month,
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


class WeatherReadingsLoader:
    """Reads every weather file in a directory and aggregates the readings by month."""

    def __init__(self, file_parser: WeatherDataParser) -> None:
        """Injects the required single-file parser dependency."""
        self.file_parser = file_parser

    def load_directory(self, directory_path: Path) -> ReadingsByMonth:
        """Scans a directory and aggregates all valid observations bucketed by year and month."""
        weather_files = self._find_weather_files(directory_path)
        readings_by_month: ReadingsByMonth = {}

        for file_path in weather_files:
            try:
                self._add_file_readings(file_path, readings_by_month)
            except (OSError, csv.Error):
                continue

        return readings_by_month

    def _find_weather_files(self, directory_path: Path) -> list[Path]:
        """Validates the directory and returns the .txt files inside it."""
        if not directory_path.is_dir():
            raise NotADirectoryError(f"'{directory_path}' is not a valid directory")

        weather_files = sorted(directory_path.glob("*.txt"))
        if not weather_files:
            raise FileNotFoundError(
                f"No .txt weather files found in '{directory_path}'"
            )

        return weather_files

    def _add_file_readings(
        self, file_path: Path, readings_by_month: ReadingsByMonth
    ) -> None:
        """Parses one file and merges its readings into the shared month buckets."""
        for weather_reading in self.file_parser.parse_file(file_path):
            month_key = (
                weather_reading.reading_date.year,
                weather_reading.reading_date.month,
            )
            readings_by_month.setdefault(month_key, []).append(weather_reading)


class WeatherReportService:
    """Produces rendered report text for one report type, or a not-found message."""

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
        """Runs compute(); renders the result if found, otherwise reports why not."""
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


class RequestedReportBuilder:
    """Builds and runs the report calls the user requested via the CLI."""

    def __init__(self, readings_by_month: ReadingsByMonth) -> None:
        self.report_service = WeatherReportService(
            WeatherCalculator(readings_by_month), ConsoleReportGenerator()
        )
        self._call_builders: dict[str, Callable[[Any, bool], ReportCall]] = {
            "yearly": self._yearly_call,
            "monthly": self._monthly_call,
            "daily": self._daily_call,
        }

    def _yearly_call(self, year: int, combined: bool) -> ReportCall:
        return lambda: self.report_service.yearly_report(year)

    def _monthly_call(self, year_month: tuple[int, int], combined: bool) -> ReportCall:
        year, month = year_month
        return lambda: self.report_service.monthly_report(year, month)

    def _daily_call(self, year_month: tuple[int, int], combined: bool) -> ReportCall:
        year, month = year_month
        return lambda: self.report_service.daily_report(year, month, combined)

    def _requested_calls(self, args: argparse.Namespace) -> list[ReportCall]:
        """Builds one no-argument call per requested report, in the exact order
        and repetition the user typed -e/-a/-c on the command line."""
        return [
            self._call_builders[report_kind](report_argument, args.combined)
            for report_kind, report_argument in args.requested_reports
        ]

    def build_reports(self, args: argparse.Namespace) -> list[ReportResult]:
        """Computes every report the user asked for, in the order requested."""
        return [produce_report() for produce_report in self._requested_calls(args)]
