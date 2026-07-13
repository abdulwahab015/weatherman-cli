"""Module for parsing weather data files using object-oriented principles."""

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from constants import DATE_FORMAT
from data_models import ReadingsByMonth, WeatherReading
from mappings import NUMERIC_COLUMNS_BY_FIELD


class WeatherDataParser:
    """Parses individual raw weather CSV files into structured data models."""

    def _parse_integer(self, cell_data: Optional[str]) -> Optional[int]:
        """Converts a raw string cell value into an integer safely."""
        clean_data = (cell_data or "").strip()
        parsed_value: Optional[int] = None

        if clean_data:
            try:
                parsed_value = int(round(float(clean_data)))
            except ValueError:
                parsed_value = None

        return parsed_value

    def _parse_date(self, cell_data: Optional[str]) -> Optional[date]:
        """Parses a raw date string cell into a standard datetime.date object."""
        parsed_date: Optional[date] = None

        try:
            parsed_date = datetime.strptime(
                (cell_data or "").strip(), DATE_FORMAT
            ).date()
        except ValueError:
            parsed_date = None

        return parsed_date

    def _build_reading(
        self, row_data: dict[str, str], date_column: str
    ) -> Optional[WeatherReading]:
        """Constructs a single WeatherReading from a normalized row dictionary."""
        reading_date = self._parse_date(row_data.get(date_column, ""))
        weather_reading: Optional[WeatherReading] = None

        if reading_date:
            numeric_fields = {
                field_name: self._parse_integer(row_data.get(column_name))
                for field_name, column_name in NUMERIC_COLUMNS_BY_FIELD.items()
            }

            if any(value is not None for value in numeric_fields.values()):
                weather_reading = WeatherReading(
                    reading_date=reading_date, **numeric_fields
                )

        return weather_reading

    def parse_file(self, file_path: Path) -> list[WeatherReading]:
        """Reads and parses every usable row from a specific file."""
        file_readings: list[WeatherReading] = []

        with file_path.open(newline="", encoding="utf-8", errors="replace") as stream:
            reader = csv.DictReader(stream)
            clean_headers = [
                header.strip() for header in (reader.fieldnames or []) if header
            ]

            if clean_headers:
                date_column, *_ = clean_headers
                for raw_row in reader:
                    normalized_row = {
                        column_name.strip(): cell_data
                        for column_name, cell_data in raw_row.items()
                        if column_name is not None
                    }
                    weather_reading = self._build_reading(normalized_row, date_column)
                    if weather_reading:
                        file_readings.append(weather_reading)

        return file_readings


class DirectoryParser:
    """Handles directory scanning and aggregates streamed weather observations by month."""

    def __init__(self, file_parser: WeatherDataParser) -> None:
        """Injects the required single-file parser dependency."""
        self.file_parser = file_parser

    def process_directory(self, directory_path: Path) -> ReadingsByMonth:
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
