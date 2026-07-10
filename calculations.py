"""Computes aggregate statistics from weather data models."""

from __future__ import annotations

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
        for (bucket_year, _), month_readings in self.readings_by_month.items():
            if bucket_year == year:
                yearly_readings.extend(month_readings)

        return yearly_readings

    def _find_extreme_reading(
        self,
        readings: list[WeatherReading],
        extractor: Callable[[WeatherReading], Optional[int]],
        comparator: Callable[..., WeatherReading],
    ) -> Optional[WeatherReading]:
        """Locates the reading containing the extreme maximum or minimum value."""
        valid_readings = [
            reading for reading in readings if extractor(reading) is not None
        ]
        extreme_reading: Optional[WeatherReading] = None

        if valid_readings:
            extreme_reading = comparator(valid_readings, key=extractor)

        return extreme_reading

    def _calculate_mean(
        self,
        readings: list[WeatherReading],
        extractor: Callable[[WeatherReading], Optional[int]],
    ) -> Optional[float]:
        """Computes the mean of a specific metric across a list of readings."""
        valid_mean_values = [
            value for reading in readings if (value := extractor(reading)) is not None
        ]
        mean_value: Optional[float] = None

        if valid_mean_values:
            mean_value = mean(valid_mean_values)

        return mean_value

    def calculate_yearly_extremes(self, year: int) -> Optional[YearlyExtremes]:
        """Computes the highest temperature, lowest temperature, and maximum
        humidity for a year."""
        year_readings = self._get_readings_for_year(year)

        hottest = self._find_extreme_reading(
            year_readings, lambda reading: reading.max_temp, max
        )
        coldest = self._find_extreme_reading(
            year_readings, lambda reading: reading.min_temp, min
        )
        most_humid = self._find_extreme_reading(
            year_readings, lambda reading: reading.max_humidity, max
        )

        result: Optional[YearlyExtremes] = None
        if hottest or coldest or most_humid:
            result = YearlyExtremes(
                year=year,
                highest_temp=hottest.max_temp if hottest else None,
                highest_temp_date=hottest.reading_date if hottest else None,
                lowest_temp=coldest.min_temp if coldest else None,
                lowest_temp_date=coldest.reading_date if coldest else None,
                most_humid_value=most_humid.max_humidity if most_humid else None,
                most_humid_date=most_humid.reading_date if most_humid else None,
            )

        return result

    def calculate_monthly_averages(
        self, year: int, month: int
    ) -> Optional[MonthlyAverages]:
        """Computes the average high, low, and humidity for a specific month."""
        month_readings = self.readings_by_month.get((year, month), [])
        result: Optional[MonthlyAverages] = None

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
        month_readings = self.readings_by_month.get((year, month), [])
        daily_extremes: Optional[list[DailyExtreme]] = None

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
