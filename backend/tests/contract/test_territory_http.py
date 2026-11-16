"""API contract tests with a validated, explicitly synthetic territory catalog."""

import asyncio
from dataclasses import replace

import httpx

from melliatlas.api.app import create_app
from melliatlas.territories import InMemoryTerritoryCatalog
from melliatlas.territories.api import (
    CountryCode,
    ExpectedInventory,
    GeometryStatus,
    ReferenceSnapshot,
    ReferenceUnavailableError,
    TerritoryAtPoint,
)
from melliatlas.territories.validation import snapshot_checksum


async def _request(catalog: InMemoryTerritoryCatalog | None, url: str) -> httpx.Response:
    app = create_app(territories=catalog)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.get(url)


def _loaded(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> InMemoryTerritoryCatalog:
    snapshot, inventory = reference_case
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(snapshot, inventory))
    return catalog


def test_countries_available_without_claiming_loaded_catalog() -> None:
    response = asyncio.run(_request(None, "/api/v1/territories/countries"))
    assert response.status_code == 200
    assert {entry["code"] for entry in response.json()} == {"RU", "BY"}


def test_missing_dataset_is_unavailable_not_empty() -> None:
    response = asyncio.run(_request(None, "/api/v1/territories/regions?country=RU"))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "TERRITORY_REFERENCE_UNAVAILABLE"


def test_region_and_district_responses(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    catalog = _loaded(reference_case)
    regions = asyncio.run(_request(catalog, "/api/v1/territories/regions?country=BY"))
    assert regions.status_code == 200
    assert {item["id"] for item in regions.json()} == reference_case[1].region_ids[CountryCode.BY]
    districts = asyncio.run(
        _request(catalog, "/api/v1/territories/districts?region_id=by:region:vitebsk")
    )
    assert districts.status_code == 200
    assert [item["parent_id"] for item in districts.json()] == ["by:region:vitebsk"]


def test_nonpilot_district_request_is_not_false_complete(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    response = asyncio.run(
        _request(_loaded(reference_case), "/api/v1/territories/districts?region_id=ru:region:other")
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DISTRICT_COVERAGE_UNSUPPORTED"


def test_unknown_territory_is_explicit(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    response = asyncio.run(_request(_loaded(reference_case), "/api/v1/territories/unknown"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TERRITORY_NOT_FOUND"


def test_geometry_retains_reference_and_coordinate_system(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    response = asyncio.run(_request(_loaded(reference_case), "/api/v1/territories/geometry/RU"))
    assert response.status_code == 200
    assert response.json()["coordinate_system"] == "EPSG:4326"
    assert response.json()["reference_id"] == "SYNTHETIC-TEST-ONLY"
    assert response.json()["geometry"]["type"] == "Polygon"


def test_invalid_country_has_sanitized_error() -> None:
    response = asyncio.run(_request(None, "/api/v1/territories/regions?country=ZZ"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_openapi_includes_versioned_territory_contract() -> None:
    response = asyncio.run(_request(None, "/openapi.json"))
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/territories/countries" in paths
    assert "/api/v1/territories/regions" in paths
    assert "/api/v1/territories/geometry/{territory_id}" in paths


def test_openapi_declares_actual_territory_error_envelopes() -> None:
    schema = asyncio.run(_request(None, "/openapi.json")).json()
    expected = {
        "/api/v1/territories/regions": {422, 503},
        "/api/v1/territories/districts": {404, 409, 422, 503},
        "/api/v1/territories/geometry/{territory_id}": {404, 422, 503},
        "/api/v1/territories/{territory_id}": {404, 422, 503},
    }
    for path, statuses in expected.items():
        responses = schema["paths"][path]["get"]["responses"]
        for code in statuses:
            response = responses[str(code)]
            assert response["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/ErrorResponse"
            }
    assert "ApiErrorCode" in schema["components"]["schemas"]


def test_structured_error_codes_are_consistent_across_endpoints(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    loaded = _loaded(reference_case)
    cases = (
        (None, "/api/v1/territories/regions?country=RU", 503, "TERRITORY_REFERENCE_UNAVAILABLE"),
        (
            loaded,
            "/api/v1/territories/districts?region_id=ru:region:other",
            409,
            "DISTRICT_COVERAGE_UNSUPPORTED",
        ),
        (loaded, "/api/v1/territories/unknown", 404, "TERRITORY_NOT_FOUND"),
        (
            loaded,
            "/api/v1/territories/districts?region_id=unknown",
            404,
            "TERRITORY_NOT_FOUND",
        ),
        (
            loaded,
            "/api/v1/territories/districts?region_id=RU",
            422,
            "INVALID_TERRITORY_REQUEST",
        ),
        (None, "/api/v1/territories/regions?country=XX", 422, "INVALID_REQUEST"),
    )
    for catalog, url, status, code in cases:
        response = asyncio.run(_request(catalog, url))
        assert response.status_code == status
        assert response.json()["error"]["code"] == code
        assert isinstance(response.json()["error"]["message"], str)


def test_geometry_missing_has_documented_error_shape(
    reference_case: tuple[ReferenceSnapshot, ExpectedInventory],
) -> None:
    snapshot, inventory = reference_case
    updated = replace(
        snapshot,
        territories=tuple(
            replace(item, geometry_status=GeometryStatus.MISSING) if item.id == "RU" else item
            for item in snapshot.territories
        ),
        geometries=tuple(g for g in snapshot.geometries if g.territory_id != "RU"),
    )
    updated = replace(
        updated,
        manifest=replace(updated.manifest, checksum_sha256=snapshot_checksum(updated)),
    )
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.apply_reference(updated, inventory))
    response = asyncio.run(_request(catalog, "/api/v1/territories/geometry/RU"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TERRITORY_GEOMETRY_MISSING"


class PointCatalog(InMemoryTerritoryCatalog):
    def __init__(self, result: TerritoryAtPoint | None, fail: bool = False) -> None:
        super().__init__()
        self.result = result
        self.fail = fail

    async def locate_point(
        self, *, country: CountryCode, longitude: float, latitude: float
    ) -> TerritoryAtPoint | None:
        assert country == CountryCode.RU
        assert longitude == 32.0
        assert latitude == 54.0
        if self.fail:
            raise ReferenceUnavailableError("Overlapping source boundaries")
        return self.result


async def _resolve_point(
    catalog: InMemoryTerritoryCatalog | None, payload: dict[str, object]
) -> httpx.Response:
    app = create_app(territories=catalog)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.post("/api/v1/territories/resolve-point", json=payload)


def test_click_lookup_returns_only_validated_canonical_ids() -> None:
    payload: dict[str, object] = {"country": "RU", "longitude": 32.0, "latitude": 54.0}
    catalog = PointCatalog(TerritoryAtPoint("ru:region:smo", "ru:district:abc"))
    response = asyncio.run(_resolve_point(catalog, payload))
    assert response.status_code == 200
    assert response.json() == {"region_id": "ru:region:smo", "district_id": "ru:district:abc"}
    assert asyncio.run(_resolve_point(PointCatalog(None), payload)).status_code == 404
    invalid_identity = PointCatalog(TerritoryAtPoint("by:region:vi", "by:district:one"))
    assert asyncio.run(_resolve_point(invalid_identity, payload)).status_code == 503
    ambiguous = asyncio.run(_resolve_point(PointCatalog(None, fail=True), payload))
    assert ambiguous.status_code == 503
    assert asyncio.run(_resolve_point(None, payload)).status_code == 503
    invalid = asyncio.run(_resolve_point(catalog, {**payload, "latitude": 91}))
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_REQUEST"
