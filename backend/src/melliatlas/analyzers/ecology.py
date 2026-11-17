"""Pure spatial intersection screening for synthetic ecology zones."""

from math import isfinite

from shapely.errors import GEOSException
from shapely.geometry import Point, shape

from melliatlas.geography import (
    LATITUDE_MAX,
    LATITUDE_MIN,
    LONGITUDE_MAX,
    LONGITUDE_MIN,
    is_wgs84_position,
)
from melliatlas.planning.api import CandidateSite, EcologyOverlap, EcologyZone


def find_ecology_overlaps(
    site: CandidateSite, zones: tuple[EcologyZone, ...]
) -> tuple[EcologyOverlap, ...]:
    """Identify point-in-polygon overlaps without assigning legal or eligibility policy."""
    if not is_wgs84_position(site.longitude, site.latitude):
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
            or min_lon < LONGITUDE_MIN
            or max_lon > LONGITUDE_MAX
            or min_lat < LATITUDE_MIN
            or max_lat > LATITUDE_MAX
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
