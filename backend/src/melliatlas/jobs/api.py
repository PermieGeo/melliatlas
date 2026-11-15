"""Public non-durable investigation lifecycle for synthetic V01/V04 slices."""

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from enum import StrEnum
from math import isfinite
from threading import Lock
from typing import Literal, Protocol, TypeGuard
from uuid import UUID, uuid4

from melliatlas.agent.api import (
    CombinedPlanner,
    DeterministicPlanner,
    ReplanDecision,
    ReplanDecisionKind,
    ReplanOutcome,
    ReplanResult,
    TreatmentPlanner,
)
from melliatlas.planning.api import (
    EcologyStatus,
    EvidenceSummary,
    ReportedTreatmentProduct,
    SeasonPlan,
    SeasonStop,
    SiteAssessment,
    SyntheticScenario,
    TimeWindow,
    TreatmentProximity,
    TreatmentReview,
    TreatmentScreening,
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
    replanning: ReplanResult | None = None
    treatment_review: TreatmentReview | None = None


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


EcologyPlannerFactory = Callable[[SyntheticScenario], DeterministicPlanner]
TreatmentPlannerFactory = Callable[[SyntheticScenario], TreatmentPlanner]


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

    encoded = asdict(snapshot)
    if snapshot.replanning is None:
        del encoded["replanning"]
    if snapshot.treatment_review is None:
        del encoded["treatment_review"]
    return json.dumps(encoded, default=encode_temporal, sort_keys=True, allow_nan=False)


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


def _stored_plan(value: object) -> SeasonPlan:
    item = _stored_object(value, "plan")
    return SeasonPlan(
        stops=tuple(_stored_stop(stop) for stop in _stored_list(item["stops"], "stops")),
        relocations=_stored_integer(item["relocations"], "relocations"),
        rationale=_stored_text(item["rationale"], "rationale"),
    )


def _stored_assessment(value: object) -> SiteAssessment:
    item = _stored_object(value, "replanning assessment")
    if item["synthetic"] is not True:
        raise ValueError("Stored ecology assessment must be explicitly synthetic")
    return SiteAssessment(
        site_id=_stored_text(item["site_id"], "assessment site_id"),
        status=EcologyStatus(_stored_text(item["status"], "ecology status")),
        evidence_ids=_stored_texts(item["evidence_ids"], "assessment evidence IDs"),
        rule_ids=_stored_texts(item["rule_ids"], "assessment rule IDs"),
        reasons=_stored_texts(item["reasons"], "assessment reasons"),
        unknowns=_stored_texts(item["unknowns"], "assessment unknowns"),
        synthetic=True,
    )


def _stored_decision(value: object) -> ReplanDecision:
    item = _stored_object(value, "replanning decision")
    return ReplanDecision(
        kind=ReplanDecisionKind(_stored_text(item["kind"], "decision kind")),
        site_ids=_stored_texts(item["site_ids"], "decision sites"),
        evidence_ids=_stored_texts(item["evidence_ids"], "decision evidence"),
        rule_ids=_stored_texts(item["rule_ids"], "decision rules"),
        note=_stored_text(item["note"], "decision note"),
    )


def _stored_replanning(value: object) -> ReplanResult:
    item = _stored_object(value, "replanning")
    raw_plan = item["plan"]
    count = _stored_integer(item["checks_used"], "checks_used")
    if count < 0:
        raise ValueError("Stored replanning check count must not be negative")
    assessments = tuple(
        _stored_assessment(entry) for entry in _stored_list(item["assessments"], "assessments")
    )
    if len(assessments) != count:
        raise ValueError("Stored replanning check count disagrees with assessments")
    result = ReplanResult(
        outcome=ReplanOutcome(_stored_text(item["outcome"], "replanning outcome")),
        plan=_stored_plan(raw_plan) if raw_plan is not None else None,
        assessments=assessments,
        excluded_site_ids=_stored_texts(item["excluded_site_ids"], "excluded_site_ids"),
        unknown_site_ids=_stored_texts(item["unknown_site_ids"], "unknown_site_ids"),
        trace=tuple(_stored_decision(event) for event in _stored_list(item["trace"], "trace")),
        checks_used=count,
        warnings=_stored_texts(item["warnings"], "warnings"),
    )
    if (result.outcome is ReplanOutcome.PLAN_FOUND) != (result.plan is not None):
        raise ValueError("Stored replanning plan and outcome are inconsistent")
    return result


def _stored_optional_timestamp(value: object, field: str) -> datetime | None:
    if value is None:
        return None
    timestamp = datetime.fromisoformat(_stored_text(value, field))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"Stored {field} requires a timezone offset")
    return timestamp


def _stored_reported_product(value: object) -> ReportedTreatmentProduct:
    item = _stored_object(value, "reported treatment product")
    hazard = item["bee_hazard_class"]
    if hazard is not None and (type(hazard) is not int or hazard not in (1, 2, 3)):
        raise ValueError("Stored bee hazard class must be a reported value from 1 to 3")
    reported_hazard: Literal[1, 2, 3] | None = None
    if hazard == 1:
        reported_hazard = 1
    elif hazard == 2:
        reported_hazard = 2
    elif hazard == 3:
        reported_hazard = 3
    name = item["name"]
    crop = item["crop"]
    return ReportedTreatmentProduct(
        name=_stored_text(name, "product name") if name is not None else None,
        crop=_stored_text(crop, "crop") if crop is not None else None,
        bee_hazard_class=reported_hazard,
    )


def _stored_treatment_screening(value: object) -> TreatmentScreening:
    item = _stored_object(value, "treatment screening")
    raw_distance = item["approximate_distance_km"]
    distance = (
        _stored_number(raw_distance, "approximate_distance_km")
        if raw_distance is not None
        else None
    )
    if distance is not None and distance < 0:
        raise ValueError("Treatment screening distance must not be negative")
    captured_at = _stored_optional_timestamp(item["captured_at"], "captured_at")
    scheduled_start = _stored_optional_timestamp(item["scheduled_start"], "scheduled_start")
    scheduled_end = _stored_optional_timestamp(item["scheduled_end"], "scheduled_end")
    if (
        scheduled_start is not None
        and scheduled_end is not None
        and scheduled_end < scheduled_start
    ):
        raise ValueError("Stored treatment interval is reversed")
    source_uri = item["source_uri"]
    return TreatmentScreening(
        site_id=_stored_text(item["site_id"], "screening site_id"),
        source_record_id=_stored_text(item["source_record_id"], "source_record_id"),
        source_id=_stored_text(item["source_id"], "screening source_id"),
        proximity=TreatmentProximity(_stored_text(item["proximity"], "proximity")),
        approximate_distance_km=distance,
        warnings=_stored_texts(item["warnings"], "screening warnings"),
        captured_at=captured_at,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        source_uri=_stored_text(source_uri, "source_uri") if source_uri is not None else None,
        products=tuple(
            _stored_reported_product(product)
            for product in _stored_list(item["products"], "reported products")
        ),
    )


def _stored_treatment_review(value: object) -> TreatmentReview:
    item = _stored_object(value, "treatment review")
    screenings = tuple(
        _stored_treatment_screening(entry)
        for entry in _stored_list(item["screenings"], "screenings")
    )
    avoided_ids = _stored_texts(item["avoided_site_ids"], "avoided_site_ids")
    if not screenings:
        raise ValueError("Stored treatment review must retain source observations")
    seen: set[tuple[str, str, str]] = set()
    should_avoid: set[str] = set()
    for screening in screenings:
        identity = (screening.site_id, screening.source_id, screening.source_record_id)
        if not all(identity) or identity in seen:
            raise ValueError("Stored treatment source identities must be nonempty and unique")
        seen.add(identity)
        if screening.proximity in (
            TreatmentProximity.FIELD_INTERSECTION,
            TreatmentProximity.NEAR_REPORTED_FIELD,
        ):
            should_avoid.add(screening.site_id)
    if avoided_ids != tuple(sorted(should_avoid)):
        raise ValueError("Stored avoided candidates disagree with treatment findings")
    return TreatmentReview(
        screenings=screenings,
        avoided_site_ids=avoided_ids,
        warnings=_stored_texts(item["warnings"], "treatment warnings"),
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
    plan = _stored_plan(raw_plan) if raw_plan is not None else None
    raw_replanning = data.get("replanning")
    replanning = _stored_replanning(raw_replanning) if raw_replanning is not None else None
    raw_treatment = data.get("treatment_review")
    treatment_review = (
        _stored_treatment_review(raw_treatment) if raw_treatment is not None else None
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
        replanning=replanning,
        treatment_review=treatment_review,
    )
    if snapshot.status is not InvestigationStatus.COMPLETED or snapshot.outcome is None:
        raise ValueError("Stored investigation is not a completed snapshot")
    if snapshot.replanning is not None:
        if snapshot.replanning.plan != snapshot.plan:
            raise ValueError("Stored replanning plan disagrees with investigation plan")
        expected_outcome = {
            ReplanOutcome.PLAN_FOUND: InvestigationOutcomeKind.PLAN_FOUND,
            ReplanOutcome.NO_FEASIBLE_ALTERNATIVE: InvestigationOutcomeKind.NO_FEASIBLE_ALTERNATIVE,
            ReplanOutcome.CHECK_LIMIT_REACHED: InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE,
        }[snapshot.replanning.outcome]
        if snapshot.outcome is not expected_outcome:
            raise ValueError("Stored replanning outcome disagrees with investigation outcome")
    if snapshot.treatment_review is not None:
        if snapshot.replanning is not None:
            evaluated = {item.site_id for item in snapshot.replanning.assessments}
            reviewed = {item.site_id for item in snapshot.treatment_review.screenings}
            if (snapshot.plan is not None and evaluated != reviewed) or (
                snapshot.plan is None and not evaluated.issubset(reviewed)
            ):
                raise ValueError("Stored combined screening coverage disagrees")
            qualified = {
                item.site_id
                for item in snapshot.replanning.assessments
                if item.status is EcologyStatus.CAUTION
            }
            if snapshot.plan is not None and any(
                stop.site_id not in qualified for stop in snapshot.plan.stops
            ):
                raise ValueError("Stored combined plan uses a site without ecological caution")
            traced = tuple(
                (event.site_ids, event.evidence_ids)
                for event in snapshot.replanning.trace
                if event.kind is ReplanDecisionKind.TREATMENT_CHECK
            )
            expected = tuple(
                ((item.site_id,), (item.source_record_id,))
                for item in snapshot.treatment_review.screenings
            )
            if traced != expected:
                raise ValueError("Stored combined trace disagrees with treatment findings")
        source_records = {(item.source_id, item.id) for item in snapshot.evidence}
        if any(
            (item.source_id, item.source_record_id) not in source_records
            for item in snapshot.treatment_review.screenings
        ):
            raise ValueError("Stored treatment observations lack matching source evidence")
        if snapshot.plan is not None and any(
            stop.site_id in snapshot.treatment_review.avoided_site_ids
            for stop in snapshot.plan.stops
        ):
            raise ValueError("Stored treatment plan uses a candidate withheld by source evidence")
        if (snapshot.outcome is InvestigationOutcomeKind.PLAN_FOUND) != (snapshot.plan is not None):
            raise ValueError("Stored treatment plan and outcome disagree")
    if snapshot.created_at.tzinfo is None or snapshot.updated_at.tzinfo is None:
        raise ValueError("Stored investigation timestamps must contain timezone offsets")
    return snapshot


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
