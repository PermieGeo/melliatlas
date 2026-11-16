"""Validate a single explicitly captured Saturn district directory without network access."""

import json
from dataclasses import dataclass
from typing import TypeGuard

MAX_DISTRICT_DIRECTORY_BYTES = 64_000
MAX_DISTRICTS_PER_SUBJECT = 150


@dataclass(frozen=True)
class SaturnDistrict:
    """Source-owned identifier and label; never a canonical territory identifier."""

    id: int
    name: str


def normalized_district_name(value: str) -> str:
    """Normalize spelling, whitespace and the explicit municipal-district qualifier."""
    words = " ".join(value.casefold().replace("ё", "е").split())
    return words.replace(" муниципальный район", " район")


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def validate_district_directory(raw: bytes) -> tuple[SaturnDistrict, ...]:
    """Reject partial, duplicated and unexpected upstream district dictionaries."""
    if not raw or len(raw) > MAX_DISTRICT_DIRECTORY_BYTES:
        raise ValueError("Saturn district directory is empty or exceeds the byte limit")
    try:
        payload: object = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Invalid Saturn district directory JSON") from exc
    if not _is_list(payload) or not 1 <= len(payload) <= MAX_DISTRICTS_PER_SUBJECT:
        raise ValueError("Unexpected Saturn district directory size")
    entries: list[SaturnDistrict] = []
    for item in payload:
        if not _is_object(item):
            raise ValueError("Invalid Saturn district entry")
        identifier, name = item.get("id"), item.get("name")
        if type(identifier) is not int or not 1 <= identifier <= 999999:
            raise ValueError("Invalid Saturn district identifier")
        if not isinstance(name, str) or not normalized_district_name(name):
            raise ValueError("Invalid Saturn district name")
        entries.append(SaturnDistrict(identifier, name.strip()))
    if len({item.id for item in entries}) != len(entries):
        raise ValueError("Duplicate Saturn district identifiers")
    if len({normalized_district_name(item.name) for item in entries}) != len(entries):
        raise ValueError("Duplicate Saturn district names")
    return tuple(entries)
