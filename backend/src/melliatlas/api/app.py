"""FastAPI application composition."""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from melliatlas.api.composition import (
    SourceProviderMode,
    compose_saturn_reader,
    compose_sources,
    compose_weather_reader,
)
from melliatlas.api.providers.open_meteo.routes import (
    WeatherReaderState,
    create_weather_router,
    weather_capability,
)
from melliatlas.api.providers.saturn.routes import create_saturn_router, saturn_capability
from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse, HealthResponse
from melliatlas.api.reference_loader import read_reference_documents
from melliatlas.api.routes_investigations import create_investigation_router
from melliatlas.api.routes_sources import create_source_router
from melliatlas.api.routes_territories import create_territory_router
from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvestigationService,
)
from melliatlas.sources.api import TreatmentNoticeReader, WeatherForecastReader
from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import SourceTerritoryCodeLookup, TerritoryCatalog


@dataclass(frozen=True)
class AppSettings:
    title: str = "MelliAtlas"
    version: str = "0.1.0"
    reference_snapshot_path: Path | None = None
    reference_inventory_path: Path | None = None
    source_provider: SourceProviderMode = SourceProviderMode.DISABLED
    saturn_live_enabled: bool = False
    weather_live_enabled: bool = False


def create_app(
    *,
    settings: AppSettings | None = None,
    territories: TerritoryCatalog | None = None,
    investigations: InvestigationService | None = None,
    saturn_reader: TreatmentNoticeReader | None = None,
    weather_reader: WeatherForecastReader | None = None,
    weather_reader_factory: Callable[[], WeatherForecastReader | None] | None = None,
    source_region_lookup: SourceTerritoryCodeLookup | None = None,
) -> FastAPI:
    config = settings if settings is not None else AppSettings()
    snapshot_path = config.reference_snapshot_path
    inventory_path = config.reference_inventory_path
    if (snapshot_path is None) != (inventory_path is None):
        raise ValueError("Both reference snapshot and independent inventory paths are required")
    if snapshot_path is not None and territories is not None:
        raise ValueError("Explicit territory injection cannot be combined with reference files")

    if weather_reader is not None and weather_reader_factory is not None:
        raise ValueError("Weather reader and weather reader factory are mutually exclusive")

    loaded_catalog = InMemoryTerritoryCatalog() if snapshot_path is not None else None
    initial_weather_reader: WeatherForecastReader | None = None
    if config.weather_live_enabled and weather_reader_factory is None:
        initial_weather_reader = (
            weather_reader if weather_reader is not None else compose_weather_reader(True)
        )
    weather_state = WeatherReaderState(initial_weather_reader)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        if config.weather_live_enabled and weather_reader_factory is not None:
            # Do not query optional database settings during ASGI module import.
            weather_state.reader = await run_in_threadpool(weather_reader_factory)
        try:
            if (
                snapshot_path is not None
                and inventory_path is not None
                and loaded_catalog is not None
            ):
                snapshot, inventory = await run_in_threadpool(
                    read_reference_documents, snapshot_path, inventory_path
                )
                await loaded_catalog.apply_reference(snapshot, inventory)
            yield
        finally:
            if weather_reader_factory is not None:
                weather_state.reader = None

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
    live_reader = (
        (saturn_reader if saturn_reader is not None else compose_saturn_reader(True))
        if config.saturn_live_enabled
        else None
    )
    app.include_router(
        create_source_router((saturn_capability(live_reader), weather_capability(weather_state)))
    )
    app.include_router(create_saturn_router(live_reader, source_region_lookup))
    app.include_router(create_weather_router(weather_state))
    source_runtime = compose_sources(config.source_provider)
    job_service = (
        investigations
        if investigations is not None
        else InMemoryInvestigationService(
            source_runtime.provider,
            replan_factory=source_runtime.ecology_factory,
            treatment_planner_factory=source_runtime.treatment_factory,
        )
    )
    app.include_router(
        create_investigation_router(
            job_service,
            source_runtime.provider.list_scenarios if investigations is None else None,
        )
    )
    return app
