"""Negative and boundary cases for normalized reference geometry."""

import asyncio
from dataclasses import replace

import pytest

from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    GeometryStatus,
    PolygonWgs84,
    ReferenceSnapshot,
    TerritoryReferenceError,
)
from melliatlas.territories.validation import snapshot_checksum


def _replace_geometry(reference: ReferenceSnapshot, geometry: PolygonWgs84) -> ReferenceSnapshot:
    original = reference.geometries[0]
    updated = replace(
        reference, geometries=(replace(original, geometry=geometry),) + reference.geometries[1:]
    )
    return replace(
        updated, manifest=replace(updated.manifest, checksum_sha256=snapshot_checksum(updated))
    )


@pytest.mark.parametrize(
    "positions",
    [
        [(30.0, 55.0), (30.1, 55.0), (30.1, 55.1), (30.0, 55.1)],
        [(30.0, 55.0), (30.1, 55.0), (30.1, 95.0), (30.0, 55.0)],
        [(30.0, 55.0), (30.1, 55.1), (30.1, 55.0), (30.0, 55.1), (30.0, 55.0)],
    ],
)
def test_invalid_geometry_fails_before_import(
    positions: list[tuple[float, float]],
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    reference, inventory = reference_case
    invalid: PolygonWgs84 = {"type": "Polygon", "coordinates": [positions]}
    with pytest.raises(TerritoryReferenceError):
        asyncio.run(
            InMemoryTerritoryCatalog().apply_reference(
                _replace_geometry(reference, invalid), inventory
            )
        )


def test_geometry_status_cannot_claim_available_without_geometry(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    reference, inventory = reference_case
    changed = replace(reference, geometries=reference.geometries[1:])
    changed = replace(
        changed, manifest=replace(changed.manifest, checksum_sha256=snapshot_checksum(changed))
    )
    with pytest.raises(TerritoryReferenceError, match="availability"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(changed, inventory))


def test_missing_geometry_must_be_explicit(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    reference, inventory = reference_case
    country = replace(reference.territories[0], geometry_status=GeometryStatus.MISSING)
    changed = replace(
        reference,
        territories=(country,) + reference.territories[1:],
        geometries=reference.geometries[1:],
    )
    changed = replace(
        changed, manifest=replace(changed.manifest, checksum_sha256=snapshot_checksum(changed))
    )
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(changed, inventory))
    assert asyncio.run(catalog.get_geometry("RU")) is None


@pytest.mark.parametrize(
    ("original_id", "foreign_id", "country"),
    [
        ("ru:region:other", "by:region:russian-territory", CountryCode.RU),
        ("by:region:other", "ru:region:belarusian-territory", CountryCode.BY),
    ],
)
def test_region_id_prefix_must_match_country_even_with_matching_inventory(
    original_id: str,
    foreign_id: str,
    country: CountryCode,
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    reference, inventory = reference_case
    changed = replace(
        reference,
        territories=tuple(
            replace(item, id=foreign_id) if item.id == original_id else item
            for item in reference.territories
        ),
        geometries=tuple(
            replace(item, territory_id=foreign_id) if item.territory_id == original_id else item
            for item in reference.geometries
        ),
    )
    changed = replace(
        changed, manifest=replace(changed.manifest, checksum_sha256=snapshot_checksum(changed))
    )
    expected = replace(
        inventory,
        region_ids={
            key: (frozenset((values - {original_id}) | {foreign_id}) if key is country else values)
            for key, values in inventory.region_ids.items()
        },
    )
    with pytest.raises(TerritoryReferenceError, match="country prefix"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(changed, expected))


@pytest.mark.parametrize(
    ("original_id", "foreign_id", "region_id"),
    [
        ("ru:district:smolensk-test", "by:district:smolensk-test", "ru:region:smolensk"),
        ("by:district:vitebsk-test", "ru:district:vitebsk-test", "by:region:vitebsk"),
    ],
)
def test_district_id_prefix_must_match_country_and_parent(
    original_id: str,
    foreign_id: str,
    region_id: str,
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    reference, inventory = reference_case
    changed = replace(
        reference,
        territories=tuple(
            replace(item, id=foreign_id) if item.id == original_id else item
            for item in reference.territories
        ),
        geometries=tuple(
            replace(item, territory_id=foreign_id) if item.territory_id == original_id else item
            for item in reference.geometries
        ),
    )
    changed = replace(
        changed, manifest=replace(changed.manifest, checksum_sha256=snapshot_checksum(changed))
    )
    expected = replace(
        inventory,
        pilot_district_ids={
            key: (
                frozenset((values - {original_id}) | {foreign_id}) if key == region_id else values
            )
            for key, values in inventory.pilot_district_ids.items()
        },
    )
    with pytest.raises(TerritoryReferenceError, match="country prefix"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(changed, expected))
