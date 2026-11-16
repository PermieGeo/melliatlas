"""Offline verification of one-shot Saturn district capture and reviewed identity joins."""

import hashlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Self

import pytest
from import_saturn_districts import (
    CanonicalDistrict,
    parse_overrides,
    propose_mappings,
    run_import,
)

from melliatlas.api.subject_capture import capture_subjects
from melliatlas.sources.providers.saturn.districts import (
    SaturnDistrict,
    normalized_district_name,
    validate_district_directory,
)


def _district_directory(size: int = 27) -> bytes:
    entries: list[dict[str, object]] = [
        {"id": 2000 + index, "name": f"Test district {index}"} for index in range(size)
    ]
    entries[0] = {
        "id": 1524,
        "name": "Велижский муниципальный район",
        "latitude": 55.6038,
        "longitude": 31.1972,
    }
    return json.dumps(entries, ensure_ascii=False).encode("utf-8")


def test_historical_smolensk_directory_and_operator_capture(tmp_path: Path) -> None:
    raw = _district_directory()
    parsed = validate_district_directory(raw)
    assert len(parsed) == 27
    assert parsed[0] == SaturnDistrict(1524, "Велижский муниципальный район")
    assert normalized_district_name(parsed[0].name) == "велижский район"
    output = tmp_path / "districts.json"
    count, digest, _ = capture_subjects(
        output, lambda: raw, lambda payload: len(validate_district_directory(payload))
    )
    assert count == 27
    assert output.read_bytes() == raw
    assert digest == hashlib.sha256(raw).hexdigest()
    with pytest.raises(FileExistsError):
        capture_subjects(
            output, lambda: b"", lambda payload: len(validate_district_directory(payload))
        )


@pytest.mark.parametrize(
    "raw",
    [
        b"{}",
        b"[]",
        b"not-json",
        b" " * 64_001,
        b'[{"id": true, "name": "District"}]',
        b'[{"id": 0, "name": "District"}]',
        b'[{"id": 55, "name": "  "}]',
        b'[{"id": 55, "name": "A"}, {"id": 55, "name": "B"}]',
        b'[{"id": 55, "name": "A"}, {"id": 56, "name": "A"}]',
    ],
)
def test_directory_rejects_unsafe_or_ambiguous_source(raw: bytes) -> None:
    with pytest.raises(ValueError):
        validate_district_directory(raw)


def test_exact_names_need_review_and_missing_names_remain_unmapped() -> None:
    source = (
        SaturnDistrict(1524, "Велижский муниципальный район"),
        SaturnDistrict(1777, "Unknown municipality"),
    )
    canonical = (
        CanonicalDistrict("ru:district:vel", "Velizhsky district", "Велижский район"),
        CanonicalDistrict("ru:district:other", "Different district", None),
    )
    matches, missing = propose_mappings(source, canonical, {})
    assert matches[0].district_id == "ru:district:vel"
    assert matches[0].provider_district_code == 1524
    assert matches[0].match_method == "exact_normalized_name"
    assert missing == (source[1],)
    overridden, missing = propose_mappings(source, canonical, {1777: "ru:district:other"})
    assert len(overridden) == 2
    assert not missing
    assert overridden[1].match_method == "operator_override"


def test_ambiguous_names_and_conflicting_overrides_fail_closed(tmp_path: Path) -> None:
    source = (SaturnDistrict(1524, "Велижский муниципальный район"),)
    canonical = (
        CanonicalDistrict("ru:district:a", "A", "Велижский район"),
        CanonicalDistrict("ru:district:b", "B", "Велижский район"),
    )
    found, missing = propose_mappings(source, canonical, {})
    assert found == () and missing == source
    with pytest.raises(ValueError, match="one canonical"):
        propose_mappings(
            (source[0], SaturnDistrict(1777, "Other")),
            canonical,
            {1524: "ru:district:a", 1777: "ru:district:a"},
        )
    path = tmp_path / "overrides.json"
    path.write_text('{"1524": "ru:district:a", "1777": "ru:district:a"}')
    with pytest.raises(ValueError, match="same canonical"):
        parse_overrides(path)
    path.write_text('{"1524": "by:district:a"}')
    with pytest.raises(ValueError, match="RU district"):
        parse_overrides(path)
    path.write_text('{"1524": "ru:district:a"}')
    assert parse_overrides(path) == {1524: "ru:district:a"}


class _DatabaseCursor:
    def __init__(self, *, subject: int = 55, existing: int | None = None) -> None:
        self.subject = subject
        self.existing = existing
        self.sql: list[str] = []
        self.params: list[tuple[object, ...]] = []
        self._one: tuple[object, ...] | None = None
        self.writes = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        self.sql.append(query)
        self.params.append(params)
        self._one = None
        if "INSERT INTO melliatlas_source_saturn_district" in query:
            self.writes += 1
            self._one = ("ru:district:vel",) if self.existing is None else None
        elif "SELECT subject_id FROM melliatlas_source_saturn" in query:
            self._one = (self.subject,)

    def fetchone(self) -> tuple[object, ...] | None:
        return self._one

    def fetchall(self) -> list[tuple[object, ...]]:
        sql = self.sql[-1]
        if "FROM melliatlas_admin_geometry" in sql:
            return [("ru:district:vel", "Velizhsky district", "Велижский район")]
        if "SELECT m.district_id" in sql:
            return [] if self.existing is None else [("ru:district:vel", self.existing)]
        raise AssertionError(f"Unexpected query: {sql}")


class _DatabaseConnection:
    def __init__(self, cursor: _DatabaseCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self) -> _DatabaseCursor:
        return self._cursor


def _inject_psycopg(monkeypatch: pytest.MonkeyPatch, cursor: _DatabaseCursor) -> None:
    fake = ModuleType("psycopg")

    def connect(dsn: str, connect_timeout: int) -> _DatabaseConnection:
        assert dsn == "fake-dsn" and connect_timeout == 5
        return _DatabaseConnection(cursor)

    monkeypatch.setattr(fake, "connect", connect, raising=False)
    monkeypatch.setitem(sys.modules, "psycopg", fake)


def test_dry_run_does_not_write_but_approved_import_inserts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _DatabaseCursor()
    _inject_psycopg(monkeypatch, cursor)
    directory = (SaturnDistrict(1524, "Велижский муниципальный район"),)
    proposed = run_import("fake-dsn", directory, "hash", {}, apply=False)
    assert proposed["proposed_count"] == 1
    assert proposed["applied"] is False
    assert cursor.writes == 0
    applied = run_import("fake-dsn", directory, "hash", {}, apply=True)
    assert applied["inserted"] == 1
    assert cursor.writes == 1
    assert cursor.params[-1][0] == "ru:district:vel"
    assert cursor.params[-1][1] == 1524


def test_existing_mapping_is_idempotent_and_mismatches_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _DatabaseCursor(existing=1524)
    _inject_psycopg(monkeypatch, cursor)
    directory = (SaturnDistrict(1524, "Велижский муниципальный район"),)
    repeated = run_import("fake-dsn", directory, "hash", {}, apply=True)
    assert repeated["inserted"] == 0
    cursor.existing = 1555
    with pytest.raises(ValueError, match="conflicts"):
        run_import("fake-dsn", directory, "hash", {}, apply=True)
    cursor.subject = 56
    with pytest.raises(ValueError, match="subject"):
        run_import("fake-dsn", directory, "hash", {}, apply=False)
