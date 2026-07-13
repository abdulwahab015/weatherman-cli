"""Computes aggregate statistics from weather data models."""

from __future__ import annotations

from datetime import date
from statistics import mean
from typing import Callable, Optional

from data_models import (
    DailyExtreme,
    MonthlyAverages,
    ReadingsByMonth,
    WeatherReading,
    YearlyExtremes,
)


class WeatherCalculator:
    """Calculates aggregate weather statistics from grouped monthly readings."""

    def __init__(self, readings_by_month: ReadingsByMonth) -> None:
        """Injects the dataset dependency."""
        self.readings_by_month = readings_by_month

    def _get_readings_for_year(self, year: int) -> list[WeatherReading]:
        """Aggregates all monthly readings into a flat list for a given year."""
        yearly_readings: list[WeatherReading] = []
        for month_key, month_readings in self.readings_by_month.items():
            entry_year, _entry_month = month_key
            if entry_year == year:
                yearly_readings.extend(month_readings)

        return yearly_readings

    def _find_extreme_reading(
        self,
        candidate_readings: list[WeatherReading],
        value_extractor: Callable[[WeatherReading], Optional[int]],
        select_extreme: Callable[..., WeatherReading],
    ) -> Optional[WeatherReading]:
        """Locates the reading containing the extreme maximum or minimum value."""
        extreme_reading: Optional[WeatherReading] = None
        readings_with_value = [
            reading
            for reading in candidate_readings
            if value_extractor(reading) is not None
        ]

        if readings_with_value:
            extreme_reading = select_extreme(readings_with_value, key=value_extractor)

        return extreme_reading

    def _calculate_mean(
        self,
        candidate_readings: list[WeatherReading],
        value_extractor: Callable[[WeatherReading], Optional[int]],
    ) -> Optional[float]:
        """Computes the mean of a specific metric across a list of readings."""
        mean_value: Optional[float] = None
        valid_mean_values = [
            value
            for reading in candidate_readings
            if (value := value_extractor(reading)) is not None
        ]

        if valid_mean_values:
            mean_value = mean(valid_mean_values)

        return mean_value

    def _extreme_value_and_date(
        self,
        candidate_readings: list[WeatherReading],
        value_extractor: Callable[[WeatherReading], Optional[int]],
        select_extreme: Callable[..., WeatherReading],
    ) -> tuple[Optional[int], Optional[date]]:
        """Finds the extreme reading for one metric and returns its (value, date).

        Returns (None, None) if no reading in the list has this field at all.
        """
        extreme_reading = self._find_extreme_reading(
            candidate_readings, value_extractor, select_extreme
        )
        value: Optional[int] = None
        reading_date: Optional[date] = None

        if extreme_reading is not None:
            value = value_extractor(extreme_reading)
            reading_date = extreme_reading.reading_date

        return value, reading_date

    def calculate_yearly_extremes(self, year: int) -> Optional[YearlyExtremes]:
        """Computes the highest temperature, lowest temperature, and maximum
        humidity for a year."""
        result: Optional[YearlyExtremes] = None
        year_readings = self._get_readings_for_year(year)

        highest_temp, highest_temp_date = self._extreme_value_and_date(
            year_readings, lambda reading: reading.max_temp, max
        )
        lowest_temp, lowest_temp_date = self._extreme_value_and_date(
            year_readings, lambda reading: reading.min_temp, min
        )
        most_humid_value, most_humid_date = self._extreme_value_and_date(
            year_readings, lambda reading: reading.max_humidity, max
        )

        if any((highest_temp_date, lowest_temp_date, most_humid_date)):
            result = YearlyExtremes(
                year=year,
                highest_temp=highest_temp,
                highest_temp_date=highest_temp_date,
                lowest_temp=lowest_temp,
                lowest_temp_date=lowest_temp_date,
                most_humid_value=most_humid_value,
                most_humid_date=most_humid_date,
            )

        return result

    def calculate_monthly_averages(
        self, year: int, month: int
    ) -> Optional[MonthlyAverages]:
        """Computes the average high, low, and humidity for a specific month."""
        result: Optional[MonthlyAverages] = None
        month_readings = self.readings_by_month.get((year, month), [])

        if month_readings:
            result = MonthlyAverages(
                year=year,
                month=month,
                avg_highest_temp=self._calculate_mean(
                    month_readings, lambda reading: reading.max_temp
                ),
                avg_lowest_temp=self._calculate_mean(
                    month_readings, lambda reading: reading.min_temp
                ),
                avg_mean_humidity=self._calculate_mean(
                    month_readings, lambda reading: reading.mean_humidity
                ),
            )

        return result

    def calculate_daily_extremes(
        self, year: int, month: int
    ) -> Optional[list[DailyExtreme]]:
        """Extracts the high and low temperatures for each day in a month."""
        daily_extremes: Optional[list[DailyExtreme]] = None
        month_readings = self.readings_by_month.get((year, month), [])

        if month_readings:
            latest_reading_by_day = {
                reading.reading_date.day: reading for reading in month_readings
            }
            daily_extremes = [
                DailyExtreme(
                    day=day,
                    max_temp=reading.max_temp,
                    min_temp=reading.min_temp,
                )
                for day, reading in sorted(latest_reading_by_day.items())
            ]

        return daily_extremes
