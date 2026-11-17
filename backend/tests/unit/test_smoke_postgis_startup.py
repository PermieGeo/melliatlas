"""Offline safety checks for the opt-in migrated ASGI startup smoke command."""

from pathlib import Path

import pytest
from smoke_postgis_startup import assert_test_database, migration_paths


def test_smoke_test_rejects_non_test_database() -> None:
    for value in (None, "melliatlas", "melliatlas_test_backup", 1):
        with pytest.raises(ValueError, match="ends with _test"):
            assert_test_database(value)
    assert_test_database("melliatlas_test")


def test_smoke_test_loads_sequential_migrations() -> None:
    root = Path(__file__).resolve().parents[2] / "migrations"
    paths = migration_paths(root)
    assert len(paths) >= 7
    assert paths[0].name == "0001_completed_investigations.sql"
    assert paths[6].name == "0007_weather_provider_endpoints.sql"


def test_smoke_test_rejects_gapped_or_empty_migration_series(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="complete sequence"):
        migration_paths(tmp_path)
    (tmp_path / "0001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "0003_third.sql").write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(ValueError, match="complete sequence"):
        migration_paths(tmp_path)
