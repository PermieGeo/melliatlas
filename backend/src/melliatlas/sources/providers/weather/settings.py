"""Validated Open-Meteo HTTP policy; network URLs come from provider configuration.

The adapter accepts only its reviewed HTTPS host and exact endpoint path.
Changing to a different provider format requires registering a separate adapter.
"""

from dataclasses import dataclass
from urllib.parse import urlsplit

FORECAST_HOURS = 24
MAX_ALLOWED_BODY_BYTES = 100_000
MAX_ALLOWED_TIMEOUT_SECONDS = 15
_APPROVED_API_HOST = "api.open-meteo.com"
_APPROVED_DOC_HOST = "open-meteo.com"
_APPROVED_FORECAST_PATH = "/v1/forecast"


def _safe_url(value: object, *, hostname: str, path: str | None = None) -> bool:
    """Validate untrusted configuration values before URL parsing."""
    if not isinstance(value, str) or value != value.strip():
        return False
    try:
        url = urlsplit(value)
        return (
            url.scheme == "https"
            and url.hostname == hostname
            and url.username is None
            and url.password is None
            and url.port is None
            and not url.query
            and not url.fragment
            and (url.path == path if path is not None else url.path.startswith("/"))
            and not any(char in value for char in ("\\", "@", "?", "#", " ", "\t", "\n", "\r"))
        )
    except ValueError:
        return False


@dataclass(frozen=True)
class WeatherTransportSettings:
    """Resource limits and explicitly approved endpoints for one forecast adapter."""

    forecast_url: str
    source_uri: str
    timeout_seconds: int
    max_body_bytes: int

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
        if not _safe_url(
            self.forecast_url, hostname=_APPROVED_API_HOST, path=_APPROVED_FORECAST_PATH
        ):
            raise ValueError("Forecast URL must use the approved Open-Meteo HTTPS endpoint")
        if not _safe_url(self.source_uri, hostname=_APPROVED_DOC_HOST):
            raise ValueError("Weather attribution URL must use the approved HTTPS origin")
