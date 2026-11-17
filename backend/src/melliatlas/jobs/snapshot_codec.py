"""Strict JSON codec for completed immutable investigation snapshots."""

import json
from dataclasses import asdict
from datetime import date, datetime
from uuid import UUID

from melliatlas.agent.api import ReplanDecisionKind
from melliatlas.geography import POSITION_DIMENSIONS
from melliatlas.planning.api import EcologyStatus
from melliatlas.territories.api import CountryCode

from .codec_fields import (
    stored_evidence,
    stored_list,
    stored_number,
    stored_object,
    stored_plan,
    stored_replanning,
    stored_text,
    stored_texts,
    stored_treatment_review,
    stored_window,
)
from .models import (
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
)
from .outcomes import REPLAN_OUTCOME_TO_INVESTIGATION


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


def deserialize_completed_snapshot(payload: str) -> InvestigationSnapshot:
    """Validate a stored JSON snapshot before restoring typed domain values."""
    raw: object = json.loads(payload)
    data = stored_object(raw, "investigation payload")
    request = stored_object(data["request"], "request")
    coordinates = request["starting_point"]
    starting_point: tuple[float, float] | None = None
    if coordinates is not None:
        values = stored_list(coordinates, "starting_point")
        if len(values) != POSITION_DIMENSIONS:
            raise ValueError("Stored starting_point must contain exactly two coordinates")
        starting_point = (
            stored_number(values[0], "starting_point.longitude"),
            stored_number(values[1], "starting_point.latitude"),
        )

    raw_plan = data["plan"]
    plan = stored_plan(raw_plan) if raw_plan is not None else None
    raw_replanning = data.get("replanning")
    replanning = stored_replanning(raw_replanning) if raw_replanning is not None else None
    raw_treatment = data.get("treatment_review")
    treatment_review = stored_treatment_review(raw_treatment) if raw_treatment is not None else None

    raw_outcome = data["outcome"]
    snapshot = InvestigationSnapshot(
        id=UUID(stored_text(data["id"], "id")),
        status=InvestigationStatus(stored_text(data["status"], "status")),
        request=InvestigationRequest(
            country=CountryCode(stored_text(request["country"], "country")),
            territory_id=stored_text(request["territory_id"], "territory_id"),
            scenario_id=stored_text(request["scenario_id"], "scenario_id"),
            season=stored_window(request["season"], "season"),
            starting_point=starting_point,
        ),
        created_at=datetime.fromisoformat(stored_text(data["created_at"], "created_at")),
        updated_at=datetime.fromisoformat(stored_text(data["updated_at"], "updated_at")),
        reference_version=stored_text(data["reference_version"], "reference_version"),
        limitations=stored_texts(data["limitations"], "limitations"),
        outcome=(
            InvestigationOutcomeKind(stored_text(raw_outcome, "outcome"))
            if raw_outcome is not None
            else None
        ),
        plan=plan,
        evidence=tuple(stored_evidence(item) for item in stored_list(data["evidence"], "evidence")),
        decision_trace=stored_texts(data["decision_trace"], "decision_trace"),
        diagnostics=stored_texts(data["diagnostics"], "diagnostics"),
        replanning=replanning,
        treatment_review=treatment_review,
    )
    if snapshot.status is not InvestigationStatus.COMPLETED or snapshot.outcome is None:
        raise ValueError("Stored investigation is not a completed snapshot")
    if snapshot.replanning is not None:
        if snapshot.replanning.plan != snapshot.plan:
            raise ValueError("Stored replanning plan disagrees with investigation plan")
        expected_outcome = REPLAN_OUTCOME_TO_INVESTIGATION[snapshot.replanning.outcome]
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
