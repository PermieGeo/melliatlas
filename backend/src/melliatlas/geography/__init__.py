"""Public geographic primitives; no persistence or provider implementations."""

from .coordinates import (
    BOUNDARY_SIMPLIFICATION_DEGREES,
    GEOJSON_COORDINATE_PRECISION,
    LATITUDE_MAX,
    LATITUDE_MIN,
    LONGITUDE_MAX,
    LONGITUDE_MIN,
    MIN_LINEAR_RING_POSITIONS,
    POSITION_DIMENSIONS,
    WGS84_CRS,
    WGS84_SRID,
    Wgs84Crs,
    is_wgs84_position,
)
from .distance import approximate_distance_to_boundary_km

__all__ = [
    "BOUNDARY_SIMPLIFICATION_DEGREES",
    "GEOJSON_COORDINATE_PRECISION",
    "Wgs84Crs",
    "LATITUDE_MAX",
    "LATITUDE_MIN",
    "LONGITUDE_MAX",
    "LONGITUDE_MIN",
    "MIN_LINEAR_RING_POSITIONS",
    "POSITION_DIMENSIONS",
    "WGS84_CRS",
    "WGS84_SRID",
    "is_wgs84_position",
    "approximate_distance_to_boundary_km",
]
