"""Data structures used across the Weatherman application.

Each record is an immutable NamedTuple: cheaper to create and compare
than a dict (no hashing of string keys per access), and self-documenting
through attribute access (reading.max_temp) instead of string keys
(reading["max_temp"]), which also means a typo becomes an AttributeError
at the point of use instead of a silent None from a mistyped dict key.
"""

from __future__ import annotations

from datetime import date
from typing import NamedTuple, Optional


class WeatherReading(NamedTuple):
    """One day's weather reading.

    Any numeric field may be None if the source file left that cell blank."""

    date: date
    max_temp: Optional[int]
    mean_temp: Optional[int]
    min_temp: Optional[int]
    max_humidity: Optional[int]
    mean_humidity: Optional[int]
    min_humidity: Optional[int]


# All readings for a directory, bucketed by (year, month) at parse time.
# This stays a plain dict rather than a NamedTuple, since it is a lookup
# index with a variable number of entries - not a fixed-shape record.
# Grouping up front means monthly/daily reports do a direct dict lookup
# instead of re-scanning every reading in the whole dataset.
ReadingsByMonth = dict[tuple[int, int], list[WeatherReading]]


class YearlyExtremes(NamedTuple):
    """Result of the yearly extremes report (``-e``)."""

    year: int
    highest_temp: int
    highest_temp_date: date
    lowest_temp: int
    lowest_temp_date: date
    most_humid_value: int
    most_humid_date: date


class MonthlyAverages(NamedTuple):
    """Result of the monthly averages report (``-a``)."""

    year: int
    month: int
    avg_highest_temp: float
    avg_lowest_temp: float
    avg_mean_humidity: float


class DailyExtreme(NamedTuple):
    """One day's high/low pair, used for the ``-c`` bar chart report."""

    day: int
    max_temp: Optional[int]
    min_temp: Optional[int]
