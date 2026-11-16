"""Saturn-specific FastAPI request, country gating and notice projection.

The generic source catalog never knows provider identifiers or page details.
Only the composition root attaches this disabled-by-default live route.
"""

from datetime import datetime
from typing import Literal, Self

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from melliatlas.api.public import ApiErrorCode, ErrorResponse
from melliatlas.api.routes_sources import SourceCapability, SourceListingDto, source_failure
from melliatlas.sources.api import SourceReadError, TreatmentNoticeReader
from melliatlas.sources.providers.saturn.api import MAX_PAGE_RECORDS
from melliatlas.territories.api import (
    CountryCode,
    GeometryWgs84,
    ReferenceUnavailableError,
    SourceTerritoryCodeLookup,
)


class SaturnPageRequestDto(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: CountryCode
    region_code: int | None = Field(default=None, strict=True, ge=1, le=999999)
    region_id: str | None = Field(default=None, min_length=1, max_length=128)
    page_number: int = Field(default=0, strict=True, ge=0, le=50)

    @model_validator(mode="after")
    def require_one_region_identifier(self) -> Self:
        if (self.region_code is None) == (self.region_id is None):
            raise ValueError("Specify exactly one of region_id or region_code")
        return self


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
    region_id: str | None = None


def saturn_capability(reader: TreatmentNoticeReader | None) -> SourceCapability:
    """Advertise only a configured Russian treatment source."""

    def listing(country: CountryCode) -> SourceListingDto | None:
        if country is not CountryCode.RU or reader is None:
            return None
        return SourceListingDto(
            id="saturn",
            country=country,
            kind="TREATMENT_NOTICE",
            mode="LIVE",
            status="EXPERIMENTAL",
        )

    return listing


def create_saturn_router(
    reader: TreatmentNoticeReader | None,
    region_lookup: SourceTerritoryCodeLookup | None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/sources", tags=["sources"])

    @router.post(
        "/saturn/treatments",
        response_model=SaturnPageDto,
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def read_saturn_treatments(body: SaturnPageRequestDto) -> SaturnPageDto | JSONResponse:
        if body.country is not CountryCode.RU:
            return source_failure(
                404, ApiErrorCode.SOURCE_NOT_AVAILABLE, "Saturn is not available for this country"
            )
        if reader is None:
            return source_failure(
                503, ApiErrorCode.SOURCE_NOT_AVAILABLE, "Saturn live reading is disabled"
            )
        region_code = body.region_code
        if body.region_id is not None:
            if region_lookup is None:
                return source_failure(
                    503,
                    ApiErrorCode.TERRITORY_REFERENCE_UNAVAILABLE,
                    "A region directory is not configured",
                )
            try:
                region_code = await region_lookup.find_code(
                    source_id="saturn", country=body.country, region_id=body.region_id
                )
            except ReferenceUnavailableError:
                return source_failure(
                    503,
                    ApiErrorCode.TERRITORY_REFERENCE_UNAVAILABLE,
                    "Region directory is unavailable",
                )
            if region_code is None:
                return source_failure(
                    409,
                    ApiErrorCode.SOURCE_REGION_UNMAPPED,
                    "No verified Saturn mapping exists for this region",
                )
        if region_code is None:
            return source_failure(422, ApiErrorCode.INVALID_REQUEST, "Region is required")
        try:
            page = await run_in_threadpool(
                reader.read_page,
                country=body.country,
                region_code=region_code,
                page_number=body.page_number,
            )
        except SourceReadError:
            # Never expose upstream URLs, credentials, HTML, or provider errors.
            return source_failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The Saturn public feed could not be read or validated",
            )
        if (
            page.country is not CountryCode.RU
            or page.region_code != region_code
            or page.page_number != body.page_number
            or len(page.notices) > MAX_PAGE_RECORDS
            or any(
                notice.country is not CountryCode.RU
                or notice.source_id != page.source_id
                or notice.source_mode != "LIVE"
                or notice.synthetic is not False
                for notice in page.notices
            )
        ):
            return source_failure(
                502,
                ApiErrorCode.SOURCE_READ_FAILED,
                "The Saturn provider returned mismatched scope",
            )
        return SaturnPageDto(
            source_id=page.source_id,
            country="RU",
            region_code=page.region_code,
            region_id=body.region_id,
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
