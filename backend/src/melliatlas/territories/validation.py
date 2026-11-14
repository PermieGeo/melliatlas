"""Structural reference and WGS84 validation without provider-specific logic."""

import hashlib
import json
import re
from datetime import timezone
from math import isfinite

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


def _segments_intersect(a: Position, b: Position, c: Position, d: Position) -> bool:
    def orientation(p: Position, q: Position, r: Position) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p: Position, q: Position, r: Position) -> bool:
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[1] <= max(
            p[1], r[1]
        )

    o1, o2 = orientation(a, b, c), orientation(a, b, d)
    o3, o4 = orientation(c, d, a), orientation(c, d, b)
    if ((o1 > 0 and o2 < 0) or (o1 < 0 and o2 > 0)) and (
        (o3 > 0 and o4 < 0) or (o3 < 0 and o4 > 0)
    ):
        return True
    return (
        (o1 == 0 and on_segment(a, c, b))
        or (o2 == 0 and on_segment(a, d, b))
        or (o3 == 0 and on_segment(c, a, d))
        or (o4 == 0 and on_segment(c, b, d))
    )


def _validate_ring(ring: list[Position]) -> None:
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise TerritoryReferenceError("Polygon rings must contain four positions and be closed")
    for longitude, latitude in ring:
        if not (isfinite(longitude) and isfinite(latitude)):
            raise TerritoryReferenceError("Non-finite GeoJSON coordinate")
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise TerritoryReferenceError("GeoJSON coordinates must use WGS84 longitude/latitude")
    if any(a == b for a, b in zip(ring, ring[1:])):
        raise TerritoryReferenceError("Polygon rings contain repeated adjacent coordinates")
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:]))
    if abs(area) < 1e-12:
        raise TerritoryReferenceError("Polygon rings cannot have zero signed area")
    segments = list(zip(ring, ring[1:]))
    for index, (a, b) in enumerate(segments):
        for next_index in range(index + 1, len(segments)):
            if next_index in {index + 1, len(segments) - 1} and index == 0:
                continue
            if next_index == index + 1:
                continue
            c, d = segments[next_index]
            if _segments_intersect(a, b, c, d):
                raise TerritoryReferenceError("Self-intersecting polygon ring")


def validate_geometry(geometry: GeometryWgs84) -> None:
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
    # Full hole topology and inter-polygon validity require a spatial database check.


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
    if manifest.coordinate_system != "EPSG:4326":
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
            if not _REGION_ID.fullmatch(item.id) or item.parent_id != item.country.value:
                raise TerritoryReferenceError("Invalid region ID or parent")
        elif item.kind is TerritoryKind.DISTRICT:
            if not _DISTRICT_ID.fullmatch(item.id):
                raise TerritoryReferenceError("Invalid district ID")
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
            or entry.coordinate_system != "EPSG:4326"
        ):
            raise TerritoryReferenceError("Geometry and status/SRID disagree")
        validate_geometry(entry.geometry)
    for item in snapshot.territories:
        if (item.id in geometries) != (item.geometry_status is GeometryStatus.AVAILABLE):
            raise TerritoryReferenceError("Geometry availability and territory status disagree")
