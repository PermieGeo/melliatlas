"""Public non-durable investigation lifecycle for the V01 synthetic slice."""

import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock
from typing import Protocol
from uuid import UUID, uuid4

from melliatlas.planning.api import (
    EvidenceSummary,
    SeasonPlan,
    SyntheticScenario,
    TimeWindow,
    build_season_plan,
)
from melliatlas.territories.api import CountryCode

_LOGGER = logging.getLogger(__name__)


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


class InvalidInvestigationRequest(ValueError):
    pass


class ScenarioProvider(Protocol):
    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None: ...


class InvestigationService(Protocol):
    def submit(self, request: InvestigationRequest) -> InvestigationSnapshot: ...
    def get(self, identifier: UUID) -> InvestigationSnapshot | None: ...
    def process(self, identifier: UUID) -> None: ...


class InMemoryInvestigationService:
    """Development-only store scoped to one app; completed snapshots are never rewritten."""

    def __init__(self, provider: ScenarioProvider) -> None:
        self._provider = provider
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
            return self._records.get(identifier)

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
            finished = replace(
                current,
                status=InvestigationStatus.COMPLETED,
                updated_at=datetime.now(timezone.utc),
                outcome=outcome,
                plan=plan,
                evidence=scenario.evidence,
                decision_trace=trace,
                diagnostics=diagnostics,
            )
        except Exception:
            _LOGGER.exception("Synthetic investigation processing failed")
            finished = replace(
                current,
                status=InvestigationStatus.FAILED,
                updated_at=datetime.now(timezone.utc),
                diagnostics=("Synthetic analysis failed",),
            )
        with self._lock:
            self._records[identifier] = finished
            del self._pending[identifier]
