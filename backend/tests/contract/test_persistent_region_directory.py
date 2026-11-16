"""Contract checks for independent region identities and RU-only Saturn mapping."""

import asyncio
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from melliatlas.api.app import AppSettings, create_app
from melliatlas.persistence.regions import PostgresRegionCatalog
from melliatlas.sources.api import TreatmentNoticePage
from melliatlas.territories.api import (
    CatalogDepthUnsupported,
    CountryCode,
    GeometryStatus,
    ReferenceUnavailableError,
)


class RegionDatabase:
    def __init__(self) -> None:
        self.rows = (
            ("ru:region:smo", "RU", "Смоленская область", "iso-codes:4.18.0", date(2026, 11, 16)),
            ("ru:region:mos", "RU", "Московская область", "iso-codes:4.18.0", date(2026, 11, 16)),
            ("by:region:vi", "BY", "Витебская область", "iso-codes:4.18.0", date(2026, 11, 16)),
        )
        self.connections: list[RegionConnection] = []
        self.fail = False

    def connect(self) -> "RegionConnection":
        if self.fail:
            raise OSError("PRIVATE DB CONNECTION FAILURE")
        connection = RegionConnection(self)
        self.connections.append(connection)
        return connection


class RegionConnection:
    def __init__(self, db: RegionDatabase) -> None:
        self.db = db
        self.rows: tuple[tuple[object, ...], ...] = ()
        self.index = 0
        self.closed = False
        self.cursor_closed = False
        self.statements: list[tuple[str, tuple[object, ...]]] = []

    def cursor(self) -> "RegionConnection":
        return self

    def execute(self, query: str, params: Sequence[object] = ()) -> None:
        self.statements.append((query, tuple(params)))
        if "FROM melliatlas_source_saturn_district" in query:
            self.rows = ((1472,),) if params == ("ru:district:verified", "ru:region:smo") else ()
        elif "FROM melliatlas_source_saturn" in query:
            self.rows = ((55,),) if params == ("ru:region:smo",) else ()
        elif "WHERE country_code = %s" in query:
            self.rows = tuple(x for x in self.db.rows if x[1] == params[0])
        elif "WHERE id = %s" in query:
            self.rows = tuple(x for x in self.db.rows if x[0] == params[0])
        else:
            raise AssertionError("Unexpected region query")
        self.index = 0

    def fetchone(self) -> tuple[object, ...] | None:
        if self.index == len(self.rows):
            return None
        row = self.rows[self.index]
        self.index += 1
        return row

    def close(self) -> None:
        if not self.cursor_closed:
            self.cursor_closed = True
        else:
            self.closed = True

    def commit(self) -> None:
        raise AssertionError("Region reads must not commit")

    def rollback(self) -> None:
        raise AssertionError("Region reads must not roll back")


class RecordedSaturnReader:
    def __init__(self) -> None:
        self.calls: list[tuple[CountryCode, int, int]] = []

    def read_page(
        self,
        *,
        country: CountryCode,
        region_code: int,
        page_number: int,
        district_code: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TreatmentNoticePage:
        from datetime import datetime, timezone

        self.calls.append((country, region_code, page_number))
        return TreatmentNoticePage(
            source_id="saturn:public-beekeeper-portal",
            country=country,
            region_code=region_code,
            captured_at=datetime.now(timezone.utc),
            page_number=page_number,
            next_page=None,
            total_elements=0,
            unidentified_records=0,
            notices=(),
        )


async def _get(app: FastAPI, url: str) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get(url)


async def _post(app: FastAPI, body: dict[str, object]) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.post("/api/v1/sources/saturn/treatments", json=body)


def test_seed_data_has_independent_country_and_iso_identifiers() -> None:
    path = Path(__file__).resolve().parents[2] / "reference" / "iso3166-2-regions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    regions = data["regions"]
    assert data["version"] == "4.18.0"
    assert len(regions) == 90
    assert sum(x["country"] == "RU" for x in regions) == 83
    assert sum(x["country"] == "BY" for x in regions) == 7
    assert len({x["id"] for x in regions}) == 90
    assert all(
        x["id"] == x["country"].lower() + ":region:" + x["iso_code"].split("-")[1].lower()
        for x in regions
    )
    assert any(x["id"] == "ru:region:smo" and x["name"] == "Смоленская область" for x in regions)
    assert any(x["id"] == "by:region:hm" and x["name"] == "Минск" for x in regions)
    assert not any("saturn" in x for x in regions)


def test_region_directory_is_not_dependent_on_saturn() -> None:
    db = RegionDatabase()
    store = PostgresRegionCatalog(db.connect)
    ru = asyncio.run(store.list_regions(CountryCode.RU))
    by = asyncio.run(store.list_regions(CountryCode.BY))
    assert {x.id for x in ru} == {"ru:region:smo", "ru:region:mos"}
    assert [x.id for x in by] == ["by:region:vi"]
    assert all(x.geometry_status is GeometryStatus.MISSING for x in ru)
    assert all(conn.closed and conn.cursor_closed for conn in db.connections)
    assert (found := asyncio.run(store.get("ru:region:smo"))) is not None
    assert found.id == "ru:region:smo"
    assert asyncio.run(store.get_geometry("ru:region:smo")) is None
    with pytest.raises(CatalogDepthUnsupported):
        asyncio.run(store.list_districts("ru:region:smo"))


def test_source_mapping_is_ru_only_and_never_guessed() -> None:
    db = RegionDatabase()
    store = PostgresRegionCatalog(db.connect)
    assert (
        asyncio.run(
            store.find_code(source_id="saturn", country=CountryCode.RU, region_id="ru:region:smo")
        )
        == 55
    )
    assert (
        asyncio.run(
            store.find_code(source_id="saturn", country=CountryCode.RU, region_id="ru:region:mos")
        )
        is None
    )
    count = len(db.connections)
    assert (
        asyncio.run(
            store.find_code(source_id="saturn", country=CountryCode.BY, region_id="by:region:vi")
        )
        is None
    )
    assert (
        asyncio.run(
            store.find_code(source_id="other", country=CountryCode.RU, region_id="ru:region:smo")
        )
        is None
    )
    assert len(db.connections) == count


def test_saturn_district_mapping_is_distinct_from_geography_identity() -> None:
    db = RegionDatabase()
    store = PostgresRegionCatalog(db.connect)
    assert (
        asyncio.run(
            store.find_district_code(
                source_id="saturn",
                country=CountryCode.RU,
                region_id="ru:region:smo",
                district_id="ru:district:verified",
            )
        )
        == 1472
    )
    assert (
        asyncio.run(
            store.find_district_code(
                source_id="saturn",
                country=CountryCode.RU,
                region_id="ru:region:mos",
                district_id="ru:district:verified",
            )
        )
        is None
    )
    before = len(db.connections)
    assert (
        asyncio.run(
            store.find_district_code(
                source_id="saturn",
                country=CountryCode.BY,
                region_id="by:region:vi",
                district_id="by:district:verified",
            )
        )
        is None
    )
    assert len(db.connections) == before


def test_database_failure_is_not_reported_as_empty_catalog() -> None:
    db = RegionDatabase()
    db.fail = True
    store = PostgresRegionCatalog(db.connect)
    with pytest.raises(ReferenceUnavailableError, match="Region database unavailable") as exc:
        asyncio.run(store.list_regions(CountryCode.RU))
    assert "PRIVATE" not in str(exc.value)


def test_api_returns_country_scoped_real_region_names() -> None:
    store = PostgresRegionCatalog(RegionDatabase().connect)
    app = create_app(territories=store, source_region_lookup=store)
    response = asyncio.run(_get(app, "/api/v1/territories/regions?country=RU"))
    assert response.status_code == 200
    assert {x["name"] for x in response.json()} == {"Смоленская область", "Московская область"}
    assert all(x["geometry_status"] == "missing" for x in response.json())
    district = asyncio.run(_get(app, "/api/v1/territories/districts?region_id=ru:region:smo"))
    assert district.status_code == 409
    geometry = asyncio.run(_get(app, "/api/v1/territories/geometry/ru:region:smo"))
    assert geometry.status_code == 404


def test_saturn_uses_database_mapping_without_exposing_subject_code_to_ui() -> None:
    store = PostgresRegionCatalog(RegionDatabase().connect)
    saturn = RecordedSaturnReader()
    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        territories=store,
        source_region_lookup=store,
        saturn_reader=saturn,
    )
    response = asyncio.run(
        _post(app, {"country": "RU", "region_id": "ru:region:smo", "page_number": 0})
    )
    assert response.status_code == 200
    assert response.json()["region_id"] == "ru:region:smo"
    assert response.json()["region_code"] == 55
    assert saturn.calls == [(CountryCode.RU, 55, 0)]
    unknown = asyncio.run(_post(app, {"country": "RU", "region_id": "ru:region:mos"}))
    assert unknown.status_code == 409
    assert unknown.json()["error"]["code"] == "SOURCE_REGION_UNMAPPED"
    assert len(saturn.calls) == 1
    by = asyncio.run(_post(app, {"country": "BY", "region_id": "by:region:vi"}))
    assert by.status_code == 404
    assert len(saturn.calls) == 1
    both = asyncio.run(
        _post(app, {"country": "RU", "region_id": "ru:region:smo", "region_code": 55})
    )
    assert both.status_code == 422
    assert len(saturn.calls) == 1
