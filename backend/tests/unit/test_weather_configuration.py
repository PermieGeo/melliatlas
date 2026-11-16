"""Weather settings are optional, bounded and never sourced from the browser.

A database override may tighten HTTP resource budgets, not replace the
fixed forecast wire contract or redirect provider requests to another host.
These deterministic fakes do not assert real PostgreSQL migration behavior.
"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import LiteralString

import pytest

from melliatlas.persistence.weather_config import read_weather_configuration
from melliatlas.sources.providers.open_meteo.settings import WeatherTransportSettings


class WeatherCursor:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row
        self.closed = False
        self.parameters: tuple[object, ...] | None = None
        self.executed_query: str | None = None

    def execute(self, query: LiteralString, params: Sequence[object] = ()) -> None:
        self.executed_query = query
        self.parameters = tuple(params)

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row

    def close(self) -> None:
        self.closed = True


class WeatherConnection:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.test_cursor = WeatherCursor(row)
        self.closed = False

    def cursor(self) -> WeatherCursor:
        return self.test_cursor

    def commit(self) -> None:
        raise AssertionError("Weather configuration is read-only")

    def rollback(self) -> None:
        raise AssertionError("Weather configuration is read-only")

    def close(self) -> None:
        self.closed = True


def test_weather_config_reads_only_single_registered_provider() -> None:
    connection = WeatherConnection((True, 5, 50_000, "https://open-meteo.com/en/docs"))
    enabled, timeout, body_limit, uri = read_weather_configuration(lambda: connection)
    settings = WeatherTransportSettings(timeout, body_limit, uri)
    assert enabled is True
    assert settings.timeout_seconds == 5
    assert settings.max_body_bytes == 50_000
    assert connection.test_cursor.parameters == ("open-meteo",)
    assert connection.test_cursor.executed_query is not None
    assert "FROM melliatlas_weather_provider_config" in connection.test_cursor.executed_query
    assert connection.test_cursor.closed and connection.closed


@pytest.mark.parametrize(
    "row",
    [
        None,
        (),
        (True, 3, 4096),
        ("true", 3, 4096, "https://open-meteo.com/en/docs"),
        (True, True, 4096, "https://open-meteo.com/en/docs"),
        (True, 3, 4096, None),
    ],
)
def test_weather_config_rejects_missing_or_invalid_database_row(
    row: tuple[object, ...] | None,
) -> None:
    connection = WeatherConnection(row)
    with pytest.raises(ValueError, match="configuration"):
        read_weather_configuration(lambda: connection)
    assert connection.test_cursor.closed and connection.closed


@pytest.mark.parametrize(
    "invalid",
    [
        lambda: WeatherTransportSettings(timeout_seconds=0),
        lambda: WeatherTransportSettings(timeout_seconds=16),
        lambda: WeatherTransportSettings(max_body_bytes=1023),
        lambda: WeatherTransportSettings(max_body_bytes=100_001),
        lambda: WeatherTransportSettings(source_uri="https://evil.example/docs"),
        lambda: WeatherTransportSettings(source_uri="http://open-meteo.com/en/docs"),
        lambda: WeatherTransportSettings(source_uri="https://open-meteo.com@evil.example/docs"),
        lambda: WeatherTransportSettings(source_uri="https://open-meteo.com/en/docs#fragment"),
        lambda: WeatherTransportSettings(source_uri="https://open-meteo.com/en/docs?track=user"),
    ],
)
def test_weather_transport_policy_rejects_unsafe_overrides(
    invalid: Callable[[], WeatherTransportSettings],
) -> None:
    with pytest.raises(ValueError):
        invalid()


def test_weather_migration_is_idempotent_and_enforces_limits() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "0004_weather_provider_configuration.sql"
    )
    migration = migration_path.read_text()
    assert "CREATE TABLE IF NOT EXISTS melliatlas_weather_provider_config" in migration
    assert "ON CONFLICT DO NOTHING" in migration
    assert "timeout_seconds BETWEEN 1 AND 15" in migration
    assert "max_body_bytes BETWEEN 1024 AND 100000" in migration
