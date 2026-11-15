"""Contract tests for the offline combined ecology/treatment investigation."""

import asyncio
import json
import socket
from dataclasses import replace
from datetime import date
from unittest.mock import patch
from uuid import UUID

import httpx
import pytest

from melliatlas.agent.api import DeterministicPlanner, TreatmentPlanner
from melliatlas.analyzers.api import find_ecology_overlaps, screen_treatment_notices
from melliatlas.api.app import create_app
from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)
from melliatlas.planning.api import (
    CandidateSite,
    SiteAssessment,
    SyntheticScenario,
    TimeWindow,
    TreatmentProximity,
    TreatmentScreening,
    assess_ecology,
)
from melliatlas.sources.api import (
    SYNTHETIC_COMBINED_SCENARIO_ID,
    SyntheticFixtureProvider,
    treatment_fixture_notices,
)
from melliatlas.territories.api import CountryCode


def _request() -> InvestigationRequest:
    return InvestigationRequest(
        country=CountryCode.RU,
        territory_id="ru:region:smolensk",
        scenario_id=SYNTHETIC_COMBINED_SCENARIO_ID,
        season=TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
        starting_point=(32.0, 54.0),
    )


def _ecology_factory(scenario: SyntheticScenario) -> DeterministicPlanner:
    def inspect(site: CandidateSite) -> SiteAssessment:
        return assess_ecology(site.id, find_ecology_overlaps(site, scenario.ecology_zones))

    return DeterministicPlanner(inspect)


def _treatment_factory(_scenario: SyntheticScenario) -> TreatmentPlanner:
    notices = treatment_fixture_notices()
    return TreatmentPlanner(lambda site: screen_treatment_notices(site, notices))


def _complete() -> InvestigationSnapshot:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(),
        replan_factory=_ecology_factory,
        treatment_planner_factory=_treatment_factory,
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None
    return completed


def test_combined_http_retains_both_findings_and_selects_a_joint_alternative() -> None:
    async def check() -> None:
        with patch.object(
            socket.socket, "connect", side_effect=AssertionError("Fixture must not use network")
        ):
            app = create_app()
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                response = await client.post(
                    "/api/v1/investigations",
                    json={
                        "country": "RU",
                        "territory_id": "ru:region:smolensk",
                        "scenario_id": SYNTHETIC_COMBINED_SCENARIO_ID,
                        "season_start": "2026-05-01",
                        "season_end": "2026-08-15",
                    },
                )
                assert response.status_code == 202
                identifier = UUID(response.json()["id"])
                completed = (await client.get(f"/api/v1/investigations/{identifier}")).json()
                assert completed["status"] == "COMPLETED"
                assert completed["outcome"] == "PLAN_FOUND"
                assert [stop["site_id"] for stop in completed["plan"]["stops"]] == [
                    "fixture-site-alpha-treatment-alternative",
                    "fixture-site-beta",
                    "fixture-site-gamma",
                ]
                assert "fixture-site-alpha" in completed["replanning"]["excluded_site_ids"]
                assert (
                    "fixture-site-alpha-alternative"
                    in completed["treatment_review"]["avoided_site_ids"]
                )
                assert any(
                    decision["kind"] == "TREATMENT_CHECK"
                    for decision in completed["replanning"]["decisions"]
                )
                assert any(
                    decision["kind"] == "ECOLOGY_CHECK"
                    for decision in completed["replanning"]["decisions"]
                )
                assert any("Wind" in note for note in completed["limitations"])
                assert "starting_point" not in completed["request"]
                reopened = (await client.get(f"/api/v1/investigations/{identifier}")).json()
                assert reopened == completed

    asyncio.run(check())


def test_combined_snapshot_roundtrips_and_rejects_different_forged_plans() -> None:
    completed = _complete()
    assert completed.status is InvestigationStatus.COMPLETED
    assert completed.outcome is InvestigationOutcomeKind.PLAN_FOUND
    assert deserialize_completed_snapshot(serialize_completed_snapshot(completed)) == completed
    encoded = json.loads(serialize_completed_snapshot(completed))
    encoded["plan"]["stops"][0]["site_id"] = "fixture-site-alpha"
    encoded["replanning"]["plan"]["stops"][0]["site_id"] = "fixture-site-alpha"
    with pytest.raises(ValueError):
        deserialize_completed_snapshot(json.dumps(encoded))
    encoded = json.loads(serialize_completed_snapshot(completed))
    encoded["treatment_review"]["screenings"][0]["source_record_id"] = "forged"
    with pytest.raises(ValueError):
        deserialize_completed_snapshot(json.dumps(encoded))
    encoded = json.loads(serialize_completed_snapshot(completed))
    encoded["replanning"]["trace"] = [
        event for event in encoded["replanning"]["trace"] if event["kind"] != "TREATMENT_CHECK"
    ]
    with pytest.raises(ValueError, match="trace disagrees"):
        deserialize_completed_snapshot(json.dumps(encoded))
    encoded = json.loads(serialize_completed_snapshot(completed))
    for item in encoded["replanning"]["assessments"]:
        if item["site_id"] == "fixture-site-alpha-treatment-alternative":
            item["status"] = "UNKNOWN"
    with pytest.raises(ValueError, match="without ecological caution"):
        deserialize_completed_snapshot(json.dumps(encoded))


@pytest.mark.parametrize("missing", ["ecology", "treatment"])
def test_combined_requires_both_injected_planners(missing: str) -> None:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(),
        replan_factory=None if missing == "ecology" else _ecology_factory,
        treatment_planner_factory=None if missing == "treatment" else _treatment_factory,
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None
    assert completed.status is InvestigationStatus.FAILED
    assert completed.plan is None
    assert completed.replanning is None
    assert completed.treatment_review is None


def test_combined_missing_treatment_observation_does_not_recommend() -> None:
    def broken(_scenario: SyntheticScenario) -> TreatmentPlanner:
        return TreatmentPlanner(lambda _site: ())

    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(),
        replan_factory=_ecology_factory,
        treatment_planner_factory=broken,
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None and completed.status is InvestigationStatus.FAILED
    assert completed.plan is None


def test_combined_without_two_joint_stops_reports_no_plan() -> None:
    def restrictive(_scenario: SyntheticScenario) -> TreatmentPlanner:
        def inspect(site: CandidateSite) -> tuple[TreatmentScreening, ...]:
            return tuple(
                replace(observation, proximity=TreatmentProximity.NEAR_REPORTED_FIELD)
                for observation in screen_treatment_notices(site, treatment_fixture_notices())
            )

        return TreatmentPlanner(inspect)

    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(),
        replan_factory=_ecology_factory,
        treatment_planner_factory=restrictive,
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None and completed.status is InvestigationStatus.COMPLETED
    assert completed.outcome is InvestigationOutcomeKind.NO_FEASIBLE_ALTERNATIVE
    assert completed.plan is None
    assert completed.treatment_review is not None


def test_combined_short_season_returns_readable_no_plan_with_separate_findings() -> None:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(),
        replan_factory=_ecology_factory,
        treatment_planner_factory=_treatment_factory,
    )
    request = replace(_request(), season=TimeWindow(date(2026, 7, 16), date(2026, 7, 20)))
    queued = service.submit(request)
    service.process(queued.id)
    result = service.get(queued.id)
    assert result is not None and result.status is InvestigationStatus.COMPLETED
    assert result.plan is None
    assert result.outcome is InvestigationOutcomeKind.NO_FEASIBLE_ALTERNATIVE
    assert result.replanning is not None and result.treatment_review is not None
    assert len(result.treatment_review.screenings) == 1
    assert deserialize_completed_snapshot(serialize_completed_snapshot(result)) == result


def test_combined_ecology_check_limit_never_recommends_uninspected_sites() -> None:
    def limited(scenario: SyntheticScenario) -> DeterministicPlanner:
        def inspect(site: CandidateSite) -> SiteAssessment:
            return assess_ecology(site.id, find_ecology_overlaps(site, scenario.ecology_zones))

        return DeterministicPlanner(inspect, max_checks=2)

    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(),
        replan_factory=limited,
        treatment_planner_factory=_treatment_factory,
    )
    queued = service.submit(_request())
    service.process(queued.id)
    result = service.get(queued.id)
    assert result is not None and result.status is InvestigationStatus.COMPLETED
    assert result.outcome is InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
    assert result.plan is None
    assert result.replanning is not None and result.treatment_review is not None
    assert result.replanning.checks_used == 2
    assert deserialize_completed_snapshot(serialize_completed_snapshot(result)) == result
