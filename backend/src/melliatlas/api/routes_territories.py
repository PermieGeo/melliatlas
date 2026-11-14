"""Public HTTP representation of the injected territory catalog."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

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


def _failure(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _catalog_failure(exc: Exception) -> JSONResponse:
    if isinstance(exc, ReferenceUnavailableError):
        return _failure(503, "TERRITORY_REFERENCE_UNAVAILABLE", str(exc))
    if isinstance(exc, TerritoryNotFound):
        return _failure(404, "TERRITORY_NOT_FOUND", "Unknown territory")
    if isinstance(exc, CatalogDepthUnsupported):
        return _failure(
            409,
            "DISTRICT_COVERAGE_UNSUPPORTED",
            "District catalog is not supported for this region",
        )
    if isinstance(exc, TerritoryReferenceError):
        return _failure(422, "INVALID_TERRITORY_REQUEST", str(exc))
    raise exc


def create_territory_router(catalog: TerritoryCatalog | None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/territories", tags=["territories"])

    @router.get("/countries", response_model=list[CountryResponse])
    async def list_countries() -> list[CountryResponse]:
        return [
            CountryResponse(code=CountryCode.RU, name="Russia"),
            CountryResponse(code=CountryCode.BY, name="Belarus"),
        ]

    @router.get("/regions", response_model=list[TerritoryResponse])
    async def list_regions(country: CountryCode) -> list[TerritoryResponse] | JSONResponse:
        if catalog is None:
            return _catalog_failure(
                ReferenceUnavailableError("No validated territory reference loaded")
            )
        try:
            return [_territory_response(item) for item in await catalog.list_regions(country)]
        except (ReferenceUnavailableError, TerritoryReferenceError) as exc:
            return _catalog_failure(exc)

    @router.get("/districts", response_model=list[TerritoryResponse])
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

    @router.get("/geometry/{territory_id}", response_model=GeometryResponse)
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
                404, "TERRITORY_GEOMETRY_MISSING", "No validated geometry for territory"
            )
        return _geometry_response(item)

    @router.get("/{territory_id}", response_model=TerritoryResponse)
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
            return _failure(404, "TERRITORY_NOT_FOUND", "Unknown territory")
        return _territory_response(item)

    return router
