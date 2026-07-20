"""Data models for the Weatherman application.

This module provides strictly typed, memory-efficient data structures
using slotted dataclasses to represent weather data and report results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True, slots=True)
class WeatherReading:
    """Represents a single day's weather observation."""

    reading_date: date
    max_temp: Optional[int]
    mean_temp: Optional[int]
    min_temp: Optional[int]
    max_humidity: Optional[int]
    mean_humidity: Optional[int]
    min_humidity: Optional[int]


ReadingsByMonth = dict[tuple[int, int], list[WeatherReading]]


@dataclass(frozen=True, slots=True)
class YearlyExtremes:
    """Encapsulates the computed results for the yearly extremes report."""

    year: int
    highest_temp: Optional[int]
    highest_temp_date: Optional[date]
    lowest_temp: Optional[int]
    lowest_temp_date: Optional[date]
    most_humid_value: Optional[int]
    most_humid_date: Optional[date]


@dataclass(frozen=True, slots=True)
class MonthlyAverages:
    """Encapsulates the computed results for the monthly averages report."""

    year: int
    month: int
    avg_highest_temp: Optional[float]
    avg_lowest_temp: Optional[float]
    avg_mean_humidity: Optional[float]


@dataclass(frozen=True, slots=True)
class DailyExtreme:
    """Encapsulates the high and low temperatures for a specific day."""

    day: int
    max_temp: Optional[int]
    min_temp: Optional[int]
