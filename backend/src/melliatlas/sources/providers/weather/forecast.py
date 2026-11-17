"""Validate Open-Meteo's public forecast format without interpreting drift or safety.

Uses the documented /v1/forecast hourly arrays with UTC timestamps and fixed
metric units. Upstream data are model estimates, not field measurements.
The free endpoint permits non-commercial use only; commercial deployment needs
a reviewed Open-Meteo account/license and a different approved transport.
"""

import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import TypeGuard

from melliatlas.geography import (
    LATITUDE_MAX,
    LATITUDE_MIN,
    LONGITUDE_MAX,
    LONGITUDE_MIN,
    is_wgs84_position,
)
from melliatlas.sources.api import ForecastHour, SourceReadError, WeatherForecast
from melliatlas.sources.providers.weather.failures import WeatherReadFailure
from melliatlas.sources.providers.weather.settings import (
    FORECAST_HOURS,
    MAX_ALLOWED_BODY_BYTES,
    SOURCE_URI,
)

SOURCE_ID = "open-meteo:forecast"

MAX_BODY_BYTES = MAX_ALLOWED_BODY_BYTES
_EXPECTED_UNITS = {
    "wind_speed_10m": "km/h",
    "wind_direction_10m": "°",
    "wind_gusts_10m": "km/h",
    "precipitation": "mm",
}


def _is_object_dict(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _record(value: object) -> dict[str, object]:
    if not _is_object_dict(value):
        raise ValueError("Expected an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Forecast field keys must be strings")
        result[key] = item
    return result


def _finite(value: object, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Forecast numeric value is missing or invalid")
    number = float(value)
    if not isfinite(number) or not minimum <= number <= maximum:
        raise ValueError("Forecast numeric value is out of bounds")
    return number


def _optional(value: object, *, minimum: float, maximum: float) -> float | None:
    return None if value is None else _finite(value, minimum=minimum, maximum=maximum)


class OpenMeteoForecastReader:
    """Decode one on-demand 24-hour forecast from an injected fixed-origin transport."""

    def __init__(
        self, transport: Callable[[float, float], bytes], *, source_uri: str = SOURCE_URI
    ) -> None:
        self._transport = transport
        self._source_uri = source_uri

    def forecast(self, *, latitude: float, longitude: float) -> WeatherForecast:
        if not is_wgs84_position(longitude, latitude):
            raise ValueError("Forecast coordinates must be finite WGS84")
        try:
            raw = self._transport(latitude, longitude)
            if len(raw) > MAX_BODY_BYTES:
                raise ValueError("Forecast response exceeds byte limit")
            payload: object = json.loads(raw)
            root = _record(payload)
            if root.get("error") is True:
                raise ValueError("Upstream returned a forecast error")
            if root.get("timezone") != "GMT" or root.get("utc_offset_seconds") != 0:
                raise ValueError("Expected UTC forecast")
            grid_lat = _finite(root.get("latitude"), minimum=LATITUDE_MIN, maximum=LATITUDE_MAX)
            grid_lon = _finite(root.get("longitude"), minimum=LONGITUDE_MIN, maximum=LONGITUDE_MAX)
            units = _record(root.get("hourly_units"))
            for field, unit in _EXPECTED_UNITS.items():
                if units.get(field) != unit:
                    raise ValueError("Unexpected forecast units")
            hourly = _record(root.get("hourly"))
            fields = ("time", *tuple(_EXPECTED_UNITS))
            arrays: dict[str, list[object]] = {}
            for key in fields:
                value = hourly.get(key)
                if not _is_object_list(value) or len(value) != FORECAST_HOURS:
                    raise ValueError("Missing or truncated hourly forecast")
                arrays[key] = value
            hours: list[ForecastHour] = []
            previous: datetime | None = None
            for i in range(FORECAST_HOURS):
                raw_time = arrays["time"][i]
                if not isinstance(raw_time, str):
                    raise ValueError("Forecast time must be ISO-8601 UTC")
                timestamp = datetime.fromisoformat(raw_time)
                if timestamp.tzinfo is not None:
                    raise ValueError("Expected GMT timestamps without offsets")
                timestamp = timestamp.replace(tzinfo=timezone.utc)
                if previous is not None and timestamp - previous != timedelta(hours=1):
                    raise ValueError("Forecast hours must be consecutive")
                previous = timestamp
                hours.append(
                    ForecastHour(
                        time=timestamp,
                        wind_speed_kmh=_optional(
                            arrays["wind_speed_10m"][i], minimum=0, maximum=500
                        ),
                        wind_direction_degrees=_optional(
                            arrays["wind_direction_10m"][i], minimum=0, maximum=360
                        ),
                        wind_gusts_kmh=_optional(
                            arrays["wind_gusts_10m"][i], minimum=0, maximum=600
                        ),
                        precipitation_mm=_optional(
                            arrays["precipitation"][i], minimum=0, maximum=1000
                        ),
                    )
                )
            return WeatherForecast(
                source_id=SOURCE_ID,
                source_uri=self._source_uri,
                captured_at=datetime.now(timezone.utc),
                requested_latitude=latitude,
                requested_longitude=longitude,
                grid_latitude=grid_lat,
                grid_longitude=grid_lon,
                hours=tuple(hours),
                uncertainties=(
                    "Model forecast, not an observed measurement",
                    "Forecast grid coordinates can differ from the requested point",
                    "No pesticide dispersion, exposure or apiary safety model has been applied",
                ),
            )
        except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
            raise SourceReadError(WeatherReadFailure.WEATHER_FORMAT) from error
