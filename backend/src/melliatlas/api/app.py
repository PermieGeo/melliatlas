"""FastAPI application composition."""

from dataclasses import dataclass

from fastapi import FastAPI

from melliatlas.api.public import HealthResponse


@dataclass(frozen=True)
class AppSettings:
    title: str = "MelliAtlas"
    version: str = "0.1.0"


def create_app(*, settings: AppSettings | None = None) -> FastAPI:
    config = settings if settings is not None else AppSettings()
    app = FastAPI(title=config.title, version=config.version)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app
