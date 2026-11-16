"""Ensure public Saturn reads use reviewed district IDs and bounded date filters."""

import asyncio
import json
from datetime import date

import httpx
import pytest
from fastapi import FastAPI

from melliatlas.api.app import AppSettings, create_app
from melliatlas.sources.providers.saturn.live import SaturnPublicTreatmentReader
from melliatlas.territories.api import CountryCode, ReferenceUnavailableError


class RegionLookup:
    async def find_code(
        self, *, source_id: str, country: CountryCode, region_id: str
    ) -> int | None:
        if source_id == "saturn" and country is CountryCode.RU and region_id == "ru:region:smo":
            return 55
        return None


class DistrictLookup:
    def __init__(self, code: int | None, unavailable: bool = False) -> None:
        self.code = code
        self.unavailable = unavailable
        self.calls = 0

    async def find_district_code(
        self, *, source_id: str, country: CountryCode, region_id: str, district_id: str
    ) -> int | None:
        self.calls += 1
        if self.unavailable:
            raise ReferenceUnavailableError("Database unavailable")
        if (source_id, country, region_id, district_id) != (
            "saturn",
            CountryCode.RU,
            "ru:region:smo",
            "ru:district:verified",
        ):
            return None
        return self.code


def _upstream_page() -> bytes:
    return json.dumps(
        {
            "content": [],
            "number": 0,
            "size": 10,
            "numberOfElements": 0,
            "totalElements": 0,
            "totalPages": 0,
            "last": True,
        }
    ).encode()


async def _read(app: FastAPI, body: dict[str, object]) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.post("/api/v1/sources/saturn/treatments", json=body)


SCOPE: dict[str, object] = {
    "country": "RU",
    "region_id": "ru:region:smo",
    "district_id": "ru:district:verified",
    "page_number": 0,
    "date_start": "2026-11-16",
    "date_end": "2026-12-16",
}


def test_district_scope_and_dates_are_sent_to_upstream_and_echoed() -> None:
    bodies: list[dict[str, object]] = []

    def transport(body: bytes) -> bytes:
        bodies.append(json.loads(body))
        return _upstream_page()

    lookup = DistrictLookup(1472)
    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=SaturnPublicTreatmentReader(transport),
        source_region_lookup=RegionLookup(),
        source_district_lookup=lookup,
    )
    result = asyncio.run(_read(app, SCOPE))
    assert result.status_code == 200, result.text
    assert result.json()["district_id"] == "ru:district:verified"
    assert result.json()["date_start"] == "2026-11-16"
    assert result.json()["date_end"] == "2026-12-16"
    assert lookup.calls == 1
    assert bodies == [
        {
            "pageNumber": 0,
            "pageSize": 10,
            "sortColumn": "datePublishing",
            "sortDirection": "desc",
            "beekeperSearchFilter": {
                "subject": 55,
                "district": 1472,
                "startDateUpdateMap": "2026-11-16T00:00:00.000Z",
                "endDateUpdateMap": "2026-12-16T23:59:59.999Z",
            },
        }
    ]


@pytest.mark.parametrize(
    "lookup,expected",
    [
        (DistrictLookup(None), 409),
        (DistrictLookup(None, unavailable=True), 503),
    ],
)
def test_unmapped_or_unavailable_district_never_uses_region_fallback(
    lookup: DistrictLookup, expected: int
) -> None:
    calls: list[bytes] = []
    reader = SaturnPublicTreatmentReader(lambda body: calls.append(body) or _upstream_page())
    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=reader,
        source_region_lookup=RegionLookup(),
        source_district_lookup=lookup,
    )
    result = asyncio.run(_read(app, SCOPE))
    assert result.status_code == expected
    assert calls == []


@pytest.mark.parametrize(
    "changes",
    [
        {"district_id": "ru:district:unverified"},
        {"region_id": "ru:region:another"},
    ],
)
def test_unverified_identity_does_not_contact_upstream(changes: dict[str, object]) -> None:
    calls: list[bytes] = []
    lookup = DistrictLookup(1472)
    reader = SaturnPublicTreatmentReader(lambda body: calls.append(body) or _upstream_page())
    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=reader,
        source_region_lookup=RegionLookup(),
        source_district_lookup=lookup,
    )
    result = asyncio.run(_read(app, {**SCOPE, **changes}))
    assert result.status_code == 409
    assert calls == []


@pytest.mark.parametrize(
    "changes",
    [
        {"date_start": "2026-12-17", "date_end": "2026-12-16"},
        {"date_start": "2026-11-01", "date_end": "2026-12-16"},
        {"date_end": None},
        {"region_id": None},
    ],
)
def test_reject_invalid_scope_before_transport(changes: dict[str, object]) -> None:
    calls: list[bytes] = []
    reader = SaturnPublicTreatmentReader(lambda body: calls.append(body) or _upstream_page())
    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=reader,
        source_region_lookup=RegionLookup(),
        source_district_lookup=DistrictLookup(1472),
    )
    result = asyncio.run(_read(app, {**SCOPE, **changes}))
    assert result.status_code == 422
    assert calls == []


def test_reader_rejects_district_without_valid_code_and_excessively_long_date_range() -> None:
    reader = SaturnPublicTreatmentReader(lambda body: _upstream_page())
    with pytest.raises(ValueError, match="district code"):
        reader.read_page(country=CountryCode.RU, region_code=55, page_number=0, district_code=0)
    with pytest.raises(ValueError, match="date interval"):
        reader.read_page(
            country=CountryCode.RU,
            region_code=55,
            page_number=0,
            district_code=1472,
            start_date=date(2026, 11, 1),
            end_date=date(2027, 1, 1),
        )
