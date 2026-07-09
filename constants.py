"""Shared constant values for the Weatherman application."""

from __future__ import annotations

# ANSI escape codes used when rendering colored bar charts.
ANSI_RED = "\033[31m"
ANSI_BLUE = "\033[34m"
ANSI_RESET = "\033[0m"

# Date format used in the source weather files, e.g. "2004-8-1".
DATE_FORMAT = "%Y-%m-%d"

# Column names as they appear in the source CSV weather files.
COLUMN_MAX_TEMP = "Max TemperatureC"
COLUMN_MEAN_TEMP = "Mean TemperatureC"
COLUMN_MIN_TEMP = "Min TemperatureC"
COLUMN_MAX_HUMIDITY = "Max Humidity"
COLUMN_MEAN_HUMIDITY = "Mean Humidity"
COLUMN_MIN_HUMIDITY = "Min Humidity"
