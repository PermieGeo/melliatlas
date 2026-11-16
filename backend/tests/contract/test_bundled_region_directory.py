"""An offline region list must not depend on migrations or fictional coordinates."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from melliatlas.api.app import create_app
from melliatlas.api.reference_loader import read_iso_region_directory
from melliatlas.territories.region_directory import RegionDirectoryCatalog

DATASET = Path(__file__).resolve().parents[2] / "reference" / "iso3166-2-regions.json"


async def _get(app: FastAPI, path: str) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get(path)


def test_pinned_ru_by_region_names_are_available_without_postgres() -> None:
    catalog = RegionDirectoryCatalog(read_iso_region_directory(DATASET))
    app = create_app(territories=catalog)
    ru = asyncio.run(_get(app, "/api/v1/territories/regions?country=RU"))
    by = asyncio.run(_get(app, "/api/v1/territories/regions?country=BY"))
    assert ru.status_code == by.status_code == 200
    assert len(ru.json()) == 83
    assert len(by.json()) == 7
    assert {item["id"] for item in ru.json()} >= {"ru:region:smo"}
    assert {item["id"] for item in by.json()} >= {"by:region:vi", "by:region:hm"}
    assert all(item["geometry_status"] == "missing" for item in ru.json() + by.json())
    assert all(item["reference_id"] == "iso-codes:4.18.0" for item in ru.json() + by.json())
    assert all(item["parent_id"] is None for item in ru.json() + by.json())


def test_name_only_regions_do_not_claim_districts_or_geometries() -> None:
    catalog = RegionDirectoryCatalog(read_iso_region_directory(DATASET))
    app = create_app(territories=catalog)
    district = asyncio.run(_get(app, "/api/v1/territories/districts?region_id=ru:region:smo"))
    assert district.status_code == 409
    assert district.json()["error"]["code"] == "DISTRICT_COVERAGE_UNSUPPORTED"
    unknown = asyncio.run(_get(app, "/api/v1/territories/districts?region_id=ru:region:unknown"))
    assert unknown.status_code == 404
    geometry = asyncio.run(_get(app, "/api/v1/territories/geometry/ru:region:smo"))
    assert geometry.status_code == 404
    assert geometry.json()["error"]["code"] == "TERRITORY_GEOMETRY_MISSING"


@pytest.mark.parametrize("change", ["duplicate", "missing", "bad_identity", "bad_version"])
def test_corrupted_bundled_region_list_fails_at_load(tmp_path: Path, change: str) -> None:
    raw = json.loads(DATASET.read_text(encoding="utf-8"))
    if change == "duplicate":
        raw["regions"][1] = raw["regions"][0]
    elif change == "missing":
        raw["regions"].pop()
    elif change == "bad_identity":
        raw["regions"][0]["iso_code"] = "RU-SMO"
    else:
        raw["version"] = "unverified"
    path = tmp_path / "corrupted.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        read_iso_region_directory(path)
