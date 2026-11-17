"""Small explicit composition root for source providers and scenario planners."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING

from melliatlas.agent import DeterministicPlanner, TreatmentPlanner
from melliatlas.analyzers import find_ecology_overlaps, screen_treatment_notices
from melliatlas.jobs import EcologyPlannerFactory, TreatmentPlannerFactory
from melliatlas.planning import (
    CandidateSite,
    SiteAssessment,
    SyntheticScenario,
    TreatmentScreening,
    assess_ecology,
)
from melliatlas.sources.api import (
    ScenarioListing,
    ScenarioProvider,
    TreatmentNoticeReader,
    WeatherForecastReader,
)
from melliatlas.territories.api import CountryCode

if TYPE_CHECKING:
    from melliatlas.sources.providers.synthetic import SyntheticFixtureProvider
    from melliatlas.sources.providers.weather.settings import WeatherTransportSettings


class SourceProviderMode(StrEnum):
    """Explicit source selection; disabled prevents accidental fixture execution."""

    DISABLED = "disabled"
    SYNTHETIC = "synthetic"


@dataclass(frozen=True)
class SourceComposition:
    """Provider and optional decision collaborators assembled at startup."""

    provider: ScenarioProvider
    ecology_factory: EcologyPlannerFactory | None = None
    treatment_factory: TreatmentPlannerFactory | None = None


class _DisabledScenarioProvider:
    """Fail-closed absence of a configured investigation source."""

    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None:
        return None

    def list_scenarios(self, country: CountryCode) -> tuple[ScenarioListing, ...]:
        return ()


def _synthetic_ecology_planner(scenario: SyntheticScenario) -> DeterministicPlanner:
    def inspect(site: CandidateSite) -> SiteAssessment:
        return assess_ecology(site.id, find_ecology_overlaps(site, scenario.ecology_zones))

    return DeterministicPlanner(inspect)


def _synthetic_treatment_planner(
    provider: SyntheticFixtureProvider, scenario: SyntheticScenario
) -> TreatmentPlanner:
    notices = provider.load_treatment_notices(scenario.id)
    if not notices:
        raise ValueError("Required fictional treatment claims are unavailable")

    def inspect(site: CandidateSite) -> tuple[TreatmentScreening, ...]:
        return screen_treatment_notices(site, notices)

    return TreatmentPlanner(inspect)


def compose_sources(mode: SourceProviderMode) -> SourceComposition:
    """Construct provider-owned adapters only for an explicitly selected mode."""
    if mode is SourceProviderMode.DISABLED:
        return SourceComposition(provider=_DisabledScenarioProvider())
    if mode is SourceProviderMode.SYNTHETIC:
        from melliatlas.sources.providers.synthetic import SyntheticFixtureProvider

        provider = SyntheticFixtureProvider()
        return SourceComposition(
            provider=provider,
            ecology_factory=_synthetic_ecology_planner,
            treatment_factory=lambda scenario: _synthetic_treatment_planner(provider, scenario),
        )
    raise ValueError(f"Unsupported source provider mode: {mode}")


def compose_saturn_reader(enabled: bool) -> TreatmentNoticeReader | None:
    """Create the opt-in RU-only live transport, separate from scenario selection."""
    if not enabled:
        return None
    from melliatlas.sources.providers.saturn import SaturnPublicTreatmentReader
    from melliatlas.sources.providers.saturn.http import post_public_page

    return SaturnPublicTreatmentReader(post_public_page)


def compose_weather_reader(
    enabled: bool, options: "WeatherTransportSettings | None" = None
) -> WeatherForecastReader | None:
    """Opt into Open-Meteo reads without creating a global source registry."""
    if not enabled:
        return None
    from melliatlas.sources.providers.weather import OpenMeteoForecastReader
    from melliatlas.sources.providers.weather.http import get_public_forecast
    from melliatlas.sources.providers.weather.settings import SOURCE_URI

    return OpenMeteoForecastReader(
        get_public_forecast if options is None else partial(get_public_forecast, settings=options),
        source_uri=options.source_uri if options is not None else SOURCE_URI,
    )
