"""Offline loading of normalized reference files and independent inventories."""

from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    GeometryStatus,
    ReferenceManifest,
    ReferenceSnapshot,
    Territory,
    TerritoryGeometry,
    TerritoryKind,
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


class _IsoSubdivision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    country: CountryCode
    iso_code: str
    name: str
    name_en: str


class _IsoDirectory(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source: str
    version: str
    source_uri: str
    license: str
    scope_note: str
    regions: list[_IsoSubdivision] = Field(min_length=1)


def read_iso_region_directory(path: Path) -> tuple[Territory, ...]:
    """Load the pinned source catalog; no claim about boundaries or current completeness."""
    document = _IsoDirectory.model_validate_json(path.read_bytes())
    if (document.source, document.version) != ("iso-codes", "4.18.0"):
        raise ValueError("Unexpected ISO region dataset version")
    if not document.source_uri or not document.license or not document.scope_note:
        raise ValueError("Region source provenance is missing")
    if len(document.regions) != 90 or {
        country: sum(item.country is country for item in document.regions)
        for country in CountryCode
    } != {CountryCode.RU: 83, CountryCode.BY: 7}:
        raise ValueError("Incomplete pinned ISO subdivision list")
    if (
        len({item.id for item in document.regions}) != 90
        or len({item.iso_code for item in document.regions}) != 90
    ):
        raise ValueError("Duplicate ISO region identities")
    for item in document.regions:
        suffix = item.id.rsplit(":", 1)[-1]
        if (
            item.id != f"{item.country.value.lower()}:region:{suffix}"
            or item.iso_code != f"{item.country.value}-{suffix.upper()}"
            or not item.name.strip()
            or not item.name_en.strip()
        ):
            raise ValueError("Invalid ISO region identity or name")
    return tuple(
        Territory(
            id=item.id,
            country=item.country,
            kind=TerritoryKind.REGION,
            name=item.name,
            parent_id=None,
            reference_id=f"iso-codes:{document.version}",
            valid_on=date.today(),
            geometry_status=GeometryStatus.MISSING,
        )
        for item in document.regions
    )
