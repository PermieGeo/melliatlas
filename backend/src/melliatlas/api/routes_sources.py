"""Explicit source capability listing and bounded, RU-only Saturn live observations."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse
from melliatlas.sources.api import SourceReadError, TreatmentNoticeReader, WeatherForecastReader
from melliatlas.territories.api import CountryCode, GeometryWgs84


class SourceListingDto(BaseModel):
    id: Literal["saturn", "open-meteo"]
    country: CountryCode
    kind: Literal["TREATMENT_NOTICE", "WEATHER_FORECAST"]
    mode: Literal["LIVE"]
    status: Literal["EXPERIMENTAL"]


class SaturnPageRequestDto(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: CountryCode
    region_code: int = Field(strict=True, ge=1, le=999999)
    page_number: int = Field(default=0, strict=True, ge=0, le=50)


class SaturnProductDto(BaseModel):
    name: str | None
    crop: str | None
    reported_bee_hazard_class: Literal[1, 2, 3] | None


class SaturnNoticeDto(BaseModel):
    record_id: str
    plan_id: str | None
    country: Literal["RU"]
    source_id: str
    source_uri: str | None
    source_mode: Literal["LIVE"]
    synthetic: Literal[False]
    captured_at: datetime
    published_at: datetime | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    revised: bool | None
    cadastral_number: str | None
    geometry: GeometryWgs84 | None
    products: tuple[SaturnProductDto, ...]
    uncertainties: tuple[str, ...]


class SaturnPageDto(BaseModel):
    source_id: str
    country: Literal["RU"]
    region_code: int
    captured_at: datetime
    page_number: int
    next_page: int | None
    total_elements: int | None
    unidentified_records: int
    notices: tuple[SaturnNoticeDto, ...]
    coverage_complete: Literal[False] = False


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


def _failure(status: int, code: ApiErrorCode, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(
            mode="json"
        ),
    )


def create_source_router(
    reader: TreatmentNoticeReader | None, weather: WeatherForecastReader | None = None
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/sources", tags=["sources"])

    @router.get("", response_model=list[SourceListingDto])
    async def list_sources(country: CountryCode) -> list[SourceListingDto]:
        sources: list[SourceListingDto] = []
        if country is CountryCode.RU and reader is not None:
            sources.append(
                SourceListingDto(
                    id="saturn",
                    country=country,
                    kind="TREATMENT_NOTICE",
                    mode="LIVE",
                    status="EXPERIMENTAL",
                )
            )
        if weather is not None:
            sources.append(
                SourceListingDto(
                    id="open-meteo",
                    country=country,
                    kind="WEATHER_FORECAST",
                    mode="LIVE",
                    status="EXPERIMENTAL",
                )
            )
        return sources

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
        if weather is None:
            return _failure(
                503, ApiErrorCode.SOURCE_NOT_AVAILABLE, "Weather forecast reading is disabled"
            )
        try:
            value = await run_in_threadpool(
                weather.forecast, latitude=body.latitude, longitude=body.longitude
            )
        except SourceReadError:
            return _failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The weather forecast could not be read or validated",
            )
        if (
            value.requested_latitude != body.latitude
            or value.requested_longitude != body.longitude
            or value.source_id != "open-meteo:forecast"
            or len(value.hours) != 24
        ):
            return _failure(
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

    @router.post(
        "/saturn/treatments",
        response_model=SaturnPageDto,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def read_saturn_treatments(body: SaturnPageRequestDto) -> SaturnPageDto | JSONResponse:
        if body.country is not CountryCode.RU:
            return _failure(
                404, ApiErrorCode.SOURCE_NOT_AVAILABLE, "Saturn is not available for this country"
            )
        if reader is None:
            return _failure(
                503, ApiErrorCode.SOURCE_NOT_AVAILABLE, "Saturn live reading is disabled"
            )
        try:
            page = await run_in_threadpool(
                reader.read_page,
                country=body.country,
                region_code=body.region_code,
                page_number=body.page_number,
            )
        except SourceReadError:
            # Never expose upstream URLs, credentials, HTML, or provider errors.
            return _failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The Saturn public feed could not be read or validated",
            )
        if (
            page.country is not CountryCode.RU
            or page.region_code != body.region_code
            or page.page_number != body.page_number
            or len(page.notices) > 10
            or any(
                notice.country is not CountryCode.RU
                or notice.source_id != page.source_id
                or notice.source_mode != "LIVE"
                or notice.synthetic is not False
                for notice in page.notices
            )
        ):
            return _failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The Saturn provider returned mismatched scope",
            )
        return SaturnPageDto(
            source_id=page.source_id,
            country="RU",
            region_code=page.region_code,
            captured_at=page.captured_at,
            page_number=page.page_number,
            next_page=page.next_page,
            total_elements=page.total_elements,
            unidentified_records=page.unidentified_records,
            notices=tuple(
                SaturnNoticeDto(
                    record_id=item.record_id,
                    plan_id=item.plan_id,
                    country="RU",
                    source_id=item.source_id,
                    source_uri=item.source_uri,
                    source_mode="LIVE",
                    synthetic=False,
                    captured_at=item.captured_at,
                    published_at=item.published_at,
                    scheduled_start=item.scheduled_start,
                    scheduled_end=item.scheduled_end,
                    revised=item.revised,
                    cadastral_number=item.cadastral_number,
                    geometry=item.geometry,
                    products=tuple(
                        SaturnProductDto(
                            name=product.name,
                            crop=product.crop,
                            reported_bee_hazard_class=product.reported_bee_hazard_class,
                        )
                        for product in item.products
                    ),
                    uncertainties=item.uncertainties,
                )
                for item in page.notices
            ),
        )

    return router
