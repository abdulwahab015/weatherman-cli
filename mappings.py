"""Data layout maps and lookups for translating weather dataset structures."""

NUMERIC_COLUMNS_BY_FIELD: dict[str, str] = {
    "max_temp": "Max TemperatureC",
    "mean_temp": "Mean TemperatureC",
    "min_temp": "Min TemperatureC",
    "max_humidity": "Max Humidity",
    "mean_humidity": "Mean Humidity",
    "min_humidity": "Min Humidity",
}
