"""ASGI application entry point with opt-in local territory references."""

import os
from pathlib import Path

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode, compose_weather_reader
from melliatlas.api.reference_loader import read_iso_region_directory
from melliatlas.persistence.geography import PostgisTerritoryCatalog
from melliatlas.sources.api import WeatherForecastReader
from melliatlas.sources.providers.open_meteo.settings import WeatherTransportSettings
from melliatlas.territories.region_directory import RegionDirectoryCatalog


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
_weather_allowed = _weather_enabled()


def _configured_weather_reader() -> WeatherForecastReader | None:
    """Load optional Postgres settings only during the ASGI lifespan startup."""
    if _regions is None:
        return compose_weather_reader(True)

    from melliatlas.persistence.postgres import connection_factory
    from melliatlas.persistence.weather_config import read_weather_configuration

    dsn = os.environ["MELLIATLAS_DATABASE_URL"]
    enabled, timeout, max_body, docs = read_weather_configuration(connection_factory(dsn))
    if not enabled:
        return None
    return compose_weather_reader(True, WeatherTransportSettings(timeout, max_body, docs))


_reference_snapshot = _optional_path("MELLIATLAS_REFERENCE_SNAPSHOT")
_reference_inventory = _optional_path("MELLIATLAS_REFERENCE_INVENTORY")
if _reference_snapshot is not None or _reference_inventory is not None:
    _catalog = None
elif _regions is not None:
    _catalog = _regions
else:
    _catalog = RegionDirectoryCatalog(
        read_iso_region_directory(
            Path(__file__).resolve().parents[2] / "reference" / "iso3166-2-regions.json"
        )
    )

app = create_app(
    territories=_catalog,
    source_region_lookup=_regions,
    source_district_lookup=_regions,
    weather_reader_factory=_configured_weather_reader if _weather_allowed else None,
    settings=AppSettings(
        reference_snapshot_path=_reference_snapshot,
        reference_inventory_path=_reference_inventory,
        source_provider=_source_provider_mode(),
        saturn_live_enabled=_saturn_enabled(),
        weather_live_enabled=_weather_allowed,
    ),
)
