"""Reads raw Weatherman data files into WeatherReading records."""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from constants import (
    COLUMN_MAX_HUMIDITY,
    COLUMN_MAX_TEMP,
    COLUMN_MEAN_HUMIDITY,
    COLUMN_MEAN_TEMP,
    COLUMN_MIN_HUMIDITY,
    COLUMN_MIN_TEMP,
    DATE_FORMAT,
)
from data_models import ReadingsByMonth, WeatherReading

logger = logging.getLogger(__name__)

# Maps each WeatherReading numeric field name to the CSV column it comes
# from. Iterating this in one place - instead of six near-identical lines
# repeated wherever fields are read - is what keeps column names DRY.
NUMERIC_COLUMNS_BY_FIELD = {
    "max_temp": COLUMN_MAX_TEMP,
    "mean_temp": COLUMN_MEAN_TEMP,
    "min_temp": COLUMN_MIN_TEMP,
    "max_humidity": COLUMN_MAX_HUMIDITY,
    "mean_humidity": COLUMN_MEAN_HUMIDITY,
    "min_humidity": COLUMN_MIN_HUMIDITY,
}


def _parse_numeric_cell(raw_value: Optional[str]) -> Optional[int]:
    """Convert a CSV cell to an int; blanks or non-numeric text become None."""
    stripped_value = (raw_value or "").strip()
    parsed_value: Optional[int] = None
    if stripped_value:
        try:
            parsed_value = int(round(float(stripped_value)))
        except ValueError:
            parsed_value = None
    return parsed_value


def _parse_reading_date(raw_value: str) -> Optional[date]:
    """Parse a date cell; anything not matching DATE_FORMAT becomes None."""
    parsed_date: Optional[date] = None
    try:
        parsed_date = datetime.strptime(raw_value.strip(), DATE_FORMAT).date()
    except ValueError:
        parsed_date = None
    return parsed_date


def _normalize_row_keys(raw_row: Dict[str, str]) -> Dict[str, str]:
    """Strip stray whitespace from column names, e.g. ' Mean Humidity'."""
    return {key.strip(): value for key, value in raw_row.items() if key is not None}


def _extract_numeric_fields(row: Dict[str, str]) -> Dict[str, Optional[int]]:
    """Pull and parse all six numeric columns from one CSV row."""
    return {
        field_name: _parse_numeric_cell(row.get(column_name))
        for field_name, column_name in NUMERIC_COLUMNS_BY_FIELD.items()
    }


def _has_any_numeric_data(numeric_fields: Dict[str, Optional[int]]) -> bool:
    """A row is only usable if at least one numeric field was present."""
    return any(value is not None for value in numeric_fields.values())


def _build_reading_from_row(
    date_column_name: str, row: Dict[str, str]
) -> Optional[WeatherReading]:
    """Build one WeatherReading from a CSV row, or None if the row is unusable."""
    reading: Optional[WeatherReading] = None
    reading_date = _parse_reading_date(row.get(date_column_name, "") or "")

    if reading_date:
        numeric_fields = _extract_numeric_fields(row)
        if _has_any_numeric_data(numeric_fields):
            reading = WeatherReading(date=reading_date, **numeric_fields)

    return reading


def read_readings_from_file(path: Path) -> Iterator[WeatherReading]:
    """Yield one WeatherReading per usable row in a single weather file."""
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return

        date_column_name = reader.fieldnames[0].strip()

        for line_number, raw_row in enumerate(reader, start=2):
            row = _normalize_row_keys(raw_row)
            reading = _build_reading_from_row(date_column_name, row)
            if reading is None:
                logger.debug(
                    "%s line %d: skipped (bad date or fully blank row)",
                    path.name,
                    line_number,
                )
                continue
            yield reading


def group_readings_by_month(readings: Iterable[WeatherReading]) -> ReadingsByMonth:
    """Index a flat stream of readings into a dict keyed by (year, month)."""
    readings_by_month: ReadingsByMonth = {}
    for reading in readings:
        month_key = (reading.date.year, reading.date.month)
        readings_by_month.setdefault(month_key, []).append(reading)
    return readings_by_month


def _find_weather_files(directory: Path) -> List[Path]:
    """Locate the .txt weather files inside a directory, validating as we go."""
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a valid directory")

    weather_files = sorted(directory.glob("*.txt"))
    if not weather_files:
        raise FileNotFoundError(f"No .txt weather files found in {directory}")

    return weather_files


def _read_all_readings(weather_files: Iterable[Path]) -> List[WeatherReading]:
    """Read every given file, skipping (and logging) any that can't be read."""
    all_readings: List[WeatherReading] = []
    for file_path in weather_files:
        try:
            all_readings.extend(read_readings_from_file(file_path))
        except (OSError, csv.Error) as exc:
            logger.warning("Skipping unreadable file %s: %s", file_path.name, exc)
    return all_readings


def parse_directory(directory: Path) -> ReadingsByMonth:
    """Read every .txt file in directory and index all readings by month."""
    weather_files = _find_weather_files(directory)
    all_readings = _read_all_readings(weather_files)
    return group_readings_by_month(all_readings)
