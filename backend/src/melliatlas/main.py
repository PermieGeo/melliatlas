"""ASGI application entry point with opt-in local territory references."""

import os
from pathlib import Path

from melliatlas.api.app import AppSettings, create_app


def _optional_path(env_name: str) -> Path | None:
    value = os.environ.get(env_name)
    return Path(value) if value else None


app = create_app(
    settings=AppSettings(
        reference_snapshot_path=_optional_path("MELLIATLAS_REFERENCE_SNAPSHOT"),
        reference_inventory_path=_optional_path("MELLIATLAS_REFERENCE_INVENTORY"),
    )
)
