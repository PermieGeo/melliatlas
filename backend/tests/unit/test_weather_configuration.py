"""Weather endpoints are database values but adapter validation remains fail-closed."""

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import LiteralString

import pytest

from melliatlas.api.composition import compose_weather_reader
from melliatlas.persistence.api import WeatherProviderConfig
from melliatlas.persistence.weather.config import read_weather_configuration
from melliatlas.sources.providers.weather.settings import WeatherTransportSettings

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DOCS_URL = "https://open-meteo.com/en/docs"


class WeatherCursor:
    def __init__(self, rows: tuple[tuple[object, ...], ...]) -> None:
        self.rows = iter(rows)
        self.closed = False
        self.executed_query: str | None = None

    def execute(self, query: LiteralString, params: Sequence[object] = ()) -> None:
        assert not params
        self.executed_query = query

    def fetchone(self) -> tuple[object, ...] | None:
        return next(self.rows, None)

    def close(self) -> None:
        self.closed = True


class WeatherConnection:
    def __init__(self, *rows: tuple[object, ...]) -> None:
        self.test_cursor = WeatherCursor(rows)
        self.closed = False

    def cursor(self) -> WeatherCursor:
        return self.test_cursor

    def commit(self) -> None:
        raise AssertionError("Weather configuration is read-only")

    def rollback(self) -> None:
        raise AssertionError("Weather configuration is read-only")

    def close(self) -> None:
        self.closed = True


def provider_row(*, provider_id: str = "open-meteo", enabled: bool = True) -> tuple[object, ...]:
    return (provider_id, enabled, 5, 50_000, DOCS_URL, FORECAST_URL)


def test_weather_config_reads_only_one_enabled_provider() -> None:
    connection = WeatherConnection(provider_row())
    config = read_weather_configuration(lambda: connection)
    assert config == WeatherProviderConfig("open-meteo", 5, 50_000, DOCS_URL, FORECAST_URL)
    assert config is not None
    settings = WeatherTransportSettings(
        config.forecast_url, config.source_uri, config.timeout_seconds, config.max_body_bytes
    )
    assert settings.timeout_seconds == 5
    assert settings.max_body_bytes == 50_000
    assert connection.test_cursor.executed_query is not None
    assert "FROM melliatlas_weather_provider_config" in connection.test_cursor.executed_query
    assert connection.test_cursor.closed and connection.closed
    assert compose_weather_reader(True, config) is not None


def test_disabled_provider_is_not_advertised() -> None:
    config = read_weather_configuration(lambda: WeatherConnection(provider_row(enabled=False)))
    assert config is None


def test_multiple_enabled_providers_fail_closed() -> None:
    conn = WeatherConnection(provider_row(), provider_row(provider_id="another"))
    with pytest.raises(ValueError, match="More than one"):
        read_weather_configuration(lambda: conn)


def test_unknown_provider_is_not_sent_to_network() -> None:
    config = WeatherProviderConfig("unknown", 5, 50_000, DOCS_URL, FORECAST_URL)
    with pytest.raises(ValueError, match="not implemented"):
        compose_weather_reader(True, config)


@pytest.mark.parametrize(
    "row",
    [
        (),
        ("open-meteo", True, 3, 4096),
        ("open-meteo", "true", 3, 4096, DOCS_URL, FORECAST_URL),
        ("open-meteo", True, True, 4096, DOCS_URL, FORECAST_URL),
        ("open-meteo", True, 3, 4096, None, FORECAST_URL),
    ],
)
def test_weather_config_rejects_invalid_database_row(row: tuple[object, ...]) -> None:
    conn = WeatherConnection(row)
    with pytest.raises(ValueError, match="configuration"):
        read_weather_configuration(lambda: conn)
    assert conn.test_cursor.closed and conn.closed


def _settings() -> WeatherTransportSettings:
    return WeatherTransportSettings(FORECAST_URL, DOCS_URL, 8, 100_000)


@pytest.mark.parametrize(
    "invalid",
    [
        lambda: replace(_settings(), timeout_seconds=0),
        lambda: replace(_settings(), timeout_seconds=16),
        lambda: replace(_settings(), max_body_bytes=1023),
        lambda: replace(_settings(), max_body_bytes=100_001),
        lambda: replace(_settings(), source_uri="https://evil.example/docs"),
        lambda: replace(_settings(), source_uri="http://open-meteo.com/en/docs"),
        lambda: replace(_settings(), source_uri="https://open-meteo.com@evil.example/docs"),
        lambda: replace(_settings(), source_uri=f"{DOCS_URL}#fragment"),
        lambda: replace(_settings(), source_uri=f"{DOCS_URL}?track=user"),
        lambda: replace(_settings(), forecast_url="https://127.0.0.1/v1/forecast"),
        lambda: replace(_settings(), forecast_url="https://evil.example/v1/forecast"),
        lambda: replace(_settings(), forecast_url="http://api.open-meteo.com/v1/forecast"),
        lambda: replace(
            _settings(), forecast_url="https://api.open-meteo.com@evil.example/v1/forecast"
        ),
        lambda: replace(_settings(), forecast_url=f"{FORECAST_URL}?url=https://evil.example"),
        lambda: replace(_settings(), forecast_url=f"{FORECAST_URL}#"),
        lambda: replace(_settings(), forecast_url=f"{FORECAST_URL}?"),
        lambda: replace(_settings(), forecast_url="https://api.open-meteo.com/v1/other"),
    ],
)
def test_weather_transport_policy_rejects_unsafe_overrides(
    invalid: Callable[[], WeatherTransportSettings],
) -> None:
    with pytest.raises(ValueError):
        invalid()


def test_weather_migrations_preserve_operator_state_and_add_forecast_url() -> None:
    migrations = Path(__file__).resolve().parents[2] / "migrations"
    original = (migrations / "0004_weather_provider_configuration.sql").read_text()
    update = (migrations / "0007_weather_provider_endpoints.sql").read_text()
    assert "ON CONFLICT DO NOTHING" in original
    assert "timeout_seconds BETWEEN 1 AND 15" in original
    assert "max_body_bytes BETWEEN 1024 AND 100000" in original
    assert "ADD COLUMN IF NOT EXISTS forecast_url" in update
    assert "WHERE provider_id = 'open-meteo' AND forecast_url IS NULL" in update
    assert "DROP CONSTRAINT IF EXISTS" in update
