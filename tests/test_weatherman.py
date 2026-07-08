"""Regression tests for the Weatherman calculation logic."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations import NoDataError, daily_extremes, monthly_averages, yearly_extremes


def _reading(day, max_t=None, min_t=None, mean_hum=None, max_hum=None):
    return {
        "date": date.fromisoformat(day),
        "max_temp": max_t,
        "mean_temp": None,
        "min_temp": min_t,
        "max_humidity": max_hum,
        "mean_humidity": mean_hum,
        "min_humidity": None,
    }


def _bucket(readings):
    """Group a flat list of readings into the (year, month) dict shape."""
    by_month = {}
    for r in readings:
        key = (r["date"].year, r["date"].month)
        by_month.setdefault(key, []).append(r)
    return by_month


class YearlyExtremesTests(unittest.TestCase):
    def test_finds_highest_lowest_and_most_humid_across_months(self):
        readings = _bucket(
            [
                _reading("2004-06-23", max_t=45, min_t=10, max_hum=50),
                _reading("2004-12-22", max_t=20, min_t=1, max_hum=60),
                _reading("2004-08-14", max_t=30, min_t=15, max_hum=95),
            ]
        )
        result = yearly_extremes(readings, 2004)
        self.assertEqual(result["highest_temp"], 45)
        self.assertEqual(result["highest_temp_date"], date(2004, 6, 23))
        self.assertEqual(result["lowest_temp"], 1)
        self.assertEqual(result["most_humid_value"], 95)

    def test_raises_when_year_missing(self):
        readings = _bucket([_reading("2004-01-01", max_t=10, min_t=1, max_hum=50)])
        with self.assertRaises(NoDataError):
            yearly_extremes(readings, 1999)


class MonthlyAveragesTests(unittest.TestCase):
    def test_averages_only_use_readings_from_that_month(self):
        readings = _bucket(
            [
                _reading("2005-06-01", max_t=40, min_t=20, mean_hum=70),
                _reading("2005-06-02", max_t=38, min_t=16, mean_hum=72),
                _reading("2005-07-01", max_t=100, min_t=100, mean_hum=100),
            ]
        )
        result = monthly_averages(readings, 2005, 6)
        self.assertAlmostEqual(result["avg_highest_temp"], 39)
        self.assertAlmostEqual(result["avg_lowest_temp"], 18)
        self.assertAlmostEqual(result["avg_mean_humidity"], 71)

    def test_missing_month_raises(self):
        readings = _bucket([_reading("2005-06-01", max_t=40, min_t=20, mean_hum=70)])
        with self.assertRaises(NoDataError):
            monthly_averages(readings, 2005, 1)


class DailyExtremesTests(unittest.TestCase):
    def test_skips_days_with_no_data(self):
        readings = _bucket(
            [
                _reading("2011-03-01", max_t=25, min_t=11),
                _reading("2011-03-02", max_t=22, min_t=8),
            ]
        )
        days = daily_extremes(readings, 2011, 3)
        self.assertEqual([d["day"] for d in days], [1, 2])
        self.assertEqual(days[0]["max_temp"], 25)
        self.assertEqual(days[0]["min_temp"], 11)


if __name__ == "__main__":
    unittest.main()
