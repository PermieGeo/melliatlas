"""PostGIS-backed administrative geometry for independently owned RU/BY territories.

The geometry dataset is loaded explicitly, never fetched from external providers at startup.
District parents come from reviewed spatial joins, not Saturn district identifiers.
"""

import asyncio
import json
from dataclasses import replace
from datetime import date
from typing import Final, LiteralString, TypeGuard

from melliatlas.geography import (
    BOUNDARY_SIMPLIFICATION_DEGREES,
    GEOJSON_COORDINATE_PRECISION,
    MIN_LINEAR_RING_POSITIONS,
    POSITION_DIMENSIONS,
    WGS84_CRS,
    is_wgs84_position,
)
from melliatlas.persistence.area_districts import PostgisAreaDistrictLookup
from melliatlas.persistence.point_locator import PostgisPointLocator
from melliatlas.persistence.regions import PostgresRegionCatalog
from melliatlas.territories.api import (
    AreaDistrictResult,
    CountryCode,
    GeometryStatus,
    GeometryWgs84,
    MultiPolygonWgs84,
    PolygonWgs84,
    ReferenceUnavailableError,
    Territory,
    TerritoryAtPoint,
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
    if not _is_list(value) or len(value) != POSITION_DIMENSIONS:
        raise ValueError("Invalid coordinate")
    longitude, latitude = value
    if isinstance(longitude, bool) or not isinstance(longitude, (int, float)):
        raise ValueError("Invalid coordinate value")
    if isinstance(latitude, bool) or not isinstance(latitude, (int, float)):
        raise ValueError("Invalid coordinate value")
    x, y = float(longitude), float(latitude)
    if not is_wgs84_position(x, y):
        raise ValueError("Invalid WGS84 coordinate")
    return x, y


def _ring(value: object) -> list[tuple[float, float]]:
    if not _is_list(value):
        raise ValueError("Invalid polygon ring")
    coords = [_position(point) for point in value]
    if len(coords) < MIN_LINEAR_RING_POSITIONS or coords[0] != coords[-1]:
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
        SELECT territory_id, country_code, name, region_id, reference_id, valid_on, name_ru
        FROM melliatlas_admin_geometry
        WHERE region_id = %s AND kind = 'district'
        ORDER BY name, territory_id
    """
    _DISTRICT: Final[LiteralString] = """
        SELECT territory_id, country_code, name, region_id, reference_id, valid_on, name_ru
        FROM melliatlas_admin_geometry
        WHERE territory_id = %s AND kind = 'district'
    """
    _GEOMETRY: Final[LiteralString] = """
        SELECT reference_id, ST_AsGeoJSON(ST_SimplifyPreserveTopology(boundary, %s), %s)
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
        # The last column is a nullable translated label; identity columns stay source-owned.
        match row:
            case (
                str(identifier),
                str(country),
                str(name),
                str(region),
                str(reference),
                date() as valid_on,
                translated,
            ):
                pass
            case _:
                raise ReferenceUnavailableError("Invalid district database row")
        if translated is not None and (not isinstance(translated, str) or not translated.strip()):
            raise ReferenceUnavailableError("Invalid district display name")
        localized_name: str | None = translated if isinstance(translated, str) else None
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
            valid_on=valid_on,
            geometry_status=GeometryStatus.AVAILABLE,
            name_ru=localized_name,
        )

    async def locate_point(
        self, *, country: CountryCode, longitude: float, latitude: float
    ) -> TerritoryAtPoint | None:
        return await PostgisPointLocator(self._read).locate_point(
            country=country, longitude=longitude, latitude=latitude
        )

    async def intersect_districts(
        self,
        *,
        country: CountryCode,
        region_id: str,
        longitude: float,
        latitude: float,
        width_km: float,
        height_km: float,
    ) -> AreaDistrictResult:
        region = await self.get(region_id)
        if region is None or region.country != country or region.kind is not TerritoryKind.REGION:
            raise TerritoryNotFound("Unknown region for analysis area")
        if region.geometry_status is not GeometryStatus.AVAILABLE:
            raise ReferenceUnavailableError("Region geometry has not been imported")
        return await PostgisAreaDistrictLookup(self._read).intersect_districts(
            country=country,
            region_id=region_id,
            longitude=longitude,
            latitude=latitude,
            width_km=width_km,
            height_km=height_km,
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
        rows = await asyncio.to_thread(
            self._read,
            self._GEOMETRY,
            (BOUNDARY_SIMPLIFICATION_DEGREES, GEOJSON_COORDINATE_PRECISION, territory_id),
        )
        if not rows:
            return None
        # The geometry query must return exactly one reference ID and GeoJSON document.
        match rows:
            case ((str(reference_id), str(geometry_json)),):
                pass
            case _:
                raise ReferenceUnavailableError("Invalid geometry database row")
        try:
            geo = _decode_geometry(geometry_json)
        except (ValueError, TypeError) as exc:
            raise ReferenceUnavailableError("Invalid stored boundary geometry") from exc
        # PostGIS enforces SRID and topology when the boundary is inserted.
        return TerritoryGeometry(
            territory_id=territory_id,
            geometry=geo,
            reference_id=reference_id,
            coordinate_system=WGS84_CRS,
        )
