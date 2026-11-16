"""Source-neutral HTTP catalog and sanitized error envelope.

Provider routes register capabilities at composition; this module is unaware
of any individual country, provider name or provider-specific endpoint.
"""

from collections.abc import Callable, Sequence
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse
from melliatlas.territories.api import CountryCode


class SourceListingDto(BaseModel):
    id: str
    country: CountryCode
    kind: Literal["TREATMENT_NOTICE", "WEATHER_FORECAST"]
    mode: Literal["LIVE"]
    status: Literal["EXPERIMENTAL"]


SourceCapability = Callable[[CountryCode], SourceListingDto | None]


def source_failure(status: int, code: ApiErrorCode, message: str) -> JSONResponse:
    """Return only sanitized messages, never upstream exception text."""
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(
            mode="json"
        ),
    )


def create_source_router(capabilities: Sequence[SourceCapability]) -> APIRouter:
    """Advertise only active providers with explicit country compatibility."""
    router = APIRouter(prefix="/api/v1/sources", tags=["sources"])

    @router.get("", response_model=list[SourceListingDto])
    async def list_sources(country: CountryCode) -> list[SourceListingDto]:
        return [entry for capability in capabilities if (entry := capability(country)) is not None]

    return router
