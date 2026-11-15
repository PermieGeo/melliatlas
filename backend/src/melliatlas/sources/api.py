"""Offline and explicitly fictional source fixture for the first investigation slice."""

from dataclasses import dataclass, replace
from datetime import date
from typing import Literal

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
from melliatlas.sources.synthetic_treatments import (
    TREATMENT_FIXTURE_RECORD_ID,
    TREATMENT_FIXTURE_SOURCE_ID,
    treatment_fixture_notices,
)
from melliatlas.territories.api import CountryCode

SYNTHETIC_SCENARIO_ID = "synthetic-ru-2026-v01"
SYNTHETIC_ECOLOGY_SCENARIO_ID = "synthetic-ru-2026-v04-ecology"
SYNTHETIC_TREATMENT_SCENARIO_ID = "synthetic-ru-2026-v04-treatment"
SYNTHETIC_COMBINED_SCENARIO_ID = "synthetic-ru-2026-v04-ecology-treatment"
_SYNTHETIC_TERRITORY_ID = "ru:region:smolensk"


@dataclass(frozen=True)
class ScenarioListing:
    """Public metadata for an executable fictional scenario, not a geography catalog."""

    id: str
    name: str
    country: CountryCode
    territory_id: str
    territory_name: str
    source_mode: Literal["SYNTHETIC"]
    season_start: date
    season_end: date
    is_default: bool


class SyntheticFixtureProvider:
    """A fixed offline source; its territory name does not attest to real reference coverage."""

    def list_scenarios(self, country: CountryCode) -> tuple[ScenarioListing, ...]:
        """Describe scenarios actually supported by this provider for a country."""
        definitions = (
            (SYNTHETIC_COMBINED_SCENARIO_ID, "Ecology and reported treatments"),
            (SYNTHETIC_ECOLOGY_SCENARIO_ID, "Ecology screening"),
            (SYNTHETIC_TREATMENT_SCENARIO_ID, "Reported treatment screening"),
            (SYNTHETIC_SCENARIO_ID, "Forage windows"),
        )
        available: list[ScenarioListing] = []
        for identifier, name in definitions:
            scenario = self.load(
                country=country,
                territory_id=_SYNTHETIC_TERRITORY_ID,
                scenario_id=identifier,
            )
            if scenario is None:
                continue
            available.append(
                ScenarioListing(
                    id=scenario.id,
                    name=f"{name} (fictional)",
                    country=scenario.country,
                    territory_id=scenario.territory_id,
                    territory_name="Smolensk region (fictional)",
                    source_mode="SYNTHETIC",
                    season_start=scenario.supported_season.start,
                    season_end=scenario.supported_season.end,
                    is_default=identifier == SYNTHETIC_COMBINED_SCENARIO_ID,
                )
            )
        return tuple(available)

    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None:
        if country != CountryCode.RU or territory_id != _SYNTHETIC_TERRITORY_ID:
            return None
        if scenario_id not in (
            SYNTHETIC_SCENARIO_ID,
            SYNTHETIC_ECOLOGY_SCENARIO_ID,
            SYNTHETIC_TREATMENT_SCENARIO_ID,
            SYNTHETIC_COMBINED_SCENARIO_ID,
        ):
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

        if scenario_id == SYNTHETIC_COMBINED_SCENARIO_ID:
            ecology = self.load(
                country=country,
                territory_id=territory_id,
                scenario_id=SYNTHETIC_ECOLOGY_SCENARIO_ID,
            )
            treatments = self.load(
                country=country,
                territory_id=territory_id,
                scenario_id=SYNTHETIC_TREATMENT_SCENARIO_ID,
            )
            if ecology is None or treatments is None:
                raise ValueError("Combined fictional reference scenarios are unavailable")
            ecology_ids = {item.id for item in ecology.candidates}
            evidence_ids = {item.id for item in ecology.evidence}
            return replace(
                ecology,
                id=SYNTHETIC_COMBINED_SCENARIO_ID,
                reference_version="SYNTHETIC-V04-JOINT-NOT-REAL-APPLICATIONS",
                candidates=ecology.candidates
                + tuple(item for item in treatments.candidates if item.id not in ecology_ids),
                evidence=ecology.evidence
                + tuple(item for item in treatments.evidence if item.id not in evidence_ids),
                treatment_screening_required=True,
                limitations=ecology.limitations
                + tuple(item for item in treatments.limitations if item not in ecology.limitations),
            )

        if scenario_id == SYNTHETIC_TREATMENT_SCENARIO_ID:
            notices = treatment_fixture_notices()
            notice = notices[0]
            if notice.scheduled_start is None or notice.scheduled_end is None:
                raise ValueError("Synthetic treatment fixture is missing planned dates")
            alternative = replace(
                original.candidates[0],
                id="fixture-site-alpha-treatment-alternative",
                longitude=32.16,
                evidence_id="fixture-evidence-alpha-treatment-alternative",
            )
            return replace(
                original,
                id=SYNTHETIC_TREATMENT_SCENARIO_ID,
                reference_version="SYNTHETIC-V04-TREATMENT-NOT-REAL-APPLICATIONS",
                candidates=(original.candidates[0], alternative, *original.candidates[1:]),
                evidence=original.evidence
                + (
                    EvidenceSummary(
                        id=alternative.evidence_id,
                        source_id="fixture:fictional-forage-windows",
                        source_mode="FIXTURE",
                        synthetic=True,
                        effective_window=alternative.forage_window,
                        uncertainty=(
                            "Illustrative alternative without verified field or forage data"
                        ),
                    ),
                    EvidenceSummary(
                        id=notice.record_id,
                        source_id=notice.source_id,
                        source_mode="FIXTURE",
                        synthetic=True,
                        effective_window=TimeWindow(
                            notice.scheduled_start.date(), notice.scheduled_end.date()
                        ),
                        uncertainty=(
                            "Historical-shaped fictional treatment notice; no live spraying evidence"
                        ),
                    ),
                ),
                treatment_screening_required=True,
                limitations=original.limitations
                + (
                    "Treatment notice is a synthetic exercise, not a real agricultural warning",
                    "Absence of nearby notices does not establish coverage or site safety",
                ),
            )

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

    def load_treatment_notices(self, scenario_id: str) -> tuple[TreatmentNotice, ...] | None:
        """Return fictional treatment claims only for the explicit treatment scenario."""
        if scenario_id not in (
            SYNTHETIC_TREATMENT_SCENARIO_ID,
            SYNTHETIC_COMBINED_SCENARIO_ID,
        ):
            return None
        return treatment_fixture_notices()


# These are intentional public re-exports and must survive Ruff auto-fix.
__all__ = [
    "SYNTHETIC_SCENARIO_ID",
    "SYNTHETIC_ECOLOGY_SCENARIO_ID",
    "SYNTHETIC_TREATMENT_SCENARIO_ID",
    "SYNTHETIC_COMBINED_SCENARIO_ID",
    "SyntheticFixtureProvider",
    "TreatmentProduct",
    "TreatmentNotice",
    "SaturnTreatmentPage",
    "parse_saturn_treatment_page",
    "next_saturn_treatment_page",
    "TREATMENT_FIXTURE_RECORD_ID",
    "TREATMENT_FIXTURE_SOURCE_ID",
]
