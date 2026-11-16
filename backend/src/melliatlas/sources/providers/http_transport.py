"""Shared fixed-origin HTTPS transport used only by audited provider adapters.

The caller supplies a pinned HTTPS destination and its expected hostname.
No redirect, retry, credentials, caller-provided destination or streaming bypass
is permitted. Upstream failures are mapped to sanitized reason codes.
"""

import socket
from dataclasses import dataclass
from http.client import HTTPException
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from melliatlas.sources.api import SourceReadError


@dataclass(frozen=True)
class JsonTransportFailures:
    http: str
    mime: str
    encoding: str
    size: str
    transport: str


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: object, code: int, msg: str, headers: object, newurl: str
    ) -> None:
        return None


def read_fixed_origin_json(
    url: str,
    *,
    expected_host: str,
    method: Literal["GET", "POST"],
    body: bytes | None,
    timeout_seconds: int,
    max_body_bytes: int,
    failures: JsonTransportFailures,
) -> bytes:
    """Read a single JSON response with fixed origin and bounded memory usage."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != expected_host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or parsed.fragment
        or not parsed.path.startswith("/")
    ):
        raise ValueError("Source transport endpoint is not a pinned HTTPS origin")
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "MelliAtlas-ReadOnly/0.1",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
        method=method,
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise SourceReadError(failures.http)
            if response.headers.get_content_type() != "application/json":
                raise SourceReadError(failures.mime)
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise SourceReadError(failures.encoding)
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdecimal() or int(length) > max_body_bytes):
                raise SourceReadError(failures.size)
            payload = response.read(max_body_bytes + 1)
            if len(payload) > max_body_bytes:
                raise SourceReadError(failures.size)
            return payload
    except (HTTPError, URLError, TimeoutError, socket.timeout, HTTPException, OSError) as error:
        raise SourceReadError(failures.transport) from error
