"""Structural reference and WGS84 validation without provider-specific logic."""

import hashlib
import json
import re
from datetime import timezone

from shapely.errors import GEOSException
from shapely.geometry import shape
from shapely.validation import explain_validity

from melliatlas.geography import MIN_LINEAR_RING_POSITIONS, WGS84_CRS, is_wgs84_position
from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    GeometryStatus,
    GeometryWgs84,
    Position,
    ReferenceSnapshot,
    TerritoryIncompleteError,
    TerritoryKind,
    TerritoryReferenceError,
)

_REGION_ID = re.compile(r"^(ru|by):region:[a-z0-9-]+$")
_DISTRICT_ID = re.compile(r"^(ru|by):district:[a-z0-9-]+$")
_CHECKSUM = re.compile(r"^[0-9a-f]{64}$")


def snapshot_checksum(snapshot: ReferenceSnapshot) -> str:
    """Digest normalized payload, excluding its provenance-bearing manifest."""
    normalized = {
        "territories": [
            {
                "id": item.id,
                "country": item.country.value,
                "kind": item.kind.value,
                "name": item.name,
                "parent_id": item.parent_id,
                "reference_id": item.reference_id,
                "valid_on": item.valid_on.isoformat(),
                "geometry_status": item.geometry_status.value,
            }
            for item in sorted(snapshot.territories, key=lambda value: value.id)
        ],
        "geometries": [
            {
                "territory_id": item.territory_id,
                "geometry": item.geometry,
                "reference_id": item.reference_id,
                "coordinate_system": item.coordinate_system,
            }
            for item in sorted(snapshot.geometries, key=lambda value: value.territory_id)
        ],
    }
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_ring(ring: list[Position]) -> None:
    if len(ring) < MIN_LINEAR_RING_POSITIONS or ring[0] != ring[-1]:
        raise TerritoryReferenceError("Polygon rings must contain four positions and be closed")
    for longitude, latitude in ring:
        if not is_wgs84_position(longitude, latitude):
            raise TerritoryReferenceError("GeoJSON coordinates must use WGS84 longitude/latitude")
    if any(a == b for a, b in zip(ring, ring[1:])):
        raise TerritoryReferenceError("Polygon rings contain repeated adjacent coordinates")


def validate_geometry(geometry: GeometryWgs84) -> None:
    """Validate WGS84 coordinate structure and GEOS polygon topology."""
    polygon_groups = (
        [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    )
    if not polygon_groups:
        raise TerritoryReferenceError("GeoJSON geometry has no polygons")
    for polygon in polygon_groups:
        if not polygon:
            raise TerritoryReferenceError("GeoJSON polygon has no rings")
        for ring in polygon:
            _validate_ring(ring)

    try:
        parsed = shape(dict(geometry))
    except (GEOSException, ValueError, TypeError) as exc:
        raise TerritoryReferenceError("Malformed GeoJSON polygon topology") from exc
    if parsed.is_empty or parsed.area == 0 or not parsed.is_valid:
        raise TerritoryReferenceError(
            f"Invalid GeoJSON polygon topology: {explain_validity(parsed)}"
        )


def _require_catalogs(snapshot: ReferenceSnapshot, inventory: ExpectedInventory) -> None:
    if not inventory.source_uri or not inventory.version:
        raise TerritoryReferenceError("Independent reference inventory provenance is required")
    expected_countries = set(CountryCode)
    if set(inventory.region_ids) != expected_countries:
        raise TerritoryReferenceError("Independent inventories for RU and BY are required")
    if set(inventory.pilot_district_ids) != {"ru:region:smolensk", "by:region:vitebsk"}:
        raise TerritoryReferenceError(
            "Independent Smolensk and Vitebsk district inventories are required"
        )
    if "by:region:minsk-city" not in inventory.region_ids[CountryCode.BY]:
        raise TerritoryIncompleteError("The Minsk city first-order entry is required")
    territories = {item.id: item for item in snapshot.territories}
    for country in CountryCode:
        country_record = territories.get(country.value)
        if country_record is None or country_record.kind is not TerritoryKind.COUNTRY:
            raise TerritoryIncompleteError(f"Missing country record: {country.value}")
        if country_record.country is not country or country_record.parent_id is not None:
            raise TerritoryReferenceError("Invalid country identity or parent")
        actual = frozenset(
            item.id
            for item in snapshot.territories
            if item.kind is TerritoryKind.REGION and item.country is country
        )
        expected = inventory.region_ids[country]
        if not expected or actual != expected:
            raise TerritoryIncompleteError(
                f"Incomplete {country.value} region inventory: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )
    for region_id, expected in inventory.pilot_district_ids.items():
        parent = territories.get(region_id)
        if parent is None or parent.kind is not TerritoryKind.REGION:
            raise TerritoryReferenceError(f"Unknown pilot region: {region_id}")
        actual = frozenset(
            item.id
            for item in snapshot.territories
            if item.kind is TerritoryKind.DISTRICT and item.parent_id == region_id
        )
        if not expected or actual != expected:
            raise TerritoryIncompleteError(
                f"Incomplete pilot district inventory {region_id}: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )
    if any(
        item.kind is TerritoryKind.DISTRICT and item.parent_id not in inventory.pilot_district_ids
        for item in snapshot.territories
    ):
        raise TerritoryReferenceError("MVP-01 permits district data only for the two pilot regions")


def validate_reference(snapshot: ReferenceSnapshot, inventory: ExpectedInventory) -> None:
    manifest = snapshot.manifest
    if not (
        manifest.reference_id
        and manifest.source_uri
        and manifest.license_id
        and manifest.declared_scope
        and manifest.normalization_version
    ):
        raise TerritoryReferenceError("Reference manifest metadata is incomplete")
    if manifest.retrieved_at.tzinfo is None or manifest.retrieved_at.utcoffset() is None:
        raise TerritoryReferenceError("Reference retrieval timestamp must include a timezone")
    if manifest.retrieved_at.astimezone(timezone.utc).date() < manifest.snapshot_date:
        raise TerritoryReferenceError("Reference retrieval predates the snapshot")
    if manifest.coordinate_system != WGS84_CRS:
        raise TerritoryReferenceError("Unsupported coordinate system")
    if (
        not _CHECKSUM.fullmatch(manifest.checksum_sha256)
        or snapshot_checksum(snapshot) != manifest.checksum_sha256
    ):
        raise TerritoryReferenceError("Reference payload checksum mismatch")
    if len({item.id for item in snapshot.territories}) != len(snapshot.territories):
        raise TerritoryReferenceError("Duplicate canonical territory ID")
    identifiers = {item.id: item for item in snapshot.territories}
    for item in snapshot.territories:
        if not item.name.strip() or item.reference_id != manifest.reference_id:
            raise TerritoryReferenceError("Territory lacks name or matching reference ID")
        if item.valid_on != manifest.snapshot_date:
            raise TerritoryReferenceError("Territory validity date differs from selected snapshot")
        if item.kind is TerritoryKind.COUNTRY:
            if item.id != item.country.value:
                raise TerritoryReferenceError("Country must use its ISO code as canonical ID")
        elif item.kind is TerritoryKind.REGION:
            if not _REGION_ID.fullmatch(item.id) or not item.id.startswith(
                f"{item.country.value.lower()}:region:"
            ):
                raise TerritoryReferenceError("Region ID must match country prefix")
            if item.parent_id != item.country.value:
                raise TerritoryReferenceError("Invalid region parent")
        elif item.kind is TerritoryKind.DISTRICT:
            if not _DISTRICT_ID.fullmatch(item.id) or not item.id.startswith(
                f"{item.country.value.lower()}:district:"
            ):
                raise TerritoryReferenceError("District ID must match country prefix")
            parent = identifiers.get(item.parent_id or "")
            if (
                parent is None
                or parent.kind is not TerritoryKind.REGION
                or parent.country is not item.country
            ):
                raise TerritoryReferenceError(
                    "District parent must be a region in the same country"
                )
    _require_catalogs(snapshot, inventory)
    geometries = {entry.territory_id: entry for entry in snapshot.geometries}
    if len(geometries) != len(snapshot.geometries):
        raise TerritoryReferenceError("Duplicate territory geometry")
    for entry in snapshot.geometries:
        territory = identifiers.get(entry.territory_id)
        if territory is None or entry.reference_id != manifest.reference_id:
            raise TerritoryReferenceError("Orphaned or mismatched geometry")
        if (
            territory.geometry_status is not GeometryStatus.AVAILABLE
            or entry.coordinate_system != WGS84_CRS
        ):
            raise TerritoryReferenceError("Geometry and status/SRID disagree")
        validate_geometry(entry.geometry)
    for item in snapshot.territories:
        if (item.id in geometries) != (item.geometry_status is GeometryStatus.AVAILABLE):
            raise TerritoryReferenceError("Geometry availability and territory status disagree")
