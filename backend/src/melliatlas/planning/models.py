"""Immutable domain models for fictional season, ecology and treatment evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from melliatlas.territories.api import CountryCode, GeometryWgs84


@dataclass(frozen=True)
class TimeWindow:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("Season start must not follow season end")


@dataclass(frozen=True)
class CandidateSite:
    id: str
    longitude: float
    latitude: float
    forage_window: TimeWindow
    forage_level: Literal["LOW", "MEDIUM", "HIGH"]
    evidence_id: str


@dataclass(frozen=True)
class EvidenceSummary:
    id: str
    source_id: str
    source_mode: Literal["FIXTURE"]
    synthetic: Literal[True]
    effective_window: TimeWindow
    uncertainty: str


@dataclass(frozen=True)
class SyntheticScenario:
    id: str
    country: CountryCode
    territory_id: str
    supported_season: TimeWindow
    reference_version: str
    candidates: tuple[CandidateSite, ...]
    evidence: tuple[EvidenceSummary, ...]
    limitations: tuple[str, ...]
    ecology_zones: tuple[EcologyZone, ...] = ()
    treatment_screening_required: bool = False


@dataclass(frozen=True)
class SeasonStop:
    site_id: str
    longitude: float
    latitude: float
    window: TimeWindow
    forage_level: Literal["LOW", "MEDIUM", "HIGH"]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class SeasonPlan:
    stops: tuple[SeasonStop, ...]
    relocations: int
    rationale: str


class EcologyEvidenceKind(StrEnum):
    DEMO_RESTRICTION = "DEMO_RESTRICTION"
    DEMO_PRECAUTION = "DEMO_PRECAUTION"


class EcologyStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    EXCLUDED = "EXCLUDED"
    CAUTION = "CAUTION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EcologyZone:
    evidence_id: str
    rule_id: str
    kind: EcologyEvidenceKind
    geometry: GeometryWgs84


@dataclass(frozen=True)
class EcologyOverlap:
    evidence_id: str
    rule_id: str
    kind: EcologyEvidenceKind


@dataclass(frozen=True)
class SiteAssessment:
    site_id: str
    status: EcologyStatus
    evidence_ids: tuple[str, ...]
    rule_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    unknowns: tuple[str, ...]
    synthetic: Literal[True] = True


class TreatmentProximity(StrEnum):
    FIELD_INTERSECTION = "FIELD_INTERSECTION"
    NEAR_REPORTED_FIELD = "NEAR_REPORTED_FIELD"
    OUTSIDE_SCREEN_RADIUS = "OUTSIDE_SCREEN_RADIUS"
    UNKNOWN_GEOMETRY = "UNKNOWN_GEOMETRY"
    OUTSIDE_STATED_PERIOD = "OUTSIDE_STATED_PERIOD"
    UNKNOWN_PERIOD = "UNKNOWN_PERIOD"


@dataclass(frozen=True)
class ReportedTreatmentProduct:
    name: str | None
    crop: str | None
    bee_hazard_class: Literal[1, 2, 3] | None


@dataclass(frozen=True)
class TreatmentScreening:
    site_id: str
    source_record_id: str
    source_id: str
    proximity: TreatmentProximity
    approximate_distance_km: float | None
    warnings: tuple[str, ...]
    captured_at: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    source_uri: str | None = None
    products: tuple[ReportedTreatmentProduct, ...] = ()


class TreatmentWarningCode(StrEnum):
    """Stable warning identifiers; UI language must not change domain evidence."""

    SYNTHETIC_NOTICE_UNVERIFIED = "SYNTHETIC_NOTICE_UNVERIFIED"
    COVERAGE_NOT_ESTABLISHED = "COVERAGE_NOT_ESTABLISHED"
    DRIFT_NOT_EVALUATED = "DRIFT_NOT_EVALUATED"
    DEMONSTRATION_ONLY = "DEMONSTRATION_ONLY"


@dataclass(frozen=True)
class TreatmentReview:
    """Evidence-aware fictional planning preference, never legal exclusion or clearance."""

    screenings: tuple[TreatmentScreening, ...]
    avoided_site_ids: tuple[str, ...]
    warnings: tuple[str, ...]
