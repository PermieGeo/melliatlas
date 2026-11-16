"""One bounded, pinned HTTPS transport for opt-in public Saturn reads."""

import socket
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from melliatlas.sources.api import SourceReadError

SATURN_PUBLIC_URL = "https://bee-saturn.ru/backend/beemaster/planapplybees"
SATURN_SUBJECTS_URL = "https://bee-saturn.ru/backend/beemaster/oktmo-subjects"
MAX_BODY_BYTES = 1_000_000
SATURN_SUBJECTS_BODY_LIMIT = 256_000
TIMEOUT_SECONDS = 8


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> None:
        return None


def post_public_page(body: bytes) -> bytes:
    """No redirects, retries, user-supplied destinations, or unbounded response reads."""
    request = Request(
        SATURN_PUBLIC_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "MelliAtlas-ReadOnly/0.1",
        },
        method="POST",
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise SourceReadError("Public portal did not return HTTP 200")
            if response.headers.get_content_type() != "application/json":
                raise SourceReadError("Public portal response is not JSON")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SourceReadError("Unsupported public portal response encoding")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdecimal() or int(length) > MAX_BODY_BYTES):
                raise SourceReadError("Public portal response exceeds size budget")
            payload = response.read(MAX_BODY_BYTES + 1)
            if len(payload) > MAX_BODY_BYTES:
                raise SourceReadError("Public portal response exceeds size budget")
            return payload
    except (HTTPError, URLError, TimeoutError, socket.timeout, HTTPException, OSError) as error:
        raise SourceReadError("Public portal request failed") from error


def get_public_subject_directory() -> bytes:
    """Fetch exactly one public subject directory without redirects or retries.

    This operator-triggered read is separate from ordinary application startup.
    """
    request = Request(
        SATURN_SUBJECTS_URL,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "MelliAtlas-ReadOnly/0.1",
        },
        method="GET",
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise SourceReadError("Public subject directory did not return HTTP 200")
            if response.headers.get_content_type() != "application/json":
                raise SourceReadError("Public subject directory response is not JSON")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SourceReadError("Unsupported public subject directory encoding")
            length = response.headers.get("Content-Length")
            if length is not None and (
                not length.isdecimal() or int(length) > SATURN_SUBJECTS_BODY_LIMIT
            ):
                raise SourceReadError("Public subject directory exceeds size budget")
            body = response.read(SATURN_SUBJECTS_BODY_LIMIT + 1)
            if len(body) > SATURN_SUBJECTS_BODY_LIMIT:
                raise SourceReadError("Public subject directory exceeds size budget")
            return body
    except (HTTPError, URLError, TimeoutError, socket.timeout, HTTPException, OSError) as exc:
        raise SourceReadError("Public subject directory request failed") from exc
