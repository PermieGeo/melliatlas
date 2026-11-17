"""Shared, provider-neutral WGS84 and GeoJSON coordinate invariants."""

from math import isfinite
from typing import Final, Literal, TypeAlias

Wgs84Crs: TypeAlias = Literal["EPSG:4326"]
WGS84_CRS: Final[Wgs84Crs] = "EPSG:4326"
WGS84_SRID: Final = 4326
LONGITUDE_MIN: Final = -180.0
LONGITUDE_MAX: Final = 180.0
LATITUDE_MIN: Final = -90.0
LATITUDE_MAX: Final = 90.0
POSITION_DIMENSIONS: Final = 2
MIN_LINEAR_RING_POSITIONS: Final = 4
BOUNDARY_SIMPLIFICATION_DEGREES: Final = 0.002
GEOJSON_COORDINATE_PRECISION: Final = 5


def is_wgs84_position(longitude: float, latitude: float) -> bool:
    """Reject non-finite and out-of-range longitude/latitude in that order."""
    return (
        not isinstance(longitude, bool)
        and not isinstance(latitude, bool)
        and isfinite(longitude)
        and isfinite(latitude)
        and LONGITUDE_MIN <= longitude <= LONGITUDE_MAX
        and LATITUDE_MIN <= latitude <= LATITUDE_MAX
    )
