"""Pinned Open-Meteo forecast request construction and operational budgets.

Only the configured byte and timeout budgets vary; the HTTPS origin, hourly
variables, UTC timestamps and metric units belong to the validated forecast
contract. Geography is supplied by the explicit end-user request.
"""

from math import isfinite
from urllib.parse import urlencode

from melliatlas.sources.providers.http_transport import (
    JsonTransportFailures,
    read_fixed_origin_json,
)
from melliatlas.sources.providers.open_meteo.failures import WeatherReadFailure
from melliatlas.sources.providers.open_meteo.settings import (
    FORECAST_ENDPOINT,
    FORECAST_HOURS,
    WeatherTransportSettings,
)

FORECAST_URL = FORECAST_ENDPOINT
DEFAULT_SETTINGS = WeatherTransportSettings()
MAX_BODY_BYTES = DEFAULT_SETTINGS.max_body_bytes
TIMEOUT_SECONDS = DEFAULT_SETTINGS.timeout_seconds
_HOST = "api.open-meteo.com"
_FAILURES = JsonTransportFailures(
    WeatherReadFailure.WEATHER_HTTP,
    WeatherReadFailure.WEATHER_CONTENT_TYPE,
    WeatherReadFailure.WEATHER_ENCODING,
    WeatherReadFailure.WEATHER_SIZE,
    WeatherReadFailure.WEATHER_REQUEST,
)


def get_public_forecast(
    latitude: float, longitude: float, *, settings: WeatherTransportSettings = DEFAULT_SETTINGS
) -> bytes:
    """Send only validated WGS84 coordinates to the fixed weather origin."""
    if not (isfinite(latitude) and isfinite(longitude)) or not (
        -90 <= latitude <= 90 and -180 <= longitude <= 180
    ):
        raise ValueError("Invalid WGS84 forecast coordinates")
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation",
            "forecast_hours": FORECAST_HOURS,
            "timezone": "GMT",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }
    )
    return read_fixed_origin_json(
        f"{FORECAST_URL}?{params}",
        expected_host=_HOST,
        method="GET",
        body=None,
        timeout_seconds=settings.timeout_seconds,
        max_body_bytes=settings.max_body_bytes,
        failures=_FAILURES,
    )
