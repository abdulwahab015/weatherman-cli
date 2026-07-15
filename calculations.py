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


def _readings_for_year(
    readings_by_month: ReadingsByMonth, year: int
) -> list[WeatherReading]:
    """Aggregates all monthly readings into a flat list for a given year."""
    return [
        reading
        for (entry_year, _entry_month), month_readings in readings_by_month.items()
        if entry_year == year
        for reading in month_readings
    ]


class WeatherCalculator:
    """Calculates aggregate weather statistics from grouped monthly readings."""

    def __init__(self, readings_by_month: ReadingsByMonth) -> None:
        """Injects the dataset dependency."""
        self.readings_by_month = readings_by_month

    def _find_extreme_reading(
        self,
        weather_file_readings: list[WeatherReading],
        metric_value_extractor: Callable[[WeatherReading], Optional[int]],
        select_extreme_reading: Callable[..., WeatherReading],
    ) -> Optional[WeatherReading]:
        """Locates the reading containing the extreme maximum or minimum value."""
        extreme_reading: Optional[WeatherReading] = None
        readings_with_metric_value = [
            reading
            for reading in weather_file_readings
            if metric_value_extractor(reading) is not None
        ]

        if readings_with_metric_value:
            extreme_reading = select_extreme_reading(
                readings_with_metric_value, key=metric_value_extractor
            )

        return extreme_reading

    def _calculate_mean(
        self,
        weather_file_readings: list[WeatherReading],
        metric_value_extractor: Callable[[WeatherReading], Optional[int]],
    ) -> Optional[float]:
        """Computes the mean of a specific metric across a list of readings."""
        computed_mean_value: Optional[float] = None
        present_metric_values = [
            metric_value
            for reading in weather_file_readings
            if (metric_value := metric_value_extractor(reading)) is not None
        ]

        if present_metric_values:
            computed_mean_value = mean(present_metric_values)

        return computed_mean_value

    def _extreme_value_and_date(
        self,
        weather_file_readings: list[WeatherReading],
        metric_value_extractor: Callable[[WeatherReading], Optional[int]],
        select_extreme_reading: Callable[..., WeatherReading],
    ) -> tuple[Optional[int], Optional[date]]:
        """Finds the extreme reading for one metric and returns its (value, date).

        Returns (None, None) if no reading in the list has this field at all.
        """
        extreme_metric_value: Optional[int] = None
        extreme_reading_date: Optional[date] = None
        extreme_reading = self._find_extreme_reading(
            weather_file_readings, metric_value_extractor, select_extreme_reading
        )

        if extreme_reading:
            extreme_metric_value = metric_value_extractor(extreme_reading)
            extreme_reading_date = extreme_reading.reading_date

        return extreme_metric_value, extreme_reading_date

    def calculate_yearly_extremes(self, year: int) -> Optional[YearlyExtremes]:
        """Computes the highest temperature, lowest temperature, and maximum
        humidity for a year."""
        yearly_extremes: Optional[YearlyExtremes] = None
        year_readings = _readings_for_year(self.readings_by_month, year)

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
            yearly_extremes = YearlyExtremes(
                year=year,
                highest_temp=highest_temp,
                highest_temp_date=highest_temp_date,
                lowest_temp=lowest_temp,
                lowest_temp_date=lowest_temp_date,
                most_humid_value=most_humid_value,
                most_humid_date=most_humid_date,
            )

        return yearly_extremes

    def calculate_monthly_averages(
        self, year: int, month: int
    ) -> Optional[MonthlyAverages]:
        """Computes the average high, low, and humidity for a specific month."""
        monthly_averages: Optional[MonthlyAverages] = None
        month_readings = self.readings_by_month.get((year, month), [])

        if month_readings:
            monthly_averages = MonthlyAverages(
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

        return monthly_averages

    def calculate_daily_extremes(
        self, year: int, month: int
    ) -> Optional[list[DailyExtreme]]:
        """Extracts the high and low temperatures for each day in a month."""
        daily_temperature_extremes: Optional[list[DailyExtreme]] = None
        month_readings = self.readings_by_month.get((year, month), [])

        if month_readings:
            reading_by_day_number = {
                reading.reading_date.day: reading for reading in month_readings
            }
            daily_temperature_extremes = [
                DailyExtreme(
                    day=day_number,
                    max_temp=reading_for_day.max_temp,
                    min_temp=reading_for_day.min_temp,
                )
                for day_number, reading_for_day in sorted(reading_by_day_number.items())
            ]

        return daily_temperature_extremes
