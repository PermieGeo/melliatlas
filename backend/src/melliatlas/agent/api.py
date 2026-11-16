"""Public observation and planner contracts for the agent capability.

Callers inject typed inspectors; implementations need not inherit these Protocols.
The domain result values are stable and shared across alternative planners.
"""

from typing import Protocol

from melliatlas.planning import CandidateSite, SiteAssessment, TimeWindow, TreatmentScreening

from .models import (
    CombinedPlanningResult,
    ReplanDecision,
    ReplanDecisionKind,
    ReplanOutcome,
    ReplanResult,
    TreatmentPlanningResult,
)


class SiteInspector(Protocol):
    """Inspect a site positionally; callback parameter names are not contractual."""

    def __call__(self, site: CandidateSite, /) -> SiteAssessment: ...


class TreatmentInspector(Protocol):
    """Inspect one candidate positionally without constraining callback parameter names."""

    def __call__(self, site: CandidateSite, /) -> tuple[TreatmentScreening, ...]: ...


class EcologyPlanner(Protocol):
    """Ecology planning boundary used for dependency injection."""

    def plan(self, candidates: tuple[CandidateSite, ...], season: TimeWindow) -> ReplanResult: ...


class TreatmentPlannerPort(Protocol):
    """Treatment planning boundary used for dependency injection."""

    def plan(
        self, candidates: tuple[CandidateSite, ...], season: TimeWindow
    ) -> TreatmentPlanningResult: ...


__all__ = [
    "ReplanOutcome",
    "ReplanDecisionKind",
    "ReplanDecision",
    "ReplanResult",
    "TreatmentPlanningResult",
    "CombinedPlanningResult",
    "SiteInspector",
    "TreatmentInspector",
    "EcologyPlanner",
    "TreatmentPlannerPort",
]
