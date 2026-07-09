"""CLI entry point for the Weatherman application."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from calculations import (
    calculate_daily_extremes,
    calculate_monthly_averages,
    calculate_yearly_extremes,
)
from data_models import ReadingsByMonth
from file_parser import parse_directory
from report_generator import (
    render_combined_temperature_bars,
    render_separate_temperature_bars,
    render_monthly_averages,
    render_yearly_extremes,
)


def parse_year_month_argument(value: str) -> Tuple[int, int]:
    """argparse type-hook: parse 'YYYY/M' into (year, month)."""
    try:
        year_text, month_text = value.split("/")
        return int(year_text), int(month_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY/M, got {value!r}") from exc


def build_argument_parser() -> argparse.ArgumentParser:
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

    # DRY Improvement: Loop through similar report arguments
    reports = [
        ("-e", int, "YEAR", "Yearly extremes report"),
        ("-a", parse_year_month_argument, "YEAR/MONTH", "Monthly averages report"),
        ("-c", parse_year_month_argument, "YEAR/MONTH", "Daily bar chart report"),
    ]

    for flag, arg_type, metavar, help_text in reports:
        parser.add_argument(flag, type=arg_type, metavar=metavar, help=help_text)

    return parser


def build_requested_reports(
    args: argparse.Namespace, readings_by_month: ReadingsByMonth
) -> Tuple[List[str], Optional[str]]:
    """Compute and render every report the user asked for, in a fixed order."""
    reports: List[str] = []

    if args.e is not None:
        yearly_result = calculate_yearly_extremes(readings_by_month, args.e)
        if yearly_result is None:
            return reports, f"No readings found for year {args.e}"
        reports.append(render_yearly_extremes(yearly_result))

    if args.a is not None:
        year, month = args.a
        monthly_result = calculate_monthly_averages(readings_by_month, year, month)
        if monthly_result is None:
            return reports, f"No readings found for {year}-{month:02d}"
        reports.append(render_monthly_averages(monthly_result))

    if args.c is not None:
        year, month = args.c
        daily_results = calculate_daily_extremes(readings_by_month, year, month)
        if daily_results is None:
            return reports, f"No readings found for {year}-{month:02d}"
        render_chart = (
            render_combined_temperature_bars
            if args.combined
            else render_separate_temperature_bars
        )
        reports.append(render_chart(year, month, daily_results))

    return reports, None


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.e is None and args.a is None and args.c is None:
        parser.error("at least one of -e, -a, -c is required")

    try:
        # 1. Parse Data
        readings_by_month = parse_directory(args.directory)

        # 2. Generate Sections
        sections: List[str] = []
        if args.e is not None:
            result = calculate_yearly_extremes(readings_by_month, args.e)
            sections.append(render_yearly_extremes(result))

        if args.a is not None:
            year, month = args.a
            result = calculate_monthly_averages(readings_by_month, year, month)
            sections.append(render_monthly_averages(result))

        if args.c is not None:
            year, month = args.c
            days = calculate_daily_extremes(readings_by_month, year, month)
            renderer = (
                render_combined_temperature_bars
                if args.combined
                else render_separate_temperature_bars
            )
            sections.append(renderer(year, month, days))

        # 3. Output
        print("\n\n".join(sections))
        return 0

    # Consolidated Error Handling
    except (NotADirectoryError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(1)
