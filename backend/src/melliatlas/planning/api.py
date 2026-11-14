"""Typed deterministic planning primitives for the synthetic V01 scenario."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from melliatlas.territories.api import CountryCode


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
