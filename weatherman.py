"""CLI entry point for the Weatherman application."""

from __future__ import annotations

import os
import sys

from file_parser import WeatherDataParser
from helpers import build_argument_parser, build_requested_reports, format_report_result
from readings_loader import WeatherReadingsLoader


def main(argv: list[str] | None = None) -> int:
    """Orchestrates the lifecycle of parsing data, calculating metrics, and printing reports."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if not args.requested_reports:
        parser.error("at least one of -e, -a, -c is required")

    try:
        readings_loader = WeatherReadingsLoader(WeatherDataParser())
        readings_by_month = readings_loader.load_directory(args.directory)
    except (NotADirectoryError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report_results = build_requested_reports(args, readings_by_month)
    formatted_reports = [format_report_result(result) for result in report_results]
    any_report_failed = any(error is not None for _, error in report_results)
    print("\n\n".join(formatted_reports))

    exit_code = 1 if any_report_failed else 0

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(1)
