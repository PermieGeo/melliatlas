"""Public Open-Meteo forecast types; execution belongs to forecast.py.

The generic WeatherForecastReader Protocol is defined by the sources capability.
The bounded forecast horizon remains a source-specific fixed contract.
"""

from melliatlas.sources.api import WeatherForecast, WeatherForecastReader

from .settings import FORECAST_HOURS

__all__ = ["FORECAST_HOURS", "WeatherForecast", "WeatherForecastReader"]
