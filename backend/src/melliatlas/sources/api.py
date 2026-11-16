"""Public source-provider boundary, independent of concrete source adapters."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol, runtime_checkable

from melliatlas.planning import SyntheticScenario
from melliatlas.sources.notices import TreatmentNotice, TreatmentProduct
from melliatlas.territories.api import CountryCode


@dataclass(frozen=True)
class ScenarioListing:
    """Executable scenario metadata; advertised coverage is provider-owned."""

    id: str
    name: str
    country: CountryCode
    territory_id: str
    territory_name: str
    source_mode: Literal["SYNTHETIC"]
    season_start: date
    season_end: date
    is_default: bool


class SourceReadError(RuntimeError):
    """Live source could not be read or validated; never assume no notices."""


@dataclass(frozen=True)
class TreatmentNoticePage:
    """One bounded source read. Empty or partial pages never establish coverage."""

    source_id: str
    country: CountryCode
    region_code: int
    captured_at: datetime
    page_number: int
    next_page: int | None
    total_elements: int | None
    unidentified_records: int
    notices: tuple[TreatmentNotice, ...]


@runtime_checkable
class TreatmentNoticeReader(Protocol):
    """Explicit on-demand read with no implicit polling or synthetic fallback."""

    def read_page(
        self,
        *,
        country: CountryCode,
        region_code: int,
        page_number: int,
        district_code: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TreatmentNoticePage: ...


@dataclass(frozen=True)
class ForecastHour:
    """UTC forecast values for one hour; missing measurements stay nullable."""

    time: datetime
    wind_speed_kmh: float | None
    wind_direction_degrees: float | None
    wind_gusts_kmh: float | None
    precipitation_mm: float | None


@dataclass(frozen=True)
class WeatherForecast:
    """Attributed model forecast, never an observation or pesticide-drift estimate."""

    source_id: str
    source_uri: str
    captured_at: datetime
    requested_latitude: float
    requested_longitude: float
    grid_latitude: float
    grid_longitude: float
    hours: tuple[ForecastHour, ...]
    uncertainties: tuple[str, ...]


@runtime_checkable
class WeatherForecastReader(Protocol):
    """Read a bounded forecast for an explicitly requested WGS84 point."""

    def forecast(self, *, latitude: float, longitude: float) -> WeatherForecast: ...


@runtime_checkable
class ScenarioProvider(Protocol):
    """Load explicit scenarios and expose only actually executable definitions.

    No implicit network access, synthetic fallback or live-source interpretation
    is imposed by this interface. The current scenario model is MVP fixture-only.
    """

    def load(
        self, *, country: CountryCode, territory_id: str, scenario_id: str
    ) -> SyntheticScenario | None: ...

    def list_scenarios(self, country: CountryCode) -> tuple[ScenarioListing, ...]: ...


__all__ = [
    "ScenarioListing",
    "ScenarioProvider",
    "TreatmentNotice",
    "TreatmentProduct",
    "TreatmentNoticePage",
    "TreatmentNoticeReader",
    "SourceReadError",
    "ForecastHour",
    "WeatherForecast",
    "WeatherForecastReader",
]
