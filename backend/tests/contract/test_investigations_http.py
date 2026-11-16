"""Contract tests for the deliberately non-durable synthetic investigation API."""

import asyncio
from uuid import UUID

import httpx
from pytest import MonkeyPatch

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode
from melliatlas.jobs import InMemoryInvestigationService
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)


async def _http(
    method: str, path: str, *, payload: dict[str, object] | None = None
) -> httpx.Response:
    app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.request(method, path, json=payload)


def _request(*, start: str = "2026-05-01", end: str = "2026-08-15") -> dict[str, object]:
    return {
        "country": "RU",
        "territory_id": "ru:region:smolensk",
        "scenario_id": SYNTHETIC_SCENARIO_ID,
        "season_start": start,
        "season_end": end,
        "starting_point": {"longitude": 32.0, "latitude": 54.0},
    }


def test_successful_post_then_get_is_synthetic_and_deterministic() -> None:
    async def check() -> None:
        app = create_app(
            settings=AppSettings(
                title="Synthetic V01", source_provider=SourceProviderMode.SYNTHETIC
            )
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            post = await client.post("/api/v1/investigations", json=_request())
            assert post.status_code == 202
            queued = post.json()
            assert queued["status"] == "QUEUED"
            assert queued["synthetic"] is True
            identifier = UUID(queued["id"])
            assert identifier.version == 4
            assert queued["plan"] is None

            result = await client.get(f"/api/v1/investigations/{identifier}")
            assert result.status_code == 200
            final = result.json()
            assert final["id"] == str(identifier)
            assert final["status"] == "COMPLETED"
            assert final["outcome"] == "PLAN_FOUND"
            assert final["synthetic"] is True
            assert final["reference_version"] == "SYNTHETIC-V01-NOT-REAL-GEOGRAPHY"
            assert len(final["plan"]["stops"]) >= 2
            assert final["plan"]["relocations"] >= 1
            assert [stop["site_id"] for stop in final["plan"]["stops"]] == [
                "fixture-site-alpha",
                "fixture-site-beta",
                "fixture-site-gamma",
            ]
            assert final["plan"]["stops"][0]["start"] == "2026-05-01"
            assert final["plan"]["stops"][0]["end"] == "2026-06-14"
            assert len(final["evidence"]) == 3
            assert all(item["synthetic"] for item in final["evidence"])
            assert all(item["source_mode"] == "FIXTURE" for item in final["evidence"])
            assert any("not verified" in note.lower() for note in final["limitations"])
            assert "starting_point" not in final["request"]
            assert "longitude" not in str(final["request"])
            assert (await client.get(f"/api/v1/investigations/{identifier}")).json() == final

    asyncio.run(check())


def test_evidence_limited_outcome_is_not_an_execution_failure() -> None:
    async def check() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            post = await client.post(
                "/api/v1/investigations", json=_request(start="2026-05-10", end="2026-05-10")
            )
            assert post.status_code == 202
            result = (await client.get(f"/api/v1/investigations/{post.json()['id']}")).json()
            assert result["status"] == "COMPLETED"
            assert result["outcome"] == "INSUFFICIENT_EVIDENCE"
            assert result["plan"] is None
            assert result["diagnostics"]
            assert result["evidence"]

    asyncio.run(check())


def test_invalid_requests_have_no_job_side_effects() -> None:
    async def check() -> None:
        provider = SyntheticFixtureProvider()
        service = InMemoryInvestigationService(provider)
        app = create_app(investigations=service)
        cases = [
            {**_request(), "country": "BY"},
            {**_request(), "scenario_id": "unknown"},
            {**_request(), "territory_id": "by:region:vitebsk"},
            {**_request(), "season_start": "2026-08-15", "season_end": "2026-05-01"},
            {**_request(), "season_start": "2027-05-01", "season_end": "2027-08-15"},
            {**_request(), "starting_point": {"longitude": 181.0, "latitude": 54.0}},
            {**_request(), "starting_point": {"longitude": 32.0, "latitude": -91.0}},
        ]
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            for payload in cases:
                response = await client.post("/api/v1/investigations", json=payload)
                assert response.status_code == 422
                assert response.json()["error"]["code"] in {
                    "INVALID_INVESTIGATION_REQUEST",
                    "INVALID_REQUEST",
                }
            assert service.record_count == 0
            malformed = await client.post("/api/v1/investigations", json={"bogus": True})
            assert malformed.status_code == 422
            assert malformed.json()["error"]["code"] == "INVALID_REQUEST"
            assert service.record_count == 0

    asyncio.run(check())


def test_get_can_report_not_ready_without_fabricating_plan() -> None:
    class DeferredFixtureService(InMemoryInvestigationService):
        def process(self, identifier: UUID) -> None:
            pass

    async def check() -> None:
        service = DeferredFixtureService(SyntheticFixtureProvider())
        app = create_app(investigations=service)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            post = await client.post("/api/v1/investigations", json=_request())
            assert post.status_code == 202
            result = await client.get(f"/api/v1/investigations/{post.json()['id']}")
            assert result.status_code == 200
            assert result.json()["status"] == "QUEUED"
            assert result.json()["outcome"] is None
            assert result.json()["plan"] is None

    asyncio.run(check())


def test_unknown_and_invalid_result_identifiers_are_sanitized() -> None:
    missing = asyncio.run(
        _http("GET", "/api/v1/investigations/00000000-0000-4000-8000-000000000001")
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"
    malformed = asyncio.run(_http("GET", "/api/v1/investigations/not-a-uuid"))
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "INVALID_REQUEST"


def test_fixture_investigation_performs_no_network_io(monkeypatch: MonkeyPatch) -> None:
    from socket import socket

    def block_connect(_sock: socket, _address: object) -> None:
        raise AssertionError("V01 fixture must not open an outbound connection")

    monkeypatch.setattr(socket, "connect", block_connect)
    response = asyncio.run(_http("POST", "/api/v1/investigations", payload=_request()))
    assert response.status_code == 202


def test_openapi_contains_typed_investigation_responses_and_preserves_territories() -> None:
    schema = asyncio.run(_http("GET", "/openapi.json")).json()
    paths = schema["paths"]
    assert "/api/v1/territories/countries" in paths
    assert "/api/v1/investigations" in paths
    assert "/api/v1/investigations/{id}" in paths
    create = paths["/api/v1/investigations"]["post"]
    assert create["responses"]["202"]["content"]["application/json"]["schema"]
    for response in (
        create["responses"]["422"],
        paths["/api/v1/investigations/{id}"]["get"]["responses"]["404"],
    ):
        assert response["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }
    assert "InvestigationResponse" in schema["components"]["schemas"]
