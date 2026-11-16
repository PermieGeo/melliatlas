"""Tests of manual Saturn diagnostics without network access or raw-value exposure."""

import json
from dataclasses import asdict
from email.message import Message
from urllib.error import HTTPError

import pytest

from melliatlas.sources.api import SourceReadError
from melliatlas.sources.providers.saturn.diagnostics import (
    describe_page_shape,
    probe_one_page,
)


def _valid_page(rows: list[dict[str, object]]) -> bytes:
    return json.dumps(
        {
            "content": rows,
            "number": 0,
            "size": 10,
            "totalElements": len(rows),
            "totalPages": 1 if rows else 0,
            "last": True,
            "numberOfElements": len(rows),
        }
    ).encode()


def test_probe_returns_only_structural_counts_for_realistic_notices() -> None:
    secret = "PRIVATE-APIARY-LATITUDE:54.123456"
    source = _valid_page(
        [
            {
                "beeAcreage": {
                    "id": secret,
                    "planDate": 1780617600,
                    "geo": {"coordinates": [54.1]},
                },
                "allPatList": [{"patName": "PRIVATE-CHEMICAL-DETAIL"}],
            }
        ]
    )
    observed: list[bytes] = []

    def transport(request: bytes) -> bytes:
        observed.append(request)
        return source

    report = probe_one_page(region_code=55, page_number=0, transport=transport)
    assert report.outcome == "PARSED"
    assert report.parsed_notices == 1
    assert report.unidentified_records == 0
    assert report.shape is not None
    assert report.shape.record_count == 1
    assert report.shape.field_record_count == 1
    assert len(observed) == 1
    output = json.dumps(asdict(report))
    assert secret not in output
    assert "PRIVATE-CHEMICAL-DETAIL" not in output
    assert "coordinates" not in output


def test_unknown_rows_are_not_reported_as_clean_source_coverage() -> None:
    raw = _valid_page([{"unrecognizedRawField": "PRIVATE-COORDINATES"}])
    result = probe_one_page(region_code=55, page_number=0, transport=lambda _: raw)
    assert result.outcome == "UNRECOGNIZED_ROWS"
    assert result.parsed_notices == 0
    assert result.unidentified_records == 1
    assert result.coverage_complete is False
    assert "unrecognizedRawField" not in str(result)
    assert "PRIVATE-COORDINATES" not in str(result)


@pytest.mark.parametrize(
    ("raw", "kind", "content_kind"),
    [
        (b"not json", "invalid", "missing"),
        (b"[" * 1_000_001, "invalid", "missing"),
        (b"[]", "array", "missing"),
        (b'{"rawField":"PRIVATE-DATA"}', "object", "missing"),
        (b'{"content":{"record": "PRIVATE-DATA"}}', "object", "other"),
    ],
)
def test_response_diagnostics_preserve_shape_without_values(
    raw: bytes, kind: str, content_kind: str
) -> None:
    result = probe_one_page(region_code=55, page_number=0, transport=lambda _: raw)
    assert result.outcome == "RESPONSE_ERROR"
    assert result.shape is not None
    assert result.shape.json_kind == kind
    assert result.shape.content_kind == content_kind
    assert b"PRIVATE" not in repr(result).encode()
    assert describe_page_shape(raw).known_envelope_fields == result.shape.known_envelope_fields


def test_transport_failure_does_not_invent_empty_page_or_disclose_error() -> None:
    def transport(_: bytes) -> bytes:
        raise SourceReadError("PRIVATE UPSTREAM TOKEN")

    result = probe_one_page(region_code=55, page_number=0, transport=transport)
    assert result.outcome == "TRANSPORT_ERROR"
    assert result.shape is None
    assert result.parsed_notices is None
    assert "PRIVATE" not in repr(result)


def test_http_status_is_available_without_upstream_body_or_url() -> None:
    def transport(_: bytes) -> bytes:
        raise SourceReadError("Public portal request failed") from HTTPError(
            "https://private.example/internal", 403, "PRIVATE MESSAGE", Message(), None
        )

    result = probe_one_page(region_code=55, page_number=0, transport=transport)
    assert result.outcome == "HTTP_ERROR"
    assert result.upstream_http_status == 403
    assert "example" not in repr(result)
    assert "PRIVATE" not in repr(result)


def test_invalid_scope_is_rejected_before_transport() -> None:
    observed = False

    def transport(_: bytes) -> bytes:
        nonlocal observed
        observed = True
        return _valid_page([])

    with pytest.raises(ValueError):
        probe_one_page(region_code=0, page_number=0, transport=transport)
    assert not observed
