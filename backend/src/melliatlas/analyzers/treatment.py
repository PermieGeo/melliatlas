"""Approximate field-treatment screening with explicit uncertainty."""

from datetime import timedelta
from math import isfinite

from shapely.geometry import Point, shape

from melliatlas.geography import approximate_distance_to_boundary_km, is_wgs84_position
from melliatlas.planning import (
    CandidateSite,
    ReportedTreatmentProduct,
    TreatmentProximity,
    TreatmentScreening,
)
from melliatlas.sources.api import TreatmentNotice

from .api import DEFAULT_WATCH_RADIUS_KM, MAX_DEMO_WATCH_RADIUS_KM


def screen_treatment_notices(
    site: CandidateSite,
    notices: tuple[TreatmentNotice, ...],
    *,
    watch_radius_km: float = DEFAULT_WATCH_RADIUS_KM,
) -> tuple[TreatmentScreening, ...]:
    """Screen fictional treatment claims without inferring safety or wind-drift direction.

    Local equirectangular distances are approximate only and never clear a site.
    """
    if not isfinite(watch_radius_km) or not 0 < watch_radius_km <= MAX_DEMO_WATCH_RADIUS_KM:
        raise ValueError("watch_radius_km must be finite and within (0, 50]")
    if not is_wgs84_position(site.longitude, site.latitude):
        raise ValueError("Site coordinates must be finite WGS84")
    if not site.id:
        raise ValueError("Site ID is required")

    results: list[TreatmentScreening] = []
    for notice in notices:
        warnings = [
            "Source claim is not a verified spraying event",
            "Wind, weather and bee flight have not been evaluated",
            "Stated UTC dates have a one-day uncertainty margin for local planning",
        ]
        distance: float | None = None
        if notice.scheduled_start is None or notice.scheduled_end is None:
            proximity = TreatmentProximity.UNKNOWN_PERIOD
        elif notice.scheduled_end.date() < site.forage_window.start - timedelta(
            days=1
        ) or notice.scheduled_start.date() > site.forage_window.end + timedelta(days=1):
            proximity = TreatmentProximity.OUTSIDE_STATED_PERIOD
        elif notice.geometry is None:
            proximity = TreatmentProximity.UNKNOWN_GEOMETRY
        else:
            polygon = shape(dict(notice.geometry))
            point = Point(site.longitude, site.latitude)
            if polygon.covers(point):
                proximity = TreatmentProximity.FIELD_INTERSECTION
                distance = 0.0
            else:
                # Wide or polar geometries cannot support a reliable local approximation.
                distance = approximate_distance_to_boundary_km(
                    polygon, site.longitude, site.latitude
                )
                if distance is None:
                    proximity = TreatmentProximity.UNKNOWN_GEOMETRY
                    warnings.append("Geometry extent prevents local distance screening")
                else:
                    proximity = (
                        TreatmentProximity.NEAR_REPORTED_FIELD
                        if distance <= watch_radius_km
                        else TreatmentProximity.OUTSIDE_SCREEN_RADIUS
                    )
        results.append(
            TreatmentScreening(
                site_id=site.id,
                source_record_id=notice.record_id,
                source_id=notice.source_id,
                proximity=proximity,
                approximate_distance_km=distance,
                warnings=tuple(warnings),
                captured_at=notice.captured_at,
                scheduled_start=notice.scheduled_start,
                scheduled_end=notice.scheduled_end,
                source_uri=notice.source_uri,
                products=tuple(
                    ReportedTreatmentProduct(
                        name=product.name,
                        crop=product.crop,
                        bee_hazard_class=product.reported_bee_hazard_class,
                    )
                    for product in notice.products
                ),
            )
        )
    return tuple(sorted(results, key=lambda item: (item.source_id, item.source_record_id)))
