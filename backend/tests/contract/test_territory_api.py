"""Contract checks for validated country and pilot-district navigation."""

import asyncio
from dataclasses import replace

import pytest

from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import (
    CatalogDepthUnsupported,
    CountryCode,
    ExpectedInventory,
    ReferenceSnapshot,
    ReferenceUnavailableError,
    TerritoryIncompleteError,
    TerritoryKind,
    TerritoryNotFound,
    TerritoryReferenceError,
)
from melliatlas.territories.validation import snapshot_checksum


def _rehash(snapshot: ReferenceSnapshot) -> ReferenceSnapshot:
    return replace(
        snapshot, manifest=replace(snapshot.manifest, checksum_sha256=snapshot_checksum(snapshot))
    )


def test_unloaded_catalog_is_not_a_complete_empty_result() -> None:
    with pytest.raises(ReferenceUnavailableError):
        asyncio.run(InMemoryTerritoryCatalog().list_regions(CountryCode.RU))


def test_regions_and_districts_preserve_canonical_parents(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(snapshot, inventory))
    ru = asyncio.run(catalog.list_regions(CountryCode.RU))
    by = asyncio.run(catalog.list_regions(CountryCode.BY))
    assert {item.id for item in ru} == inventory.region_ids[CountryCode.RU]
    assert {item.id for item in by} == inventory.region_ids[CountryCode.BY]
    districts = asyncio.run(catalog.list_districts("ru:region:smolensk"))
    assert len(districts) == 1
    assert districts[0].kind is TerritoryKind.DISTRICT
    assert districts[0].parent_id == "ru:region:smolensk"


def test_unsupported_depth_is_not_silent_empty_inventory(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(snapshot, inventory))
    with pytest.raises(CatalogDepthUnsupported):
        asyncio.run(catalog.list_districts("ru:region:other"))
    with pytest.raises(TerritoryNotFound):
        asyncio.run(catalog.list_districts("ru:region:unknown"))


def test_missing_reference_member_fails_against_independent_inventory(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    incomplete = replace(
        snapshot,
        territories=tuple(t for t in snapshot.territories if t.id != "ru:region:other"),
        geometries=tuple(g for g in snapshot.geometries if g.territory_id != "ru:region:other"),
    )
    with pytest.raises(TerritoryIncompleteError):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(_rehash(incomplete), inventory))


def test_missing_district_fails_against_independent_inventory(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    missing = replace(
        snapshot,
        territories=tuple(t for t in snapshot.territories if t.id != "by:district:vitebsk-test"),
        geometries=tuple(
            g for g in snapshot.geometries if g.territory_id != "by:district:vitebsk-test"
        ),
    )
    with pytest.raises(TerritoryIncompleteError):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(_rehash(missing), inventory))


def test_duplicate_id_rejected(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    duplicate = replace(snapshot, territories=snapshot.territories + (snapshot.territories[0],))
    with pytest.raises(TerritoryReferenceError, match="Duplicate"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(_rehash(duplicate), inventory))


def test_cross_country_parent_rejected(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    updated = replace(
        snapshot,
        territories=tuple(
            replace(t, parent_id="by:region:vitebsk") if t.id == "ru:district:smolensk-test" else t
            for t in snapshot.territories
        ),
    )
    with pytest.raises(TerritoryReferenceError, match="parent"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(_rehash(updated), inventory))


def test_mismatched_checksum_rejected(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    updated = replace(
        snapshot,
        territories=tuple(
            replace(t, name="Changed") if t.id == "RU" else t for t in snapshot.territories
        ),
    )
    with pytest.raises(TerritoryReferenceError, match="checksum"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(updated, inventory))


def test_same_import_is_idempotent_and_conflicting_import_does_not_mutate(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(snapshot, inventory))
    asyncio.run(catalog.apply_reference(snapshot, inventory))
    changed = _rehash(
        replace(
            snapshot,
            territories=tuple(
                replace(t, name="Different") if t.id == "RU" else t for t in snapshot.territories
            ),
        )
    )
    with pytest.raises(TerritoryReferenceError, match="immutable"):
        asyncio.run(catalog.apply_reference(changed, inventory))
    assert asyncio.run(catalog.get("RU")) is not None
    stored = asyncio.run(catalog.get("RU"))
    assert stored is not None
    assert stored.name == "Synthetic RU"


def test_geometry_is_isolated_from_caller_mutation(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(snapshot, inventory))
    geometry = asyncio.run(catalog.get_geometry("RU"))
    assert geometry is not None
    if geometry.geometry["type"] == "Polygon":
        geometry.geometry["coordinates"][0][0] = (-50.0, -50.0)
    unmodified = asyncio.run(catalog.get_geometry("RU"))
    assert unmodified is not None
    assert unmodified.geometry["coordinates"] != geometry.geometry["coordinates"]


def test_missing_inventory_is_rejected(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    invalid = replace(inventory, region_ids={CountryCode.RU: inventory.region_ids[CountryCode.RU]})
    with pytest.raises(TerritoryReferenceError, match="RU and BY"):
        asyncio.run(InMemoryTerritoryCatalog().apply_reference(snapshot, invalid))
