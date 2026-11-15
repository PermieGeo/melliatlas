"""Executable synthetic scenario discovery for the country-neutral Web workspace."""

import asyncio

import httpx

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode
from melliatlas.sources.providers.synthetic.api import SYNTHETIC_COMBINED_SCENARIO_ID


def test_scenarios_are_server_defined_and_country_scoped() -> None:
    async def check() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(
                app=create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
            ),
            base_url="http://testserver",
        ) as client:
            ru = await client.get("/api/v1/investigations/scenarios?country=RU")
            assert ru.status_code == 200
            entries = ru.json()
            assert entries and sum(item["is_default"] for item in entries) == 1
            selected = next(item for item in entries if item["is_default"])
            assert selected == {
                "id": SYNTHETIC_COMBINED_SCENARIO_ID,
                "name": "Ecology and reported treatments (fictional)",
                "country": "RU",
                "territory_id": "ru:region:smolensk",
                "territory_name": "Smolensk region (fictional)",
                "source_mode": "SYNTHETIC",
                "season_start": "2026-05-01",
                "season_end": "2026-08-15",
                "is_default": True,
            }
            created = await client.post(
                "/api/v1/investigations",
                json={
                    "country": selected["country"],
                    "territory_id": selected["territory_id"],
                    "scenario_id": selected["id"],
                    "season_start": selected["season_start"],
                    "season_end": selected["season_end"],
                },
            )
            assert created.status_code == 202
            by = await client.get("/api/v1/investigations/scenarios?country=BY")
            assert by.status_code == 200 and by.json() == []
            invalid = await client.get("/api/v1/investigations/scenarios?country=XX")
            assert invalid.status_code == 422
            assert invalid.json()["error"]["code"] == "INVALID_REQUEST"

    asyncio.run(check())


def test_scenario_discovery_is_documented_in_openapi() -> None:
    spec = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC)).openapi()
    op = spec["paths"]["/api/v1/investigations/scenarios"]["get"]
    assert op["responses"]["200"]["content"]["application/json"]["schema"]
