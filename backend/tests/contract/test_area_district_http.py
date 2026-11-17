"""HTTP area intersection requires reviewed geography and uses request bodies."""

import asyncio

import httpx

from melliatlas.api.app import create_app
from melliatlas.geography import make_analysis_bounds
from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import (
    AreaDistrict,
    AreaDistrictCoverage,
    AreaDistrictResult,
    CountryCode,
    TerritoryNotFound,
)


class AreaCatalog(InMemoryTerritoryCatalog):
    async def intersect_districts(
        self,
        *,
        country: CountryCode,
        region_id: str,
        longitude: float,
        latitude: float,
        width_km: float,
        height_km: float,
    ) -> AreaDistrictResult:
        if region_id != "ru:region:smo":
            raise TerritoryNotFound(region_id)
        return AreaDistrictResult(
            bounds=make_analysis_bounds(
                longitude=longitude, latitude=latitude, width_km=width_km, height_km=height_km
            ),
            districts=(AreaDistrict("ru:district:a", region_id, "A", "fixture"),),
            coverage=AreaDistrictCoverage.UNVERIFIED,
        )


async def request(
    catalog: InMemoryTerritoryCatalog | None, payload: dict[str, object]
) -> httpx.Response:
    app = create_app(territories=catalog)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.post("/api/v1/territories/intersecting-districts", json=payload)


PAYLOAD: dict[str, object] = {
    "country": "RU",
    "region_id": "ru:region:smo",
    "longitude": 32.0,
    "latitude": 54.0,
    "width_km": 15,
    "height_km": 15,
}


def test_backend_geometry_read_is_explicit_and_unverified() -> None:
    response = asyncio.run(request(AreaCatalog(), PAYLOAD))
    assert response.status_code == 200
    body = response.json()
    assert body["coverage"] == "UNVERIFIED"
    assert body["nominal_area_km2"] == 225
    assert body["districts"] == [
        {
            "id": "ru:district:a",
            "region_id": "ru:region:smo",
            "name": "A",
            "reference_id": "fixture",
        }
    ]


def test_unavailable_geometry_is_explicit_not_empty_success() -> None:
    response = asyncio.run(request(InMemoryTerritoryCatalog(), PAYLOAD))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "TERRITORY_REFERENCE_UNAVAILABLE"


def test_invalid_area_and_unknown_region_are_distinct() -> None:
    bad = asyncio.run(request(AreaCatalog(), {**PAYLOAD, "width_km": 31}))
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "INVALID_REQUEST"
    boolean = asyncio.run(request(AreaCatalog(), {**PAYLOAD, "width_km": True}))
    assert boolean.status_code == 422
    missing = asyncio.run(request(AreaCatalog(), {**PAYLOAD, "region_id": "ru:region:missing"}))
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TERRITORY_NOT_FOUND"


def test_private_center_does_not_appear_in_the_request_url_or_error() -> None:
    invalid = asyncio.run(request(AreaCatalog(), {**PAYLOAD, "longitude": 999}))
    assert "999" not in invalid.text
    assert invalid.status_code == 422
    assert "longitude" not in invalid.url.path


def test_openapi_declares_post_operation_and_error_contracts() -> None:
    schema = create_app().openapi()
    assert "/api/v1/places" not in schema["paths"]
    operation = schema["paths"]["/api/v1/territories/intersecting-districts"]["post"]
    for status in (404, 422, 503):
        assert operation["responses"][str(status)]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponse"
        }
