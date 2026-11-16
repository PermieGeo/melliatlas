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
        {"date_start": "2026-11-01", "date_end": "2027-11-02"},
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
            end_date=date(2027, 11, 2),
        )


@pytest.mark.parametrize(
    ("start", "end", "allowed"),
    [
        ("2026-11-16", "2027-11-16", True),
        ("2026-11-16", "2027-11-17", False),
        ("2024-02-29", "2025-02-28", True),
        ("2024-02-29", "2025-03-01", False),
    ],
)
def test_calendar_year_scope_before_source_access(start: str, end: str, allowed: bool) -> None:
    calls: list[dict[str, object]] = []

    def transport(body: bytes) -> bytes:
        calls.append(json.loads(body))
        return _upstream_page()

    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=SaturnPublicTreatmentReader(transport),
        source_region_lookup=RegionLookup(),
        source_district_lookup=DistrictLookup(1472),
    )
    result = asyncio.run(_read(app, {**SCOPE, "date_start": start, "date_end": end}))
    assert result.status_code == (200 if allowed else 422)
    assert len(calls) == int(allowed)
    if allowed:
        assert calls[0]["beekeperSearchFilter"] == {
            "subject": 55,
            "district": 1472,
            "startDateUpdateMap": f"{start}T00:00:00.000Z",
            "endDateUpdateMap": f"{end}T23:59:59.999Z",
        }


@pytest.mark.parametrize("page_number", [10, 50])
def test_source_record_budget_rejects_pages_outside_first_hundred(page_number: int) -> None:
    calls: list[bytes] = []
    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=SaturnPublicTreatmentReader(
            lambda body: calls.append(body) or _upstream_page()
        ),
        source_region_lookup=RegionLookup(),
        source_district_lookup=DistrictLookup(1472),
    )
    result = asyncio.run(_read(app, {**SCOPE, "page_number": page_number}))
    assert result.status_code == 422
    assert calls == []


@pytest.mark.parametrize("reported_total", [101, None])
def test_upstream_total_over_hundred_returns_partial_budget_warning(
    reported_total: int | None,
) -> None:
    from datetime import datetime, timezone

    from melliatlas.sources.api import TreatmentNoticePage

    class Reader:
        def read_page(
            self,
            *,
            country: CountryCode,
            region_code: int,
            page_number: int,
            district_code: int | None = None,
            start_date: date | None = None,
            end_date: date | None = None,
        ) -> TreatmentNoticePage:
            return TreatmentNoticePage(
                source_id="saturn:public-beekeeper-portal",
                country=country,
                region_code=region_code,
                captured_at=datetime.now(timezone.utc),
                page_number=page_number,
                next_page=page_number + 1,
                total_elements=reported_total,
                unidentified_records=0,
                notices=(),
            )

    app = create_app(
        settings=AppSettings(saturn_live_enabled=True),
        saturn_reader=Reader(),
        source_region_lookup=RegionLookup(),
        source_district_lookup=DistrictLookup(1472),
    )
    first = asyncio.run(_read(app, SCOPE))
    assert first.status_code == 200, first.text
    assert first.json()["record_limit_exceeded"] is (reported_total is not None)
    assert first.json()["next_page"] == 1
    last = asyncio.run(_read(app, {**SCOPE, "page_number": 9}))
    assert last.status_code == 200, last.text
    assert last.json()["record_limit_exceeded"] is True
    assert last.json()["next_page"] is None


def test_upstream_page_may_not_return_more_than_ten_records() -> None:
    # Eleven unrecognized records are still eleven source records within the budget.
    payload = {
        "content": [{"unexpected": "shape"} for _ in range(11)],
        "number": 0,
        "numberOfElements": 11,
        "size": 10,
        "totalElements": 11,
        "totalPages": 2,
        "last": False,
    }
    reader = SaturnPublicTreatmentReader(lambda body: json.dumps(payload).encode())
    from melliatlas.sources.api import SourceReadError

    with pytest.raises(SourceReadError):
        reader.read_page(country=CountryCode.RU, region_code=55, page_number=0)
