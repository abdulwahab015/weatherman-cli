from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from calculations import NoDataError, daily_extremes, monthly_averages, yearly_extremes
from file_parser import parse_directory
from report_generator import (
    render_daily_bar_chart_combined,
    render_daily_bar_charts,
    render_monthly_averages,
    render_yearly_extremes,
)


def _year_month(value: str) -> Tuple[int, int]:
    """argparse type-hook: parse 'YYYY/M' into (year, month)."""
    try:
        year_str, month_str = value.split("/")
        return int(year_str), int(month_str)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY/M, got {value!r}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weatherman.py",
        description="Generate reports from historical weather data files.",
    )
    parser.add_argument(
        "directory", type=Path, help="Directory containing weather .txt files"
    )
    parser.add_argument("-e", type=int, metavar="YEAR", help="Yearly extremes report")
    parser.add_argument(
        "-a", type=_year_month, metavar="YEAR/MONTH", help="Monthly averages report"
    )
    parser.add_argument(
        "-c", type=_year_month, metavar="YEAR/MONTH", help="Daily bar chart report"
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Render -c as one combined bar per day (bonus report) instead of two bars",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.e is None and args.a is None and args.c is None:
        parser.error("at least one of -e, -a, -c is required")

    try:
        readings_by_month = parse_directory(args.directory)
    except (NotADirectoryError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    sections: List[str] = []
    try:
        if args.e is not None:
            result = yearly_extremes(readings_by_month, args.e)
            sections.append(render_yearly_extremes(result))
        if args.a is not None:
            year, month = args.a
            result = monthly_averages(readings_by_month, year, month)
            sections.append(render_monthly_averages(result))
        if args.c is not None:
            year, month = args.c
            days = daily_extremes(readings_by_month, year, month)
            renderer = (
                render_daily_bar_chart_combined
                if args.combined
                else render_daily_bar_charts
            )
            sections.append(renderer(year, month, days))
    except NoDataError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\n\n".join(sections))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Output was piped into something like `head` that closed early.
        # Silence the noisy traceback; exit non-zero is still accurate.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
