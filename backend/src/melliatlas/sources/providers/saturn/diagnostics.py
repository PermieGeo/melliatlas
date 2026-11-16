"""One-shot, privacy-preserving diagnostics for a historical Saturn page shape.

This is an operator aid, not a source contract or an automatic crawler. Only
allowlisted JSON field names and aggregate counts leave this module; raw notices,
field identifiers, coordinates and HTTP bodies must never appear in its output.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypeGuard
from urllib.error import HTTPError

from melliatlas.sources.api import SourceReadError
from melliatlas.sources.providers.saturn.live import MAX_BODY_BYTES, SaturnPublicTreatmentReader
from melliatlas.territories.api import CountryCode

_ENVELOPE_FIELDS = frozenset(
    {
        "content",
        "number",
        "size",
        "numberOfElements",
        "totalElements",
        "totalPages",
        "last",
        "pageable",
    }
)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


@dataclass(frozen=True)
class SaturnPageShape:
    """Structural metadata, excluding all source-provided field values and keys."""

    json_kind: Literal["object", "array", "scalar", "invalid"]
    known_envelope_fields: tuple[str, ...]
    content_kind: Literal["list", "missing", "other"]
    record_count: int | None
    field_record_count: int | None
    map_index_record_count: int | None
    other_record_count: int | None


@dataclass(frozen=True)
class SaturnProbeResult:
    """The result of one manual request; never evidence of complete coverage."""

    outcome: Literal[
        "PARSED", "UNRECOGNIZED_ROWS", "RESPONSE_ERROR", "HTTP_ERROR", "TRANSPORT_ERROR"
    ]
    upstream_http_status: int | None
    shape: SaturnPageShape | None
    parsed_notices: int | None
    unidentified_records: int | None
    has_next_page: bool | None
    coverage_complete: Literal[False] = False


def describe_page_shape(raw: bytes) -> SaturnPageShape:
    """Report only allowlisted schema names and counts from a bounded JSON page."""
    if len(raw) > MAX_BODY_BYTES:
        return SaturnPageShape("invalid", (), "missing", None, None, None, None)
    try:
        parsed: object = json.loads(raw)
    except (ValueError, UnicodeError, RecursionError):
        return SaturnPageShape("invalid", (), "missing", None, None, None, None)

    if _is_list(parsed):
        return SaturnPageShape("array", (), "missing", None, None, None, None)
    if not _is_mapping(parsed):
        return SaturnPageShape("scalar", (), "missing", None, None, None, None)

    envelope = tuple(sorted(key for key in _ENVELOPE_FIELDS if key in parsed))
    if "content" not in parsed:
        return SaturnPageShape("object", envelope, "missing", None, None, None, None)
    content = parsed["content"]
    if not _is_list(content):
        return SaturnPageShape("object", envelope, "other", None, None, None, None)

    fields = 0
    indexes = 0
    others = 0
    for item in content:
        if not _is_mapping(item):
            others += 1
        elif _is_mapping(item.get("beeAcreage")):
            fields += 1
        elif "centerX" in item and "centerY" in item and "planId" in item:
            indexes += 1
        else:
            others += 1
    return SaturnPageShape("object", envelope, "list", len(content), fields, indexes, others)


def probe_one_page(
    *, region_code: int, page_number: int, transport: Callable[[bytes], bytes]
) -> SaturnProbeResult:
    """Make at most one transport call and distinguish failures from empty pages.

    No data is persisted. The caller must opt into this historical public endpoint
    and verify current access and reuse permissions independently.
    """
    shape: SaturnPageShape | None = None

    def inspect(request: bytes) -> bytes:
        nonlocal shape
        raw = transport(request)
        shape = describe_page_shape(raw)
        return raw

    try:
        page = SaturnPublicTreatmentReader(inspect).read_page(
            country=CountryCode.RU, region_code=region_code, page_number=page_number
        )
    except SourceReadError as error:
        cause = error.__cause__
        http_status = cause.code if isinstance(cause, HTTPError) else None
        outcome: Literal["RESPONSE_ERROR", "HTTP_ERROR", "TRANSPORT_ERROR"]
        if http_status is not None:
            outcome = "HTTP_ERROR"
        elif shape is not None:
            outcome = "RESPONSE_ERROR"
        else:
            outcome = "TRANSPORT_ERROR"
        return SaturnProbeResult(
            outcome=outcome,
            upstream_http_status=http_status,
            shape=shape,
            parsed_notices=None,
            unidentified_records=None,
            has_next_page=None,
        )

    return SaturnProbeResult(
        outcome="UNRECOGNIZED_ROWS" if page.unidentified_records else "PARSED",
        upstream_http_status=200,
        shape=shape,
        parsed_notices=len(page.notices),
        unidentified_records=page.unidentified_records,
        has_next_page=page.next_page is not None,
    )
