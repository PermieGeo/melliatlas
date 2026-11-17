"""Shared geo primitives and local screening remain conservative at boundaries."""

import math

import pytest
from shapely.geometry import Polygon

from melliatlas.geography import (
    LATITUDE_MAX,
    LONGITUDE_MAX,
    POSITION_DIMENSIONS,
    WGS84_CRS,
    approximate_distance_to_boundary_km,
    is_wgs84_position,
)


def test_wgs84_invariants_are_shared_and_reject_nonfinite() -> None:
    assert POSITION_DIMENSIONS == 2
    assert WGS84_CRS == "EPSG:4326"
    assert is_wgs84_position(LONGITUDE_MAX, LATITUDE_MAX)
    assert is_wgs84_position(-LONGITUDE_MAX, -LATITUDE_MAX)
    for lon, lat in (
        (LONGITUDE_MAX + 0.001, 0),
        (0, LATITUDE_MAX + 0.001),
        (math.nan, 1),
        (2, math.inf),
        (True, 40),
        (30, False),
    ):
        assert not is_wgs84_position(lon, lat)


def test_local_screening_rejects_large_and_polar_geometry() -> None:
    near = Polygon(((30, 50), (30.01, 50), (30.01, 50.01), (30, 50.01)))
    far = Polygon(((-20, 0), (-10, 0), (-10, 1), (-20, 1)))
    assert approximate_distance_to_boundary_km(near, 31.0, 50.0) == pytest.approx(70, abs=5)
    assert approximate_distance_to_boundary_km(far, 0, 0) is None
    assert approximate_distance_to_boundary_km(near, 31, 85) is None
