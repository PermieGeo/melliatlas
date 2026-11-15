"""Pure spatial analysis of explicitly fictional ecology evidence."""

from math import isfinite

from shapely.errors import GEOSException
from shapely.geometry import Point, shape

from melliatlas.planning.api import CandidateSite, EcologyOverlap, EcologyZone


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
