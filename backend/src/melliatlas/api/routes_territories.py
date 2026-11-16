"""Public HTTP representation of the injected territory catalog."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse
from melliatlas.territories.api import (
    CatalogDepthUnsupported,
    CountryCode,
    GeometryStatus,
    GeometryWgs84,
    ReferenceUnavailableError,
    Territory,
    TerritoryCatalog,
    TerritoryGeometry,
    TerritoryKind,
    TerritoryNotFound,
    TerritoryPointLocator,
    TerritoryReferenceError,
)


class CountryResponse(BaseModel):
    code: CountryCode
    name: str


class TerritoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    country: CountryCode
    kind: TerritoryKind
    name: str
    parent_id: str | None
    reference_id: str
    valid_on: str
    geometry_status: GeometryStatus


class ResolvePointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: CountryCode
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)


class ResolvePointResponse(BaseModel):
    region_id: str
    district_id: str | None


class GeometryResponse(BaseModel):
    territory_id: str
    reference_id: str
    coordinate_system: str
    geometry: GeometryWgs84


def _territory_response(item: Territory) -> TerritoryResponse:
    return TerritoryResponse(
        id=item.id,
        country=item.country,
        kind=item.kind,
        name=item.name,
        parent_id=item.parent_id,
        reference_id=item.reference_id,
        valid_on=item.valid_on.isoformat(),
        geometry_status=item.geometry_status,
    )


def _geometry_response(item: TerritoryGeometry) -> GeometryResponse:
    return GeometryResponse(
        territory_id=item.territory_id,
        reference_id=item.reference_id,
        coordinate_system=item.coordinate_system,
        geometry=item.geometry,
    )


def _failure(status: int, code: ApiErrorCode, message: str) -> JSONResponse:
    response = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status, content=response.model_dump(mode="json"))


def _catalog_failure(exc: Exception) -> JSONResponse:
    if isinstance(exc, ReferenceUnavailableError):
        return _failure(503, ApiErrorCode.TERRITORY_REFERENCE_UNAVAILABLE, str(exc))
    if isinstance(exc, TerritoryNotFound):
        return _failure(404, ApiErrorCode.TERRITORY_NOT_FOUND, "Unknown territory")
    if isinstance(exc, CatalogDepthUnsupported):
        return _failure(
            409,
            ApiErrorCode.DISTRICT_COVERAGE_UNSUPPORTED,
            "District catalog is not supported for this region",
        )
    if isinstance(exc, TerritoryReferenceError):
        return _failure(422, ApiErrorCode.INVALID_TERRITORY_REQUEST, str(exc))
    raise exc


def create_territory_router(catalog: TerritoryCatalog | None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/territories", tags=["territories"])

    @router.get("/countries", response_model=list[CountryResponse])
    async def list_countries() -> list[CountryResponse]:
        return [
            CountryResponse(code=CountryCode.RU, name="Russia"),
            CountryResponse(code=CountryCode.BY, name="Belarus"),
        ]

    @router.get(
        "/regions",
        response_model=list[TerritoryResponse],
        responses={
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def list_regions(country: CountryCode) -> list[TerritoryResponse] | JSONResponse:
        if catalog is None:
            return _catalog_failure(
                ReferenceUnavailableError("No validated territory reference loaded")
            )
        try:
            return [_territory_response(item) for item in await catalog.list_regions(country)]
        except (ReferenceUnavailableError, TerritoryReferenceError) as exc:
            return _catalog_failure(exc)

    @router.get(
        "/districts",
        response_model=list[TerritoryResponse],
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def list_districts(region_id: str) -> list[TerritoryResponse] | JSONResponse:
        if catalog is None:
            return _catalog_failure(
                ReferenceUnavailableError("No validated territory reference loaded")
            )
        try:
            return [_territory_response(item) for item in await catalog.list_districts(region_id)]
        except (
            ReferenceUnavailableError,
            TerritoryNotFound,
            CatalogDepthUnsupported,
            TerritoryReferenceError,
        ) as exc:
            return _catalog_failure(exc)

    @router.post(
        "/resolve-point",
        response_model=ResolvePointResponse,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def resolve_point(body: ResolvePointRequest) -> ResolvePointResponse | JSONResponse:
        if catalog is None or not isinstance(catalog, TerritoryPointLocator):
            return _failure(
                503,
                ApiErrorCode.TERRITORY_REFERENCE_UNAVAILABLE,
                "Point lookup needs imported PostGIS boundaries",
            )
        try:
            located = await catalog.locate_point(
                country=body.country, longitude=body.longitude, latitude=body.latitude
            )
        except ReferenceUnavailableError:
            return _failure(
                503,
                ApiErrorCode.TERRITORY_REFERENCE_UNAVAILABLE,
                "Point lookup is ambiguous or unavailable",
            )
        if located is None:
            return _failure(
                404,
                ApiErrorCode.TERRITORY_NOT_FOUND,
                "No imported region contains the selected point",
            )
        prefix = body.country.value.lower()
        if not located.region_id.startswith(f"{prefix}:region:") or (
            located.district_id is not None
            and not located.district_id.startswith(f"{prefix}:district:")
        ):
            return _failure(
                503,
                ApiErrorCode.TERRITORY_REFERENCE_UNAVAILABLE,
                "Invalid spatial reference identity",
            )
        return ResolvePointResponse(region_id=located.region_id, district_id=located.district_id)

    @router.get(
        "/geometry/{territory_id}",
        response_model=GeometryResponse,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def get_geometry(territory_id: str) -> GeometryResponse | JSONResponse:
        if catalog is None:
            return _catalog_failure(
                ReferenceUnavailableError("No validated territory reference loaded")
            )
        try:
            item = await catalog.get_geometry(territory_id)
        except (ReferenceUnavailableError, TerritoryNotFound, TerritoryReferenceError) as exc:
            return _catalog_failure(exc)
        if item is None:
            return _failure(
                404, ApiErrorCode.TERRITORY_GEOMETRY_MISSING, "No validated geometry for territory"
            )
        return _geometry_response(item)

    @router.get(
        "/{territory_id}",
        response_model=TerritoryResponse,
        responses={
            404: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def get_territory(territory_id: str) -> TerritoryResponse | JSONResponse:
        if catalog is None:
            return _catalog_failure(
                ReferenceUnavailableError("No validated territory reference loaded")
            )
        try:
            item = await catalog.get(territory_id)
        except (ReferenceUnavailableError, TerritoryReferenceError) as exc:
            return _catalog_failure(exc)
        if item is None:
            return _failure(404, ApiErrorCode.TERRITORY_NOT_FOUND, "Unknown territory")
        return _territory_response(item)

    return router
