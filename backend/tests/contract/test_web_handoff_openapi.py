"""Protect existing HTTP wire contracts needed for the selected browser MVP."""

import asyncio
import json
from pathlib import Path
from uuid import UUID

import httpx
import pytest

from melliatlas.api.app import AppSettings, create_app
from melliatlas.api.composition import SourceProviderMode
from melliatlas.sources.providers.synthetic import SYNTHETIC_COMBINED_SCENARIO_ID


def test_browser_handoff_openapi_exposes_existing_typed_operations() -> None:
    schema = create_app(
        settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC)
    ).openapi()
    paths = schema["paths"]
    for path, method in (
        ("/api/v1/territories/countries", "get"),
        ("/api/v1/territories/regions", "get"),
        ("/api/v1/territories/districts", "get"),
        ("/api/v1/territories/geometry/{territory_id}", "get"),
        ("/api/v1/investigations", "post"),
        ("/api/v1/investigations/{id}", "get"),
    ):
        assert method in paths[path]

    models = schema["components"]["schemas"]
    created = models["InvestigationCreateDto"]["properties"]
    response = models["InvestigationResponse"]["properties"]
    request_echo = models["InvestigationRequestDto"]["properties"]
    assert {"country", "territory_id", "scenario_id", "season_start", "season_end"} <= set(created)
    assert "starting_point" in created
    assert "starting_point" not in request_echo
    assert "starting_point" not in response
    assert {
        "plan",
        "replanning",
        "treatment_review",
        "evidence",
        "limitations",
        "synthetic",
    } <= set(response)
    assert {"screenings", "avoided_site_ids", "warnings"} <= set(
        models["TreatmentReviewDto"]["properties"]
    )
    assert {"assessments", "decisions", "warnings"} <= set(models["ReplanSummaryDto"]["properties"])


def test_browser_handoff_joint_fixture_is_source_attributed_and_private() -> None:
    async def check() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            posted = await client.post(
                "/api/v1/investigations",
                json={
                    "country": "RU",
                    "territory_id": "ru:region:smolensk",
                    "scenario_id": SYNTHETIC_COMBINED_SCENARIO_ID,
                    "season_start": "2026-05-01",
                    "season_end": "2026-08-15",
                    "starting_point": {"longitude": 32.0, "latitude": 54.0},
                },
            )
            assert posted.status_code == 202
            identifier = str(UUID(posted.json()["id"]))
            completed_response = await client.get(f"/api/v1/investigations/{identifier}")
            assert completed_response.status_code == 200
            data = completed_response.json()
            assert data["status"] == "COMPLETED"
            assert data["synthetic"] is True
            assert data["plan"] is not None and len(data["plan"]["stops"]) >= 2
            assert data["replanning"] is not None
            assert data["treatment_review"] is not None
            assert any(item["source_record_id"] for item in data["treatment_review"]["screenings"])
            assert all(item["synthetic"] for item in data["evidence"])
            assert all(item["source_mode"] == "FIXTURE" for item in data["evidence"])
            assert data["limitations"]
            assert "starting_point" not in data["request"]
            assert (await client.get(f"/api/v1/investigations/{identifier}")).json() == data

    asyncio.run(check())


def test_browser_handoff_unavailable_reference_and_unknown_result_are_explicit() -> None:
    async def check() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            countries = await client.get("/api/v1/territories/countries")
            assert countries.status_code == 200
            assert {item["code"] for item in countries.json()} == {"RU", "BY"}

            regions = await client.get("/api/v1/territories/regions?country=BY")
            assert regions.status_code == 503
            assert regions.json()["error"]["code"] == "TERRITORY_REFERENCE_UNAVAILABLE"

            missing = await client.get(
                "/api/v1/investigations/00000000-0000-4000-8000-000000000001"
            )
            assert missing.status_code == 404
            assert missing.json()["error"]["code"] == "INVESTIGATION_NOT_FOUND"

    asyncio.run(check())


def test_web_w01_fixture_tracks_the_real_combined_http_contract() -> None:
    """Fail if the client fixture drifts from the actual synthetic API response."""
    fixture_path = Path(__file__).parents[3] / "web/tests/fixtures/combined.json"
    expected = json.loads(fixture_path.read_text(encoding="utf-8"))

    async def check() -> None:
        app = create_app(settings=AppSettings(source_provider=SourceProviderMode.SYNTHETIC))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            posted = await client.post(
                "/api/v1/investigations",
                json={
                    "country": "RU",
                    "territory_id": "ru:region:smolensk",
                    "scenario_id": SYNTHETIC_COMBINED_SCENARIO_ID,
                    "season_start": "2026-05-01",
                    "season_end": "2026-08-15",
                },
            )
            assert posted.status_code == 202
            actual_response = await client.get(f"/api/v1/investigations/{posted.json()['id']}")
            assert actual_response.status_code == 200
            actual = actual_response.json()
            actual["id"] = expected["id"]
            actual["created_at"] = expected["created_at"]
            actual["updated_at"] = expected["updated_at"]
            actual_screenings = actual["treatment_review"]["screenings"]
            expected_screenings = expected["treatment_review"]["screenings"]
            assert len(actual_screenings) == len(expected_screenings)
            for actual_item, expected_item in zip(
                actual_screenings, expected_screenings, strict=True
            ):
                actual_distance = actual_item["approximate_distance_km"]
                expected_distance = expected_item["approximate_distance_km"]
                if expected_distance is None:
                    assert actual_distance is None
                else:
                    # GEOS can produce slightly different floating-point distances across platforms.
                    assert actual_distance == pytest.approx(expected_distance, rel=1e-7, abs=1e-6)
                    actual_item["approximate_distance_km"] = expected_distance
                assert actual_item == expected_item
            assert actual == expected

    asyncio.run(check())
