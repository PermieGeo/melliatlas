"""Settlement search is explicit, bounded and independent from district evidence."""

import asyncio
import json

import httpx
import pytest

from melliatlas.api.app import create_app
from melliatlas.sources.api import SourceReadError
from melliatlas.sources.providers.geocoding import OpenMeteoSettlementReader
from melliatlas.territories.api import CountryCode


async def _request(reader: OpenMeteoSettlementReader, payload: dict[str, str]) -> httpx.Response:
    app = create_app(settlement_reader=reader)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.post("/api/v1/sources/geocoding/settlements", json=payload)


def _reader(raw: object) -> OpenMeteoSettlementReader:
    return OpenMeteoSettlementReader(lambda _query, _country, _language: json.dumps(raw).encode())


def test_settlement_search_returns_attributed_populated_places_only() -> None:
    reader = _reader(
        {
            "results": [
                {
                    "id": 123,
                    "name": "Смоленск",
                    "country_code": "RU",
                    "feature_code": "PPLA",
                    "latitude": 54.78,
                    "longitude": 32.04,
                    "admin1": "Smolensk",
                },
                {
                    "id": 234,
                    "name": "Other",
                    "country_code": "BY",
                    "feature_code": "PPL",
                    "latitude": 53.0,
                    "longitude": 27.0,
                },
                {
                    "id": 345,
                    "name": "Lake",
                    "country_code": "RU",
                    "feature_code": "LK",
                    "latitude": 54.0,
                    "longitude": 30.0,
                },
            ]
        }
    )
    result = asyncio.run(_request(reader, {"country": "RU", "query": "Смоленск", "language": "ru"}))
    assert result.status_code == 200
    assert result.json() == [
        {
            "id": 123,
            "name": "Смоленск",
            "country": "RU",
            "admin1": "Smolensk",
            "latitude": 54.78,
            "longitude": 32.04,
            "source_uri": "https://open-meteo.com/en/docs/geocoding-api",
        }
    ]


def test_settlement_search_rejects_bad_queries_and_upstream_data() -> None:
    reader = _reader(
        {
            "results": [
                {
                    "id": 1,
                    "name": "Bad",
                    "country_code": "RU",
                    "feature_code": "PPL",
                    "latitude": "invalid",
                    "longitude": 30,
                }
            ]
        }
    )
    too_short = asyncio.run(_request(reader, {"country": "RU", "query": "x"}))
    assert too_short.status_code == 422
    blank = asyncio.run(_request(reader, {"country": "RU", "query": "  "}))
    assert blank.status_code == 422
    failure = asyncio.run(_request(reader, {"country": "RU", "query": "somewhere"}))
    assert failure.status_code == 502
    assert failure.json()["error"]["code"] == "SOURCE_READ_FAILED"


def test_settlement_search_avoids_network_when_invalid() -> None:
    called: list[tuple[str, CountryCode, str]] = []

    def fetch(query: str, country: CountryCode, language: str) -> bytes:
        called.append((query, country, language))
        raise SourceReadError("NO_CONNECTION")

    reader = OpenMeteoSettlementReader(fetch)
    invalid = asyncio.run(_request(reader, {"country": "BY", "query": "x"}))
    assert invalid.status_code == 422
    assert called == []

    response = asyncio.run(_request(reader, {"country": "BY", "query": "Minsk", "language": "en"}))
    assert response.status_code == 502
    assert called == [("Minsk", CountryCode.BY, "en")]


INVALID_UPSTREAM_CASES: list[object] = [
    {"results": None},
    {"results": [{}]},
    {"results": ["invalid"]},
    {
        "results": [
            {
                "id": True,
                "name": "A",
                "country_code": "RU",
                "feature_code": "PPL",
                "latitude": 54,
                "longitude": 32,
            }
        ]
    },
    {
        "results": [
            {
                "id": 1,
                "name": "A",
                "country_code": "RU",
                "feature_code": "PPL",
                "latitude": True,
                "longitude": 32,
            }
        ]
    },
    {
        "results": [
            {
                "id": 1,
                "name": "A",
                "country_code": "RU",
                "feature_code": "PPL",
                "latitude": 91,
                "longitude": 32,
            }
        ]
    },
    {
        "results": [
            {
                "id": 1,
                "name": "A",
                "country_code": "RU",
                "feature_code": "PPL",
                "latitude": 54,
                "longitude": 32,
                "admin1": 123,
            }
        ]
    },
]


@pytest.mark.parametrize("upstream", INVALID_UPSTREAM_CASES)
def test_settlement_search_rejects_invalid_external_shapes(upstream: object) -> None:
    reader = _reader(upstream)
    with pytest.raises(SourceReadError, match="GEOCODING_INVALID_RESPONSE"):
        reader.search(country=CountryCode.RU, query="Smolensk", language="en")
