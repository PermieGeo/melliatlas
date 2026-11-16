"""Public Open-Meteo adapter entry point.

No HTTP transport or domain parsing is implemented in this facade.
The source remains explicit and disabled unless enabled by composition.
"""

from melliatlas.sources.providers.open_meteo.forecast import OpenMeteoForecastReader
from melliatlas.sources.providers.open_meteo.settings import FORECAST_HOURS

__all__ = ["OpenMeteoForecastReader", "FORECAST_HOURS"]
