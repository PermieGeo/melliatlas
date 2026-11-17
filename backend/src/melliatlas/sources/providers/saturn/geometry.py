"""Validate only reported WGS84 field geometries from legacy Saturn fixtures."""

from typing import TypeGuard

from shapely.errors import GEOSException
from shapely.geometry import shape

from melliatlas.geography import MIN_LINEAR_RING_POSITIONS, POSITION_DIMENSIONS, is_wgs84_position
from melliatlas.territories.api import GeometryWgs84, MultiPolygonWgs84, PolygonWgs84, Position

MAX_FIELD_RINGS = 150
MAX_FIELD_POLYGONS = 100
MAX_FIELD_POSITIONS = 5000


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _position(value: object) -> Position | None:
    if not _is_list(value) or len(value) != POSITION_DIMENSIONS:
        return None
    longitude, latitude = value
    if (
        not isinstance(longitude, (float, int))
        or isinstance(longitude, bool)
        or not isinstance(latitude, (float, int))
        or isinstance(latitude, bool)
    ):
        return None
    lon, lat = float(longitude), float(latitude)
    if not is_wgs84_position(lon, lat):
        return None
    return (lon, lat)


def _rings(value: object) -> list[list[Position]] | None:
    if not _is_list(value) or not 1 <= len(value) <= MAX_FIELD_RINGS:
        return None
    parsed_rings: list[list[Position]] = []
    total_positions = 0
    for ring in value:
        if not _is_list(ring) or len(ring) < MIN_LINEAR_RING_POSITIONS:
            return None
        total_positions += len(ring)
        if total_positions > MAX_FIELD_POSITIONS:
            return None
        positions: list[Position] = []
        for item in ring:
            point = _position(item)
            if point is None:
                return None
            positions.append(point)
        if positions[0] != positions[-1]:
            return None
        parsed_rings.append(positions)
    return parsed_rings


def parse_field_geometry(raw: dict[str, object] | None) -> GeometryWgs84 | None:
    if raw is None:
        return None
    geometry: GeometryWgs84
    kind = raw.get("type")
    if kind == "Polygon":
        rings = _rings(raw.get("coordinates"))
        if rings is None:
            return None
        geometry = PolygonWgs84(type="Polygon", coordinates=rings)
    elif kind == "MultiPolygon":
        value_polygons = raw.get("coordinates")
        if not _is_list(value_polygons) or not 1 <= len(value_polygons) <= MAX_FIELD_POLYGONS:
            return None
        polygons: list[list[list[Position]]] = []
        total_positions = 0
        for value_polygon in value_polygons:
            rings = _rings(value_polygon)
            if rings is None:
                return None
            total_positions += sum(len(ring) for ring in rings)
            if total_positions > MAX_FIELD_POSITIONS:
                return None
            polygons.append(rings)
        geometry = MultiPolygonWgs84(type="MultiPolygon", coordinates=polygons)
    else:
        return None
    try:
        polygon_shape = shape(dict(geometry))
        if polygon_shape.is_empty or not polygon_shape.is_valid or polygon_shape.area <= 0:
            return None
        return geometry
    except (GEOSException, ValueError, TypeError, OverflowError):
        return None
