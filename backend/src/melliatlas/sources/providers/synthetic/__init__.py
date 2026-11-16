"""Public synthetic-provider package facade for explicit application composition."""

from .api import (
    SYNTHETIC_COMBINED_SCENARIO_ID,
    SYNTHETIC_ECOLOGY_SCENARIO_ID,
    SYNTHETIC_SCENARIO_ID,
    SYNTHETIC_TREATMENT_SCENARIO_ID,
)
from .provider import SyntheticFixtureProvider

__all__ = [
    "SYNTHETIC_SCENARIO_ID",
    "SYNTHETIC_ECOLOGY_SCENARIO_ID",
    "SYNTHETIC_TREATMENT_SCENARIO_ID",
    "SYNTHETIC_COMBINED_SCENARIO_ID",
    "SyntheticFixtureProvider",
]
