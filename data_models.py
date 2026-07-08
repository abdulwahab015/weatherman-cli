"""Data structures used across the Weatherman application"""

from __future__ import annotations

from datetime import date
from typing import Optional, TypedDict


class WeatherReading(TypedDict):
    """One day's weather reading."""

    date: date
    max_temp: Optional[int]
    mean_temp: Optional[int]
    min_temp: Optional[int]
    max_humidity: Optional[int]
    mean_humidity: Optional[int]
    min_humidity: Optional[int]


# All readings bucketed by (year, month)
ReadingsByMonth = dict[tuple[int, int], list[WeatherReading]]


class YearlyExtremes(TypedDict):
    """Result shape for the yearly extremes report (-e)"""

    year: int
    highest_temp: int
    highest_temp_date: date
    lowest_temp: int
    lowest_temp_date: date
    most_humid_value: int
    most_humid_date: date


class MonthlyAverages(TypedDict):
    """Result shape for the monthly averages report (-a)"""

    year: int
    month: int
    avg_highest_temp: float
    avg_lowest_temp: float
    avg_mean_humidity: float


class DailyExtremes(TypedDict):
    """One day's high/low pair, used for the (-c) bar chart report"""

    day: int
    max_temp: Optional[int]
    min_temp: Optional[int]
