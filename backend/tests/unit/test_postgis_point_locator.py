"""Read-only point lookup must reject ambiguous or malformed spatial matches."""

import asyncio
from collections.abc import Sequence
from typing import LiteralString

import pytest

from melliatlas.persistence.point_locator import PostgisPointLocator
from melliatlas.territories.api import CountryCode, ReferenceUnavailableError


def test_unique_region_and_optional_district_use_parameterized_srid() -> None:
    queries: list[tuple[str, tuple[object, ...]]] = []

    def read(sql: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        queries.append((sql, tuple(params)))
        if "kind = 'region'" in sql:
            return (("ru:region:smo",),)
        return ()

    locator = PostgisPointLocator(read)
    result = asyncio.run(
        locator.locate_point(country=CountryCode.RU, longitude=32.0, latitude=54.0)
    )
    assert result is not None
    assert result.region_id == "ru:region:smo"
    assert result.district_id is None
    assert queries[0][1] == ("RU", 32.0, 54.0, 4326)
    assert queries[1][1] == ("ru:region:smo", 32.0, 54.0, 4326)


@pytest.mark.parametrize(
    "invalid",
    [
        (("ru:region:smo",), ("ru:region:other",)),
        (("ru:region:smo", "unexpected"),),
        ((123,),),
    ],
)
def test_ambiguous_or_malformed_region_is_not_silently_chosen(
    invalid: tuple[tuple[object, ...], ...],
) -> None:
    def read(sql: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        return invalid

    with pytest.raises(ReferenceUnavailableError, match="region reference"):
        asyncio.run(
            PostgisPointLocator(read).locate_point(
                country=CountryCode.RU, longitude=32.0, latitude=54.0
            )
        )


def test_ambiguous_district_fails_without_guessing() -> None:
    def read(sql: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        if "kind = 'region'" in sql:
            return (("ru:region:smo",),)
        return (("ru:district:a",), ("ru:district:b",))

    with pytest.raises(ReferenceUnavailableError, match="district reference"):
        asyncio.run(
            PostgisPointLocator(read).locate_point(
                country=CountryCode.RU, longitude=32.0, latitude=54.0
            )
        )


def test_invalid_coordinates_fail_before_sql() -> None:
    def read(sql: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        raise AssertionError("Unexpected database read")

    with pytest.raises(ValueError, match="WGS84"):
        asyncio.run(
            PostgisPointLocator(read).locate_point(
                country=CountryCode.RU, longitude=200.0, latitude=54.0
            )
        )
