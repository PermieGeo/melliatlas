"""HTTP transport must use the validated provider URL rather than a hidden constant."""

from typing import Literal

import pytest

from melliatlas.sources.providers import http_transport
from melliatlas.sources.providers.weather import http as weather_http
from melliatlas.sources.providers.weather.settings import WeatherTransportSettings


def test_weather_transport_uses_configured_url_and_enforces_resource_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, str, int, int]] = []

    def read(
        url: str,
        *,
        expected_host: str,
        method: Literal["GET", "POST"],
        body: bytes | None,
        timeout_seconds: int,
        max_body_bytes: int,
        failures: http_transport.JsonTransportFailures,
    ) -> bytes:
        assert method == "GET" and body is None
        seen.append((url, expected_host, timeout_seconds, max_body_bytes))
        return b"{}"

    monkeypatch.setattr(weather_http, "read_fixed_origin_json", read)
    settings = WeatherTransportSettings(
        "https://api.open-meteo.com/v1/forecast",
        "https://open-meteo.com/en/docs",
        4,
        5000,
    )
    result = weather_http.get_public_forecast(54.0, 32.0, settings=settings)
    assert result == b"{}"
    assert len(seen) == 1
    url, host, timeout, body_budget = seen[0]
    assert url.startswith(settings.forecast_url + "?")
    assert "latitude=54.0" in url and "longitude=32.0" in url
    assert host == "api.open-meteo.com"
    assert (timeout, body_budget) == (4, 5000)
