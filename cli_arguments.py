"""Command-line argument parsing setup for the Weatherman application."""

from __future__ import annotations

import argparse
from pathlib import Path


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
