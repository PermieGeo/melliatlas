"""One-shot Saturn directory capture never guesses mappings or contacts live services."""

import hashlib
import json
import stat
from email.message import Message
from pathlib import Path
from types import TracebackType
from typing import Self
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request

import pytest

from melliatlas.api.subject_capture import capture_subjects
from melliatlas.sources.api import SourceReadError
from melliatlas.sources.providers import http_transport
from melliatlas.sources.providers.saturn import http as saturn_http
from melliatlas.sources.providers.saturn.subjects import validate_subject_directory


def _items(size: int = 86) -> list[dict[str, object]]:
    items: list[dict[str, object]] = [
        {"id": index, "oktmoCode": f"{index:08d}", "name": f"Test subject {index}"}
        for index in range(1, size + 1)
    ]
    items[0] = {
        "id": 55,
        "oktmoCode": "66000000",
        "name": "Смоленская область",
        "x": 32.04,
        "y": 54.78,
    }
    # Source identifiers in the synthetic contract fixture must remain distinct.
    items[54] = {"id": 1, "oktmoCode": "00000001", "name": "Other subject"}
    return items


def _directory(size: int = 86) -> bytes:
    return json.dumps(_items(size), ensure_ascii=False).encode("utf-8")


def test_validate_historical_subject_directory_shape() -> None:
    subjects = validate_subject_directory(_directory(), min_entries=80)
    assert len(subjects) == 86
    assert subjects[0].id == 55
    assert subjects[0].oktmo_code == "66000000"
    assert subjects[0].name == "Смоленская область"


@pytest.mark.parametrize(
    "payload",
    [
        b"not JSON",
        b"{}",
        b"[]",
        b"[] " * 100_000,
        b'[{"id": true, "oktmoCode": "66000000", "name": "Private"}]',
        b'[{"id": 55, "oktmoCode": 66000000, "name": "Private"}]',
        b'[{"id": 55, "oktmoCode": "66000000", "name": "  "}]',
    ],
)
def test_validation_rejects_wrong_or_unbounded_envelopes(payload: bytes) -> None:
    with pytest.raises(ValueError):
        validate_subject_directory(payload)


def test_validation_rejects_duplicate_identifiers_and_names() -> None:
    raw = _items()
    raw[1]["id"] = 55
    with pytest.raises(ValueError, match="Duplicate Saturn subject IDs"):
        validate_subject_directory(json.dumps(raw).encode())
    raw[1]["id"] = 2
    raw[1]["name"] = "Смоленская область"
    with pytest.raises(ValueError, match="Duplicate Saturn subject names"):
        validate_subject_directory(json.dumps(raw, ensure_ascii=False).encode())


def test_capture_is_exclusive_private_and_retains_source_bytes(tmp_path: Path) -> None:
    raw = _directory()
    destination = tmp_path / "subjects.json"
    calls = 0

    def fetch() -> bytes:
        nonlocal calls
        calls += 1
        return raw

    def count_subjects(payload: bytes) -> int:
        return len(validate_subject_directory(payload, min_entries=80))

    count, digest, captured_at = capture_subjects(destination, fetch, count_subjects)
    assert calls == 1
    assert count == 86
    assert digest == hashlib.sha256(raw).hexdigest()
    assert captured_at.utcoffset() is not None
    assert destination.read_bytes() == raw
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        capture_subjects(destination, fetch, count_subjects)
    assert calls == 1
    assert destination.read_bytes() == raw


def test_invalid_capture_does_not_create_a_file(tmp_path: Path) -> None:
    destination = tmp_path / "invalid.json"
    with pytest.raises(ValueError):
        capture_subjects(
            destination,
            lambda: b'{"private":"SECRET"}',
            lambda raw: len(validate_subject_directory(raw, min_entries=80)),
        )
    assert not destination.exists()


class FakeResponse:
    def __init__(
        self, body: bytes, *, mime: str = "application/json", encoding: str = "identity"
    ) -> None:
        self.status = 200
        self.headers: Message[str, str] = Message()
        self.headers["Content-Type"] = mime
        self.headers["Content-Encoding"] = encoding
        self._body = body

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self._body[:limit]


class FakeOpener:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.requests: list[Request] = []

    def open(self, request: Request, *, timeout: int) -> FakeResponse:
        assert timeout == saturn_http.TIMEOUT_SECONDS
        self.requests.append(request)
        return self.response


def test_bounded_transport_uses_single_fixed_get_no_user_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeOpener(FakeResponse(_directory()))

    def builder(handler: object) -> FakeOpener:
        assert isinstance(handler, HTTPRedirectHandler)
        return fake

    monkeypatch.setattr(http_transport, "build_opener", builder)
    body = saturn_http.get_public_subject_directory()
    assert len(fake.requests) == 1
    assert fake.requests[0].get_method() == "GET"
    assert fake.requests[0].full_url == saturn_http.SATURN_SUBJECTS_URL
    assert body == _directory()


@pytest.mark.parametrize(
    "mime,encoding,body",
    [
        ("text/html", "identity", b"<html>not json</html>"),
        ("application/json", "gzip", b"compressed"),
        ("application/json", "identity", b" " * 256_001),
    ],
)
def test_transport_rejects_bad_content_and_oversize(
    monkeypatch: pytest.MonkeyPatch, mime: str, encoding: str, body: bytes
) -> None:
    fake = FakeOpener(FakeResponse(body, mime=mime, encoding=encoding))

    def builder(handler: object) -> FakeOpener:
        return fake

    monkeypatch.setattr(http_transport, "build_opener", builder)
    with pytest.raises(SourceReadError):
        saturn_http.get_public_subject_directory()


def test_transport_rejects_upstream_403_without_returning_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ErrorOpener:
        def open(self, request: Request, *, timeout: int) -> FakeResponse:
            raise HTTPError(request.full_url, 403, "PRIVATE", Message(), None)

    def builder(handler: object) -> ErrorOpener:
        return ErrorOpener()

    monkeypatch.setattr(http_transport, "build_opener", builder)
    with pytest.raises(SourceReadError, match="Public subject directory request failed") as info:
        saturn_http.get_public_subject_directory()
    assert "PRIVATE" not in str(info.value)
