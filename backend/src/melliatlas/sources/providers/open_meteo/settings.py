"""Bounded Open-Meteo request policy, distinct from the forecast wire contract.

The 24-hour, UTC, metric field selection is an invariant of the current API,
not an arbitrary database setting. Only operational budgets are configurable.
"""

from dataclasses import dataclass

FORECAST_HOURS = 24
SOURCE_URI = "https://open-meteo.com/en/docs"
FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
MAX_ALLOWED_BODY_BYTES = 100_000
MAX_ALLOWED_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class WeatherTransportSettings:
    """Bounds protect the fixed provider HTTP contract from DB overrides."""

    timeout_seconds: int = 8
    max_body_bytes: int = MAX_ALLOWED_BODY_BYTES
    source_uri: str = SOURCE_URI

    def __post_init__(self) -> None:
        if (
            type(self.timeout_seconds) is not int
            or not 1 <= self.timeout_seconds <= MAX_ALLOWED_TIMEOUT_SECONDS
        ):
            raise ValueError("Weather timeout must be between 1 and 15 seconds")
        if (
            type(self.max_body_bytes) is not int
            or not 1024 <= self.max_body_bytes <= MAX_ALLOWED_BODY_BYTES
        ):
            raise ValueError("Weather response budget must be between 1024 and 100000 bytes")
        if not self.source_uri.startswith("https://open-meteo.com/") or any(
            token in self.source_uri for token in ("?", "#", "@", "\\", " ")
        ):
            raise ValueError("Weather documentation link must use the fixed verified HTTPS origin")
