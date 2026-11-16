"""Combine attributed fictional ecology and treatment results without skipping either."""

from dataclasses import replace

from melliatlas.planning import CandidateSite, EcologyStatus, TimeWindow, build_season_plan

from .api import EcologyPlanner, TreatmentPlannerPort
from .models import CombinedPlanningResult, ReplanDecision, ReplanDecisionKind, ReplanOutcome


class CombinedPlanner:
    """Combine bounded fictional checks without treating either as a safety certificate."""

    def __init__(self, ecology: EcologyPlanner, treatment: TreatmentPlannerPort) -> None:
        self._ecology = ecology
        self._treatment = treatment

    def plan(
        self, candidates: tuple[CandidateSite, ...], season: TimeWindow
    ) -> CombinedPlanningResult:
        active = tuple(
            site
            for site in candidates
            if site.forage_window.start <= season.end and site.forage_window.end >= season.start
        )
        ecology = self._ecology.plan(active, season)
        treatment = self._treatment.plan(active, season)
        qualified = {
            item.site_id for item in ecology.assessments if item.status is EcologyStatus.CAUTION
        }
        avoided = set(treatment.review.avoided_site_ids)
        plan = (
            None
            if ecology.outcome is ReplanOutcome.CHECK_LIMIT_REACHED
            else build_season_plan(
                tuple(site for site in active if site.id in qualified and site.id not in avoided),
                season,
            )
        )
        outcome = (
            ReplanOutcome.CHECK_LIMIT_REACHED
            if ecology.outcome is ReplanOutcome.CHECK_LIMIT_REACHED
            else (
                ReplanOutcome.PLAN_FOUND
                if plan is not None
                else ReplanOutcome.NO_FEASIBLE_ALTERNATIVE
            )
        )
        trace = [item for item in ecology.trace if item.kind is not ReplanDecisionKind.TERMINAL]
        for observation in treatment.review.screenings:
            trace.append(
                ReplanDecision(
                    kind=ReplanDecisionKind.TREATMENT_CHECK,
                    site_ids=(observation.site_id,),
                    evidence_ids=(observation.source_record_id,),
                    rule_ids=(),
                    note=f"Fictional field-treatment finding: {observation.proximity.value}",
                )
            )
        previous = tuple(stop.site_id for stop in ecology.plan.stops) if ecology.plan else ()
        selected = tuple(stop.site_id for stop in plan.stops) if plan else ()
        if selected != previous:
            withheld = set(previous) - set(selected)
            trace.append(
                ReplanDecision(
                    kind=ReplanDecisionKind.REVISION,
                    site_ids=selected,
                    evidence_ids=tuple(
                        dict.fromkeys(
                            item.source_record_id
                            for item in treatment.review.screenings
                            if item.site_id in withheld
                        )
                    ),
                    rule_ids=(),
                    note="Revised fictional proposal after considering both screening results",
                )
            )
        trace.append(
            ReplanDecision(
                kind=ReplanDecisionKind.TERMINAL,
                site_ids=selected,
                evidence_ids=(),
                rule_ids=(),
                note=(
                    "Provisional joint plan with unverified ecological and chemical coverage"
                    if plan is not None
                    else "No two-stop plan supported by both fictional checks"
                ),
            )
        )
        replanning = replace(
            ecology,
            outcome=outcome,
            plan=plan,
            trace=tuple(trace),
            warnings=tuple(dict.fromkeys((*ecology.warnings, *treatment.review.warnings))),
        )
        return CombinedPlanningResult(replanning, treatment.review)
