"""Parses a single weather data file into structured WeatherReading records."""

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from constants import DATE_FORMAT
from data_models import WeatherReading
from mappings import NUMERIC_COLUMNS_BY_FIELD


class WeatherDataParser:
    """Parses one raw weather CSV file into a list of WeatherReading records."""

    def _parse_integer(self, cell_data: Optional[str]) -> Optional[int]:
        """Converts a raw string cell into an int."""
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

            if any(field_value is not None for field_value in numeric_fields.values()):
                weather_reading = WeatherReading(
                    reading_date=reading_date, **numeric_fields
                )

        return weather_reading

    def parse_file(self, file_path: Path) -> list[WeatherReading]:
        """Reads and parses every usable row from a specific file."""
        weather_file_readings: list[WeatherReading] = []

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
                        weather_file_readings.append(weather_reading)

        return weather_file_readings
