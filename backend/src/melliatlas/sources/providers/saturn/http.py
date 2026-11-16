"""Pinned Saturn endpoints and bounded user-triggered public reads.

Both operations are explicit and region-independent at the transport layer.
No automated crawler, HTTP redirect, retry, or upstream credential is used.
The shared transport owns HTTP mechanics; this module owns provider policy.
"""

from melliatlas.sources.providers.http_transport import (
    JsonTransportFailures,
    read_fixed_origin_json,
)
from melliatlas.sources.providers.saturn.failures import SaturnReadFailure
from melliatlas.sources.providers.saturn.limits import MAX_BODY_BYTES

SATURN_PUBLIC_URL = "https://bee-saturn.ru/backend/beemaster/planapplybees"
SATURN_SUBJECTS_URL = "https://bee-saturn.ru/backend/beemaster/oktmo-subjects"
SATURN_SUBJECTS_BODY_LIMIT = 256_000
SATURN_SMOLENSK_DISTRICTS_URL = "https://bee-saturn.ru/backend/beemaster/district/55"
SATURN_DISTRICTS_BODY_LIMIT = 64_000
TIMEOUT_SECONDS = 8
_HOST = "bee-saturn.ru"

_PAGE_FAILURES = JsonTransportFailures(
    SaturnReadFailure.SATURN_PAGE_HTTP,
    SaturnReadFailure.SATURN_PAGE_TYPE,
    SaturnReadFailure.SATURN_PAGE_ENCODING,
    SaturnReadFailure.SATURN_PAGE_SIZE,
    SaturnReadFailure.SATURN_PAGE_REQUEST,
)
_DIRECTORY_FAILURES = JsonTransportFailures(
    SaturnReadFailure.SATURN_DIRECTORY_HTTP,
    SaturnReadFailure.SATURN_DIRECTORY_TYPE,
    SaturnReadFailure.SATURN_DIRECTORY_ENCODING,
    SaturnReadFailure.SATURN_DIRECTORY_SIZE,
    SaturnReadFailure.SATURN_DIRECTORY_REQUEST,
)
_DISTRICT_FAILURES = JsonTransportFailures(
    SaturnReadFailure.SATURN_DISTRICT_HTTP,
    SaturnReadFailure.SATURN_DISTRICT_TYPE,
    SaturnReadFailure.SATURN_DISTRICT_ENCODING,
    SaturnReadFailure.SATURN_DISTRICT_SIZE,
    SaturnReadFailure.SATURN_DISTRICT_REQUEST,
)


def post_public_page(body: bytes) -> bytes:
    """Return one bounded provider page; body is created by the decoder, not a caller URL."""
    return read_fixed_origin_json(
        SATURN_PUBLIC_URL,
        expected_host=_HOST,
        method="POST",
        body=body,
        timeout_seconds=TIMEOUT_SECONDS,
        max_body_bytes=MAX_BODY_BYTES,
        failures=_PAGE_FAILURES,
    )


def get_public_subject_directory() -> bytes:
    """Capture one operator-requested directory for explicit offline review."""
    return read_fixed_origin_json(
        SATURN_SUBJECTS_URL,
        expected_host=_HOST,
        method="GET",
        body=None,
        timeout_seconds=TIMEOUT_SECONDS,
        max_body_bytes=SATURN_SUBJECTS_BODY_LIMIT,
        failures=_DIRECTORY_FAILURES,
    )


def get_smolensk_district_directory() -> bytes:
    """Capture one explicit Smolensk directory for offline operator review."""
    return read_fixed_origin_json(
        SATURN_SMOLENSK_DISTRICTS_URL,
        expected_host=_HOST,
        method="GET",
        body=None,
        timeout_seconds=TIMEOUT_SECONDS,
        max_body_bytes=SATURN_DISTRICTS_BODY_LIMIT,
        failures=_DISTRICT_FAILURES,
    )
