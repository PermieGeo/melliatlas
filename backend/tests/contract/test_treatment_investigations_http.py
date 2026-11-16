"""MVP01-BE-R08/R10/R14/R18: offline treatment-aware investigation decisions."""

import asyncio
import json
from datetime import date, datetime, timezone
from socket import socket
from unittest.mock import patch
from uuid import UUID

import httpx
import pytest

from melliatlas.agent import TreatmentInspector, TreatmentPlanner
from melliatlas.analyzers import screen_treatment_notices
from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode
from melliatlas.jobs import (
    InMemoryInvestigationService,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    TreatmentPlannerFactory,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)
from melliatlas.planning import (
    CandidateSite,
    EcologyEvidenceKind,
    EcologyZone,
    ReportedTreatmentProduct,
    SyntheticScenario,
    TimeWindow,
    TreatmentProximity,
    TreatmentScreening,
)
from melliatlas.sources.providers.synthetic import (
    SYNTHETIC_TREATMENT_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.sources.providers.synthetic.treatments import (
    TREATMENT_FIXTURE_RECORD_ID,
    TREATMENT_FIXTURE_SOURCE_ID,
    treatment_fixture_notices,
)
from melliatlas.territories.api import CountryCode, PolygonWgs84


def _request(*, season_end: date = date(2026, 8, 15)) -> InvestigationRequest:
    return InvestigationRequest(
        country=CountryCode.RU,
        territory_id="ru:region:smolensk",
        scenario_id=SYNTHETIC_TREATMENT_SCENARIO_ID,
        season=TimeWindow(date(2026, 5, 1), season_end),
        starting_point=(32.0, 54.0),
    )


def _run(factory: TreatmentPlannerFactory | None = None) -> InvestigationSnapshot:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(), treatment_planner_factory=factory
    )
    queued = service.submit(_request())
    service.process(queued.id)
    result = service.get(queued.id)
    assert result is not None
    return result


def _single_observation(
    site: CandidateSite, proximity: TreatmentProximity
) -> tuple[TreatmentScreening, ...]:
    return (
        TreatmentScreening(
            site_id=site.id,
            source_record_id=TREATMENT_FIXTURE_RECORD_ID,
            source_id=TREATMENT_FIXTURE_SOURCE_ID,
            proximity=proximity,
            approximate_distance_km=(
                0.0 if proximity is TreatmentProximity.FIELD_INTERSECTION else None
            ),
            warnings=("Synthetic claim, not a verified application",),
            captured_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
            scheduled_start=datetime(2026, 6, 5, tzinfo=timezone.utc),
            scheduled_end=datetime(2026, 6, 6, tzinfo=timezone.utc),
            source_uri=None,
            products=(ReportedTreatmentProduct("FICTIONAL product", None, 2),),
        ),
    )


def test_offline_http_investigation_replaces_treatment_intersection_with_alternative() -> None:
    async def scenario() -> None:
        with patch.object(socket, "connect", side_effect=AssertionError("No network for fixtures")):
            app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                requested = {
                    "country": "RU",
                    "territory_id": "ru:region:smolensk",
                    "scenario_id": SYNTHETIC_TREATMENT_SCENARIO_ID,
                    "season_start": "2026-05-01",
                    "season_end": "2026-08-15",
                    "starting_point": {"longitude": 32.0, "latitude": 54.0},
                }
                created = await client.post("/api/v1/investigations", json=requested)
                assert created.status_code == 202, created.text
                assert created.json()["status"] == "QUEUED"
                identifier = UUID(created.json()["id"])
                completed = await client.get(f"/api/v1/investigations/{identifier}")
                assert completed.status_code == 200, completed.text
                body = completed.json()
                assert body["status"] == "COMPLETED"
                assert body["outcome"] == "PLAN_FOUND"
                assert body["replanning"] is None
                assert [stop["site_id"] for stop in body["plan"]["stops"]] == [
                    "fixture-site-alpha-treatment-alternative",
                    "fixture-site-beta",
                    "fixture-site-gamma",
                ]
                assert body["plan"]["relocations"] == 2
                review = body["treatment_review"]
                assert review["avoided_site_ids"] == ["fixture-site-alpha"]
                assert len(review["screenings"]) == 4
                assert review["screenings"][0]["proximity"] == "FIELD_INTERSECTION"
                assert review["screenings"][0]["source_record_id"] == TREATMENT_FIXTURE_RECORD_ID
                assert review["screenings"][0]["source_id"] == TREATMENT_FIXTURE_SOURCE_ID
                assert review["screenings"][0]["scheduled_start"].startswith("2026-06-05")
                assert review["screenings"][0]["scheduled_end"].startswith("2026-06-06")
                assert review["screenings"][0]["products"] == [
                    {
                        "name": "FICTIONAL demonstration product",
                        "crop": "FICTIONAL demonstration crop",
                        "bee_hazard_class": 2,
                    }
                ]
                assert "DRIFT_NOT_EVALUATED" in review["warnings"]
                assert "COVERAGE_NOT_ESTABLISHED" in review["warnings"]
                assert any(TREATMENT_FIXTURE_RECORD_ID in event for event in body["decision_trace"])
                assert any(
                    item["id"] == TREATMENT_FIXTURE_RECORD_ID
                    and item["source_mode"] == "FIXTURE"
                    and item["synthetic"] is True
                    for item in body["evidence"]
                )
                assert body["synthetic"] is True
                assert "starting_point" not in body["request"]
                assert (await client.get(f"/api/v1/investigations/{identifier}")).json() == body
                openapi = (await client.get("/openapi.json")).json()
                assert "TreatmentScreeningDto" in openapi["components"]["schemas"]
                assert "TreatmentReviewDto" in openapi["components"]["schemas"]

    asyncio.run(scenario())


def _fixture_inspector(_scenario: SyntheticScenario) -> TreatmentInspector:
    notices = treatment_fixture_notices()

    def inspect(site: CandidateSite) -> tuple[TreatmentScreening, ...]:
        return screen_treatment_notices(site, notices)

    return inspect


def _fixture_planner(scenario: SyntheticScenario) -> TreatmentPlanner:
    return TreatmentPlanner(_fixture_inspector(scenario))


def test_completed_treatment_review_roundtrips_without_recalculation() -> None:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(), treatment_planner_factory=_fixture_planner
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None and completed.treatment_review is not None
    restored = deserialize_completed_snapshot(serialize_completed_snapshot(completed))
    assert restored == completed
    assert restored.plan is not None
    assert restored.plan.stops[0].site_id == "fixture-site-alpha-treatment-alternative"
    assert restored.outcome is InvestigationOutcomeKind.PLAN_FOUND


@pytest.mark.parametrize(
    ("property_name", "bad_value"),
    [
        ("proximity", "SAFE"),
        ("approximate_distance_km", -0.5),
        ("source_record_id", ""),
        ("warnings", "not-an-array"),
        ("captured_at", "2026-05-01T00:00:00"),
        ("scheduled_start", "not-a-time"),
        ("products", "not-a-list"),
    ],
)
def test_storage_rejects_corrupted_treatment_findings(
    property_name: str, bad_value: object
) -> None:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(), treatment_planner_factory=_fixture_planner
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None
    payload = json.loads(serialize_completed_snapshot(completed))
    payload["treatment_review"]["screenings"][0][property_name] = bad_value
    with pytest.raises((ValueError, TypeError)):
        deserialize_completed_snapshot(json.dumps(payload))


def test_storage_rejects_forged_avoidance_and_unjustified_plan() -> None:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(), treatment_planner_factory=_fixture_planner
    )
    queued = service.submit(_request())
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None
    payload = json.loads(serialize_completed_snapshot(completed))
    payload["treatment_review"]["avoided_site_ids"] = []
    with pytest.raises(ValueError, match="disagree"):
        deserialize_completed_snapshot(json.dumps(payload))
    payload = json.loads(serialize_completed_snapshot(completed))
    payload["plan"]["stops"][0]["site_id"] = "fixture-site-alpha"
    with pytest.raises(ValueError, match="withheld"):
        deserialize_completed_snapshot(json.dumps(payload))
    payload = json.loads(serialize_completed_snapshot(completed))
    payload["treatment_review"]["screenings"][0]["source_record_id"] = "forged"
    with pytest.raises(ValueError, match="source evidence"):
        deserialize_completed_snapshot(json.dumps(payload))
    payload = json.loads(serialize_completed_snapshot(completed))
    payload["treatment_review"]["screenings"][0]["products"][0]["bee_hazard_class"] = 4
    with pytest.raises(ValueError, match="hazard class"):
        deserialize_completed_snapshot(json.dumps(payload))


def test_missing_inspector_fails_closed_without_proposal() -> None:
    result = _run()
    assert result.status is InvestigationStatus.FAILED
    assert result.plan is None
    assert result.treatment_review is None
    assert result.diagnostics == ("Synthetic analysis failed",)


def test_mismatched_inspection_or_missing_source_fails_closed() -> None:
    def wrong(_scenario: SyntheticScenario) -> TreatmentPlanner:
        def inspect(site: CandidateSite) -> tuple[TreatmentScreening, ...]:
            return (
                TreatmentScreening(
                    site_id="not-" + site.id,
                    source_id=TREATMENT_FIXTURE_SOURCE_ID,
                    source_record_id=TREATMENT_FIXTURE_RECORD_ID,
                    proximity=TreatmentProximity.OUTSIDE_SCREEN_RADIUS,
                    approximate_distance_km=None,
                    warnings=(),
                    captured_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
                    scheduled_start=None,
                    scheduled_end=None,
                    source_uri=None,
                    products=(),
                ),
            )

        return TreatmentPlanner(inspect)

    assert _run(wrong).status is InvestigationStatus.FAILED

    def missing(_scenario: SyntheticScenario) -> TreatmentPlanner:
        def inspect(_site: CandidateSite) -> tuple[TreatmentScreening, ...]:
            return ()

        return TreatmentPlanner(inspect)

    assert _run(missing).status is InvestigationStatus.FAILED


def test_all_candidates_near_reported_field_produces_no_fabricated_plan() -> None:
    def all_flagged(_scenario: SyntheticScenario) -> TreatmentPlanner:
        def inspect(site: CandidateSite) -> tuple[TreatmentScreening, ...]:
            return _single_observation(site, TreatmentProximity.NEAR_REPORTED_FIELD)

        return TreatmentPlanner(inspect)

    result = _run(all_flagged)
    assert result.status is InvestigationStatus.COMPLETED
    assert result.outcome is InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
    assert result.plan is None
    assert result.treatment_review is not None
    assert len(result.treatment_review.avoided_site_ids) == 4
    assert any("Insufficient alternative" in event for event in result.decision_trace)


def test_country_and_territory_scoping_for_fixture() -> None:
    provider = SyntheticFixtureProvider()
    assert (
        provider.load(
            country=CountryCode.BY,
            territory_id="by:region:vitebsk",
            scenario_id=SYNTHETIC_TREATMENT_SCENARIO_ID,
        )
        is None
    )
    assert (
        provider.load(
            country=CountryCode.RU,
            territory_id="ru:region:unknown",
            scenario_id=SYNTHETIC_TREATMENT_SCENARIO_ID,
        )
        is None
    )
    assert provider.load_treatment_notices("synthetic-ru-2026-v01") is None


def test_combined_ecology_treatment_fixture_fails_closed_until_supported() -> None:
    from dataclasses import replace

    class CombinedProvider:
        def load(
            self, *, country: CountryCode, territory_id: str, scenario_id: str
        ) -> SyntheticScenario | None:
            original = SyntheticFixtureProvider().load(
                country=country, territory_id=territory_id, scenario_id=scenario_id
            )
            if original is None:
                return None
            # Nonempty ecology input must not cause the treatment inspector to be skipped.
            return replace(original, ecology_zones=(self._zone(),))

        @staticmethod
        def _zone() -> EcologyZone:
            geometry: PolygonWgs84 = {
                "type": "Polygon",
                "coordinates": [[(31.9, 53.9), (32.1, 53.9), (32.1, 54.1), (31.9, 53.9)]],
            }
            return EcologyZone(
                evidence_id="fixture-restriction",
                rule_id="fictional-rule",
                kind=EcologyEvidenceKind.DEMO_RESTRICTION,
                geometry=geometry,
            )

    service = InMemoryInvestigationService(
        CombinedProvider(), treatment_planner_factory=_fixture_planner
    )
    queued = service.submit(_request())
    service.process(queued.id)
    result = service.get(queued.id)
    assert result is not None
    assert result.status is InvestigationStatus.FAILED
    assert result.plan is None and result.treatment_review is None


def test_treatment_screening_respects_requested_season_not_unused_forage_days() -> None:
    service = InMemoryInvestigationService(
        SyntheticFixtureProvider(), treatment_planner_factory=_fixture_planner
    )
    request = _request()
    from dataclasses import replace

    request = replace(request, season=TimeWindow(date(2026, 6, 10), date(2026, 8, 15)))
    queued = service.submit(request)
    service.process(queued.id)
    result = service.get(queued.id)
    assert result is not None and result.status is InvestigationStatus.COMPLETED
    assert result.treatment_review is not None
    assert result.treatment_review.avoided_site_ids == ()
    assert result.plan is not None
    assert result.plan.stops[0].site_id == "fixture-site-alpha"
    assert result.plan.stops[0].window.start == date(2026, 6, 10)
