"""Tests for typed completed-snapshot round trips independent of any database."""

import json
from datetime import date

import pytest

from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    deserialize_completed_snapshot,
    serialize_completed_snapshot,
)
from melliatlas.planning.api import TimeWindow
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.territories.api import CountryCode


def _completed(*, evidence_limited: bool = False) -> InvestigationSnapshot:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    request = InvestigationRequest(
        country=CountryCode.RU,
        territory_id="ru:region:smolensk",
        scenario_id=SYNTHETIC_SCENARIO_ID,
        season=TimeWindow(
            date(2026, 5, 10),
            date(2026, 5, 10) if evidence_limited else date(2026, 8, 15),
        ),
        starting_point=(32.0, 54.0),
    )
    queued = service.submit(request)
    service.process(queued.id)
    finished = service.get(queued.id)
    assert finished is not None
    return finished


@pytest.mark.parametrize("evidence_limited", [False, True])
def test_roundtrip_preserves_typed_result_and_private_start(evidence_limited: bool) -> None:
    original = _completed(evidence_limited=evidence_limited)
    restored = deserialize_completed_snapshot(serialize_completed_snapshot(original))
    assert restored == original
    assert restored.status == InvestigationStatus.COMPLETED
    assert restored.request.starting_point == (32.0, 54.0)
    assert restored.outcome == (
        InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
        if evidence_limited
        else InvestigationOutcomeKind.PLAN_FOUND
    )


def test_codec_refuses_non_completed_and_malformed_payloads() -> None:
    service = InMemoryInvestigationService(SyntheticFixtureProvider())
    pending = service.submit(
        InvestigationRequest(
            CountryCode.RU,
            "ru:region:smolensk",
            SYNTHETIC_SCENARIO_ID,
            TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            None,
        )
    )
    with pytest.raises(ValueError, match="Only completed"):
        serialize_completed_snapshot(pending)
    with pytest.raises((ValueError, TypeError)):
        deserialize_completed_snapshot("[]")
    with pytest.raises((ValueError, KeyError)):
        deserialize_completed_snapshot('{"status":"COMPLETED"}')
    with pytest.raises(ValueError, match="not a completed"):
        deserialize_completed_snapshot(
            serialize_completed_snapshot(_completed()).replace(
                '"status": "COMPLETED"', '"status": "RUNNING"'
            )
        )


@pytest.mark.parametrize(
    ("section", "field", "bad_value"),
    [
        ("request", "starting_point", [32.0]),
        ("request", "starting_point", [True, 54.0]),
        ("request", "season", "2026-06-01"),
        ("plan", "relocations", "1"),
        ("plan", "stops", "not-a-list"),
        ("evidence", "synthetic", False),
        ("evidence", "source_mode", "LIVE"),
    ],
)
def test_codec_rejects_malformed_nested_fields(section: str, field: str, bad_value: object) -> None:
    payload = json.loads(serialize_completed_snapshot(_completed()))
    if section == "evidence":
        payload["evidence"][0][field] = bad_value
    else:
        payload[section][field] = bad_value
    with pytest.raises((ValueError, TypeError)):
        deserialize_completed_snapshot(json.dumps(payload))


def test_codec_rejects_bad_snapshot_object_and_nonfinite_coordinate() -> None:
    original = json.loads(serialize_completed_snapshot(_completed()))
    original["request"]["starting_point"] = [float("nan"), 54.0]
    with pytest.raises(ValueError, match="finite number"):
        deserialize_completed_snapshot(json.dumps(original))


def _completed_ecology() -> InvestigationSnapshot:
    from melliatlas.agent.api import DeterministicPlanner
    from melliatlas.analyzers.api import find_ecology_overlaps
    from melliatlas.planning.api import (
        CandidateSite,
        SiteAssessment,
        SyntheticScenario,
        assess_ecology,
    )
    from melliatlas.sources.providers.synthetic.api import SYNTHETIC_ECOLOGY_SCENARIO_ID

    def factory(scenario: SyntheticScenario) -> DeterministicPlanner:
        def inspect(site: CandidateSite) -> SiteAssessment:
            return assess_ecology(site.id, find_ecology_overlaps(site, scenario.ecology_zones))

        return DeterministicPlanner(inspect)

    service = InMemoryInvestigationService(SyntheticFixtureProvider(), replan_factory=factory)
    queued = service.submit(
        InvestigationRequest(
            CountryCode.RU,
            "ru:region:smolensk",
            SYNTHETIC_ECOLOGY_SCENARIO_ID,
            TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            (32.0, 54.0),
        )
    )
    service.process(queued.id)
    snapshot = service.get(queued.id)
    assert snapshot is not None
    assert snapshot.status is InvestigationStatus.COMPLETED
    assert snapshot.replanning is not None
    return snapshot


def test_ecology_snapshot_codec_roundtrip_restores_typed_decisions_and_plan() -> None:
    from melliatlas.agent.api import ReplanDecisionKind, ReplanOutcome
    from melliatlas.planning.api import EcologyStatus

    original = _completed_ecology()
    restored = deserialize_completed_snapshot(serialize_completed_snapshot(original))
    assert restored == original
    assert restored.replanning is not None
    assert restored.replanning.outcome is ReplanOutcome.PLAN_FOUND
    assert restored.replanning.assessments[0].status is EcologyStatus.EXCLUDED
    assert restored.replanning.trace[-2].kind is ReplanDecisionKind.REVISION
    assert restored.plan == restored.replanning.plan


def test_legacy_snapshot_without_replanning_stays_readable_and_unchanged() -> None:
    original = _completed()
    payload = serialize_completed_snapshot(original)
    assert '"replanning"' not in payload
    assert deserialize_completed_snapshot(payload) == original


@pytest.mark.parametrize(
    ("section", "field", "bad_value"),
    [
        ("replanning", "checks_used", "four"),
        ("replanning", "outcome", "REAL_ECOLOGY_SAFE"),
        ("assessment", "status", "ELIGIBLE_REAL"),
        ("assessment", "synthetic", False),
        ("decision", "kind", "NONE"),
        ("decision", "evidence_ids", "not-a-list"),
    ],
)
def test_codec_rejects_malformed_replanning_fields(
    section: str, field: str, bad_value: object
) -> None:
    payload = json.loads(serialize_completed_snapshot(_completed_ecology()))
    if section == "assessment":
        payload["replanning"]["assessments"][0][field] = bad_value
    elif section == "decision":
        payload["replanning"]["trace"][0][field] = bad_value
    else:
        payload["replanning"][field] = bad_value
    with pytest.raises((ValueError, TypeError)):
        deserialize_completed_snapshot(json.dumps(payload))


def test_codec_rejects_replanning_plan_divergence() -> None:
    payload = json.loads(serialize_completed_snapshot(_completed_ecology()))
    payload["replanning"]["plan"]["stops"][0]["site_id"] = "forged"
    with pytest.raises(ValueError, match="disagrees"):
        deserialize_completed_snapshot(json.dumps(payload))


def test_ecology_completed_snapshot_roundtrips_through_completed_store_port() -> None:
    from uuid import UUID

    from melliatlas.agent.api import DeterministicPlanner
    from melliatlas.analyzers.api import find_ecology_overlaps
    from melliatlas.planning.api import (
        CandidateSite,
        SiteAssessment,
        SyntheticScenario,
        assess_ecology,
    )
    from melliatlas.sources.providers.synthetic.api import SYNTHETIC_ECOLOGY_SCENARIO_ID

    class SerializedStore:
        def __init__(self) -> None:
            self.saved: dict[UUID, str] = {}

        def save(self, snapshot: InvestigationSnapshot) -> None:
            self.saved[snapshot.id] = serialize_completed_snapshot(snapshot)

        def load(self, identifier: UUID) -> InvestigationSnapshot | None:
            value = self.saved.get(identifier)
            return deserialize_completed_snapshot(value) if value is not None else None

    def factory(scenario: SyntheticScenario) -> DeterministicPlanner:
        def inspect(site: CandidateSite) -> SiteAssessment:
            return assess_ecology(site.id, find_ecology_overlaps(site, scenario.ecology_zones))

        return DeterministicPlanner(inspect)

    store = SerializedStore()
    first = InMemoryInvestigationService(SyntheticFixtureProvider(), store, replan_factory=factory)
    queued = first.submit(
        InvestigationRequest(
            CountryCode.RU,
            "ru:region:smolensk",
            SYNTHETIC_ECOLOGY_SCENARIO_ID,
            TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            None,
        )
    )
    first.process(queued.id)
    original = first.get(queued.id)
    assert original is not None
    assert original.status is InvestigationStatus.COMPLETED
    reopened = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    assert reopened.record_count == 0
    assert reopened.get(queued.id) == original
