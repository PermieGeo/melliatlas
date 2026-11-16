"""Bounded inspection and illustrative treatment-aware candidate selection."""

from dataclasses import replace

from melliatlas.planning import (
    CandidateSite,
    TimeWindow,
    build_season_plan,
    prefer_sites_away_from_reported_treatments,
)

from .api import TreatmentInspector
from .models import TreatmentPlanningResult


class TreatmentPlanner:
    """Bounded fictional treatment observation and provisional alternative selection."""

    def __init__(self, inspect: TreatmentInspector, *, max_checks: int = 16) -> None:
        if type(max_checks) is not int or max_checks < 1:
            raise ValueError("max_checks must be a positive integer")
        self._inspect = inspect
        self._max_checks = max_checks

    def plan(
        self, candidates: tuple[CandidateSite, ...], season: TimeWindow
    ) -> TreatmentPlanningResult:
        active = tuple(
            replace(
                site,
                forage_window=TimeWindow(
                    max(site.forage_window.start, season.start),
                    min(site.forage_window.end, season.end),
                ),
            )
            for site in candidates
            if site.forage_window.start <= season.end and site.forage_window.end >= season.start
        )
        if len(active) > self._max_checks:
            raise ValueError("Treatment inspection budget exceeded; no unchecked plan is allowed")
        observations = tuple(item for site in active for item in self._inspect(site))
        preferred, review = prefer_sites_away_from_reported_treatments(active, observations)
        plan = build_season_plan(preferred, season)
        references = tuple(
            f"{item.site_id} / {item.source_id}:{item.source_record_id} / {item.proximity.value}"
            for item in review.screenings
            if item.site_id in review.avoided_site_ids
        )
        trace = (
            "Screened fictional candidates during the requested season",
            *(f"Withheld candidate following fictional notice: {ref}" for ref in references),
            "Selected provisional alternative windows without confirming site safety"
            if plan is not None
            else "Insufficient alternative windows after treatment screening",
        )
        return TreatmentPlanningResult(plan=plan, review=review, trace=trace)
