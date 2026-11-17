"""Small explicit composition root for source providers and scenario planners."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Mapping

from melliatlas.agent import DeterministicPlanner, TreatmentPlanner
from melliatlas.analyzers import find_ecology_overlaps, screen_treatment_notices
from melliatlas.jobs import EcologyPlannerFactory, TreatmentPlannerFactory
from melliatlas.persistence.api import WeatherProviderConfig
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


def _open_meteo_reader(config: WeatherProviderConfig) -> WeatherForecastReader:
    from melliatlas.sources.providers.weather import OpenMeteoForecastReader
    from melliatlas.sources.providers.weather.http import get_public_forecast
    from melliatlas.sources.providers.weather.settings import WeatherTransportSettings

    settings = WeatherTransportSettings(
        forecast_url=config.forecast_url,
        source_uri=config.source_uri,
        timeout_seconds=config.timeout_seconds,
        max_body_bytes=config.max_body_bytes,
    )
    return OpenMeteoForecastReader(
        partial(get_public_forecast, settings=settings), source_uri=settings.source_uri
    )


# Registered factories implement provider wire formats; the database owns endpoint URLs.
_WEATHER_READER_FACTORIES: Final[
    Mapping[str, Callable[[WeatherProviderConfig], WeatherForecastReader]]
] = MappingProxyType({"open-meteo": _open_meteo_reader})


def compose_weather_reader(
    enabled: bool, options: WeatherProviderConfig | None = None
) -> WeatherForecastReader | None:
    """Select one explicitly implemented weather adapter from the DB provider identity."""
    if not enabled:
        return None
    if options is None:
        raise ValueError("Live weather requires an explicit provider configuration")
    factory = _WEATHER_READER_FACTORIES.get(options.provider_id)
    if factory is None:
        raise ValueError("Weather provider is not implemented")
    return factory(options)
