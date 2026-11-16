"""Bounded and deterministic ecological replanning over injected observations."""

from math import isfinite

from melliatlas.planning import (
    CandidateSite,
    EcologyStatus,
    SiteAssessment,
    TimeWindow,
    build_season_plan,
)

from .api import SiteInspector
from .models import ReplanDecision, ReplanDecisionKind, ReplanOutcome, ReplanResult


def _checked_assessment(value: object, expected_site_id: str) -> SiteAssessment:
    if not isinstance(value, SiteAssessment) or value.site_id != expected_site_id:
        raise ValueError("Inspector returned a mismatched site ID or invalid assessment")
    return value


class DeterministicPlanner:
    """Replan fictional forage proposals only after bounded ecological checks."""

    def __init__(self, inspect: SiteInspector, *, max_checks: int = 16) -> None:
        if type(max_checks) is not int or max_checks < 1:
            raise ValueError("max_checks must be a positive integer")
        self._inspect = inspect
        self._max_checks = max_checks

    def plan(self, candidates: tuple[CandidateSite, ...], season: TimeWindow) -> ReplanResult:
        seen: set[str] = set()
        for site in candidates:
            if not site.id.strip():
                raise ValueError("Candidate site ID must not be empty")
            if site.id in seen:
                raise ValueError("Duplicate candidate site ID")
            seen.add(site.id)
            if not (
                isfinite(site.longitude)
                and isfinite(site.latitude)
                and -180 <= site.longitude <= 180
                and -90 <= site.latitude <= 90
            ):
                raise ValueError("Candidate site coordinate must be finite WGS84")

        ordered = tuple(sorted(candidates, key=lambda item: (item.forage_window.start, item.id)))
        initial = build_season_plan(ordered, season)
        initial_ids = tuple(stop.site_id for stop in initial.stops) if initial else ()
        trace = [
            ReplanDecision(
                ReplanDecisionKind.INITIAL,
                initial_ids,
                (),
                (),
                "Initial deterministic fictional forage proposal",
            )
        ]
        warnings = ["Fictional ecology checks do not establish real-world site eligibility"]
        if initial is None:
            trace.append(
                ReplanDecision(
                    ReplanDecisionKind.TERMINAL,
                    (),
                    (),
                    (),
                    "Fewer than two chronological forage stops are supported",
                )
            )
            return ReplanResult(
                ReplanOutcome.NO_FEASIBLE_ALTERNATIVE,
                None,
                (),
                (),
                (),
                tuple(trace),
                0,
                tuple(warnings),
            )

        assessments: list[SiteAssessment] = []
        for site in ordered[: self._max_checks]:
            assessment = _checked_assessment(self._inspect(site), site.id)
            if assessment.synthetic is not True:
                raise ValueError("Inspector returned non-synthetic ecology evidence")
            if assessment.status is EcologyStatus.ELIGIBLE:
                raise ValueError("ELIGIBLE requires independently verified ecology coverage")
            if assessment.status in (EcologyStatus.EXCLUDED, EcologyStatus.CAUTION) and (
                not assessment.evidence_ids or not assessment.rule_ids
            ):
                raise ValueError("An exclusion or caution must retain evidence and rule IDs")
            assessments.append(assessment)
            trace.append(
                ReplanDecision(
                    ReplanDecisionKind.ECOLOGY_CHECK,
                    (site.id,),
                    assessment.evidence_ids,
                    assessment.rule_ids,
                    f"Observed fictional ecology status {assessment.status.value}",
                )
            )

        excluded_ids = tuple(
            item.site_id for item in assessments if item.status is EcologyStatus.EXCLUDED
        )
        unknown_ids = tuple(
            item.site_id for item in assessments if item.status is EcologyStatus.UNKNOWN
        )
        if any(item.status is EcologyStatus.CAUTION for item in assessments):
            warnings.append("CAUTION is non-binding and requires ecological review")
        if unknown_ids:
            warnings.append("UNKNOWN ecology coverage cannot be treated as eligible")

        if len(assessments) < len(ordered):
            trace.append(
                ReplanDecision(
                    ReplanDecisionKind.LIMIT_REACHED,
                    tuple(item.id for item in ordered[len(assessments) :]),
                    (),
                    (),
                    "Ecology check limit reached; unchecked sites cannot be recommended",
                )
            )
            return ReplanResult(
                ReplanOutcome.CHECK_LIMIT_REACHED,
                None,
                tuple(assessments),
                excluded_ids,
                unknown_ids,
                tuple(trace),
                len(assessments),
                tuple(warnings),
            )

        inspected = {item.site_id: item for item in assessments}
        qualified = tuple(
            site for site in ordered if inspected[site.id].status is EcologyStatus.CAUTION
        )
        revised = build_season_plan(qualified, season)
        revised_ids = tuple(stop.site_id for stop in revised.stops) if revised else ()
        if revised_ids != initial_ids:
            changed = tuple(sorted(set(initial_ids) - set(revised_ids)))
            relevant = tuple(item for item in assessments if item.site_id in changed)
            trace.append(
                ReplanDecision(
                    ReplanDecisionKind.REVISION,
                    revised_ids,
                    tuple(dict.fromkeys(e for item in relevant for e in item.evidence_ids)),
                    tuple(dict.fromkeys(r for item in relevant for r in item.rule_ids)),
                    "Revised fictional forage proposal after observed ecology findings",
                )
            )

        outcome = (
            ReplanOutcome.PLAN_FOUND
            if revised is not None
            else ReplanOutcome.NO_FEASIBLE_ALTERNATIVE
        )
        trace.append(
            ReplanDecision(
                ReplanDecisionKind.TERMINAL,
                revised_ids,
                (),
                (),
                "Qualified fictional plan with explicit ecology limitations"
                if revised is not None
                else "Fewer than two ecology-qualified stops remain",
            )
        )
        return ReplanResult(
            outcome,
            revised,
            tuple(assessments),
            excluded_ids,
            unknown_ids,
            tuple(trace),
            len(assessments),
            tuple(warnings),
        )
