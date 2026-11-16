"""Stable identifiers for the explicitly configured fictional scenario provider.

The generic ScenarioProvider contract belongs to sources.api. Concrete fixture
construction and provider execution live in this package's feature modules.
"""

SYNTHETIC_SCENARIO_ID = "synthetic-ru-2026-v01"
SYNTHETIC_ECOLOGY_SCENARIO_ID = "synthetic-ru-2026-v04-ecology"
SYNTHETIC_TREATMENT_SCENARIO_ID = "synthetic-ru-2026-v04-treatment"
SYNTHETIC_COMBINED_SCENARIO_ID = "synthetic-ru-2026-v04-ecology-treatment"
SYNTHETIC_TERRITORY_ID = "ru:region:smolensk"

__all__ = [
    "SYNTHETIC_SCENARIO_ID",
    "SYNTHETIC_ECOLOGY_SCENARIO_ID",
    "SYNTHETIC_TREATMENT_SCENARIO_ID",
    "SYNTHETIC_COMBINED_SCENARIO_ID",
    "SYNTHETIC_TERRITORY_ID",
]
