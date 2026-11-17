"""Bounded local-distance screening for reported field boundaries.

These approximations are not valid near the poles or for wide extents and
must never be used to establish pesticide exposure or site safety.
"""

from math import cos, radians
from typing import Final

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

EARTH_RADIUS_KM: Final = 6371.0088
MAX_LOCAL_ABSOLUTE_LATITUDE: Final = 80.0
MAX_LOCAL_BOUNDARY_EXTENT_DEGREES: Final = 5.0


def approximate_distance_to_boundary_km(
    polygon: BaseGeometry, longitude: float, latitude: float
) -> float | None:
    """Compute a local equirectangular distance or decline unsafe approximations."""
    if (
        abs(latitude) > MAX_LOCAL_ABSOLUTE_LATITUDE
        or polygon.bounds[2] - polygon.bounds[0] > MAX_LOCAL_BOUNDARY_EXTENT_DEGREES
        or polygon.bounds[3] - polygon.bounds[1] > MAX_LOCAL_BOUNDARY_EXTENT_DEGREES
    ):
        return None
    latitude_scale = cos(radians(latitude))

    def to_local(lon: float, lat: float, z: float | None = None) -> tuple[float, float]:
        return (
            EARTH_RADIUS_KM * radians(lon - longitude) * latitude_scale,
            EARTH_RADIUS_KM * radians(lat - latitude),
        )

    return float(transform(to_local, polygon).distance(Point(0, 0)))
