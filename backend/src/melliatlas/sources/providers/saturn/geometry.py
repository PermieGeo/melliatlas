"""Validate only reported WGS84 field geometries from legacy Saturn fixtures."""

from math import isfinite
from typing import TypeGuard

from shapely.errors import GEOSException
from shapely.geometry import shape

from melliatlas.territories.api import GeometryWgs84, MultiPolygonWgs84, PolygonWgs84, Position


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _position(value: object) -> Position | None:
    if not _is_list(value) or len(value) != 2:
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
    if not isfinite(lon) or not isfinite(lat) or not -180 <= lon <= 180 or not -90 <= lat <= 90:
        return None
    return (lon, lat)


def _rings(value: object) -> list[list[Position]] | None:
    if not _is_list(value) or not 1 <= len(value) <= 150:
        return None
    parsed_rings: list[list[Position]] = []
    total_positions = 0
    for ring in value:
        if not _is_list(ring) or len(ring) < 4:
            return None
        total_positions += len(ring)
        if total_positions > 5000:
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
        if not _is_list(value_polygons) or not 1 <= len(value_polygons) <= 100:
            return None
        polygons: list[list[list[Position]]] = []
        total_positions = 0
        for value_polygon in value_polygons:
            rings = _rings(value_polygon)
            if rings is None:
                return None
            total_positions += sum(len(ring) for ring in rings)
            if total_positions > 5000:
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
