"""ASGI application entry point with opt-in local territory references."""

import os
from pathlib import Path

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode
from melliatlas.persistence.geography import PostgisTerritoryCatalog


def _optional_path(env_name: str) -> Path | None:
    value = os.environ.get(env_name)
    return Path(value) if value else None


def _source_provider_mode() -> SourceProviderMode:
    configured = os.environ.get("MELLIATLAS_SOURCE_PROVIDER", "disabled")
    try:
        return SourceProviderMode(configured)
    except ValueError as error:
        raise ValueError(
            "Invalid MELLIATLAS_SOURCE_PROVIDER; expected disabled or synthetic"
        ) from error


def _saturn_enabled() -> bool:
    raw = os.environ.get("MELLIATLAS_SATURN_LIVE_ENABLED", "false").lower()
    if raw not in ("false", "true"):
        raise ValueError("MELLIATLAS_SATURN_LIVE_ENABLED must be true or false")
    return raw == "true"


def _weather_enabled() -> bool:
    """Enable non-commercial forecast reads explicitly, never by default."""
    raw = os.environ.get("MELLIATLAS_WEATHER_LIVE_ENABLED", "false").lower()
    if raw not in ("true", "false"):
        raise ValueError("MELLIATLAS_WEATHER_LIVE_ENABLED must be true or false")
    return raw == "true"


def _database_regions() -> PostgisTerritoryCatalog | None:
    """Use only an explicitly configured, preseeded persistent region directory."""
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if dsn is None:
        return None
    if not dsn.strip():
        raise ValueError("MELLIATLAS_DATABASE_URL must not be empty")
    from melliatlas.persistence.postgres import connection_factory

    return PostgisTerritoryCatalog(connection_factory(dsn))


_regions = _database_regions()

app = create_app(
    territories=_regions,
    source_region_lookup=_regions,
    settings=AppSettings(
        reference_snapshot_path=_optional_path("MELLIATLAS_REFERENCE_SNAPSHOT"),
        reference_inventory_path=_optional_path("MELLIATLAS_REFERENCE_INVENTORY"),
        source_provider=_source_provider_mode(),
        saturn_live_enabled=_saturn_enabled(),
        weather_live_enabled=_weather_enabled(),
    ),
)
