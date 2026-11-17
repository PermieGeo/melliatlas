"""Area-based ADM2 lookup preserves unknown coverage and all genuine overlaps."""

import asyncio
from collections.abc import Sequence
from typing import LiteralString

import pytest

from melliatlas.persistence.area_districts import PostgisAreaDistrictLookup
from melliatlas.territories.api import (
    AreaDistrictCoverage,
    CountryCode,
    ReferenceUnavailableError,
    TerritoryNotFound,
)


def test_all_known_districts_including_neighboring_region_are_returned() -> None:
    queries: list[tuple[str, tuple[object, ...]]] = []

    def read(query: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        queries.append((query, tuple(params)))
        if "kind = 'region'" in query:
            return (("ru:region:smo",),)
        return (
            ("ru:district:a", "ru:region:smo", "A", "ref1"),
            ("ru:district:b", "ru:region:neighbor", "B", "ref2"),
            ("ru:district:c", "ru:region:smo", "C", "ref1"),
        )

    result = asyncio.run(
        PostgisAreaDistrictLookup(read).intersect_districts(
            country=CountryCode.RU,
            region_id="ru:region:smo",
            longitude=32,
            latitude=54,
            width_km=15,
            height_km=15,
        )
    )
    assert [d.id for d in result.districts] == ["ru:district:a", "ru:district:b", "ru:district:c"]
    assert result.coverage == AreaDistrictCoverage.UNVERIFIED
    assert "ST_CollectionExtract(ST_Intersection" in queries[-1][0]
    assert "::geography" in queries[-1][0]
    assert "LIMIT" not in queries[-1][0]
    assert queries[-1][1][-1] == "RU"


def test_no_known_districts_does_not_prove_complete_coverage() -> None:
    def read(query: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        if "kind = 'region'" in query:
            return (("by:region:vi",),)
        return ()

    result = asyncio.run(
        PostgisAreaDistrictLookup(read).intersect_districts(
            country=CountryCode.BY,
            region_id="by:region:vi",
            longitude=27.5,
            latitude=55.5,
            width_km=15,
            height_km=15,
        )
    )
    assert result.coverage == AreaDistrictCoverage.MISSING
    assert result.districts == ()


def test_invalid_or_duplicate_district_row_fails_closed() -> None:
    def read(query: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        if "kind = 'region'" in query:
            return (("ru:region:smo",),)
        return (("ru:district:a", "ru:region:smo", "A", "ref"),) * 2

    with pytest.raises(ReferenceUnavailableError):
        asyncio.run(
            PostgisAreaDistrictLookup(read).intersect_districts(
                country=CountryCode.RU,
                region_id="ru:region:smo",
                longitude=32,
                latitude=54,
                width_km=15,
                height_km=15,
            )
        )


def test_point_outside_requested_region_prevents_bbox_query() -> None:
    queries: list[str] = []

    def read(query: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        queries.append(query)
        if "kind = 'region'" in query:
            return (("ru:region:other",),)
        return ()

    with pytest.raises(TerritoryNotFound):
        asyncio.run(
            PostgisAreaDistrictLookup(read).intersect_districts(
                country=CountryCode.RU,
                region_id="ru:region:smo",
                longitude=32,
                latitude=54,
                width_km=15,
                height_km=15,
            )
        )
    assert len(queries) == 1


def test_invalid_region_is_rejected_before_database_read() -> None:
    def read(query: LiteralString, params: Sequence[object]) -> tuple[tuple[object, ...], ...]:
        raise AssertionError("Unexpected read")

    with pytest.raises(ValueError):
        asyncio.run(
            PostgisAreaDistrictLookup(read).intersect_districts(
                country=CountryCode.BY,
                region_id="ru:region:smo",
                longitude=32,
                latitude=54,
                width_km=15,
                height_km=15,
            )
        )
