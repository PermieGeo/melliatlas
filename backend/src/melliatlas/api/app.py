"""FastAPI application composition."""

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from melliatlas.api.public import ApiErrorCode, ErrorDetail, ErrorResponse, HealthResponse
from melliatlas.api.routes_investigations import create_investigation_router
from melliatlas.api.routes_territories import create_territory_router
from melliatlas.jobs.api import InMemoryInvestigationService, InvestigationService
from melliatlas.sources.api import SyntheticFixtureProvider
from melliatlas.territories.api import TerritoryCatalog


@dataclass(frozen=True)
class AppSettings:
    title: str = "MelliAtlas"
    version: str = "0.1.0"


def create_app(
    *,
    settings: AppSettings | None = None,
    territories: TerritoryCatalog | None = None,
    investigations: InvestigationService | None = None,
) -> FastAPI:
    config = settings if settings is not None else AppSettings()
    app = FastAPI(title=config.title, version=config.version)

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

    app.include_router(create_territory_router(territories))
    job_service = (
        investigations
        if investigations is not None
        else InMemoryInvestigationService(SyntheticFixtureProvider())
    )
    app.include_router(create_investigation_router(job_service))
    return app
