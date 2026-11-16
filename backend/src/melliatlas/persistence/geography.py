"""PostGIS-backed administrative geometry for independently owned RU/BY territories.

The geometry dataset is loaded explicitly, never fetched from external providers at startup.
District parents come from reviewed spatial joins, not Saturn district identifiers.
"""

import asyncio
import json
from dataclasses import replace
from datetime import date
from math import isfinite
from typing import Final, LiteralString, TypeGuard

from melliatlas.persistence.regions import PostgresRegionCatalog
from melliatlas.territories.api import (
    CountryCode,
    GeometryStatus,
    GeometryWgs84,
    MultiPolygonWgs84,
    PolygonWgs84,
    ReferenceUnavailableError,
    Territory,
    TerritoryGeometry,
    TerritoryKind,
    TerritoryNotFound,
)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_dict(value: object) -> TypeGuard[dict[str, object]]:
    # json.loads guarantees string keys for JSON objects.
    return isinstance(value, dict)


def _position(value: object) -> tuple[float, float]:
    if not _is_list(value) or len(value) != 2:
        raise ValueError("Invalid coordinate")
    longitude, latitude = value
    if isinstance(longitude, bool) or not isinstance(longitude, (int, float)):
        raise ValueError("Invalid coordinate value")
    if isinstance(latitude, bool) or not isinstance(latitude, (int, float)):
        raise ValueError("Invalid coordinate value")
    x, y = float(longitude), float(latitude)
    if not isfinite(x) or not isfinite(y) or abs(x) > 180 or abs(y) > 90:
        raise ValueError("Invalid WGS84 coordinate")
    return x, y


def _ring(value: object) -> list[tuple[float, float]]:
    if not _is_list(value):
        raise ValueError("Invalid polygon ring")
    coords = [_position(point) for point in value]
    if len(coords) < 4 or coords[0] != coords[-1]:
        raise ValueError("Unclosed polygon ring")
    return coords


def _polygon(value: object) -> list[list[tuple[float, float]]]:
    if not _is_list(value) or not value:
        raise ValueError("Invalid polygon coordinates")
    return [_ring(ring) for ring in value]


def _decode_geometry(text: str) -> GeometryWgs84:
    raw: object = json.loads(text)
    if not _is_dict(raw):
        raise ValueError("Invalid geometry JSON")
    if raw.get("type") == "Polygon":
        result: PolygonWgs84 = {"type": "Polygon", "coordinates": _polygon(raw.get("coordinates"))}
        return result
    if raw.get("type") == "MultiPolygon":
        polys = raw.get("coordinates")
        if not _is_list(polys) or not polys:
            raise ValueError("Invalid multipolygon")
        multi: MultiPolygonWgs84 = {
            "type": "MultiPolygon",
            "coordinates": [_polygon(poly) for poly in polys],
        }
        return multi
    raise ValueError("Unsupported boundary type")


class PostgisTerritoryCatalog(PostgresRegionCatalog):
    """Combine the canonical region directory with separately imported geometry."""

    _COUNTRY_REGIONS: Final[LiteralString] = """
        SELECT r.id, r.country_code, r.name, COALESCE(g.reference_id, r.reference_id), r.valid_on,
               (g.territory_id IS NOT NULL)
        FROM melliatlas_region AS r
        LEFT JOIN melliatlas_admin_geometry AS g ON g.territory_id = r.id
        WHERE r.country_code = %s ORDER BY r.name, r.id
    """
    _SINGLE_REGION: Final[LiteralString] = """
        SELECT r.id, r.country_code, r.name, COALESCE(g.reference_id, r.reference_id), r.valid_on,
               (g.territory_id IS NOT NULL)
        FROM melliatlas_region AS r
        LEFT JOIN melliatlas_admin_geometry AS g ON g.territory_id = r.id
        WHERE r.id = %s
    """
    _DISTRICTS: Final[LiteralString] = """
        SELECT territory_id, country_code, name, region_id, reference_id, valid_on
        FROM melliatlas_admin_geometry
        WHERE region_id = %s AND kind = 'district'
        ORDER BY name, territory_id
    """
    _DISTRICT: Final[LiteralString] = """
        SELECT territory_id, country_code, name, region_id, reference_id, valid_on
        FROM melliatlas_admin_geometry
        WHERE territory_id = %s AND kind = 'district'
    """
    _GEOMETRY: Final[LiteralString] = """
        SELECT reference_id, ST_AsGeoJSON(ST_SimplifyPreserveTopology(boundary, 0.002), 5)
        FROM melliatlas_admin_geometry WHERE territory_id = %s
    """

    @staticmethod
    def _region_with_geometry(row: tuple[object, ...]) -> Territory:
        if len(row) != 6 or not isinstance(row[5], bool):
            raise ReferenceUnavailableError("Invalid region boundary status")
        region = PostgresRegionCatalog._region(row[:5])
        return replace(
            region, geometry_status=GeometryStatus.AVAILABLE if row[5] else GeometryStatus.MISSING
        )

    @staticmethod
    def _district(row: tuple[object, ...]) -> Territory:
        if (
            len(row) != 6
            or any(not isinstance(value, str) for value in row[:5])
            or not isinstance(row[5], date)
        ):
            raise ReferenceUnavailableError("Invalid district database row")
        identifier, country, name, region, reference = row[:5]
        if (
            not isinstance(identifier, str)
            or not isinstance(country, str)
            or not isinstance(name, str)
            or not isinstance(region, str)
            or not isinstance(reference, str)
        ):
            raise ReferenceUnavailableError("Invalid district fields")
        try:
            country_code = CountryCode(country)
        except ValueError as exc:
            raise ReferenceUnavailableError("Invalid district country") from exc
        if not identifier.startswith(f"{country.lower()}:district:") or not region.startswith(
            f"{country.lower()}:region:"
        ):
            raise ReferenceUnavailableError("Invalid district hierarchy")
        return Territory(
            id=identifier,
            country=country_code,
            kind=TerritoryKind.DISTRICT,
            name=name,
            parent_id=region,
            reference_id=reference,
            valid_on=row[5],
            geometry_status=GeometryStatus.AVAILABLE,
        )

    async def list_regions(self, country: CountryCode) -> tuple[Territory, ...]:
        rows = await asyncio.to_thread(self._read, self._COUNTRY_REGIONS, (country.value,))
        if not rows:
            raise ReferenceUnavailableError("Country region directory has not been seeded")
        return tuple(self._region_with_geometry(row) for row in rows)

    async def get(self, territory_id: str) -> Territory | None:
        if ":district:" in territory_id:
            rows = await asyncio.to_thread(self._read, self._DISTRICT, (territory_id,))
            return self._district(rows[0]) if len(rows) == 1 else None
        rows = await asyncio.to_thread(self._read, self._SINGLE_REGION, (territory_id,))
        return self._region_with_geometry(rows[0]) if len(rows) == 1 else None

    async def list_districts(self, region_id: str) -> tuple[Territory, ...]:
        region = await self.get(region_id)
        if region is None or region.kind is not TerritoryKind.REGION:
            raise TerritoryNotFound(region_id)
        rows = await asyncio.to_thread(self._read, self._DISTRICTS, (region_id,))
        return tuple(self._district(row) for row in rows)

    async def get_geometry(self, territory_id: str) -> TerritoryGeometry | None:
        region = await self.get(territory_id)
        if region is None:
            raise TerritoryNotFound(territory_id)
        rows = await asyncio.to_thread(self._read, self._GEOMETRY, (territory_id,))
        if not rows:
            return None
        if (
            len(rows) != 1
            or len(rows[0]) != 2
            or not isinstance(rows[0][0], str)
            or not isinstance(rows[0][1], str)
        ):
            raise ReferenceUnavailableError("Invalid geometry database row")
        try:
            geo = _decode_geometry(rows[0][1])
        except (ValueError, TypeError) as exc:
            raise ReferenceUnavailableError("Invalid stored boundary geometry") from exc
        # PostGIS enforces SRID and topology when the boundary is inserted.
        return TerritoryGeometry(
            territory_id=territory_id,
            geometry=geo,
            reference_id=rows[0][0],
            coordinate_system="EPSG:4326",
        )
