"""Typed deterministic planning primitives for synthetic investigation scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
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


def build_season_plan(
    candidates: tuple[CandidateSite, ...], season: TimeWindow
) -> SeasonPlan | None:
    """Select chronological non-overlapping fixture windows without claiming real site safety."""
    ordered = sorted(candidates, key=lambda site: (site.forage_window.start, site.id))
    stops: list[SeasonStop] = []
    next_available = season.start
    for site in ordered:
        start = max(next_available, season.start, site.forage_window.start)
        end = min(season.end, site.forage_window.end)
        if start > end:
            continue
        stops.append(
            SeasonStop(
                site_id=site.id,
                longitude=site.longitude,
                latitude=site.latitude,
                window=TimeWindow(start, end),
                forage_level=site.forage_level,
                evidence_ids=(site.evidence_id,),
            )
        )
        next_available = end + timedelta(days=1)
    if len(stops) < 2:
        return None
    return SeasonPlan(
        stops=tuple(stops),
        relocations=len(stops) - 1,
        rationale="Illustrative chronological forage windows only; no verified exclusion screening",
    )


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


def assess_ecology(site_id: str, overlaps: tuple[EcologyOverlap, ...]) -> SiteAssessment:
    """Apply demo-only eligibility policy; absent intersections never prove site safety."""
    if not site_id:
        raise ValueError("Site ID must not be empty")
    ordered = tuple(sorted(overlaps, key=lambda item: (item.evidence_id, item.rule_id, item.kind)))
    if any(item.kind is EcologyEvidenceKind.DEMO_RESTRICTION for item in ordered):
        status = EcologyStatus.EXCLUDED
        reasons = ("An explicit fictional exclusion geometry intersects this site",)
    elif any(item.kind is EcologyEvidenceKind.DEMO_PRECAUTION for item in ordered):
        status = EcologyStatus.CAUTION
        reasons = ("A fictional precautionary geometry intersects this site",)
    else:
        status = EcologyStatus.UNKNOWN
        reasons = ("No explicit fictional ecology zone intersects this site",)
    return SiteAssessment(
        site_id=site_id,
        status=status,
        evidence_ids=tuple(dict.fromkeys(item.evidence_id for item in ordered)),
        rule_ids=tuple(dict.fromkeys(item.rule_id for item in ordered)),
        reasons=reasons,
        unknowns=("Complete ecological coverage and legal restrictions are not verified",),
    )


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


def prefer_sites_away_from_reported_treatments(
    candidates: tuple[CandidateSite, ...],
    screenings: tuple[TreatmentScreening, ...],
) -> tuple[tuple[CandidateSite, ...], TreatmentReview]:
    """Avoid reported near-field overlap in a demo; unknown coverage remains explicit."""
    site_ids = [site.id for site in candidates]
    if not site_ids or any(not site_id for site_id in site_ids):
        raise ValueError("Treatment planning requires identified candidates")
    if len(site_ids) != len(set(site_ids)):
        raise ValueError("Treatment planning requires unique candidate IDs")
    if not screenings:
        raise ValueError("Treatment planning requires explicit fixture observations")
    seen: set[tuple[str, str, str]] = set()
    observed_site_ids: set[str] = set()
    avoided: set[str] = set()
    for item in screenings:
        if (
            item.site_id not in site_ids
            or not item.source_id.strip()
            or not item.source_record_id.strip()
        ):
            raise ValueError("Treatment observation has an unknown site or source")
        identity = (item.site_id, item.source_id, item.source_record_id)
        if identity in seen:
            raise ValueError("Duplicate treatment observation")
        seen.add(identity)
        observed_site_ids.add(item.site_id)
        if item.proximity in (
            TreatmentProximity.FIELD_INTERSECTION,
            TreatmentProximity.NEAR_REPORTED_FIELD,
        ):
            avoided.add(item.site_id)
    if observed_site_ids != set(site_ids):
        raise ValueError("Each candidate must receive the same scoped fixture screening")
    preferred = tuple(site for site in candidates if site.id not in avoided)
    review = TreatmentReview(
        screenings=tuple(
            sorted(
                screenings,
                key=lambda item: (item.site_id, item.source_id, item.source_record_id),
            )
        ),
        avoided_site_ids=tuple(sorted(avoided)),
        warnings=(
            TreatmentWarningCode.SYNTHETIC_NOTICE_UNVERIFIED,
            TreatmentWarningCode.COVERAGE_NOT_ESTABLISHED,
            TreatmentWarningCode.DRIFT_NOT_EVALUATED,
            TreatmentWarningCode.DEMONSTRATION_ONLY,
        ),
    )
    return preferred, review
