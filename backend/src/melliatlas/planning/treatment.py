"""Conservative fictional field-treatment avoidance preference."""

from .models import (
    CandidateSite,
    TreatmentProximity,
    TreatmentReview,
    TreatmentScreening,
    TreatmentWarningCode,
)


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
