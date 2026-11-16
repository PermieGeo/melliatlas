"""Public Open-Meteo forecast declarations and explicitly configured reader."""

from .api import FORECAST_HOURS, WeatherForecast, WeatherForecastReader
from .forecast import OpenMeteoForecastReader

__all__ = ["FORECAST_HOURS", "WeatherForecast", "WeatherForecastReader", "OpenMeteoForecastReader"]
