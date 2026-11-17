"""One authoritative mapping from planner outcomes to investigation outcomes."""

from types import MappingProxyType
from typing import Final, Mapping

from melliatlas.agent.api import ReplanOutcome

from .models import InvestigationOutcomeKind

REPLAN_OUTCOME_TO_INVESTIGATION: Final[Mapping[ReplanOutcome, InvestigationOutcomeKind]] = (
    MappingProxyType(
        {
            ReplanOutcome.PLAN_FOUND: InvestigationOutcomeKind.PLAN_FOUND,
            ReplanOutcome.NO_FEASIBLE_ALTERNATIVE: InvestigationOutcomeKind.NO_FEASIBLE_ALTERNATIVE,
            ReplanOutcome.CHECK_LIMIT_REACHED: InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE,
        }
    )
)
