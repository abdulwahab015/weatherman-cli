from __future__ import annotations

from statistics import mean

from data_models import (
    DailyExtremes,
    MonthlyAverages,
    ReadingsByMonth,
    WeatherReading,
    YearlyExtremes,
)


class NoDataError(ValueError):
    """Raised when a report is requested but no matching data exists."""


def _readings_for_year(
    readings_by_month: ReadingsByMonth, year: int
) -> list[WeatherReading]:
    """Flatten every month-bucket that belongs to the given year."""
    year_readings: list[WeatherReading] = []
    for (reading_year, _month), month_readings in readings_by_month.items():
        if reading_year == year:
            year_readings.extend(month_readings)
    return year_readings


def yearly_extremes(readings_by_month: ReadingsByMonth, year: int) -> YearlyExtremes:
    """Highest max-temp, lowest min-temp, and highest humidity within a year."""
    year_readings = _readings_for_year(readings_by_month, year)

    highs = [r for r in year_readings if r["max_temp"] is not None]
    lows = [r for r in year_readings if r["min_temp"] is not None]
    humids = [r for r in year_readings if r["max_humidity"] is not None]

    if not highs or not lows or not humids:
        raise NoDataError(f"No complete readings found for year {year}")

    highest = max(highs, key=lambda r: r["max_temp"])
    lowest = min(lows, key=lambda r: r["min_temp"])
    most_humid = max(humids, key=lambda r: r["max_humidity"])

    return {
        "year": year,
        "highest_temp": highest["max_temp"],
        "highest_temp_date": highest["date"],
        "lowest_temp": lowest["min_temp"],
        "lowest_temp_date": lowest["date"],
        "most_humid_value": most_humid["max_humidity"],
        "most_humid_date": most_humid["date"],
    }


def monthly_averages(
    readings_by_month: ReadingsByMonth, year: int, month: int
) -> MonthlyAverages:
    """Average daily high, average daily low, and average mean humidity."""
    month_readings = readings_by_month.get((year, month), [])

    highs = [r["max_temp"] for r in month_readings if r["max_temp"] is not None]
    lows = [r["min_temp"] for r in month_readings if r["min_temp"] is not None]
    means = [
        r["mean_humidity"] for r in month_readings if r["mean_humidity"] is not None
    ]

    if not highs or not lows or not means:
        raise NoDataError(f"No complete readings found for {year}-{month:02d}")

    return {
        "year": year,
        "month": month,
        "avg_highest_temp": mean(highs),
        "avg_lowest_temp": mean(lows),
        "avg_mean_humidity": mean(means),
    }


def daily_extremes(
    readings_by_month: ReadingsByMonth, year: int, month: int
) -> list[DailyExtremes]:
    """Per-day high/low temperature pairs for a month, sorted by day."""
    month_readings = readings_by_month.get((year, month), [])
    if not month_readings:
        raise NoDataError(f"No readings found for {year}-{month:02d}")

    by_day = {r["date"].day: r for r in month_readings}
    return [
        {"day": day, "max_temp": reading["max_temp"], "min_temp": reading["min_temp"]}
        for day, reading in sorted(by_day.items())
    ]
