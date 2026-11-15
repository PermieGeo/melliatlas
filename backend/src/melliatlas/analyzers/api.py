"""Pure spatial analysis of fictional ecology and treatment evidence."""

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from math import cos, isfinite, radians

from shapely.errors import GEOSException
from shapely.geometry import Point, shape
from shapely.ops import transform

from melliatlas.planning.api import CandidateSite, EcologyOverlap, EcologyZone
from melliatlas.sources.api import TreatmentNotice


def find_ecology_overlaps(
    site: CandidateSite, zones: tuple[EcologyZone, ...]
) -> tuple[EcologyOverlap, ...]:
    """Identify point-in-polygon overlaps without assigning legal or eligibility policy."""
    if not (
        isfinite(site.longitude)
        and isfinite(site.latitude)
        and -180 <= site.longitude <= 180
        and -90 <= site.latitude <= 90
    ):
        raise ValueError("Candidate coordinates must be finite WGS84 longitude/latitude")
    if not site.id:
        raise ValueError("Candidate site ID must not be empty")
    point = Point(site.longitude, site.latitude)
    matches: list[EcologyOverlap] = []
    for zone in zones:
        if not zone.evidence_id.strip() or not zone.rule_id.strip():
            raise ValueError("Fictional ecology evidence and rule IDs must not be empty")
        try:
            polygon = shape(dict(zone.geometry))
        except (GEOSException, TypeError, ValueError) as error:
            raise ValueError("Invalid fictional ecology geometry") from error
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
            raise ValueError("Invalid fictional ecology geometry")
        min_lon, min_lat, max_lon, max_lat = polygon.bounds
        if (
            not all(isfinite(value) for value in polygon.bounds)
            or min_lon < -180
            or max_lon > 180
            or min_lat < -90
            or max_lat > 90
        ):
            raise ValueError("Invalid WGS84 fictional ecology geometry coordinates")
        if polygon.covers(point):
            matches.append(
                EcologyOverlap(
                    evidence_id=zone.evidence_id,
                    rule_id=zone.rule_id,
                    kind=zone.kind,
                )
            )
    return tuple(sorted(matches, key=lambda item: (item.evidence_id, item.rule_id, item.kind)))


class TreatmentProximity(StrEnum):
    FIELD_INTERSECTION = "FIELD_INTERSECTION"
    NEAR_REPORTED_FIELD = "NEAR_REPORTED_FIELD"
    OUTSIDE_SCREEN_RADIUS = "OUTSIDE_SCREEN_RADIUS"
    UNKNOWN_GEOMETRY = "UNKNOWN_GEOMETRY"
    OUTSIDE_STATED_PERIOD = "OUTSIDE_STATED_PERIOD"
    UNKNOWN_PERIOD = "UNKNOWN_PERIOD"


@dataclass(frozen=True)
class TreatmentScreening:
    site_id: str
    source_record_id: str
    source_id: str
    proximity: TreatmentProximity
    approximate_distance_km: float | None
    warnings: tuple[str, ...]


def screen_treatment_notices(
    site: CandidateSite,
    notices: tuple[TreatmentNotice, ...],
    *,
    watch_radius_km: float = 7.0,
) -> tuple[TreatmentScreening, ...]:
    """Screen fictional treatment claims without inferring safety or wind-drift direction.

    Local equirectangular distances are approximate only and never clear a site.
    """
    if not isfinite(watch_radius_km) or not 0 < watch_radius_km <= 50:
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
            )
        )
    return tuple(sorted(results, key=lambda item: (item.source_id, item.source_record_id)))
