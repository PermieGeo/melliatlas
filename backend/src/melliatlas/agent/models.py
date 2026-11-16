"""Typed replanning decisions, check outcomes, and synthetic observation results."""

from dataclasses import dataclass
from enum import StrEnum

from melliatlas.planning.api import SeasonPlan, SiteAssessment, TreatmentReview


class ReplanOutcome(StrEnum):
    PLAN_FOUND = "PLAN_FOUND"
    NO_FEASIBLE_ALTERNATIVE = "NO_FEASIBLE_ALTERNATIVE"
    CHECK_LIMIT_REACHED = "CHECK_LIMIT_REACHED"


class ReplanDecisionKind(StrEnum):
    INITIAL = "INITIAL"
    ECOLOGY_CHECK = "ECOLOGY_CHECK"
    TREATMENT_CHECK = "TREATMENT_CHECK"
    REVISION = "REVISION"
    TERMINAL = "TERMINAL"
    LIMIT_REACHED = "LIMIT_REACHED"


@dataclass(frozen=True)
class ReplanDecision:
    kind: ReplanDecisionKind
    site_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    rule_ids: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class ReplanResult:
    outcome: ReplanOutcome
    plan: SeasonPlan | None
    assessments: tuple[SiteAssessment, ...]
    excluded_site_ids: tuple[str, ...]
    unknown_site_ids: tuple[str, ...]
    trace: tuple[ReplanDecision, ...]
    checks_used: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class TreatmentPlanningResult:
    plan: SeasonPlan | None
    review: TreatmentReview
    trace: tuple[str, ...]


@dataclass(frozen=True)
class CombinedPlanningResult:
    replanning: ReplanResult
    treatment_review: TreatmentReview
