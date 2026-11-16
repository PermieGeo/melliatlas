"""Provider-specific sanitized source failure reasons.

These are internal diagnostic categories; public HTTP failures use the
provider-neutral SOURCE_READ_FAILED code and never reveal upstream details.
"""

from enum import StrEnum


class WeatherReadFailure(StrEnum):
    """Sanitized provider-only transport and decoder failures."""

    WEATHER_HTTP = "Weather provider did not return HTTP 200"
    WEATHER_CONTENT_TYPE = "Weather provider did not return JSON"
    WEATHER_ENCODING = "Unexpected weather response encoding"
    WEATHER_SIZE = "Forecast response exceeds byte limit"
    WEATHER_REQUEST = "Weather provider is unreachable"
    WEATHER_FORMAT = "Upstream forecast is missing, inconsistent or malformed"
