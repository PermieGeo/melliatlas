"""Validated on-demand name lookup, with no implicit background requests."""

from typing import Literal

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse
from melliatlas.sources.api import SettlementReader, SourceReadError
from melliatlas.territories.api import CountryCode


class SettlementSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: CountryCode
    query: str = Field(min_length=2, max_length=100)
    language: Literal["ru", "en"] = "ru"


class SettlementResponse(BaseModel):
    id: int
    name: str
    country: CountryCode
    admin1: str | None
    latitude: float
    longitude: float
    source_uri: str


def create_geocoding_router(reader: SettlementReader) -> APIRouter:
    router = APIRouter(prefix="/api/v1/sources/geocoding", tags=["geocoding"])

    @router.post(
        "/settlements",
        response_model=list[SettlementResponse],
        responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    )
    async def search_settlements(
        request: SettlementSearchRequest,
    ) -> list[SettlementResponse] | JSONResponse:
        if not request.query.strip() or len(request.query.strip()) < 2:
            response = ErrorResponse(
                error=ErrorDetail(code=ApiErrorCode.INVALID_REQUEST, message="Invalid search query")
            )
            return JSONResponse(status_code=422, content=response.model_dump(mode="json"))
        try:
            matches = await run_in_threadpool(
                reader.search,
                country=request.country,
                query=request.query.strip(),
                language=request.language,
            )
        except SourceReadError:
            response = ErrorResponse(
                error=ErrorDetail(
                    code=ApiErrorCode.SOURCE_READ_FAILED,
                    message="Settlement source is unavailable or invalid",
                )
            )
            return JSONResponse(status_code=502, content=response.model_dump(mode="json"))
        return [SettlementResponse.model_validate(item, from_attributes=True) for item in matches]

    return router
