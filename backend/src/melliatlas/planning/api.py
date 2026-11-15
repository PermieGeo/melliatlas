"""Typed deterministic planning primitives for synthetic investigation scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
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
