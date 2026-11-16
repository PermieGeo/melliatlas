"""Expose deterministic fictional scenarios behind the generic ScenarioProvider port.

The provider advertises only available RU scenarios. Feature-specific fixture
construction is owned by the dedicated forage, ecology and treatment modules.
"""

from melliatlas.planning import SyntheticScenario
from melliatlas.sources.api import ScenarioListing, TreatmentNotice
from melliatlas.territories.api import CountryCode

from .api import (
    SYNTHETIC_COMBINED_SCENARIO_ID,
    SYNTHETIC_ECOLOGY_SCENARIO_ID,
    SYNTHETIC_SCENARIO_ID,
    SYNTHETIC_TERRITORY_ID,
    SYNTHETIC_TREATMENT_SCENARIO_ID,
)
from .combined import combined_scenario
from .ecology import ecology_scenario
from .fixtures import base_scenario
from .treatment_scenarios import treatment_scenario
from .treatments import treatment_fixture_notices


class SyntheticFixtureProvider:
    """Expose only explicitly supported fictional RU planning demonstrations."""

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
                territory_id=SYNTHETIC_TERRITORY_ID,
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
        if country is not CountryCode.RU or territory_id != SYNTHETIC_TERRITORY_ID:
            return None
        if scenario_id not in (
            SYNTHETIC_SCENARIO_ID,
            SYNTHETIC_ECOLOGY_SCENARIO_ID,
            SYNTHETIC_TREATMENT_SCENARIO_ID,
            SYNTHETIC_COMBINED_SCENARIO_ID,
        ):
            return None
        original = base_scenario()
        if scenario_id == SYNTHETIC_SCENARIO_ID:
            return original
        if scenario_id == SYNTHETIC_ECOLOGY_SCENARIO_ID:
            return ecology_scenario(original)
        if scenario_id == SYNTHETIC_TREATMENT_SCENARIO_ID:
            return treatment_scenario(original)
        return combined_scenario(original)

    def load_treatment_notices(self, scenario_id: str) -> tuple[TreatmentNotice, ...] | None:
        """Expose fixture claims only for treatment-aware demonstration scenarios."""
        if scenario_id not in (SYNTHETIC_TREATMENT_SCENARIO_ID, SYNTHETIC_COMBINED_SCENARIO_ID):
            return None
        return treatment_fixture_notices()
