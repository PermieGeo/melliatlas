"""Validate provider-specific subject-directory captures without network access."""

import json
from dataclasses import dataclass
from typing import TypeGuard

MAX_SUBJECT_BODY_BYTES = 256_000
MAX_SUBJECTS = 150


@dataclass(frozen=True)
class SaturnSubject:
    """A public Saturn identifier, not a canonical administrative region ID."""

    id: int
    oktmo_code: str
    name: str


def normalized_subject_name(value: str) -> str:
    """Normalize only whitespace and Russian yo; never guess provider mappings."""
    return " ".join(value.casefold().replace("ё", "е").split())


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_object_dict(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def validate_subject_directory(raw: bytes, *, min_entries: int = 1) -> list[SaturnSubject]:
    """Reject partial or ambiguous catalogs before persistence or local capture."""
    if not raw or len(raw) > MAX_SUBJECT_BODY_BYTES:
        raise ValueError("Saturn subject catalog exceeds size limit or is empty")
    try:
        payload: object = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Invalid Saturn subject directory JSON") from exc
    if not _is_object_list(payload) or not min_entries <= len(payload) <= MAX_SUBJECTS:
        raise ValueError("Unexpected Saturn subject directory entry count")
    subjects: list[SaturnSubject] = []
    for item in payload:
        if not _is_object_dict(item):
            raise ValueError("Invalid Saturn subject directory entry")
        identifier = item.get("id")
        oktmo = item.get("oktmoCode")
        name = item.get("name")
        if type(identifier) is not int or not 1 <= identifier <= 999999:
            raise ValueError("Invalid Saturn subject identifier")
        if (
            not isinstance(oktmo, str)
            or len(oktmo) != 8
            or not oktmo.isascii()
            or not oktmo.isdecimal()
        ):
            raise ValueError("Invalid Saturn subject OKTMO code")
        if not isinstance(name, str) or not normalized_subject_name(name):
            raise ValueError("Invalid Saturn subject name")
        subjects.append(SaturnSubject(id=identifier, oktmo_code=oktmo, name=name))
    if len({item.id for item in subjects}) != len(subjects):
        raise ValueError("Duplicate Saturn subject IDs")
    if len({normalized_subject_name(item.name) for item in subjects}) != len(subjects):
        raise ValueError("Duplicate Saturn subject names")
    return subjects
