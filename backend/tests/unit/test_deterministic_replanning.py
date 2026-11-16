"""Contract tests for bounded fictional ecology-driven replanning."""

from dataclasses import replace
from datetime import date
from itertools import permutations

import pytest

from melliatlas.agent import (
    DeterministicPlanner,
    ReplanDecisionKind,
    ReplanOutcome,
    SiteInspector,
)
from melliatlas.analyzers import find_ecology_overlaps
from melliatlas.planning import (
    CandidateSite,
    EcologyEvidenceKind,
    EcologyStatus,
    EcologyZone,
    SiteAssessment,
    TimeWindow,
    assess_ecology,
)

SEASON = TimeWindow(date(2026, 5, 1), date(2026, 8, 1))


def _site(identifier: str, longitude: float, start: date, end: date) -> CandidateSite:
    return CandidateSite(
        id=identifier,
        longitude=longitude,
        latitude=54.0,
        forage_window=TimeWindow(start, end),
        forage_level="MEDIUM",
        evidence_id=f"forage-{identifier}",
    )


def _candidates() -> tuple[CandidateSite, ...]:
    return (
        _site("alpha", 32.0, date(2026, 5, 1), date(2026, 5, 31)),
        _site("beta", 32.2, date(2026, 5, 1), date(2026, 5, 31)),
        _site("gamma", 32.4, date(2026, 6, 1), date(2026, 6, 30)),
        _site("delta", 32.6, date(2026, 7, 1), date(2026, 7, 31)),
    )


def _zone(
    kind: EcologyEvidenceKind,
    identifier: str,
    left: float,
    right: float,
) -> EcologyZone:
    return EcologyZone(
        evidence_id=identifier,
        rule_id=f"rule-{identifier}",
        kind=kind,
        geometry={
            "type": "Polygon",
            "coordinates": [
                [(left, 53.9), (right, 53.9), (right, 54.1), (left, 54.1), (left, 53.9)]
            ],
        },
    )


def _inspector(zones: tuple[EcologyZone, ...]) -> SiteInspector:
    def inspect(site: CandidateSite) -> SiteAssessment:
        return assess_ecology(site.id, find_ecology_overlaps(site, zones))

    return inspect


def _zones() -> tuple[EcologyZone, ...]:
    return (
        _zone(EcologyEvidenceKind.DEMO_PRECAUTION, "caution", 31.9, 32.7),
        _zone(EcologyEvidenceKind.DEMO_RESTRICTION, "exclusion", 31.95, 32.05),
    )


def test_evidence_exclusion_causes_observed_revision_and_alternative() -> None:
    result = DeterministicPlanner(_inspector(_zones())).plan(_candidates(), SEASON)
    assert result.outcome is ReplanOutcome.PLAN_FOUND
    assert result.plan is not None
    assert [stop.site_id for stop in result.plan.stops] == ["beta", "gamma", "delta"]
    assert result.excluded_site_ids == ("alpha",)
    assert result.checks_used == 4
    assert result.assessments[0].status is EcologyStatus.EXCLUDED
    assert all(a.status is EcologyStatus.CAUTION for a in result.assessments[1:])
    assert [event.kind for event in result.trace] == [
        ReplanDecisionKind.INITIAL,
        *([ReplanDecisionKind.ECOLOGY_CHECK] * 4),
        ReplanDecisionKind.REVISION,
        ReplanDecisionKind.TERMINAL,
    ]
    assert any("exclusion" in event.evidence_ids for event in result.trace)
    assert any("caution" in event.evidence_ids for event in result.trace)
    assert result.warnings


def test_input_permutations_do_not_change_plan_or_trace() -> None:
    expected = DeterministicPlanner(_inspector(_zones())).plan(_candidates(), SEASON)
    for reordered in permutations(_candidates()):
        assert DeterministicPlanner(_inspector(_zones())).plan(reordered, SEASON) == expected


def test_renaming_excluded_candidate_cannot_bypass_geometry_rule() -> None:
    sites = (replace(_candidates()[0], id="zz-renamed"), *_candidates()[1:])
    result = DeterministicPlanner(_inspector(_zones())).plan(sites, SEASON)
    assert result.outcome is ReplanOutcome.PLAN_FOUND
    assert result.plan is not None
    assert [stop.site_id for stop in result.plan.stops] == ["beta", "gamma", "delta"]
    assert result.excluded_site_ids == ("zz-renamed",)


def test_precaution_is_not_prohibition_and_is_recorded() -> None:
    warning_only = (_zone(EcologyEvidenceKind.DEMO_PRECAUTION, "warning", 31.9, 32.7),)
    result = DeterministicPlanner(_inspector(warning_only)).plan(_candidates(), SEASON)
    assert result.outcome is ReplanOutcome.PLAN_FOUND
    assert result.excluded_site_ids == ()
    assert result.plan is not None
    assert result.plan.stops[0].site_id == "alpha"
    assert all(item.status is EcologyStatus.CAUTION for item in result.assessments)
    assert any("CAUTION" in note for note in result.warnings)
    assert all(event.kind is not ReplanDecisionKind.REVISION for event in result.trace)


def test_unknown_coverage_is_not_silently_promoted_to_eligible() -> None:
    only_exclusion = (_zone(EcologyEvidenceKind.DEMO_RESTRICTION, "exclusion", 31.95, 32.05),)
    result = DeterministicPlanner(_inspector(only_exclusion)).plan(_candidates(), SEASON)
    assert result.outcome is ReplanOutcome.NO_FEASIBLE_ALTERNATIVE
    assert result.plan is None
    assert result.excluded_site_ids == ("alpha",)
    assert result.unknown_site_ids == ("beta", "gamma", "delta")
    assert any("UNKNOWN" in note for note in result.warnings)


def test_check_limit_stops_without_recommending_unchecked_sites() -> None:
    checked: list[str] = []

    def inspect(site: CandidateSite) -> SiteAssessment:
        checked.append(site.id)
        return _inspector(_zones())(site)

    result = DeterministicPlanner(inspect, max_checks=2).plan(_candidates(), SEASON)
    assert checked == ["alpha", "beta"]
    assert result.outcome is ReplanOutcome.CHECK_LIMIT_REACHED
    assert result.checks_used == 2
    assert result.plan is None
    assert result.trace[-1].kind is ReplanDecisionKind.LIMIT_REACHED


def test_no_two_stop_base_plan_is_not_a_technical_failure() -> None:
    only_one = (_candidates()[0],)
    result = DeterministicPlanner(_inspector(_zones())).plan(only_one, SEASON)
    assert result.outcome is ReplanOutcome.NO_FEASIBLE_ALTERNATIVE
    assert result.checks_used == 0
    assert result.plan is None


def test_mismatched_inspection_identity_fails_closed() -> None:
    def wrong_identity(site: CandidateSite) -> SiteAssessment:
        return replace(_inspector(_zones())(site), site_id="wrong")

    with pytest.raises(ValueError, match="site ID"):
        DeterministicPlanner(wrong_identity).plan(_candidates(), SEASON)


def test_invalid_budget_duplicate_site_and_bad_coordinates_are_rejected() -> None:
    with pytest.raises(ValueError, match="max_checks"):
        DeterministicPlanner(_inspector(_zones()), max_checks=0)
    with pytest.raises(ValueError, match="max_checks"):
        DeterministicPlanner(_inspector(_zones()), max_checks=True)
    duplicates = (_candidates()[0], _candidates()[0], *_candidates()[2:])
    with pytest.raises(ValueError, match="Duplicate"):
        DeterministicPlanner(_inspector(_zones())).plan(duplicates, SEASON)
    invalid = (replace(_candidates()[0], longitude=float("inf")), *_candidates()[1:])
    with pytest.raises(ValueError, match="coordinate"):
        DeterministicPlanner(_inspector(_zones())).plan(invalid, SEASON)


def test_observation_failure_does_not_create_a_fallback_plan() -> None:
    def unavailable(_site: CandidateSite) -> SiteAssessment:
        raise RuntimeError("No fictional evidence available")

    with pytest.raises(RuntimeError, match="evidence"):
        DeterministicPlanner(unavailable).plan(_candidates(), SEASON)


def test_unsubstantiated_positive_verdict_and_caution_are_rejected() -> None:
    def unsupported(site: CandidateSite) -> SiteAssessment:
        return replace(_inspector(_zones())(site), status=EcologyStatus.ELIGIBLE)

    with pytest.raises(ValueError, match="ELIGIBLE"):
        DeterministicPlanner(unsupported).plan(_candidates(), SEASON)

    def missing_provenance(site: CandidateSite) -> SiteAssessment:
        return replace(_inspector(_zones())(site), evidence_ids=())

    with pytest.raises(ValueError, match="evidence"):
        DeterministicPlanner(missing_provenance).plan(_candidates(), SEASON)
