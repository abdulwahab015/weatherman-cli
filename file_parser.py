"""Parses raw Weatherman data files into a dict of readings grouped by month"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional


from data_models import ReadingsByMonth, WeatherReading

logger = logging.getLogger(__name__)

NUMERIC_FIELDS = (
    "max_temp",
    "mean_temp",
    "min_temp",
    "max_humidity",
    "mean_humidity",
    "min_humidity",
)


def _parse_int(raw: Optional[str]) -> Optional[int]:
    """Convert a CSV cell to an int, treating blanks as missing data"""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(round(float(raw)))
    except ValueError:
        return None


def _parse_date(raw: str) -> Optional[date]:
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _row_to_reading(date_column: str, row: dict[str, str]) -> Optional[WeatherReading]:
    """Build one WeatherReading dict from a CSV row, or None if unusable."""
    reading_date = _parse_date(row.get(date_column, "") or "")
    if reading_date is None:
        return None

    reading: WeatherReading = {
        "date": reading_date,
        "max_temp": _parse_int(row.get("Max TemperatureC")),
        "mean_temp": _parse_int(row.get("Mean TemperatureC")),
        "min_temp": _parse_int(row.get("Min TemperatureC")),
        "max_humidity": _parse_int(row.get("Max Humidity")),
        "mean_humidity": _parse_int(row.get("Mean Humidity")),
        "min_humidity": _parse_int(row.get("Min Humidity")),
    }

    if all(reading[field] is None for field in NUMERIC_FIELDS):
        return None

    return reading


def parse_file(path: Path, readings_by_month: ReadingsByMonth) -> None:
    """Parse one file, adding each valid reading into readings_by_month.

    Mutates readings_by_month in place rather than returning a new dict,
    so parse_directory can stream several files into the same structure
    without holding multiple intermediate collections in memory at once.
    """
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return

        date_column = reader.fieldnames[0].strip()

        for line_number, raw_row in enumerate(reader, start=2):
            row = {
                key.strip(): value for key, value in raw_row.items() if key is not None
            }
            reading = _row_to_reading(date_column, row)
            if reading is None:
                logger.debug(
                    "%s line %d: skipped (bad date or fully blank row)",
                    path.name,
                    line_number,
                )
                continue

            month_key = (reading["date"].year, reading["date"].month)
            readings_by_month.setdefault(month_key, []).append(reading)


def parse_directory(directory: Path) -> ReadingsByMonth:
    """Parse every .txt file in directory into one dict keyed by (year, month)."""
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a valid directory")

    files = sorted(directory.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No .txt weather files found in {directory}")

    readings_by_month: ReadingsByMonth = {}
    for file_path in files:
        try:
            parse_file(file_path, readings_by_month)
        except (OSError, csv.Error) as exc:
            logger.warning("Skipping unreadable file %s: %s", file_path.name, exc)

    return readings_by_month
