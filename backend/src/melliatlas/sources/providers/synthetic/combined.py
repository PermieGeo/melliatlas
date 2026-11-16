"""Merge independently attributed fictional ecology and treatment evidence.

The joint scenario retains each fixture's identity and limitations, and never
changes a missing source observation into a safety determination.
"""

from dataclasses import replace

from melliatlas.planning import SyntheticScenario

from .api import SYNTHETIC_COMBINED_SCENARIO_ID
from .ecology import ecology_scenario
from .treatment_scenarios import treatment_scenario


def combined_scenario(original: SyntheticScenario) -> SyntheticScenario:
    ecology = ecology_scenario(original)
    treatments = treatment_scenario(original)
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
