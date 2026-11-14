"""Offline loading of normalized reference files and independent inventories."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    ReferenceManifest,
    ReferenceSnapshot,
    Territory,
    TerritoryGeometry,
)


class _ReferenceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    manifest: ReferenceManifest
    territories: list[Territory]
    geometries: list[TerritoryGeometry]


class _InventoryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    # Independent inventory maintained separately from normalized source data.
    region_ids: dict[CountryCode, list[str]]
    pilot_district_ids: dict[str, list[str]]
    source_uri: str
    version: str


def read_reference_documents(
    snapshot_path: Path, inventory_path: Path
) -> tuple[ReferenceSnapshot, ExpectedInventory]:
    """Parse local files only; validation and approval belong to the importer boundary."""
    source = _ReferenceDocument.model_validate_json(snapshot_path.read_bytes())
    expected = _InventoryDocument.model_validate_json(inventory_path.read_bytes())
    snapshot = ReferenceSnapshot(
        manifest=source.manifest,
        territories=tuple(source.territories),
        geometries=tuple(source.geometries),
    )
    inventory = ExpectedInventory(
        region_ids={key: frozenset(ids) for key, ids in expected.region_ids.items()},
        pilot_district_ids={
            key: frozenset(ids) for key, ids in expected.pilot_district_ids.items()
        },
        source_uri=expected.source_uri,
        version=expected.version,
    )
    return snapshot, inventory


def write_reference_report(
    snapshot: ReferenceSnapshot, inventory: ExpectedInventory
) -> dict[str, str | int]:
    """Return metadata useful for a reviewed import, never an approval verdict."""
    return {
        "reference_id": snapshot.manifest.reference_id,
        "snapshot_date": snapshot.manifest.snapshot_date.isoformat(),
        "inventory_version": inventory.version,
        "region_count": sum(item.kind.value == "region" for item in snapshot.territories),
        "district_count": sum(item.kind.value == "district" for item in snapshot.territories),
        "geometry_count": len(snapshot.geometries),
    }
