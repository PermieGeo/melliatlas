"""Contract tests for the first runnable backend slice."""

import asyncio

import httpx
from fastapi import FastAPI

from melliatlas.api.app import AppSettings, create_app
from melliatlas.main import app


async def _get(application: FastAPI, path: str) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        return await client.get(path)


def test_health_response_is_typed_and_not_a_readiness_claim() -> None:
    response = asyncio.run(_get(app, "/health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_is_served_with_health_contract() -> None:
    response = asyncio.run(_get(app, "/openapi.json"))
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "MelliAtlas"
    assert (
        schema["paths"]["/health"]["get"]["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        == "#/components/schemas/HealthResponse"
    )
    assert schema["components"]["schemas"]["HealthResponse"]["required"] == ["status"]
    assert "/api/v1/investigations" not in schema["paths"]


def test_app_settings_are_injected_without_shared_mutable_state() -> None:
    configured = create_app(settings=AppSettings(title="Test atlas", version="9.8.7"))
    metadata = asyncio.run(_get(configured, "/openapi.json")).json()["info"]
    response = asyncio.run(_get(configured, "/health"))
    assert metadata["title"] == "Test atlas"
    assert metadata["version"] == "9.8.7"
    assert response.json() == {"status": "ok"}
    assert app.title == "MelliAtlas"


def test_unknown_route_has_no_implicit_domain_data() -> None:
    response = asyncio.run(_get(app, "/api/v1/territories"))
    assert response.status_code == 404
