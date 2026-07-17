"""Loads weather readings from every file in a directory into one dataset."""

import csv
from pathlib import Path

from data_models import ReadingsByMonth, WeatherReading
from file_parser import WeatherDataParser


class WeatherReadingsLoader:
    """Reads every weather file in a directory and aggregates the readings by month."""

    def __init__(self, file_parser: WeatherDataParser) -> None:
        """Injects the required single-file parser dependency."""
        self.file_parser = file_parser

    @staticmethod
    def readings_for_year(
        readings_by_month: ReadingsByMonth, year: int
    ) -> list[WeatherReading]:
        """Aggregates all monthly readings into a flat list for a given year."""
        return [
            reading
            for (entry_year, _entry_month), month_readings in readings_by_month.items()
            if entry_year == year
            for reading in month_readings
        ]

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
