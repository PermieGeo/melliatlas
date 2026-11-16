"""In-process investigation scheduling, state transitions and optional completed storage."""

import logging
from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from melliatlas.agent import CombinedPlanner, ReplanOutcome, ReplanResult
from melliatlas.planning import SyntheticScenario, TreatmentReview, build_season_plan

from .api import (
    CompletedInvestigationStore,
    EcologyPlannerFactory,
    ScenarioProvider,
    TreatmentPlannerFactory,
)
from .models import (
    InvalidInvestigationRequest,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
)

_LOGGER = logging.getLogger(__name__)


class InMemoryInvestigationService:
    """Development-only store scoped to one app; completed snapshots are never rewritten."""

    def __init__(
        self,
        provider: ScenarioProvider,
        completed_store: CompletedInvestigationStore | None = None,
        *,
        replan_factory: EcologyPlannerFactory | None = None,
        treatment_planner_factory: TreatmentPlannerFactory | None = None,
    ) -> None:
        self._provider = provider
        self._completed_store = completed_store
        self._replan_factory = replan_factory
        self._treatment_planner_factory = treatment_planner_factory
        self._records: dict[UUID, InvestigationSnapshot] = {}
        self._pending: dict[UUID, SyntheticScenario] = {}
        self._lock = Lock()

    @property
    def record_count(self) -> int:
        with self._lock:
            return len(self._records)

    def submit(self, request: InvestigationRequest) -> InvestigationSnapshot:
        scenario = self._provider.load(
            country=request.country,
            territory_id=request.territory_id,
            scenario_id=request.scenario_id,
        )
        if scenario is None:
            raise InvalidInvestigationRequest("Unsupported synthetic scenario or territory")
        if (
            request.season.start < scenario.supported_season.start
            or request.season.end > scenario.supported_season.end
        ):
            raise InvalidInvestigationRequest("Season is outside the synthetic scenario window")
        now = datetime.now(timezone.utc)
        snapshot = InvestigationSnapshot(
            id=uuid4(),
            status=InvestigationStatus.QUEUED,
            request=request,
            created_at=now,
            updated_at=now,
            reference_version=scenario.reference_version,
            limitations=scenario.limitations,
        )
        with self._lock:
            self._records[snapshot.id] = snapshot
            self._pending[snapshot.id] = scenario
        return snapshot

    def get(self, identifier: UUID) -> InvestigationSnapshot | None:
        with self._lock:
            current = self._records.get(identifier)
        if current is not None or self._completed_store is None:
            return current
        return self._completed_store.load(identifier)

    def process(self, identifier: UUID) -> None:
        with self._lock:
            current = self._records.get(identifier)
            scenario = self._pending.get(identifier)
            if current is None or scenario is None or current.status != InvestigationStatus.QUEUED:
                return
            self._records[identifier] = replace(
                current,
                status=InvestigationStatus.RUNNING,
                updated_at=datetime.now(timezone.utc),
            )
        try:
            replanning: ReplanResult | None = None
            treatment_review: TreatmentReview | None = None
            if scenario.ecology_zones and scenario.treatment_screening_required:
                if self._replan_factory is None or self._treatment_planner_factory is None:
                    raise RuntimeError("Both fictional evaluators must be configured")
                combined = CombinedPlanner(
                    self._replan_factory(scenario),
                    self._treatment_planner_factory(scenario),
                ).plan(scenario.candidates, current.request.season)
                replanning = combined.replanning
                treatment_review = combined.treatment_review
                plan = replanning.plan
                outcome = {
                    ReplanOutcome.PLAN_FOUND: InvestigationOutcomeKind.PLAN_FOUND,
                    ReplanOutcome.NO_FEASIBLE_ALTERNATIVE: (
                        InvestigationOutcomeKind.NO_FEASIBLE_ALTERNATIVE
                    ),
                    ReplanOutcome.CHECK_LIMIT_REACHED: (
                        InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
                    ),
                }[replanning.outcome]
                trace = tuple(f"{event.kind.value}: {event.note}" for event in replanning.trace)
                diagnostics = (
                    ()
                    if plan is not None
                    else ("Combined fictional checks cannot support a two-stop proposal",)
                )
                limitations = current.limitations + replanning.warnings
            elif scenario.ecology_zones:
                if self._replan_factory is None:
                    raise RuntimeError("Fictional ecology evaluator has not been configured")
                replanning = self._replan_factory(scenario).plan(
                    scenario.candidates, current.request.season
                )
                plan = replanning.plan
                outcome = {
                    ReplanOutcome.PLAN_FOUND: InvestigationOutcomeKind.PLAN_FOUND,
                    ReplanOutcome.NO_FEASIBLE_ALTERNATIVE: (
                        InvestigationOutcomeKind.NO_FEASIBLE_ALTERNATIVE
                    ),
                    ReplanOutcome.CHECK_LIMIT_REACHED: (
                        InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
                    ),
                }[replanning.outcome]
                trace = tuple(f"{event.kind.value}: {event.note}" for event in replanning.trace)
                diagnostics = (
                    ()
                    if plan is not None
                    else ("Fictional ecology evidence cannot support a qualified plan",)
                )
                limitations = current.limitations + replanning.warnings
            elif scenario.treatment_screening_required:
                if self._treatment_planner_factory is None:
                    raise RuntimeError("Fictional treatment screening has not been configured")
                treatment_result = self._treatment_planner_factory(scenario).plan(
                    scenario.candidates, current.request.season
                )
                plan = treatment_result.plan
                treatment_review = treatment_result.review
                outcome = (
                    InvestigationOutcomeKind.PLAN_FOUND
                    if plan is not None
                    else InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
                )
                trace = treatment_result.trace
                diagnostics = (
                    ()
                    if plan is not None
                    else ("Fictional treatment screening left fewer than two candidate stops",)
                )
                limitations = current.limitations + treatment_review.warnings
            else:
                plan = build_season_plan(scenario.candidates, current.request.season)
                outcome = (
                    InvestigationOutcomeKind.PLAN_FOUND
                    if plan is not None
                    else InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
                )
                trace = (
                    "Sorted synthetic forage windows by date and stable candidate ID",
                    "Selected at least two non-overlapping fixture stops"
                    if plan is not None
                    else "Fewer than two fixture stops intersect the requested season",
                )
                diagnostics = (
                    ()
                    if plan is not None
                    else (
                        "Synthetic forage evidence cannot support a two-stop proposal for this window",
                    )
                )
                limitations = current.limitations
            finished = replace(
                current,
                status=InvestigationStatus.COMPLETED,
                updated_at=datetime.now(timezone.utc),
                outcome=outcome,
                plan=plan,
                evidence=scenario.evidence,
                decision_trace=trace,
                diagnostics=diagnostics,
                limitations=limitations,
                replanning=replanning,
                treatment_review=treatment_review,
            )
        except Exception:
            _LOGGER.exception("Synthetic investigation processing failed")
            finished = replace(
                current,
                status=InvestigationStatus.FAILED,
                updated_at=datetime.now(timezone.utc),
                diagnostics=("Synthetic analysis failed",),
            )
        if finished.status is InvestigationStatus.COMPLETED and self._completed_store is not None:
            try:
                self._completed_store.save(finished)
            except Exception:
                _LOGGER.exception("Failed to persist completed synthetic investigation")
                finished = replace(
                    current,
                    status=InvestigationStatus.FAILED,
                    updated_at=datetime.now(timezone.utc),
                    diagnostics=("Investigation persistence failed",),
                )
        with self._lock:
            self._records[identifier] = finished
            del self._pending[identifier]
