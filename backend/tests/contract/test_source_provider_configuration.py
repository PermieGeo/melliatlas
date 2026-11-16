"""Contract checks for explicit source selection and dependency composition."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode, compose_sources
from melliatlas.sources.api import ScenarioProvider
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_COMBINED_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.territories.api import CountryCode


async def _request(
    app: FastAPI, method: str, path: str, *, json: dict[str, str] | None = None
) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.request(method, path, json=json)


def test_default_application_has_no_implicit_synthetic_scenarios() -> None:
    async def check() -> None:
        app = create_app()
        listed = await _request(app, "GET", "/api/v1/investigations/scenarios?country=RU")
        assert listed.status_code == 200 and listed.json() == []
        submitted = await _request(
            app,
            "POST",
            "/api/v1/investigations",
            json={
                "country": "RU",
                "territory_id": "ru:region:smolensk",
                "scenario_id": SYNTHETIC_COMBINED_SCENARIO_ID,
                "season_start": "2026-05-01",
                "season_end": "2026-08-15",
            },
        )
        assert submitted.status_code == 422
        assert submitted.json()["error"]["code"] == "INVALID_INVESTIGATION_REQUEST"

    asyncio.run(check())


def test_explicit_synthetic_provider_is_injected_and_listed() -> None:
    async def check() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        listed = await _request(app, "GET", "/api/v1/investigations/scenarios?country=RU")
        assert listed.status_code == 200
        assert len(listed.json()) == 4
        by = await _request(app, "GET", "/api/v1/investigations/scenarios?country=BY")
        assert by.json() == []

    asyncio.run(check())


def test_selection_is_explicit_and_conforms_to_structural_protocol() -> None:
    disabled = compose_sources(SourceProviderMode.DISABLED)
    synthetic = compose_sources(SourceProviderMode.SYNTHETIC)
    assert isinstance(synthetic.provider, SyntheticFixtureProvider)
    assert isinstance(disabled.provider, ScenarioProvider)
    assert isinstance(synthetic.provider, ScenarioProvider)
    assert (
        disabled.provider.load(
            country=CountryCode.RU,
            territory_id="ru:region:smolensk",
            scenario_id="synthetic-ru-2026-v01",
        )
        is None
    )
    assert disabled.ecology_factory is None and disabled.treatment_factory is None
    assert synthetic.ecology_factory is not None and synthetic.treatment_factory is not None
    with pytest.raises(ValueError, match="invalid"):
        SourceProviderMode("invalid")


def test_asgi_entrypoint_requires_explicit_source_selection() -> None:
    root = Path(__file__).resolve().parents[2] / "src"
    command = [sys.executable, "-B", "-c", "from melliatlas.main import app; print(app.title)"]
    for mode, success in (("disabled", True), ("synthetic", True), ("unexpected", False)):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        env["MELLIATLAS_SOURCE_PROVIDER"] = mode
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
        assert (result.returncode == 0) is success, result.stderr
        if not success:
            assert "Invalid MELLIATLAS_SOURCE_PROVIDER" in result.stderr


def test_disabled_import_does_not_eagerly_load_synthetic_adapter() -> None:
    root = Path(__file__).resolve().parents[2] / "src"
    code = (
        "import sys; "
        "from melliatlas.api.app import create_app; "
        "create_app(); "
        "assert 'melliatlas.sources.providers.synthetic.api' not in sys.modules"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_asgi_entrypoint_import_does_not_query_unmigrated_weather_database() -> None:
    root = Path(__file__).resolve().parents[2] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    env["MELLIATLAS_DATABASE_URL"] = "postgresql://fake:fake@127.0.0.1:1/unavailable"
    env["MELLIATLAS_WEATHER_LIVE_ENABLED"] = "true"
    result = subprocess.run(
        [sys.executable, "-B", "-c", "from melliatlas.main import app; print(app.title)"],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "MelliAtlas"
