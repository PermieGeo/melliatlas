"""PostGIS catalog contract without network or local PostgreSQL assumptions."""

import asyncio
import json
from collections.abc import Sequence
from datetime import date
from typing import LiteralString

import pytest

from melliatlas.persistence.geography import PostgisTerritoryCatalog
from melliatlas.territories.api import CountryCode, GeometryStatus, ReferenceUnavailableError


class GeographyDatabase:
    def __init__(self) -> None:
        self.closed = 0
        self.sql: list[str] = []
        self.geometry_response: str | None = None

    def connect(self) -> "GeographyConnection":
        return GeographyConnection(self)


class GeographyConnection:
    def __init__(self, db: GeographyDatabase) -> None:
        self.db = db
        self.rows: tuple[tuple[object, ...], ...] = ()
        self.index = 0

    def cursor(self) -> "GeographyConnection":
        return self

    def execute(self, query: LiteralString, params: Sequence[object] = ()) -> None:
        self.db.sql.append(query)
        if "ST_Covers(boundary" in query:
            if "kind = 'region'" in query:
                self.rows = (("by:region:vi",),) if params == ("BY", 27.5, 55.5) else ()
            else:
                self.rows = (
                    (("by:district:abc123",),) if params == ("by:region:vi", 27.5, 55.5) else ()
                )
        elif "FROM melliatlas_source_saturn" in query:
            self.rows = ((55,),)
        elif "ST_AsGeoJSON" in query:
            geometry = self.db.geometry_response
            if geometry is None:
                geometry = json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [[27, 55], [28, 55], [28, 56], [27, 55]],
                        ],
                    }
                )
            self.rows = (("geoboundaries:BLR-ADM2", geometry),)
        elif "FROM melliatlas_admin_geometry" in query and "kind = 'district'" in query:
            district = (
                "by:district:abc123",
                "BY",
                "Vitebsk district",
                "by:region:vi",
                "geoboundaries:BLR-ADM2",
                date(2026, 11, 16),
            )
            self.rows = (district,) if params[0] in ("by:region:vi", "by:district:abc123") else ()
        elif "FROM melliatlas_region" in query:
            region = (
                "by:region:vi",
                "BY",
                "Витебская область",
                "geoboundaries:BLR-ADM1",
                date(2026, 11, 16),
                True,
            )
            self.rows = (region,) if params[0] in ("BY", "by:region:vi") else ()
        else:
            raise AssertionError("Unexpected query")
        self.index = 0

    def fetchone(self) -> tuple[object, ...] | None:
        if self.index == len(self.rows):
            return None
        row = self.rows[self.index]
        self.index += 1
        return row

    def close(self) -> None:
        self.db.closed += 1

    def commit(self) -> None:
        raise AssertionError("Read-only catalog should not commit")

    def rollback(self) -> None:
        raise AssertionError("Read-only catalog should not roll back")


def test_regions_and_districts_are_independent_of_saturn() -> None:
    db = GeographyDatabase()
    store = PostgisTerritoryCatalog(db.connect)
    regions = asyncio.run(store.list_regions(CountryCode.BY))
    assert regions[0].geometry_status is GeometryStatus.AVAILABLE
    assert regions[0].reference_id == "geoboundaries:BLR-ADM1"
    districts = asyncio.run(store.list_districts("by:region:vi"))
    assert len(districts) == 1
    assert districts[0].parent_id == "by:region:vi"
    geometry = asyncio.run(store.get_geometry(districts[0].id))
    assert geometry is not None
    assert geometry.reference_id == districts[0].reference_id
    assert geometry.geometry["type"] == "Polygon"
    assert (
        asyncio.run(
            store.find_code(source_id="saturn", country=CountryCode.BY, region_id="by:region:vi")
        )
        is None
    )
    assert db.closed > 0


@pytest.mark.parametrize(
    "payload",
    [
        '{"type":"Point","coordinates":[27,55]}',
        '{"type":"Polygon","coordinates":[[[27,55],[28,55],[27,55]]]}',
        '{"type":"Polygon","coordinates":[[[999,55],[28,55],[28,56],[999,55]]]}',
        '{"type":"Polygon","coordinates":null}',
        '{"type":"Polygon","coordinates":[[[true,55],[28,55],[28,56],[true,55]]]}',
    ],
)
def test_geometry_decoder_rejects_invalid_data(payload: str) -> None:
    db = GeographyDatabase()
    db.geometry_response = payload
    store = PostgisTerritoryCatalog(db.connect)
    with pytest.raises(ReferenceUnavailableError, match="Invalid stored boundary geometry"):
        asyncio.run(store.get_geometry("by:region:vi"))


def test_empty_or_missing_region_is_explicit() -> None:
    db = GeographyDatabase()
    store = PostgisTerritoryCatalog(db.connect)
    with pytest.raises(ReferenceUnavailableError):
        asyncio.run(store.list_regions(CountryCode.RU))
    assert asyncio.run(store.get("by:district:other")) is None


def test_point_lookup_uses_imported_geometry_and_returns_canonical_district() -> None:
    db = GeographyDatabase()
    catalog = PostgisTerritoryCatalog(db.connect)
    found = asyncio.run(catalog.locate_point(country=CountryCode.BY, longitude=27.5, latitude=55.5))
    assert found is not None
    assert found.region_id == "by:region:vi"
    assert found.district_id == "by:district:abc123"
    assert sum("ST_Covers" in statement for statement in db.sql) == 2
    assert (
        asyncio.run(catalog.locate_point(country=CountryCode.BY, longitude=20, latitude=50)) is None
    )
    with pytest.raises(ValueError):
        asyncio.run(
            catalog.locate_point(country=CountryCode.BY, longitude=float("nan"), latitude=55)
        )
