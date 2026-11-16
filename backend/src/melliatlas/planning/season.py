"""Select deterministic chronological forage windows from fictional candidate sites."""

from datetime import timedelta

from .models import CandidateSite, SeasonPlan, SeasonStop, TimeWindow


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
