"""Offline and explicitly fictional source fixture for the first investigation slice."""

from dataclasses import replace
from datetime import date

from melliatlas.planning.api import (
    CandidateSite,
    EcologyEvidenceKind,
    EcologyZone,
    EvidenceSummary,
    SyntheticScenario,
    TimeWindow,
)
from melliatlas.sources.notices import TreatmentNotice, TreatmentProduct
from melliatlas.sources.providers.saturn.legacy_treatment import parse_saturn_treatment_page
from melliatlas.sources.providers.saturn.pagination import (
    SaturnTreatmentPage,
    next_saturn_treatment_page,
)
from melliatlas.territories.api import CountryCode

SYNTHETIC_SCENARIO_ID = "synthetic-ru-2026-v01"
SYNTHETIC_ECOLOGY_SCENARIO_ID = "synthetic-ru-2026-v04-ecology"
_SYNTHETIC_TERRITORY_ID = "ru:region:smolensk"


class SyntheticFixtureProvider:
    """A fixed offline source; its territory name does not attest to real reference coverage."""

    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None:
        if country != CountryCode.RU or territory_id != _SYNTHETIC_TERRITORY_ID:
            return None
        if scenario_id not in (SYNTHETIC_SCENARIO_ID, SYNTHETIC_ECOLOGY_SCENARIO_ID):
            return None

        windows = (
            TimeWindow(date(2026, 5, 1), date(2026, 6, 14)),
            TimeWindow(date(2026, 6, 15), date(2026, 7, 15)),
            TimeWindow(date(2026, 7, 16), date(2026, 8, 15)),
        )
        points = ((32.0, 54.0), (32.2, 54.1), (32.4, 54.2))
        suffixes = ("alpha", "beta", "gamma")
        candidates = tuple(
            CandidateSite(
                id=f"fixture-site-{suffix}",
                longitude=point[0],
                latitude=point[1],
                forage_window=window,
                forage_level="MEDIUM",
                evidence_id=f"fixture-evidence-{suffix}",
            )
            for suffix, point, window in zip(suffixes, points, windows)
        )
        evidence = tuple(
            EvidenceSummary(
                id=site.evidence_id,
                source_id="fixture:fictional-forage-windows",
                source_mode="FIXTURE",
                synthetic=True,
                effective_window=site.forage_window,
                uncertainty="No measured forage coverage or ecological clearance is available",
            )
            for site in candidates
        )
        original = SyntheticScenario(
            id=SYNTHETIC_SCENARIO_ID,
            country=CountryCode.RU,
            territory_id=_SYNTHETIC_TERRITORY_ID,
            supported_season=TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            reference_version="SYNTHETIC-V01-NOT-REAL-GEOGRAPHY",
            candidates=candidates,
            evidence=evidence,
            limitations=(
                "All candidate coordinates and forage windows are synthetic and not verified",
                "Real reference geography, legal exclusions and wild pollinator "
                "effects are unknown",
                "Starting-point travel distance and weather are not evaluated in V01",
                "Results exist in application memory only and disappear after restart",
            ),
        )

        if scenario_id == SYNTHETIC_SCENARIO_ID:
            return original

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


# These are intentional public re-exports and must survive Ruff auto-fix.
__all__ = [
    "SYNTHETIC_SCENARIO_ID",
    "SYNTHETIC_ECOLOGY_SCENARIO_ID",
    "SyntheticFixtureProvider",
    "TreatmentProduct",
    "TreatmentNotice",
    "SaturnTreatmentPage",
    "parse_saturn_treatment_page",
    "next_saturn_treatment_page",
]
