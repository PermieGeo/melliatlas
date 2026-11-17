"""Validate and reconstruct nested fields from untrusted stored investigation JSON.

The `stored_*` helpers are shared with the sibling snapshot codec, not public
capability APIs. Keep other field decoders private to this module.
"""

from datetime import date, datetime
from math import isfinite
from typing import Final, Literal, TypeGuard

from melliatlas.agent.api import ReplanDecision, ReplanDecisionKind, ReplanOutcome, ReplanResult
from melliatlas.planning.api import (
    EcologyStatus,
    EvidenceSummary,
    ReportedTreatmentProduct,
    SeasonPlan,
    SeasonStop,
    SiteAssessment,
    TimeWindow,
    TreatmentProximity,
    TreatmentReview,
    TreatmentScreening,
)


def _is_object_dict(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def stored_object(value: object, field: str) -> dict[str, object]:
    """Validate JSON object shape before accessing persisted fields."""
    if not _is_object_dict(value):
        raise ValueError(f"Stored {field} must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"Stored {field} contains a non-string key")
        result[key] = item
    return result


def stored_list(value: object, field: str) -> list[object]:
    if not _is_object_list(value):
        raise ValueError(f"Stored {field} must be a list")
    return value


def stored_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Stored {field} must be a string")
    return value


def stored_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Stored {field} must be a finite number")
    if not isfinite(value):
        raise ValueError(f"Stored {field} must be a finite number")
    return float(value)


def _stored_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Stored {field} must be an integer")
    return value


def stored_texts(value: object, field: str) -> tuple[str, ...]:
    return tuple(stored_text(item, field) for item in stored_list(value, field))


def _stored_date(record: dict[str, object], key: str) -> date:
    return date.fromisoformat(stored_text(record[key], key))


def stored_window(value: object, field: str) -> TimeWindow:
    window = stored_object(value, field)
    return TimeWindow(_stored_date(window, "start"), _stored_date(window, "end"))


_FORAGE_LEVELS: Final[dict[str, Literal["LOW", "MEDIUM", "HIGH"]]] = {
    "LOW": "LOW",
    "MEDIUM": "MEDIUM",
    "HIGH": "HIGH",
}


def _stored_level(value: object) -> Literal["LOW", "MEDIUM", "HIGH"]:
    # Lookup preserves the narrow Literal type without widening untrusted stored values.
    level = _FORAGE_LEVELS.get(value) if isinstance(value, str) else None
    if level is None:
        raise ValueError("Stored forage_level must be LOW, MEDIUM, or HIGH")
    return level


def _stored_stop(value: object) -> SeasonStop:
    item = stored_object(value, "stop")
    return SeasonStop(
        site_id=stored_text(item["site_id"], "site_id"),
        longitude=stored_number(item["longitude"], "longitude"),
        latitude=stored_number(item["latitude"], "latitude"),
        window=stored_window(item["window"], "stop window"),
        forage_level=_stored_level(item["forage_level"]),
        evidence_ids=stored_texts(item["evidence_ids"], "evidence_ids"),
    )


def stored_plan(value: object) -> SeasonPlan:
    item = stored_object(value, "plan")
    return SeasonPlan(
        stops=tuple(_stored_stop(stop) for stop in stored_list(item["stops"], "stops")),
        relocations=_stored_integer(item["relocations"], "relocations"),
        rationale=stored_text(item["rationale"], "rationale"),
    )


def _stored_assessment(value: object) -> SiteAssessment:
    item = stored_object(value, "replanning assessment")
    if item["synthetic"] is not True:
        raise ValueError("Stored ecology assessment must be explicitly synthetic")
    return SiteAssessment(
        site_id=stored_text(item["site_id"], "assessment site_id"),
        status=EcologyStatus(stored_text(item["status"], "ecology status")),
        evidence_ids=stored_texts(item["evidence_ids"], "assessment evidence IDs"),
        rule_ids=stored_texts(item["rule_ids"], "assessment rule IDs"),
        reasons=stored_texts(item["reasons"], "assessment reasons"),
        unknowns=stored_texts(item["unknowns"], "assessment unknowns"),
        synthetic=True,
    )


def _stored_decision(value: object) -> ReplanDecision:
    item = stored_object(value, "replanning decision")
    return ReplanDecision(
        kind=ReplanDecisionKind(stored_text(item["kind"], "decision kind")),
        site_ids=stored_texts(item["site_ids"], "decision sites"),
        evidence_ids=stored_texts(item["evidence_ids"], "decision evidence"),
        rule_ids=stored_texts(item["rule_ids"], "decision rules"),
        note=stored_text(item["note"], "decision note"),
    )


def stored_replanning(value: object) -> ReplanResult:
    item = stored_object(value, "replanning")
    raw_plan = item["plan"]
    count = _stored_integer(item["checks_used"], "checks_used")
    if count < 0:
        raise ValueError("Stored replanning check count must not be negative")
    assessments = tuple(
        _stored_assessment(entry) for entry in stored_list(item["assessments"], "assessments")
    )
    if len(assessments) != count:
        raise ValueError("Stored replanning check count disagrees with assessments")
    result = ReplanResult(
        outcome=ReplanOutcome(stored_text(item["outcome"], "replanning outcome")),
        plan=stored_plan(raw_plan) if raw_plan is not None else None,
        assessments=assessments,
        excluded_site_ids=stored_texts(item["excluded_site_ids"], "excluded_site_ids"),
        unknown_site_ids=stored_texts(item["unknown_site_ids"], "unknown_site_ids"),
        trace=tuple(_stored_decision(event) for event in stored_list(item["trace"], "trace")),
        checks_used=count,
        warnings=stored_texts(item["warnings"], "warnings"),
    )
    if (result.outcome is ReplanOutcome.PLAN_FOUND) != (result.plan is not None):
        raise ValueError("Stored replanning plan and outcome are inconsistent")
    return result


def _stored_optional_timestamp(value: object, field: str) -> datetime | None:
    if value is None:
        return None
    timestamp = datetime.fromisoformat(stored_text(value, field))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"Stored {field} requires a timezone offset")
    return timestamp


_REPORTED_HAZARD_CLASSES: Final[dict[int, Literal[1, 2, 3]]] = {1: 1, 2: 2, 3: 3}


def _stored_reported_product(value: object) -> ReportedTreatmentProduct:
    item = stored_object(value, "reported treatment product")
    hazard = item["bee_hazard_class"]
    reported_hazard: Literal[1, 2, 3] | None = None
    if hazard is not None:
        if type(hazard) is not int:
            raise ValueError("Stored bee hazard class must be a reported value from 1 to 3")
        # Map only validated integers to the narrow Literal type; bool is not a hazard class.
        try:
            reported_hazard = _REPORTED_HAZARD_CLASSES[hazard]
        except KeyError as exc:
            raise ValueError(
                "Stored bee hazard class must be a reported value from 1 to 3"
            ) from exc
    name = item["name"]
    crop = item["crop"]
    return ReportedTreatmentProduct(
        name=stored_text(name, "product name") if name is not None else None,
        crop=stored_text(crop, "crop") if crop is not None else None,
        bee_hazard_class=reported_hazard,
    )


def _stored_treatment_screening(value: object) -> TreatmentScreening:
    item = stored_object(value, "treatment screening")
    raw_distance = item["approximate_distance_km"]
    distance = (
        stored_number(raw_distance, "approximate_distance_km") if raw_distance is not None else None
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
        site_id=stored_text(item["site_id"], "screening site_id"),
        source_record_id=stored_text(item["source_record_id"], "source_record_id"),
        source_id=stored_text(item["source_id"], "screening source_id"),
        proximity=TreatmentProximity(stored_text(item["proximity"], "proximity")),
        approximate_distance_km=distance,
        warnings=stored_texts(item["warnings"], "screening warnings"),
        captured_at=captured_at,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        source_uri=stored_text(source_uri, "source_uri") if source_uri is not None else None,
        products=tuple(
            _stored_reported_product(product)
            for product in stored_list(item["products"], "reported products")
        ),
    )


def stored_treatment_review(value: object) -> TreatmentReview:
    item = stored_object(value, "treatment review")
    screenings = tuple(
        _stored_treatment_screening(entry)
        for entry in stored_list(item["screenings"], "screenings")
    )
    avoided_ids = stored_texts(item["avoided_site_ids"], "avoided_site_ids")
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
        warnings=stored_texts(item["warnings"], "treatment warnings"),
    )


def stored_evidence(value: object) -> EvidenceSummary:
    item = stored_object(value, "evidence")
    mode = item["source_mode"]
    if mode != "FIXTURE":
        raise ValueError("Stored source_mode must be FIXTURE")
    if item["synthetic"] is not True:
        raise ValueError("Stored synthetic evidence must be marked true")
    return EvidenceSummary(
        id=stored_text(item["id"], "evidence id"),
        source_id=stored_text(item["source_id"], "source_id"),
        source_mode="FIXTURE",
        synthetic=True,
        effective_window=stored_window(item["effective_window"], "effective_window"),
        uncertainty=stored_text(item["uncertainty"], "uncertainty"),
    )
