"""Derive the fictional ecology-screening scenario and demo exclusion zones.

No source polygon in this module is evidence of an actual legal restriction,
protected habitat, or safe candidate-site selection.
"""

from dataclasses import replace

from melliatlas.planning import EcologyEvidenceKind, EcologyZone, EvidenceSummary, SyntheticScenario

from .api import SYNTHETIC_ECOLOGY_SCENARIO_ID


def ecology_scenario(original: SyntheticScenario) -> SyntheticScenario:
    alternative = replace(
        original.candidates[0],
        id="fixture-site-alpha-alternative",
        longitude=32.1,
        evidence_id="fixture-evidence-alpha-alternative",
    )
    candidates = (original.candidates[0], alternative, *original.candidates[1:])
    evidence = (
        *original.evidence,
        EvidenceSummary(
            id=alternative.evidence_id,
            source_id="fixture:fictional-forage-windows",
            source_mode="FIXTURE",
            synthetic=True,
            effective_window=alternative.forage_window,
            uncertainty="Fictional alternative with no real geographical or forage validity",
        ),
        EvidenceSummary(
            id="fixture-ecology-exclusion",
            source_id="fixture:fictional-ecology-zones",
            source_mode="FIXTURE",
            synthetic=True,
            effective_window=original.supported_season,
            uncertainty="Demonstration-only exclusion, not a legal restriction",
        ),
        EvidenceSummary(
            id="fixture-ecology-precaution",
            source_id="fixture:fictional-ecology-zones",
            source_mode="FIXTURE",
            synthetic=True,
            effective_window=original.supported_season,
            uncertainty="Demonstration-only precaution, not verified ecology",
        ),
    )
    zones = (
        EcologyZone(
            evidence_id="fixture-ecology-exclusion",
            rule_id="demo-rule-exclusion",
            kind=EcologyEvidenceKind.DEMO_RESTRICTION,
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        (31.95, 53.9),
                        (32.05, 53.9),
                        (32.05, 54.3),
                        (31.95, 54.3),
                        (31.95, 53.9),
                    ]
                ],
            },
        ),
        EcologyZone(
            evidence_id="fixture-ecology-precaution",
            rule_id="demo-rule-precaution",
            kind=EcologyEvidenceKind.DEMO_PRECAUTION,
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        (31.9, 53.9),
                        (32.5, 53.9),
                        (32.5, 54.3),
                        (31.9, 54.3),
                        (31.9, 53.9),
                    ]
                ],
            },
        ),
    )
    return replace(
        original,
        id=SYNTHETIC_ECOLOGY_SCENARIO_ID,
        reference_version="SYNTHETIC-V04-ECOLOGY-NOT-REAL-GEOGRAPHY",
        candidates=candidates,
        evidence=evidence,
        ecology_zones=zones,
        limitations=original.limitations
        + (
            "Fictional ecology polygons do not establish any legal or biological restrictions",
            "CAUTION is non-binding; outside the demo zones ecological coverage is unknown",
        ),
    )
