"""Computes aggregate statistics from a dict of readings grouped by month."""

from __future__ import annotations

from statistics import mean
from typing import Callable, List, Optional

from data_models import (
    DailyExtreme,
    MonthlyAverages,
    ReadingsByMonth,
    WeatherReading,
    YearlyExtremes,
)


def _readings_in_year(
    readings_by_month: ReadingsByMonth, year: int
) -> List[WeatherReading]:
    """Flatten every month-bucket that belongs to the given year."""
    matching_readings: List[WeatherReading] = []
    for (bucket_year, _bucket_month), month_readings in readings_by_month.items():
        if bucket_year == year:
            matching_readings.extend(month_readings)
    return matching_readings


def _reading_with_extreme_value(
    readings: List[WeatherReading],
    value_of: Callable[[WeatherReading], Optional[int]],
    pick: Callable[..., WeatherReading],
) -> Optional[WeatherReading]:
    """Return the reading with the highest/lowest value of one field."""
    readings_with_value = [
        reading for reading in readings if value_of(reading) is not None
    ]
    extreme_reading: Optional[WeatherReading] = None
    if readings_with_value:
        extreme_reading = pick(readings_with_value, key=value_of)
    return extreme_reading


def _average_present_values(
    readings: List[WeatherReading],
    value_of: Callable[[WeatherReading], Optional[int]],
) -> Optional[float]:
    """Average one field across readings, skipping readings where it's missing."""
    present_values = [
        value for reading in readings if (value := value_of(reading)) is not None
    ]
    return mean(present_values) if present_values else None


def calculate_yearly_extremes(
    readings_by_month: ReadingsByMonth, year: int
) -> Optional[YearlyExtremes]:
    """Highest max-temp, lowest min-temp, and highest humidity within a year.

    Each of the three metrics is computed independently: if, say, no
    humidity readings exist anywhere in the year, the temperature
    extremes are still returned, with the humidity fields left as None.
    Returns None only if none of the three could be computed at all.
    """
    year_readings = _readings_in_year(readings_by_month, year)

    hottest_reading = _reading_with_extreme_value(
        year_readings, lambda reading: reading.max_temp, max
    )
    coldest_reading = _reading_with_extreme_value(
        year_readings, lambda reading: reading.min_temp, min
    )
    most_humid_reading = _reading_with_extreme_value(
        year_readings, lambda reading: reading.max_humidity, max
    )

    result: Optional[YearlyExtremes] = None
    if hottest_reading or coldest_reading or most_humid_reading:
        result = YearlyExtremes(
            year=year,
            highest_temp=hottest_reading.max_temp if hottest_reading else None,
            highest_temp_date=hottest_reading.date if hottest_reading else None,
            lowest_temp=coldest_reading.min_temp if coldest_reading else None,
            lowest_temp_date=coldest_reading.date if coldest_reading else None,
            most_humid_value=(
                most_humid_reading.max_humidity if most_humid_reading else None
            ),
            most_humid_date=most_humid_reading.date if most_humid_reading else None,
        )
    return result


def calculate_monthly_averages(
    readings_by_month: ReadingsByMonth, year: int, month: int
) -> Optional[MonthlyAverages]:
    """Average daily high, average daily low, and average mean humidity."""
    month_readings = readings_by_month.get((year, month), [])

    result: Optional[MonthlyAverages] = None
    if month_readings:
        result = MonthlyAverages(
            year=year,
            month=month,
            avg_highest_temp=_average_present_values(
                month_readings, lambda reading: reading.max_temp
            ),
            avg_lowest_temp=_average_present_values(
                month_readings, lambda reading: reading.min_temp
            ),
            avg_mean_humidity=_average_present_values(
                month_readings, lambda reading: reading.mean_humidity
            ),
        )
    return result


def calculate_daily_extremes(
    readings_by_month: ReadingsByMonth, year: int, month: int
) -> Optional[List[DailyExtreme]]:
    """Per-day high/low temperature pairs for a month, sorted by day."""
    month_readings = readings_by_month.get((year, month), [])

    daily_extremes: Optional[List[DailyExtreme]] = None
    if month_readings:
        latest_reading_by_day = {
            reading.date.day: reading for reading in month_readings
        }
        daily_extremes = [
            DailyExtreme(day=day, max_temp=reading.max_temp, min_temp=reading.min_temp)
            for day, reading in sorted(latest_reading_by_day.items())
        ]
    return daily_extremes
