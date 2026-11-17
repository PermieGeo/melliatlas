"""Metric analysis rectangles stay bounded and split safely at the dateline."""

import pytest

from melliatlas.geography import make_analysis_bounds


def test_default_centered_box_is_approximately_15km_in_each_direction() -> None:
    bounds = make_analysis_bounds(longitude=32.0, latitude=54.0, width_km=15, height_km=15)
    assert bounds.nominal_area_km2 == 225
    assert len(bounds.longitude_ranges) == 1
    west, east = bounds.longitude_ranges[0]
    assert (west + east) / 2 == pytest.approx(32)
    assert (bounds.north + bounds.south) / 2 == pytest.approx(54)
    assert (bounds.north - bounds.south) * 111.3 == pytest.approx(15, rel=0.02)


def test_longitude_span_changes_with_latitude() -> None:
    equator = make_analysis_bounds(longitude=30, latitude=0, width_km=20, height_km=20)
    north = make_analysis_bounds(longitude=30, latitude=65, width_km=20, height_km=20)
    width_equator = equator.longitude_ranges[0][1] - equator.longitude_ranges[0][0]
    width_north = north.longitude_ranges[0][1] - north.longitude_ranges[0][0]
    assert width_north > width_equator * 2


@pytest.mark.parametrize("lon", [179.99, -179.99])
def test_antimeridian_box_is_split_into_two_nonwrapping_intervals(lon: float) -> None:
    bounds = make_analysis_bounds(longitude=lon, latitude=55, width_km=30, height_km=15)
    assert len(bounds.longitude_ranges) == 2
    assert all(-180 <= west < east <= 180 for west, east in bounds.longitude_ranges)
    assert bounds.nominal_area_km2 == 450


@pytest.mark.parametrize(
    "center, width, height",
    [
        ((32.0, 54.0), 0, 15),
        ((32.0, 54.0), 31, 15),
        ((32.0, 54.0), 15, float("nan")),
        ((32.0, 54.0), 15, float("inf")),
        ((32.0, 54.0), True, 15),
        ((32.0, 54.0), 1e-200, 15),
        ((181.0, 54.0), 15, 15),
        ((32.0, 90.0), 15, 15),
    ],
)
def test_invalid_geometry_never_produces_an_area(
    center: tuple[float, float], width: float, height: float
) -> None:
    with pytest.raises(ValueError):
        make_analysis_bounds(
            longitude=center[0], latitude=center[1], width_km=width, height_km=height
        )


def test_pole_crossing_is_explicitly_rejected() -> None:
    with pytest.raises(ValueError, match="pole"):
        make_analysis_bounds(longitude=0, latitude=89.99, width_km=30, height_km=30)
