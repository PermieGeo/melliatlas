"""ASGI application entry point with opt-in local territory references."""

import os
from pathlib import Path

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode


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


"""Only explicit opt-in enables experimental public Saturn requests."""


def _saturn_enabled() -> bool:
    raw = os.environ.get("MELLIATLAS_SATURN_LIVE_ENABLED", "false").lower()
    if raw not in ("false", "true"):
        raise ValueError("MELLIATLAS_SATURN_LIVE_ENABLED must be true or false")
    return raw == "true"


app = create_app(
    settings=AppSettings(
        reference_snapshot_path=_optional_path("MELLIATLAS_REFERENCE_SNAPSHOT"),
        reference_inventory_path=_optional_path("MELLIATLAS_REFERENCE_INVENTORY"),
        source_provider=_source_provider_mode(),
        saturn_live_enabled=_saturn_enabled(),
    )
)
