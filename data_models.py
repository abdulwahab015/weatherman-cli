"""Data models for the Weatherman application.

This module provides strictly typed, memory-efficient data structures 
using slotted dataclasses to represent weather data and report results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True)
class WeatherReading:
    """Represents a single day's weather observation."""

    date: date
    max_temp: Optional[int]
    mean_temp: Optional[int]
    min_temp: Optional[int]
    max_humidity: Optional[int]
    mean_humidity: Optional[int]
    min_humidity: Optional[int]


ReadingsByMonth = dict[tuple[int, int], list[WeatherReading]]


@dataclass(slots=True)
class YearlyExtremes:
    """Encapsulates the computed results for the yearly extremes report."""

    year: int
    highest_temp: int
    highest_temp_date: date
    lowest_temp: int
    lowest_temp_date: date
    most_humid_value: int
    most_humid_date: date


@dataclass(slots=True)
class MonthlyAverages:
    """Encapsulates the computed results for the monthly averages report."""

    year: int
    month: int
    avg_highest_temp: float
    avg_lowest_temp: float
    avg_mean_humidity: float


@dataclass(slots=True)
class DailyExtreme:
    """Encapsulates the high and low temperatures for a specific day."""

    day: int
    max_temp: Optional[int]
    min_temp: Optional[int]
