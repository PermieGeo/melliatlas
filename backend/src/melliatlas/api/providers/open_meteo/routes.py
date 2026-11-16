"""Weather-specific FastAPI request and normalized forecast projection.

The provider response owns its attribution URL and forecast uncertainty.
Requests remain explicit, read-only and independent of Saturn geography.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from melliatlas.api.public import ApiErrorCode, ErrorResponse
from melliatlas.api.routes_sources import SourceCapability, SourceListingDto, source_failure
from melliatlas.sources.api import SourceReadError, WeatherForecastReader
from melliatlas.sources.providers.open_meteo import FORECAST_HOURS
from melliatlas.territories.api import CountryCode


@dataclass
class WeatherReaderState:
    """Application-scoped reader resolved after optional settings are loaded."""

    reader: WeatherForecastReader | None = None


class WeatherPointRequestDto(BaseModel):
    model_config = ConfigDict(extra="forbid")
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class WeatherHourDto(BaseModel):
    time: datetime
    wind_speed_kmh: float | None
    wind_direction_degrees: float | None
    wind_gusts_kmh: float | None
    precipitation_mm: float | None


class WeatherForecastDto(BaseModel):
    source_id: str
    source_uri: str
    source_mode: Literal["LIVE"]
    synthetic: Literal[False]
    captured_at: datetime
    requested_latitude: float
    requested_longitude: float
    grid_latitude: float
    grid_longitude: float
    hours: tuple[WeatherHourDto, ...]
    uncertainties: tuple[str, ...]


def weather_capability(state: WeatherReaderState) -> SourceCapability:
    """Keep forecast discovery country-neutral and enabled only by server policy."""

    def listing(country: CountryCode) -> SourceListingDto | None:
        if state.reader is None:
            return None
        return SourceListingDto(
            id="open-meteo",
            country=country,
            kind="WEATHER_FORECAST",
            mode="LIVE",
            status="EXPERIMENTAL",
        )

    return listing


def create_weather_router(state: WeatherReaderState) -> APIRouter:
    router = APIRouter(prefix="/api/v1/sources", tags=["sources"])

    @router.post(
        "/weather/forecast",
        response_model=WeatherForecastDto,
        responses={
            422: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def read_forecast(body: WeatherPointRequestDto) -> WeatherForecastDto | JSONResponse:
        reader = state.reader
        if reader is None:
            return source_failure(
                503, ApiErrorCode.SOURCE_NOT_AVAILABLE, "Weather forecast reading is disabled"
            )
        try:
            value = await run_in_threadpool(
                reader.forecast, latitude=body.latitude, longitude=body.longitude
            )
        except SourceReadError:
            return source_failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The weather forecast could not be read or validated",
            )
        if (
            value.requested_latitude != body.latitude
            or value.requested_longitude != body.longitude
            or value.source_id != "open-meteo:forecast"
            or len(value.hours) != FORECAST_HOURS
        ):
            return source_failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The weather provider returned mismatched scope",
            )
        return WeatherForecastDto(
            source_id=value.source_id,
            source_uri=value.source_uri,
            source_mode="LIVE",
            synthetic=False,
            captured_at=value.captured_at,
            requested_latitude=value.requested_latitude,
            requested_longitude=value.requested_longitude,
            grid_latitude=value.grid_latitude,
            grid_longitude=value.grid_longitude,
            hours=tuple(
                WeatherHourDto(
                    time=hour.time,
                    wind_speed_kmh=hour.wind_speed_kmh,
                    wind_direction_degrees=hour.wind_direction_degrees,
                    wind_gusts_kmh=hour.wind_gusts_kmh,
                    precipitation_mm=hour.precipitation_mm,
                )
                for hour in value.hours
            ),
            uncertainties=value.uncertainties,
        )

    return router
