"""Local WGS84 metric approximation for bounded, axis-aligned analysis rectangles."""

from dataclasses import dataclass
from math import cos, isfinite, pi, radians, sin, sqrt
from typing import Final

from .coordinates import is_wgs84_position

DEFAULT_AREA_DIMENSION_KM: Final = 15.0
MAX_AREA_DIMENSION_KM: Final = 30.0
_WGS84_A_METERS: Final = 6_378_137.0
_WGS84_ECC_SQUARED: Final = 6.6943799901413165e-3


@dataclass(frozen=True)
class Wgs84AnalysisBounds:
    south: float
    north: float
    # One interval normally; two intervals when crossing the antimeridian.
    longitude_ranges: tuple[tuple[float, float], ...]
    width_km: float
    height_km: float

    @property
    def nominal_area_km2(self) -> float:
        return self.width_km * self.height_km


def _is_valid_dimension(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and isfinite(value)
        and 0 < value <= MAX_AREA_DIMENSION_KM
    )


def make_analysis_bounds(
    *, longitude: float, latitude: float, width_km: float, height_km: float
) -> Wgs84AnalysisBounds:
    """Approximate a <=30 km tangent-plane rectangle with WGS84 curvature radii.

    Coordinate sides follow meridians and parallels rather than exact geodesics.
    The nominal area is width times height, not a surveyed or equal-area polygon.
    """
    if not is_wgs84_position(longitude, latitude):
        raise ValueError("Invalid WGS84 center")
    if not all(_is_valid_dimension(value) for value in (width_km, height_km)):
        raise ValueError("Analysis rectangle dimensions must be >0 and <=30 km")

    phi = radians(latitude)
    sin_phi = sin(phi)
    scale = 1 - _WGS84_ECC_SQUARED * sin_phi * sin_phi
    meridional_radius = _WGS84_A_METERS * (1 - _WGS84_ECC_SQUARED) / (scale**1.5)
    prime_vertical_radius = _WGS84_A_METERS / sqrt(scale)
    km_per_degree_lat = pi * meridional_radius / 180_000
    km_per_degree_lon = pi * prime_vertical_radius * cos(phi) / 180_000
    if km_per_degree_lon <= 0:
        raise ValueError("Cannot define an east-west rectangle at a geographic pole")
    dy = height_km / (2 * km_per_degree_lat)
    dx = width_km / (2 * km_per_degree_lon)
    if latitude - dy <= -90 or latitude + dy >= 90 or dx >= 180:
        raise ValueError("Analysis rectangle reaches a geographic pole")
    if longitude - dx == longitude + dx or latitude - dy == latitude + dy:
        raise ValueError("Analysis rectangle is below WGS84 coordinate precision")

    west = longitude - dx
    east = longitude + dx
    if east > 180:
        longitude_ranges = ((west, 180.0), (-180.0, east - 360))
    elif west < -180:
        longitude_ranges = ((west + 360, 180.0), (-180.0, east))
    else:
        longitude_ranges = ((west, east),)
    return Wgs84AnalysisBounds(
        south=latitude - dy,
        north=latitude + dy,
        longitude_ranges=longitude_ranges,
        width_km=float(width_km),
        height_km=float(height_km),
    )
