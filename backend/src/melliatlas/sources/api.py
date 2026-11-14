"""Offline and explicitly fictional source fixture for the first investigation slice."""

from datetime import date

from melliatlas.planning.api import (
    CandidateSite,
    EvidenceSummary,
    SyntheticScenario,
    TimeWindow,
)
from melliatlas.territories.api import CountryCode

SYNTHETIC_SCENARIO_ID = "synthetic-ru-2026-v01"
_SYNTHETIC_TERRITORY_ID = "ru:region:smolensk"


class SyntheticFixtureProvider:
    """A fixed offline source; its territory name does not attest to real reference coverage."""

    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None:
        if (
            country != CountryCode.RU
            or territory_id != _SYNTHETIC_TERRITORY_ID
            or scenario_id != SYNTHETIC_SCENARIO_ID
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
        return SyntheticScenario(
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
