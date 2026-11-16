"""Derive the synthetic treatment-aware demonstration from the base fixture.

This module uses predeclared fictional notices only; it never reads Saturn live
or infers actual spraying, coverage, or beekeeper safety.
"""

from dataclasses import replace

from melliatlas.planning import EvidenceSummary, SyntheticScenario, TimeWindow

from .api import SYNTHETIC_TREATMENT_SCENARIO_ID
from .treatments import treatment_fixture_notices


def treatment_scenario(original: SyntheticScenario) -> SyntheticScenario:
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
                uncertainty=("Illustrative alternative without verified field or forage data"),
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
