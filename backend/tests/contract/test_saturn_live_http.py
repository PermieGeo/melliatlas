"""Contract checks: real claims remain unverified and Saturn is RU-only."""

import asyncio
import json
from dataclasses import replace

import httpx
import pytest

from melliatlas.api.app import AppSettings, create_app
from melliatlas.sources.api import SourceReadError, TreatmentNoticePage
from melliatlas.sources.providers.saturn.live import (
    MAX_BODY_BYTES,
    SaturnPublicTreatmentReader,
)
from melliatlas.territories.api import CountryCode


def _page(*, field: bool = True) -> bytes:
    records: list[dict[str, object]] = []
    if field:
        records.append(
            {
                "beeAcreage": {
                    "id": 71,
                    "planId": 17,
                    "planDate": 1780617600,
                    "planDateEnd": 1780704000,
                    "datePublishing": 1780185600,
                    "geo": None,
                },
                "allPatList": [{"patName": "Observed product", "patProductDangerClassBee": 2}],
            }
        )
    return json.dumps(
        {
            "content": records,
            "number": 0,
            "size": 10,
            "numberOfElements": len(records),
            "totalElements": len(records),
            "totalPages": 1 if field else 0,
            "last": True,
        },
    ).encode()


def test_live_reader_preserves_source_claims_and_request_scope() -> None:
    observed: list[dict[str, object]] = []

    def fetch(body: bytes) -> bytes:
        observed.append(json.loads(body))
        return _page()

    reader = SaturnPublicTreatmentReader(fetch)
    page = reader.read_page(country=CountryCode.RU, region_code=55, page_number=0)
    assert observed == [
        {
            "pageNumber": 0,
            "pageSize": 10,
            "sortColumn": "datePublishing",
            "sortDirection": "desc",
            "beekeperSearchFilter": {"subject": 55},
        }
    ]
    assert page.country is CountryCode.RU
    assert page.next_page is None
    assert page.total_elements == 1
    assert page.notices[0].source_mode == "LIVE"
    assert page.notices[0].synthetic is False
    assert page.notices[0].record_id == "71"
    assert page.notices[0].source_uri == "https://bee.fgis-saturn.ru/"
    assert "Unverified public notice" in page.notices[0].uncertainties[0]
    assert page.notices[0].products[0].name == "Observed product"


def test_reader_rejects_non_ru_before_transport() -> None:
    called = False

    def fetch(_body: bytes) -> bytes:
        nonlocal called
        called = True
        return _page()

    reader = SaturnPublicTreatmentReader(fetch)
    with pytest.raises(ValueError, match="restricted to RU"):
        reader.read_page(country=CountryCode.BY, region_code=55, page_number=0)
    assert not called


@pytest.mark.parametrize("value", [0, -1, 1000000, True])
def test_reader_rejects_invalid_region_codes(value: int) -> None:
    reader = SaturnPublicTreatmentReader(lambda body: _page())
    with pytest.raises(ValueError, match="region code"):
        reader.read_page(country=CountryCode.RU, region_code=value, page_number=0)


@pytest.mark.parametrize("raw", [b"not json", b"[]", b"{}", b"{}" * (MAX_BODY_BYTES + 1)])
def test_read_fails_closed_on_unexpected_upstream_shape(raw: bytes) -> None:
    reader = SaturnPublicTreatmentReader(lambda body: raw)
    with pytest.raises(SourceReadError):
        reader.read_page(country=CountryCode.RU, region_code=55, page_number=0)


class FakeSaturnReader:
    def __init__(self, *, failing: bool = False) -> None:
        self.calls: list[tuple[CountryCode, int, int]] = []
        self._failing = failing

    def read_page(
        self, *, country: CountryCode, region_code: int, page_number: int
    ) -> TreatmentNoticePage:
        self.calls.append((country, region_code, page_number))
        if self._failing:
            raise SourceReadError("Provider secret must not leak")
        return SaturnPublicTreatmentReader(lambda body: _page()).read_page(
            country=country, region_code=region_code, page_number=page_number
        )


def test_source_catalog_and_http_enforce_country_and_enablement() -> None:
    async def check() -> None:
        reader = FakeSaturnReader()
        enabled = create_app(settings=AppSettings(saturn_live_enabled=True), saturn_reader=reader)
        disabled = create_app(saturn_reader=reader)
        for app in (enabled, disabled):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                ru = await client.get("/api/v1/sources", params={"country": "RU"})
                by = await client.get("/api/v1/sources", params={"country": "BY"})
                assert ru.status_code == 200 and by.status_code == 200
                assert by.json() == []
                assert (ru.json() != []) == (app is enabled)
                rejected = await client.post(
                    "/api/v1/sources/saturn/treatments",
                    json={"country": "BY", "region_code": 55},
                )
                assert rejected.status_code == 404
                assert rejected.json()["error"]["code"] == "SOURCE_NOT_AVAILABLE"
                missing = await client.post(
                    "/api/v1/sources/saturn/treatments",
                    json={"country": "RU", "region_code": 55},
                )
                assert missing.status_code == (200 if app is enabled else 503)
                if app is enabled:
                    data = missing.json()
                    assert data["notices"][0]["source_mode"] == "LIVE"
                    assert data["notices"][0]["synthetic"] is False
                    assert data["coverage_complete"] is False
                    assert data["next_page"] is None
                    assert data["notices"][0]["geometry"] is None
        assert reader.calls == [(CountryCode.RU, 55, 0)]

    asyncio.run(check())


def test_upstream_failure_is_not_confused_with_no_notices() -> None:
    async def check() -> None:
        reader = FakeSaturnReader(failing=True)
        app = create_app(settings=AppSettings(saturn_live_enabled=True), saturn_reader=reader)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            result = await client.post(
                "/api/v1/sources/saturn/treatments", json={"country": "RU", "region_code": 55}
            )
        assert result.status_code == 502
        assert result.json()["error"]["code"] == "SOURCE_READ_FAILED"
        assert "secret" not in result.text

    asyncio.run(check())


def test_injected_provider_cannot_label_synthetic_records_as_live() -> None:
    class InvalidReader(FakeSaturnReader):
        def read_page(
            self, *, country: CountryCode, region_code: int, page_number: int
        ) -> TreatmentNoticePage:
            page = super().read_page(
                country=country, region_code=region_code, page_number=page_number
            )
            return replace(page, notices=(replace(page.notices[0], synthetic=True),))

    async def check() -> None:
        reader = InvalidReader()
        app = create_app(settings=AppSettings(saturn_live_enabled=True), saturn_reader=reader)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            result = await client.post(
                "/api/v1/sources/saturn/treatments", json={"country": "RU", "region_code": 55}
            )
        assert result.status_code == 502
        assert result.json()["error"]["code"] == "SOURCE_READ_FAILED"

    asyncio.run(check())
