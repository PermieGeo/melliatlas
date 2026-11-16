"""Pure geometry and policy checks for explicit fictional ecological evidence."""

from dataclasses import replace
from datetime import date

import pytest

from melliatlas.analyzers import find_ecology_overlaps
from melliatlas.planning import (
    CandidateSite,
    EcologyEvidenceKind,
    EcologyStatus,
    EcologyZone,
    TimeWindow,
    assess_ecology,
)


def _site(identifier: str = "fixture-a", longitude: float = 32.0) -> CandidateSite:
    return CandidateSite(
        id=identifier,
        longitude=longitude,
        latitude=54.0,
        forage_window=TimeWindow(date(2026, 5, 1), date(2026, 6, 1)),
        forage_level="MEDIUM",
        evidence_id="forage-a",
    )


def _zone(kind: EcologyEvidenceKind, evidence_id: str = "demo-evidence") -> EcologyZone:
    return EcologyZone(
        evidence_id=evidence_id,
        rule_id="fictional-demo-rule",
        kind=kind,
        geometry={
            "type": "Polygon",
            "coordinates": [[(31.9, 53.9), (32.1, 53.9), (32.1, 54.1), (31.9, 54.1), (31.9, 53.9)]],
        },
    )


def test_explicit_fictional_exclusion_intersection_is_excluded() -> None:
    site = _site()
    overlaps = find_ecology_overlaps(site, (_zone(EcologyEvidenceKind.DEMO_RESTRICTION),))
    result = assess_ecology(site.id, overlaps)
    assert result.status is EcologyStatus.EXCLUDED
    assert result.evidence_ids == ("demo-evidence",)
    assert result.rule_ids == ("fictional-demo-rule",)
    assert result.synthetic is True


def test_precautionary_intersection_is_not_an_exclusion() -> None:
    site = _site()
    overlaps = find_ecology_overlaps(site, (_zone(EcologyEvidenceKind.DEMO_PRECAUTION),))
    result = assess_ecology(site.id, overlaps)
    assert result.status is EcologyStatus.CAUTION
    assert result.rule_ids == ("fictional-demo-rule",)


def test_unavailable_or_nonmatching_evidence_does_not_imply_eligibility() -> None:
    site = _site(longitude=40.0)
    assert assess_ecology(site.id, ()).status is EcologyStatus.UNKNOWN
    no_intersection = find_ecology_overlaps(site, (_zone(EcologyEvidenceKind.DEMO_RESTRICTION),))
    assert assess_ecology(site.id, no_intersection).status is EcologyStatus.UNKNOWN


def test_boundary_point_matches_area_and_candidate_id_does_not_change_decision() -> None:
    boundary = _site(longitude=31.9)
    area = _zone(EcologyEvidenceKind.DEMO_RESTRICTION)
    first = assess_ecology(boundary.id, find_ecology_overlaps(boundary, (area,)))
    renamed = replace(boundary, id="renamed-fixture")
    second = assess_ecology(renamed.id, find_ecology_overlaps(renamed, (area,)))
    assert first.status is second.status is EcologyStatus.EXCLUDED


def test_exclusion_overrides_precaution_independently_of_input_order() -> None:
    site = _site()
    areas = (
        _zone(EcologyEvidenceKind.DEMO_PRECAUTION, "warning"),
        _zone(EcologyEvidenceKind.DEMO_RESTRICTION, "exclusion"),
    )
    first = assess_ecology(site.id, find_ecology_overlaps(site, areas))
    second = assess_ecology(site.id, find_ecology_overlaps(site, tuple(reversed(areas))))
    assert first == second
    assert first.status is EcologyStatus.EXCLUDED
    assert first.evidence_ids == ("exclusion", "warning")


def test_invalid_or_non_finite_spatial_input_is_rejected() -> None:
    site = _site()
    with pytest.raises(ValueError, match="coordinate"):
        find_ecology_overlaps(replace(site, longitude=float("nan")), ())
    malformed = replace(
        _zone(EcologyEvidenceKind.DEMO_RESTRICTION),
        geometry={
            "type": "Polygon",
            "coordinates": [[(31.9, 53.9), (32.1, 54.1), (32.1, 53.9), (31.9, 54.1), (31.9, 53.9)]],
        },
    )
    with pytest.raises(ValueError, match="geometry"):
        find_ecology_overlaps(site, (malformed,))
    outside_wgs84 = replace(
        _zone(EcologyEvidenceKind.DEMO_RESTRICTION),
        geometry={
            "type": "Polygon",
            "coordinates": [[(200.0, 54.0), (201.0, 54.0), (201.0, 55.0), (200.0, 54.0)]],
        },
    )
    with pytest.raises(ValueError, match="WGS84"):
        find_ecology_overlaps(site, (outside_wgs84,))


def test_missing_evidence_identifiers_are_rejected_by_policy() -> None:
    site = _site()
    zone = replace(_zone(EcologyEvidenceKind.DEMO_RESTRICTION), evidence_id="")
    with pytest.raises(ValueError, match="evidence"):
        find_ecology_overlaps(site, (zone,))
