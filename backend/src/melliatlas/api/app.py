"""FastAPI application composition."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse, HealthResponse
from melliatlas.api.reference_loader import read_reference_documents
from melliatlas.api.routes_investigations import create_investigation_router
from melliatlas.api.routes_territories import create_territory_router
from melliatlas.jobs.api import InMemoryInvestigationService, InvestigationService
from melliatlas.sources.api import SyntheticFixtureProvider
from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import TerritoryCatalog


@dataclass(frozen=True)
class AppSettings:
    title: str = "MelliAtlas"
    version: str = "0.1.0"
    reference_snapshot_path: Path | None = None
    reference_inventory_path: Path | None = None


def create_app(
    *,
    settings: AppSettings | None = None,
    territories: TerritoryCatalog | None = None,
    investigations: InvestigationService | None = None,
) -> FastAPI:
    config = settings if settings is not None else AppSettings()
    snapshot_path = config.reference_snapshot_path
    inventory_path = config.reference_inventory_path
    if (snapshot_path is None) != (inventory_path is None):
        raise ValueError("Both reference snapshot and independent inventory paths are required")
    if snapshot_path is not None and territories is not None:
        raise ValueError("Explicit territory injection cannot be combined with reference files")

    loaded_catalog = InMemoryTerritoryCatalog() if snapshot_path is not None else None

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        if snapshot_path is not None and inventory_path is not None and loaded_catalog is not None:
            snapshot, inventory = await run_in_threadpool(
                read_reference_documents, snapshot_path, inventory_path
            )
            await loaded_catalog.apply_reference(snapshot, inventory)
        yield

    app = FastAPI(title=config.title, version=config.version, lifespan=lifespan)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.exception_handler(RequestValidationError)
    async def request_validation_failure(
        _request: Request, _error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ApiErrorCode.INVALID_REQUEST,
                    message="Request validation failed",
                )
            ).model_dump(mode="json"),
        )

    active_catalog = territories if territories is not None else loaded_catalog
    app.include_router(create_territory_router(active_catalog))
    job_service = (
        investigations
        if investigations is not None
        else InMemoryInvestigationService(SyntheticFixtureProvider())
    )
    app.include_router(create_investigation_router(job_service))
    return app
