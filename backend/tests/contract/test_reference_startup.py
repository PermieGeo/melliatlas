"""Opt-in, fail-closed reference loading at the ASGI lifespan boundary."""

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from melliatlas.api.app import AppSettings, create_app
from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    ReferenceSnapshot,
    TerritoryIncompleteError,
    TerritoryReferenceError,
)


def _files(
    directory: Path, snapshot: ReferenceSnapshot, inventory: ExpectedInventory
) -> tuple[Path, Path]:
    snapshot_file = directory / "snapshot.json"
    inventory_file = directory / "inventory.json"
    snapshot_file.write_text(json.dumps(asdict(snapshot), default=str), encoding="utf-8")
    inventory_file.write_text(
        json.dumps(
            {
                "region_ids": {
                    country.value: sorted(ids) for country, ids in inventory.region_ids.items()
                },
                "pilot_district_ids": {
                    region_id: sorted(ids)
                    for region_id, ids in inventory.pilot_district_ids.items()
                },
                "source_uri": inventory.source_uri,
                "version": inventory.version,
            }
        ),
        encoding="utf-8",
    )
    return snapshot_file, inventory_file


def _configured(snapshot_file: Path, inventory_file: Path) -> FastAPI:
    return create_app(
        settings=AppSettings(
            reference_snapshot_path=snapshot_file,
            reference_inventory_path=inventory_file,
        )
    )


async def _get(app: FastAPI, path: str) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.get(path)


def test_runtime_loads_independently_validated_snapshot_before_serving(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory], tmp_path: Path
) -> None:
    snapshot_file, inventory_file = _files(tmp_path, *reference_case)
    app = _configured(snapshot_file, inventory_file)

    async def scenario() -> None:
        before_start = await _get(app, "/api/v1/territories/regions?country=RU")
        assert before_start.status_code == 503
        async with app.router.lifespan_context(app):
            ru = await _get(app, "/api/v1/territories/regions?country=RU")
            by = await _get(app, "/api/v1/territories/regions?country=BY")
            districts = await _get(
                app, "/api/v1/territories/districts?region_id=ru:region:smolensk"
            )
            geometry = await _get(app, "/api/v1/territories/geometry/RU")
            assert {item["id"] for item in ru.json()} == (
                reference_case[1].region_ids[CountryCode.RU]
            )
            assert {item["id"] for item in by.json()} == (
                reference_case[1].region_ids[CountryCode.BY]
            )
            assert [item["parent_id"] for item in districts.json()] == ["ru:region:smolensk"]
            assert geometry.json()["reference_id"] == "SYNTHETIC-TEST-ONLY"
        other = await _get(create_app(), "/api/v1/territories/regions?country=RU")
        assert other.status_code == 503

    asyncio.run(scenario())


def test_loaded_snapshot_is_not_replaced_when_input_files_change(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory], tmp_path: Path
) -> None:
    snapshot_file, inventory_file = _files(tmp_path, *reference_case)
    app = _configured(snapshot_file, inventory_file)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            first = await _get(app, "/api/v1/territories/regions?country=RU")
            assert first.status_code == 200
            snapshot_file.write_text('{"invalid":true}', encoding="utf-8")
            second = await _get(app, "/api/v1/territories/regions?country=RU")
            assert second.json() == first.json()

    asyncio.run(scenario())


def test_missing_reference_pair_is_rejected_at_construction(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Both reference snapshot"):
        create_app(settings=AppSettings(reference_snapshot_path=tmp_path / "snapshot.json"))
    with pytest.raises(ValueError, match="Both reference snapshot"):
        create_app(settings=AppSettings(reference_inventory_path=tmp_path / "inventory.json"))


def test_explicit_catalog_and_reference_file_configuration_conflict(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="Explicit territory injection"):
        create_app(
            settings=AppSettings(
                reference_snapshot_path=tmp_path / "snapshot.json",
                reference_inventory_path=tmp_path / "inventory.json",
            ),
            territories=InMemoryTerritoryCatalog(),
        )


def test_missing_reference_file_fails_startup_not_silently_empty(tmp_path: Path) -> None:
    app = _configured(tmp_path / "missing.json", tmp_path / "inventory.json")

    async def scenario() -> None:
        with pytest.raises(FileNotFoundError):
            async with app.router.lifespan_context(app):
                pytest.fail("Missing reference cannot start the app")

    asyncio.run(scenario())


def test_invalid_checksum_fails_startup(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory], tmp_path: Path
) -> None:
    snapshot_file, inventory_file = _files(tmp_path, *reference_case)
    document: dict[str, object] = json.loads(snapshot_file.read_text(encoding="utf-8"))
    document["geometries"] = []
    snapshot_file.write_text(json.dumps(document), encoding="utf-8")
    app = _configured(snapshot_file, inventory_file)

    async def scenario() -> None:
        with pytest.raises(TerritoryReferenceError, match="checksum"):
            async with app.router.lifespan_context(app):
                pytest.fail("Bad reference cannot start the app")
        response = await _get(app, "/api/v1/territories/regions?country=RU")
        assert response.status_code == 503

    asyncio.run(scenario())


def test_independent_inventory_mismatch_fails_startup(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory], tmp_path: Path
) -> None:
    snapshot_file, inventory_file = _files(tmp_path, *reference_case)
    document: dict[str, object] = json.loads(inventory_file.read_text(encoding="utf-8"))
    region_ids = document["region_ids"]
    assert isinstance(region_ids, dict)
    region_ids["RU"] = []
    inventory_file.write_text(json.dumps(document), encoding="utf-8")
    app = _configured(snapshot_file, inventory_file)

    async def scenario() -> None:
        with pytest.raises(TerritoryIncompleteError, match="Incomplete RU region"):
            async with app.router.lifespan_context(app):
                pytest.fail("Incomplete reference cannot start the app")

    asyncio.run(scenario())


def test_asgi_entrypoint_respects_explicit_environment_paths(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from importlib import reload

    import melliatlas.main as main

    snapshot_file, inventory_file = _files(tmp_path, *reference_case)
    with monkeypatch.context() as environment:
        environment.setenv("MELLIATLAS_REFERENCE_SNAPSHOT", str(snapshot_file))
        environment.setenv("MELLIATLAS_REFERENCE_INVENTORY", str(inventory_file))
        environment.setenv("MELLIATLAS_WEATHER_LIVE_ENABLED", "false")
        configured = reload(main).app
        assert configured is not None

        async def scenario() -> None:
            async with configured.router.lifespan_context(configured):
                result = await _get(configured, "/api/v1/territories/regions?country=BY")
                assert result.status_code == 200

        asyncio.run(scenario())
    reload(main)
