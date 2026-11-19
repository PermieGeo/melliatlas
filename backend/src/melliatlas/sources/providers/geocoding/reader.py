"""One on-demand GeoNames location lookup via the fixed Open-Meteo HTTPS host."""

import json
from collections.abc import Callable
from math import isfinite
from typing import TypeGuard
from urllib.parse import urlencode

from melliatlas.sources.api import Settlement, SourceReadError
from melliatlas.sources.providers.http_transport import (
    JsonTransportFailures,
    read_fixed_origin_json,
)
from melliatlas.territories.api import CountryCode

_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"
_SOURCE_URI = "https://open-meteo.com/en/docs/geocoding-api"
_MAX_RESULTS = 10
_MAX_BODY_BYTES = 32768
_FAILURES = JsonTransportFailures(
    "GEOCODING_HTTP",
    "GEOCODING_MIME",
    "GEOCODING_ENCODING",
    "GEOCODING_SIZE",
    "GEOCODING_REQUEST",
)


def _fetch(name: str, country: CountryCode, language: str) -> bytes:
    params = urlencode(
        {
            "name": name,
            "count": _MAX_RESULTS,
            "language": language,
            "format": "json",
            "countryCode": country.value,
        }
    )
    return read_fixed_origin_json(
        f"{_ENDPOINT}?{params}",
        expected_host="geocoding-api.open-meteo.com",
        method="GET",
        body=None,
        timeout_seconds=8,
        max_body_bytes=_MAX_BODY_BYTES,
        failures=_FAILURES,
    )


def _is_object_dict(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _record(value: object) -> dict[str, object]:
    if not _is_object_dict(value):
        raise ValueError("Expected a geocoding object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Geocoding field keys must be strings")
        result[key] = item
    return result


def _coordinate(value: object, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Invalid geocoding coordinate")
    number = float(value)
    if not isfinite(number) or not minimum <= number <= maximum:
        raise ValueError("Geocoding coordinate is out of bounds")
    return number


class OpenMeteoSettlementReader:
    """Return only recognizable populated places, never coordinates as verified regions."""

    def __init__(self, fetch: Callable[[str, CountryCode, str], bytes] = _fetch) -> None:
        self._fetch = fetch

    def search(self, *, country: CountryCode, query: str, language: str) -> tuple[Settlement, ...]:
        if not 2 <= len(query.strip()) <= 100 or language not in ("ru", "en"):
            raise ValueError("Invalid geocoding search parameters")
        try:
            raw = self._fetch(query.strip(), country, language)
            if len(raw) > _MAX_BODY_BYTES:
                raise ValueError("Oversized geocoding payload")
            payload: object = json.loads(raw)
            root = _record(payload)
            if root.get("error") is True:
                raise ValueError("Unexpected geocoding response")
            values = root.get("results", [])
            if not _is_object_list(values) or len(values) > _MAX_RESULTS:
                raise ValueError("Unexpected geocoding result collection")
            matches: list[Settlement] = []
            seen: set[int] = set()
            for value in values:
                entry = _record(value)
                identifier = entry.get("id")
                name = entry.get("name")
                code = entry.get("country_code")
                kind = entry.get("feature_code")
                admin = entry.get("admin1")
                if (
                    not isinstance(identifier, int)
                    or isinstance(identifier, bool)
                    or identifier <= 0
                    or not isinstance(name, str)
                    or not name.strip()
                    or not isinstance(code, str)
                    or not isinstance(kind, str)
                    or (admin is not None and not isinstance(admin, str))
                ):
                    raise ValueError("Invalid geocoding result fields")
                latitude = _coordinate(entry.get("latitude"), minimum=-90, maximum=90)
                longitude = _coordinate(entry.get("longitude"), minimum=-180, maximum=180)
                if code != country.value or not kind.startswith("PPL") or identifier in seen:
                    continue
                seen.add(identifier)
                matches.append(
                    Settlement(
                        id=identifier,
                        name=name.strip(),
                        country=country,
                        admin1=admin.strip() if isinstance(admin, str) else None,
                        latitude=latitude,
                        longitude=longitude,
                        source_uri=_SOURCE_URI,
                    )
                )
            return tuple(matches)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            raise SourceReadError("GEOCODING_INVALID_RESPONSE") from error
