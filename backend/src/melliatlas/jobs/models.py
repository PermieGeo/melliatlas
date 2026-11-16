"""Typed investigation lifecycle values, diagnostics and persistence failures."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from melliatlas.agent.api import ReplanResult
from melliatlas.planning.api import EvidenceSummary, SeasonPlan, TimeWindow, TreatmentReview
from melliatlas.territories.api import CountryCode


class InvestigationStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InvestigationOutcomeKind(StrEnum):
    PLAN_FOUND = "PLAN_FOUND"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NO_FEASIBLE_ALTERNATIVE = "NO_FEASIBLE_ALTERNATIVE"


@dataclass(frozen=True)
class InvestigationRequest:
    country: CountryCode
    territory_id: str
    scenario_id: str
    season: TimeWindow
    starting_point: tuple[float, float] | None


@dataclass(frozen=True)
class InvestigationSnapshot:
    id: UUID
    status: InvestigationStatus
    request: InvestigationRequest
    created_at: datetime
    updated_at: datetime
    reference_version: str
    limitations: tuple[str, ...]
    outcome: InvestigationOutcomeKind | None = None
    plan: SeasonPlan | None = None
    evidence: tuple[EvidenceSummary, ...] = ()
    decision_trace: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    replanning: ReplanResult | None = None
    treatment_review: TreatmentReview | None = None


class InvalidInvestigationRequest(ValueError):
    pass


class InvestigationStorageError(RuntimeError):
    """Persistence failed; the public HTTP error must not expose database details."""
