"""Live forecast contracts: no silent network calls, fabricated values, or drift advice."""

import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from melliatlas.api.app import AppSettings, create_app
from melliatlas.sources.api import SourceReadError, WeatherForecast
from melliatlas.sources.providers.open_meteo import OpenMeteoForecastReader


def _payload() -> bytes:
    times = [
        (datetime(2026, 11, 15, tzinfo=timezone.utc) + timedelta(hours=i)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        for i in range(24)
    ]
    return json.dumps(
        {
            "latitude": 54.02,
            "longitude": 32.03,
            "timezone": "GMT",
            "utc_offset_seconds": 0,
            "hourly_units": {
                "wind_speed_10m": "km/h",
                "wind_direction_10m": "°",
                "wind_gusts_10m": "km/h",
                "precipitation": "mm",
            },
            "hourly": {
                "time": times,
                "wind_speed_10m": [10.0] * 24,
                "wind_direction_10m": [270] * 24,
                "wind_gusts_10m": [20.0] * 24,
                "precipitation": [None] + [0.0] * 23,
            },
        }
    ).encode("utf-8")


def test_provider_preserves_utc_units_grid_and_null_forecast_values() -> None:
    called: list[tuple[float, float]] = []

    def fetch(latitude: float, longitude: float) -> bytes:
        called.append((latitude, longitude))
        return _payload()

    forecast = OpenMeteoForecastReader(fetch).forecast(latitude=54.0, longitude=32.0)
    assert called == [(54.0, 32.0)]
    assert forecast.source_id == "open-meteo:forecast"
    assert (forecast.grid_latitude, forecast.grid_longitude) == (54.02, 32.03)
    assert forecast.hours[0].wind_direction_degrees == 270
    assert forecast.hours[0].precipitation_mm is None
    assert forecast.hours[1].time - forecast.hours[0].time == timedelta(hours=1)
    assert all(hour.time.utcoffset() == timedelta(0) for hour in forecast.hours)
    assert any("No pesticide dispersion" in note for note in forecast.uncertainties)


@pytest.mark.parametrize("value", [91.0, float("nan"), float("inf")])
def test_provider_rejects_invalid_coordinates_before_network(value: float) -> None:
    called = False

    def fetch(latitude: float, longitude: float) -> bytes:
        nonlocal called
        called = True
        return _payload()

    with pytest.raises(ValueError, match="WGS84"):
        OpenMeteoForecastReader(fetch).forecast(latitude=value, longitude=32.0)
    assert not called


@pytest.mark.parametrize(
    "case",
    ["timezone", "offset", "units", "short", "negative", "string", "skipped_hour", "error"],
)
def test_unexpected_forecast_fails_closed(case: str) -> None:
    payload: dict[str, object] = json.loads(_payload())
    if case == "timezone":
        payload["timezone"] = "Europe/Moscow"
    elif case == "offset":
        payload["utc_offset_seconds"] = 10800
    elif case == "error":
        payload["error"] = True
    else:
        field = "hourly_units" if case == "units" else "hourly"
        entry = payload[field]
        assert isinstance(entry, dict)
        if case == "units":
            entry["wind_speed_10m"] = "m/s"
        elif case == "short":
            entry["wind_gusts_10m"] = [1.0]
        elif case == "negative":
            entry["wind_direction_10m"] = [-1] * 24
        elif case == "string":
            entry["wind_speed_10m"] = ["calm"] * 24
        else:
            entry["time"] = ["2026-11-15T03:00"] * 24
    reader = OpenMeteoForecastReader(lambda latitude, longitude: json.dumps(payload).encode())
    with pytest.raises(SourceReadError):
        reader.forecast(latitude=54.0, longitude=32.0)


def test_weather_capability_is_independent_of_saturn_and_synthetic() -> None:
    async def check() -> None:
        reader = OpenMeteoForecastReader(lambda latitude, longitude: _payload())
        disabled = create_app(weather_reader=reader)
        enabled = create_app(settings=AppSettings(weather_live_enabled=True), weather_reader=reader)
        for app, active in ((disabled, False), (enabled, True)):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                for country in ("RU", "BY"):
                    listed = await client.get("/api/v1/sources", params={"country": country})
                    assert listed.status_code == 200
                    assert [item["id"] for item in listed.json()] == (
                        ["open-meteo"] if active else []
                    )
                post = await client.post(
                    "/api/v1/sources/weather/forecast", json={"latitude": 54.0, "longitude": 32.0}
                )
                assert post.status_code == (200 if active else 503)
                if active:
                    body = post.json()
                    assert body["synthetic"] is False
                    assert body["source_mode"] == "LIVE"
                    assert len(body["hours"]) == 24
                    assert body["hours"][0]["precipitation_mm"] is None
                    assert (body["grid_latitude"], body["grid_longitude"]) == (54.02, 32.03)
                    assert "starting_point" not in body
                invalid = await client.post(
                    "/api/v1/sources/weather/forecast", json={"latitude": 91, "longitude": 32}
                )
                assert invalid.status_code == 422

    asyncio.run(check())


def test_upstream_failures_never_become_empty_weather() -> None:
    class Failing:
        def forecast(self, *, latitude: float, longitude: float) -> WeatherForecast:
            raise SourceReadError("Internal upstream details")

    async def check() -> None:
        app = create_app(settings=AppSettings(weather_live_enabled=True), weather_reader=Failing())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/sources/weather/forecast", json={"latitude": 54, "longitude": 32}
            )
            assert response.status_code == 502
            assert response.json()["error"]["code"] == "SOURCE_READ_FAILED"
            assert "Internal upstream details" not in response.text

    asyncio.run(check())


def test_weather_configuration_is_loaded_at_lifespan_not_app_construction() -> None:
    calls: list[str] = []
    reader = OpenMeteoForecastReader(lambda latitude, longitude: _payload())

    def configure() -> OpenMeteoForecastReader:
        calls.append("startup")
        return reader

    application = create_app(
        settings=AppSettings(weather_live_enabled=True), weather_reader_factory=configure
    )
    assert calls == []

    async def check() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application), base_url="http://test"
        ) as client:
            before = await client.get("/api/v1/sources", params={"country": "BY"})
            assert before.json() == []
            before_forecast = await client.post(
                "/api/v1/sources/weather/forecast", json={"latitude": 54, "longitude": 32}
            )
            assert before_forecast.status_code == 503
            async with application.router.lifespan_context(application):
                assert calls == ["startup"]
                listed = await client.get("/api/v1/sources", params={"country": "BY"})
                assert [item["id"] for item in listed.json()] == ["open-meteo"]
                forecast = await client.post(
                    "/api/v1/sources/weather/forecast", json={"latitude": 54, "longitude": 32}
                )
                assert forecast.status_code == 200
            after = await client.get("/api/v1/sources", params={"country": "BY"})
            assert after.json() == []

    asyncio.run(check())
    assert calls == ["startup"]


def test_database_disabled_weather_remains_unadvertised_after_startup() -> None:
    calls = 0

    def configure() -> OpenMeteoForecastReader | None:
        nonlocal calls
        calls += 1
        return None

    application = create_app(
        settings=AppSettings(weather_live_enabled=True), weather_reader_factory=configure
    )

    async def check() -> None:
        async with application.router.lifespan_context(application):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=application), base_url="http://test"
            ) as client:
                listed = await client.get("/api/v1/sources", params={"country": "RU"})
                assert listed.json() == []
                forecast = await client.post(
                    "/api/v1/sources/weather/forecast", json={"latitude": 54, "longitude": 32}
                )
                assert forecast.status_code == 503

    asyncio.run(check())
    assert calls == 1


def test_weather_configuration_failure_blocks_startup_without_fallback() -> None:
    def configure() -> OpenMeteoForecastReader:
        raise RuntimeError("Weather configuration migration is missing")

    application = create_app(
        settings=AppSettings(weather_live_enabled=True), weather_reader_factory=configure
    )

    async def check() -> None:
        with pytest.raises(RuntimeError, match="migration is missing"):
            async with application.router.lifespan_context(application):
                pytest.fail("Misconfigured live weather must not start")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application), base_url="http://test"
        ) as client:
            listed = await client.get("/api/v1/sources", params={"country": "RU"})
            assert listed.json() == []

    asyncio.run(check())


def test_cannot_combine_explicit_weather_reader_and_startup_factory() -> None:
    reader = OpenMeteoForecastReader(lambda latitude, longitude: _payload())
    with pytest.raises(ValueError, match="mutually exclusive"):
        create_app(
            settings=AppSettings(weather_live_enabled=True),
            weather_reader=reader,
            weather_reader_factory=lambda: reader,
        )
