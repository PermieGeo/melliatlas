"""Approximate field-treatment screening with explicit uncertainty."""

from datetime import timedelta
from math import cos, isfinite, radians

from shapely.geometry import Point, shape
from shapely.ops import transform

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
    if not isfinite(site.longitude) or not isfinite(site.latitude):
        raise ValueError("Site coordinates must be finite")
    if not -180 <= site.longitude <= 180 or not -90 <= site.latitude <= 90:
        raise ValueError("Site coordinates must be WGS84")
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
                # A local metric approximation is a screening aid, not a safety boundary.
                earth_radius_km = 6371.0088
                latitude_scale = cos(radians(site.latitude))

                def to_local(lon: float, lat: float, z: float | None = None) -> tuple[float, float]:
                    return (
                        earth_radius_km * radians(lon - site.longitude) * latitude_scale,
                        earth_radius_km * radians(lat - site.latitude),
                    )

                if (
                    abs(site.latitude) > 80
                    or polygon.bounds[2] - polygon.bounds[0] > 5
                    or polygon.bounds[3] - polygon.bounds[1] > 5
                ):
                    proximity = TreatmentProximity.UNKNOWN_GEOMETRY
                    warnings.append("Geometry extent prevents local distance screening")
                else:
                    distance = transform(to_local, polygon).distance(Point(0, 0))
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
