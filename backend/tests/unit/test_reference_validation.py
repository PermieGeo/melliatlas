"""Negative and boundary cases for normalized reference geometry."""

import asyncio
from dataclasses import replace

import pytest

from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import (
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
