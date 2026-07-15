"""CLI entry point for the Weatherman application."""

from __future__ import annotations

import os
import sys

from cli_arguments import build_argument_parser
from file_parser import WeatherDataParser
from readings_loader import WeatherReadingsLoader
from report_dispatch import build_requested_reports
from report_service import ReportResult


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
