"""Synthetic administrative fixtures; never a real completeness inventory."""

from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    GeometryStatus,
    PolygonWgs84,
    ReferenceManifest,
    ReferenceSnapshot,
    Territory,
    TerritoryGeometry,
    TerritoryKind,
)
from melliatlas.territories.validation import snapshot_checksum


@pytest.fixture
def reference_case() -> tuple[ReferenceSnapshot, ExpectedInventory]:
    date_value = date(2025, 1, 1)
    reference_id = "SYNTHETIC-TEST-ONLY"

    def item(
        identifier: str, country: CountryCode, kind: TerritoryKind, parent: str | None
    ) -> Territory:
        return Territory(
            id=identifier,
            country=country,
            kind=kind,
            name=f"Synthetic {identifier}",
            parent_id=parent,
            reference_id=reference_id,
            valid_on=date_value,
            geometry_status=GeometryStatus.AVAILABLE,
        )

    territories = (
        item("RU", CountryCode.RU, TerritoryKind.COUNTRY, None),
        item("BY", CountryCode.BY, TerritoryKind.COUNTRY, None),
        item("ru:region:smolensk", CountryCode.RU, TerritoryKind.REGION, "RU"),
        item("ru:region:other", CountryCode.RU, TerritoryKind.REGION, "RU"),
        item("by:region:vitebsk", CountryCode.BY, TerritoryKind.REGION, "BY"),
        item("by:region:other", CountryCode.BY, TerritoryKind.REGION, "BY"),
        item("by:region:minsk-city", CountryCode.BY, TerritoryKind.REGION, "BY"),
        item(
            "ru:district:smolensk-test",
            CountryCode.RU,
            TerritoryKind.DISTRICT,
            "ru:region:smolensk",
        ),
        item(
            "by:district:vitebsk-test", CountryCode.BY, TerritoryKind.DISTRICT, "by:region:vitebsk"
        ),
    )
    # Deliberately fictional rectangles; not actual administrative boundaries.
    shape: PolygonWgs84 = {
        "type": "Polygon",
        "coordinates": [[(30.0, 55.0), (30.2, 55.0), (30.2, 55.2), (30.0, 55.2), (30.0, 55.0)]],
    }
    geometries = tuple(
        TerritoryGeometry(item.id, shape, reference_id, "EPSG:4326") for item in territories
    )
    manifest = ReferenceManifest(
        reference_id=reference_id,
        snapshot_date=date_value,
        retrieved_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        source_uri="fixture://synthetic-territory-contract",
        license_id="TEST-ONLY",
        checksum_sha256="0" * 64,
        coordinate_system="EPSG:4326",
        declared_scope="SYNTHETIC SUBSET ONLY; NOT AN ACTUAL RU/BY INVENTORY",
        normalization_version="test-v1",
    )
    snapshot = ReferenceSnapshot(manifest, territories, geometries)
    snapshot = replace(
        snapshot, manifest=replace(manifest, checksum_sha256=snapshot_checksum(snapshot))
    )
    inventory = ExpectedInventory(
        region_ids={
            CountryCode.RU: frozenset({"ru:region:smolensk", "ru:region:other"}),
            CountryCode.BY: frozenset(
                {"by:region:vitebsk", "by:region:other", "by:region:minsk-city"}
            ),
        },
        pilot_district_ids={
            "ru:region:smolensk": frozenset({"ru:district:smolensk-test"}),
            "by:region:vitebsk": frozenset({"by:district:vitebsk-test"}),
        },
        source_uri="fixture://synthetic-independent-inventory",
        version="test-v1",
    )
    return snapshot, inventory
