"""Public non-durable investigation lifecycle for the V01 synthetic slice."""

import json
import logging
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from enum import StrEnum
from math import isfinite
from threading import Lock
from typing import Literal, Protocol, TypeGuard
from uuid import UUID, uuid4

from melliatlas.planning.api import (
    EvidenceSummary,
    SeasonPlan,
    SeasonStop,
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


class InvestigationStorageError(RuntimeError):
    """Persistence failed; the public HTTP error must not expose database details."""


class CompletedInvestigationStore(Protocol):
    """Durable completed snapshots; in-flight jobs are intentionally not persisted."""

    def save(self, snapshot: InvestigationSnapshot) -> None: ...
    def load(self, identifier: UUID) -> InvestigationSnapshot | None: ...


def serialize_completed_snapshot(snapshot: InvestigationSnapshot) -> str:
    """Encode a terminal successful calculation without exposing transport DTOs."""
    if snapshot.status is not InvestigationStatus.COMPLETED or snapshot.outcome is None:
        raise ValueError("Only completed investigations with a domain outcome can be stored")

    def encode_temporal(value: object) -> str:
        if isinstance(value, (date, datetime, UUID)):
            return str(value) if isinstance(value, UUID) else value.isoformat()
        raise TypeError(f"Unsupported snapshot field: {type(value).__name__}")

    return json.dumps(asdict(snapshot), default=encode_temporal, sort_keys=True, allow_nan=False)


def _is_object_dict(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _stored_object(value: object, field: str) -> dict[str, object]:
    """Validate JSON object shape before accessing persisted fields."""
    if not _is_object_dict(value):
        raise ValueError(f"Stored {field} must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"Stored {field} contains a non-string key")
        result[key] = item
    return result


def _stored_list(value: object, field: str) -> list[object]:
    if not _is_object_list(value):
        raise ValueError(f"Stored {field} must be a list")
    return value


def _stored_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Stored {field} must be a string")
    return value


def _stored_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Stored {field} must be a finite number")
    if not isfinite(value):
        raise ValueError(f"Stored {field} must be a finite number")
    return float(value)


def _stored_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Stored {field} must be an integer")
    return value


def _stored_texts(value: object, field: str) -> tuple[str, ...]:
    return tuple(_stored_text(item, field) for item in _stored_list(value, field))


def _stored_date(record: dict[str, object], key: str) -> date:
    return date.fromisoformat(_stored_text(record[key], key))


def _stored_window(value: object, field: str) -> TimeWindow:
    window = _stored_object(value, field)
    return TimeWindow(_stored_date(window, "start"), _stored_date(window, "end"))


def _stored_level(value: object) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if value == "LOW":
        return "LOW"
    if value == "MEDIUM":
        return "MEDIUM"
    if value == "HIGH":
        return "HIGH"
    raise ValueError("Stored forage_level must be LOW, MEDIUM, or HIGH")


def _stored_stop(value: object) -> SeasonStop:
    item = _stored_object(value, "stop")
    return SeasonStop(
        site_id=_stored_text(item["site_id"], "site_id"),
        longitude=_stored_number(item["longitude"], "longitude"),
        latitude=_stored_number(item["latitude"], "latitude"),
        window=_stored_window(item["window"], "stop window"),
        forage_level=_stored_level(item["forage_level"]),
        evidence_ids=_stored_texts(item["evidence_ids"], "evidence_ids"),
    )


def _stored_evidence(value: object) -> EvidenceSummary:
    item = _stored_object(value, "evidence")
    mode = item["source_mode"]
    if mode != "FIXTURE":
        raise ValueError("Stored source_mode must be FIXTURE")
    if item["synthetic"] is not True:
        raise ValueError("Stored synthetic evidence must be marked true")
    return EvidenceSummary(
        id=_stored_text(item["id"], "evidence id"),
        source_id=_stored_text(item["source_id"], "source_id"),
        source_mode="FIXTURE",
        synthetic=True,
        effective_window=_stored_window(item["effective_window"], "effective_window"),
        uncertainty=_stored_text(item["uncertainty"], "uncertainty"),
    )


def deserialize_completed_snapshot(payload: str) -> InvestigationSnapshot:
    """Validate a stored JSON snapshot before restoring typed domain values."""
    raw: object = json.loads(payload)
    data = _stored_object(raw, "investigation payload")
    request = _stored_object(data["request"], "request")
    coordinates = request["starting_point"]
    starting_point: tuple[float, float] | None = None
    if coordinates is not None:
        values = _stored_list(coordinates, "starting_point")
        if len(values) != 2:
            raise ValueError("Stored starting_point must contain exactly two coordinates")
        starting_point = (
            _stored_number(values[0], "starting_point.longitude"),
            _stored_number(values[1], "starting_point.latitude"),
        )

    raw_plan = data["plan"]
    plan: SeasonPlan | None = None
    if raw_plan is not None:
        plan_data = _stored_object(raw_plan, "plan")
        plan = SeasonPlan(
            stops=tuple(_stored_stop(stop) for stop in _stored_list(plan_data["stops"], "stops")),
            relocations=_stored_integer(plan_data["relocations"], "relocations"),
            rationale=_stored_text(plan_data["rationale"], "rationale"),
        )

    raw_outcome = data["outcome"]
    snapshot = InvestigationSnapshot(
        id=UUID(_stored_text(data["id"], "id")),
        status=InvestigationStatus(_stored_text(data["status"], "status")),
        request=InvestigationRequest(
            country=CountryCode(_stored_text(request["country"], "country")),
            territory_id=_stored_text(request["territory_id"], "territory_id"),
            scenario_id=_stored_text(request["scenario_id"], "scenario_id"),
            season=_stored_window(request["season"], "season"),
            starting_point=starting_point,
        ),
        created_at=datetime.fromisoformat(_stored_text(data["created_at"], "created_at")),
        updated_at=datetime.fromisoformat(_stored_text(data["updated_at"], "updated_at")),
        reference_version=_stored_text(data["reference_version"], "reference_version"),
        limitations=_stored_texts(data["limitations"], "limitations"),
        outcome=(
            InvestigationOutcomeKind(_stored_text(raw_outcome, "outcome"))
            if raw_outcome is not None
            else None
        ),
        plan=plan,
        evidence=tuple(
            _stored_evidence(item) for item in _stored_list(data["evidence"], "evidence")
        ),
        decision_trace=_stored_texts(data["decision_trace"], "decision_trace"),
        diagnostics=_stored_texts(data["diagnostics"], "diagnostics"),
    )
    if snapshot.status is not InvestigationStatus.COMPLETED or snapshot.outcome is None:
        raise ValueError("Stored investigation is not a completed snapshot")
    if snapshot.created_at.tzinfo is None or snapshot.updated_at.tzinfo is None:
        raise ValueError("Stored investigation timestamps must contain timezone offsets")
    return snapshot


class InMemoryInvestigationService:
    """Development-only store scoped to one app; completed snapshots are never rewritten."""

    def __init__(
        self,
        provider: ScenarioProvider,
        completed_store: CompletedInvestigationStore | None = None,
    ) -> None:
        self._provider = provider
        self._completed_store = completed_store
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
