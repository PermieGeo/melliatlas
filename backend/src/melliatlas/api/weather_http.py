"""Bounded HTTPS transport for one opt-in Open-Meteo forecast; no redirects."""

import socket
from http.client import HTTPException
from math import isfinite
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from melliatlas.sources.api import SourceReadError

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MAX_BODY_BYTES = 100_000
TIMEOUT_SECONDS = 8


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> None:
        return None


def get_public_forecast(latitude: float, longitude: float) -> bytes:
    """Send only explicitly selected coordinates to a fixed weather provider URL."""
    if not (isfinite(latitude) and isfinite(longitude)) or not (
        -90 <= latitude <= 90 and -180 <= longitude <= 180
    ):
        raise ValueError("Invalid WGS84 forecast coordinates")
    params = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation",
            "forecast_hours": 24,
            "timezone": "GMT",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }
    )
    request = Request(
        f"{FORECAST_URL}?{params}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "MelliAtlas-ReadOnly/0.1",
        },
        method="GET",
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/json":
                raise SourceReadError("Weather provider did not return JSON")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SourceReadError("Unexpected weather response encoding")
            content_length = response.headers.get("Content-Length")
            if content_length is not None and (
                not content_length.isdecimal() or int(content_length) > MAX_BODY_BYTES
            ):
                raise SourceReadError("Forecast response exceeds byte limit")
            data = response.read(MAX_BODY_BYTES + 1)
            if len(data) > MAX_BODY_BYTES:
                raise SourceReadError("Forecast response exceeds byte limit")
            return data
    except (HTTPError, URLError, TimeoutError, socket.timeout, HTTPException, OSError) as error:
        raise SourceReadError("Weather provider is unreachable") from error
