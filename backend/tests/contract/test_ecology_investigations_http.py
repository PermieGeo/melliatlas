"""Contract tests for opt-in fictional ecology investigations (V04-03)."""

import asyncio
from datetime import date
from uuid import UUID

import httpx

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode
from melliatlas.jobs import (
    InMemoryInvestigationService,
    InvestigationRequest,
    InvestigationStatus,
)
from melliatlas.planning import TimeWindow
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_ECOLOGY_SCENARIO_ID,
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.territories.api import CountryCode


def _request(scenario_id: str) -> dict[str, object]:
    return {
        "country": "RU",
        "territory_id": "ru:region:smolensk",
        "scenario_id": scenario_id,
        "season_start": "2026-05-01",
        "season_end": "2026-08-15",
        "starting_point": {"longitude": 32.0, "latitude": 54.0},
    }


def test_fictional_ecology_scenario_replans_and_exposes_typed_evidence() -> None:
    async def scenario() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            created = await client.post(
                "/api/v1/investigations", json=_request(SYNTHETIC_ECOLOGY_SCENARIO_ID)
            )
            assert created.status_code == 202
            identifier = UUID(created.json()["id"])
            assert created.json()["status"] == "QUEUED"
            completed = await client.get(f"/api/v1/investigations/{identifier}")
            assert completed.status_code == 200
            body = completed.json()
            assert body["status"] == "COMPLETED"
            assert body["outcome"] == "PLAN_FOUND"
            assert body["synthetic"] is True
            assert [stop["site_id"] for stop in body["plan"]["stops"]] == [
                "fixture-site-alpha-alternative",
                "fixture-site-beta",
                "fixture-site-gamma",
            ]
            assert body["plan"]["relocations"] == 2
            assert body["replanning"]["outcome"] == "PLAN_FOUND"
            assert body["replanning"]["checks_used"] == 4
            assert body["replanning"]["excluded_site_ids"] == ["fixture-site-alpha"]
            assert body["replanning"]["unknown_site_ids"] == []
            assert [assessment["status"] for assessment in body["replanning"]["assessments"]] == [
                "EXCLUDED",
                "CAUTION",
                "CAUTION",
                "CAUTION",
            ]
            decisions = body["replanning"]["decisions"]
            assert decisions[0]["kind"] == "INITIAL"
            assert decisions[-2]["kind"] == "REVISION"
            assert decisions[-1]["kind"] == "TERMINAL"
            assert "fixture-ecology-exclusion" in decisions[-2]["evidence_ids"]
            assert "demo-rule-exclusion" in decisions[-2]["rule_ids"]
            assert "fixture-ecology-precaution" in {item["id"] for item in body["evidence"]}
            assert any("fictional" in warning.lower() for warning in body["replanning"]["warnings"])
            assert any("fictional" in note.lower() for note in body["limitations"])
            assert "starting_point" not in body["request"]
            assert (await client.get(f"/api/v1/investigations/{identifier}")).json() == body

            openapi = (await client.get("/openapi.json")).json()
            assert "ReplanSummaryDto" in openapi["components"]["schemas"]
            assert "ReplanDecisionDto" in openapi["components"]["schemas"]

    asyncio.run(scenario())


def test_original_v01_scenario_has_no_replanning_and_old_trace() -> None:
    async def scenario() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            created = await client.post(
                "/api/v1/investigations", json=_request(SYNTHETIC_SCENARIO_ID)
            )
            assert created.status_code == 202
            completed = await client.get(f"/api/v1/investigations/{created.json()['id']}")
            body = completed.json()
            assert body["outcome"] == "PLAN_FOUND"
            assert body["replanning"] is None
            assert [stop["site_id"] for stop in body["plan"]["stops"]] == [
                "fixture-site-alpha",
                "fixture-site-beta",
                "fixture-site-gamma",
            ]
            assert body["decision_trace"] == [
                "Sorted synthetic forage windows by date and stable candidate ID",
                "Selected at least two non-overlapping fixture stops",
            ]

    asyncio.run(scenario())


def test_ecology_scenario_rejects_invalid_combination_without_side_effects() -> None:
    async def scenario() -> None:
        service = InMemoryInvestigationService(SyntheticFixtureProvider())
        app = create_app(investigations=service)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            invalid = _request(SYNTHETIC_ECOLOGY_SCENARIO_ID)
            invalid["country"] = "BY"
            response = await client.post("/api/v1/investigations", json=invalid)
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "INVALID_INVESTIGATION_REQUEST"
            assert service.record_count == 0

    asyncio.run(scenario())


def test_ecology_without_injected_planner_fails_closed() -> None:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    queued = service.submit(
        InvestigationRequest(
            CountryCode.RU,
            "ru:region:smolensk",
            SYNTHETIC_ECOLOGY_SCENARIO_ID,
            TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            None,
        )
    )
    service.process(queued.id)
    finished = service.get(queued.id)
    assert finished is not None
    assert finished.status is InvestigationStatus.FAILED
    assert finished.plan is None
    assert finished.replanning is None
    assert finished.diagnostics == ("Synthetic analysis failed",)


def test_bounded_ecology_limit_produces_completed_insufficient_evidence_without_plan() -> None:
    from melliatlas.agent import DeterministicPlanner
    from melliatlas.analyzers import find_ecology_overlaps
    from melliatlas.planning import (
        CandidateSite,
        SiteAssessment,
        SyntheticScenario,
        assess_ecology,
    )

    def factory(source: SyntheticScenario) -> DeterministicPlanner:
        def inspect(site: CandidateSite) -> SiteAssessment:
            return assess_ecology(site.id, find_ecology_overlaps(site, source.ecology_zones))

        return DeterministicPlanner(inspect, max_checks=2)

    async def scenario() -> None:
        service = InMemoryInvestigationService(SyntheticFixtureProvider(), replan_factory=factory)
        app = create_app(investigations=service)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            created = await client.post(
                "/api/v1/investigations", json=_request(SYNTHETIC_ECOLOGY_SCENARIO_ID)
            )
            assert created.status_code == 202
            result = (await client.get(f"/api/v1/investigations/{created.json()['id']}")).json()
            assert result["status"] == "COMPLETED"
            assert result["outcome"] == "INSUFFICIENT_EVIDENCE"
            assert result["plan"] is None
            assert result["replanning"]["outcome"] == "CHECK_LIMIT_REACHED"
            assert result["replanning"]["checks_used"] == 2
            assert result["replanning"]["decisions"][-1]["kind"] == "LIMIT_REACHED"

    asyncio.run(scenario())


def test_ecology_inspector_failure_is_sanitized_as_failed_investigation() -> None:
    from melliatlas.agent import DeterministicPlanner
    from melliatlas.planning import CandidateSite, SiteAssessment, SyntheticScenario

    def factory(_source: SyntheticScenario) -> DeterministicPlanner:
        def unavailable(_site: CandidateSite) -> SiteAssessment:
            raise RuntimeError("Sensitive unpublished provider error")

        return DeterministicPlanner(unavailable)

    async def scenario() -> None:
        service = InMemoryInvestigationService(SyntheticFixtureProvider(), replan_factory=factory)
        app = create_app(investigations=service)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            created = await client.post(
                "/api/v1/investigations", json=_request(SYNTHETIC_ECOLOGY_SCENARIO_ID)
            )
            assert created.status_code == 202
            result = (await client.get(f"/api/v1/investigations/{created.json()['id']}")).json()
            assert result["status"] == "FAILED"
            assert result["outcome"] is None
            assert result["replanning"] is None
            assert result["plan"] is None
            assert result["diagnostics"] == ["Synthetic analysis failed"]
            assert "Sensitive" not in str(result)

    asyncio.run(scenario())
