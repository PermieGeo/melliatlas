"""Bounded Open-Meteo request construction using a validated database endpoint.

The adapter pins the allowed HTTPS host/path, fixed hourly variables and UTC
units. Its approved URL and resource budgets are selected through configuration.
"""

from urllib.parse import urlencode, urlsplit

from melliatlas.geography import is_wgs84_position
from melliatlas.sources.providers.http_transport import (
    JsonTransportFailures,
    read_fixed_origin_json,
)
from melliatlas.sources.providers.weather.failures import WeatherReadFailure
from melliatlas.sources.providers.weather.settings import FORECAST_HOURS, WeatherTransportSettings

_FAILURES = JsonTransportFailures(
    WeatherReadFailure.WEATHER_HTTP,
    WeatherReadFailure.WEATHER_CONTENT_TYPE,
    WeatherReadFailure.WEATHER_ENCODING,
    WeatherReadFailure.WEATHER_SIZE,
    WeatherReadFailure.WEATHER_REQUEST,
)


def get_public_forecast(
    latitude: float, longitude: float, *, settings: WeatherTransportSettings
) -> bytes:
    """Send bounded forecast requests to a configured, approved provider endpoint."""
    if not is_wgs84_position(longitude, latitude):
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
        f"{settings.forecast_url}?{params}",
        expected_host=urlsplit(settings.forecast_url).hostname or "",
        method="GET",
        body=None,
        timeout_seconds=settings.timeout_seconds,
        max_body_bytes=settings.max_body_bytes,
        failures=_FAILURES,
    )
