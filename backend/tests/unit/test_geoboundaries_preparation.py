"""Offline contract checks for geoBoundaries staging and manifest-locked imports."""

import hashlib
import json
from datetime import date
from pathlib import Path

import import_admin_boundaries as importer
import prepare_geoboundaries as preparation
import pytest

METADATA: dict[str, object] = {
    "boundaryID": "BLR-ADM1-45462678",
    "boundaryISO": "BLR",
    "boundaryType": "ADM1",
    "admUnitCount": "1",
    "simplifiedGeometryGeoJSON": (
        "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
        "releaseData/gbOpen/BLR/ADM1/example.geojson"
    ),
    "boundaryLicense": "CC BY 3.0",
    "boundaryYearRepresented": "2005",
    "boundarySource": "CIESIN",
}
GEOMETRY = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "shapeID": "45462678B123",
                "shapeGroup": "BLR",
                "shapeType": "ADM1",
                "shapeName": "Витебская область",
                "shapeISO": "BY-VI",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[27, 55], [28, 55], [28, 56], [27, 55]]],
            },
        }
    ],
}


def test_prepares_verified_local_files_and_review_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(url: str, _limit: int, *, metadata: bool) -> bytes:
        if metadata:
            assert url == "https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM1/"
            return json.dumps(METADATA).encode()
        assert url == METADATA["simplifiedGeometryGeoJSON"]
        return json.dumps(GEOMETRY).encode()

    monkeypatch.setattr(preparation, "_read_url", fetch)
    manifest = preparation.prepare("BY", "ADM1", tmp_path)
    source = tmp_path / str(manifest["file_name"])
    assert source.is_file()
    assert manifest["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert manifest["unmatched_regions"] == 0
    review = json.loads((tmp_path / f"{source.name}.review.json").read_text())
    assert review[0]["exact_match"] == "by:region:vi"
    metadata_path = tmp_path / f"{source.name}.manifest.json"
    assert importer.manifest_provenance(metadata_path, source, "BY", "ADM1") == (
        "geoboundaries:BLR-ADM1-45462678",
        "https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM1/",
        "CC BY 3.0",
    )
    reused = preparation.prepare("BY", "ADM1", tmp_path)
    assert reused["reused"] is True
    assert reused["sha256"] == manifest["sha256"]
    source.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="changed since"):
        importer.manifest_provenance(metadata_path, source, "BY", "ADM1")
    with pytest.raises(ValueError, match="identity"):
        importer.manifest_provenance(metadata_path, source, "RU", "ADM1")


@pytest.mark.parametrize(
    "url",
    [
        "http://www.geoboundaries.org/api/current/gbOpen/RUS/ADM2/",
        "https://localhost/releaseData/gbOpen/BLR/ADM1/file.geojson",
        "https://github.com/other/geoBoundaries/raw/9469f09/releaseData/gbOpen/BLR/ADM1/a",
        (
            "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
            "releaseData/gbOpen/BLR/ADM1/a?token=x"
        ),
        "https://127.0.0.1/internal",
    ],
)
def test_rejects_untrusted_geometry_urls(url: str) -> None:
    assert not preparation.trusted_url(url, metadata=False)


def test_rejects_cross_country_metadata() -> None:
    with pytest.raises(ValueError, match="does not match"):
        preparation.inspect_metadata("RU", "ADM1", METADATA)
    with pytest.raises(ValueError, match="Untrusted"):
        preparation.inspect_metadata(
            "BY", "ADM1", {**METADATA, "simplifiedGeometryGeoJSON": "https://localhost/data"}
        )


def test_rejects_partial_download_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        if metadata:
            return json.dumps(METADATA).encode()
        return json.dumps({"type": "FeatureCollection", "features": []}).encode()

    monkeypatch.setattr(preparation, "_read_url", fetch)
    with pytest.raises(ValueError, match="feature count"):
        preparation.prepare("BY", "ADM1", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_rejects_lfs_pointer_without_creating_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        if metadata:
            return json.dumps(METADATA).encode()
        return b"version https://git-lfs.github.com/spec/v1 oid sha256:deadbeef"

    monkeypatch.setattr(preparation, "_read_url", fetch)
    with pytest.raises(ValueError, match="LFS pointer"):
        preparation.prepare("BY", "ADM1", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_reference_metadata_requires_valid_sha_and_complete_identity(tmp_path: Path) -> None:
    source = tmp_path / "boundary.geojson"
    source.write_text(json.dumps(GEOMETRY))
    metadata = {
        "schema_version": 1,
        "country": "BY",
        "level": "ADM1",
        "file_name": source.name,
        "sha256": "a" * 64,
        "reference_id": "geoboundaries:BLR-ADM1-45462678",
        "source_uri": "https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM1/",
        "license": "CC BY 3.0",
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="changed since"):
        importer.manifest_provenance(manifest, source, "BY", "ADM1")
    metadata["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    metadata["source_uri"] = "https://example.org"
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="Unexpected boundary manifest source"):
        importer.manifest_provenance(manifest, source, "BY", "ADM1")


def test_region_mapping_never_uses_fuzzy_guesses() -> None:
    directory = [("by:region:vi", "BY-VI", "Витебская область", "Vitebsk")]
    assert importer.choose_region("sample", "VitEbSk", None, {}, directory) == "by:region:vi"
    assert importer.choose_region("sample", "Vitebsk city", None, {}, directory) is None
    assert (
        importer.choose_region(
            "sample", "Vitebsk city", None, {"sample": "by:region:vi"}, directory
        )
        == "by:region:vi"
    )
    with pytest.raises(ValueError, match="unknown region"):
        importer.choose_region(
            "sample", "Vitebsk", "BY-VI", {"sample": "by:region:other"}, directory
        )


def test_verification_requires_matching_source_versions(tmp_path: Path) -> None:
    from verify_admin_boundaries import manifest_summary

    path = tmp_path / "adm1.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "country": "BY",
                "level": "ADM1",
                "reference_id": "geoboundaries:BLR-ADM1-45462678",
                "unit_count": 7,
            }
        )
    )
    assert manifest_summary(path, "BY", "ADM1") == ("geoboundaries:BLR-ADM1-45462678", 7)
    with pytest.raises(ValueError, match="does not match"):
        manifest_summary(path, "RU", "ADM1")
    with pytest.raises(ValueError, match="does not match"):
        manifest_summary(path, "BY", "ADM2")


class _ExistingBoundaryConnection:
    def __init__(self, *, geometry_matches: bool) -> None:
        self.geometry_matches = geometry_matches
        self.failed = False
        self.statements: list[str] = []
        self.rows: list[tuple[object, ...]] = []

    def __enter__(self) -> "_ExistingBoundaryConnection":
        return self

    def __exit__(self, exception_type: type[BaseException] | None, *_args: object) -> None:
        self.failed = exception_type is not None

    def cursor(self) -> "_ExistingBoundaryConnection":
        return self

    def execute(self, query: str, _params: object = ()) -> None:
        self.statements.append(query)
        if "FROM melliatlas_region" in query:
            self.rows = [("by:region:vi", "BY-VI", "Витебская область", "Vitebsk")]
        elif "INSERT INTO melliatlas_admin_geometry" in query:
            self.rows = []
        elif "ST_Equals(boundary" in query:
            self.rows = [
                (
                    "45462678B123",
                    "geoboundaries:BLR-ADM1-45462678",
                    "Витебская область",
                    "by:region:vi",
                    "https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM1/",
                    "CC BY 3.0",
                    date(2005, 1, 1),
                    self.geometry_matches,
                )
            ]
        else:
            raise AssertionError(f"Unexpected SQL: {query}")

    def fetchall(self) -> list[tuple[object, ...]]:
        rows, self.rows = self.rows, []
        return rows

    def fetchone(self) -> tuple[object, ...] | None:
        return self.rows.pop(0) if self.rows else None


def test_reimport_checks_existing_geometry_and_rolls_back_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys
    from datetime import date
    from types import ModuleType

    document = tmp_path / "boundaries.geojson"
    document.write_text(json.dumps(GEOMETRY), encoding="utf-8")
    connection = _ExistingBoundaryConnection(geometry_matches=True)
    driver = ModuleType("psycopg")

    def connect(_dsn: str) -> _ExistingBoundaryConnection:
        return connection

    setattr(driver, "connect", connect)
    monkeypatch.setitem(sys.modules, "psycopg", driver)
    common = (
        "postgresql://test",
        document,
        "BY",
        "ADM1",
        "geoboundaries:BLR-ADM1-45462678",
        "https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM1/",
        "CC BY 3.0",
        date(2005, 1, 1),
    )
    assert importer.import_boundaries(*common) == (0, 1, 0)
    assert not connection.failed
    assert any("ST_Equals(boundary" in statement for statement in connection.statements)
    connection = _ExistingBoundaryConnection(geometry_matches=False)
    with pytest.raises(ValueError, match="Existing boundary differs"):
        importer.import_boundaries(*common)
    assert connection.failed


def test_mismatched_source_inventory_is_staged_but_import_requires_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        if metadata:
            return json.dumps({**METADATA, "admUnitCount": "2"}).encode()
        return json.dumps(GEOMETRY).encode()

    monkeypatch.setattr(preparation, "_read_url", fetch)
    manifest = preparation.prepare("BY", "ADM1", tmp_path)
    assert manifest["unit_count"] == 1
    assert manifest["advertised_unit_count"] == 2
    assert manifest["inventory_matches_metadata"] is False
    assert manifest["review_status"] == "inventory_mismatch"
    assert "advertises 2 units" in capsys.readouterr().err
    source = tmp_path / str(manifest["file_name"])
    metadata = tmp_path / f"{source.name}.manifest.json"
    with pytest.raises(ValueError, match="Source inventory differs"):
        importer.manifest_provenance(metadata, source, "BY", "ADM1")
    provenance = importer.manifest_provenance(
        metadata, source, "BY", "ADM1", acknowledge_inventory_mismatch=True
    )
    assert provenance[0] == "geoboundaries:BLR-ADM1-45462678"
    reused = preparation.prepare("BY", "ADM1", tmp_path)
    assert reused["reused"] is True
    assert reused["review_status"] == "inventory_mismatch"


def test_corrupted_cached_capture_fails_closed_without_redownloading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        return json.dumps(METADATA if metadata else GEOMETRY).encode()

    monkeypatch.setattr(preparation, "_read_url", fetch)
    manifest = preparation.prepare("BY", "ADM1", tmp_path)
    (tmp_path / str(manifest["file_name"])).write_text("corrupted", encoding="utf-8")

    def cannot_fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        raise AssertionError("Corrupt cached data must not trigger a remote download")

    monkeypatch.setattr(preparation, "_read_url", cannot_fetch)
    with pytest.raises(ValueError, match="changed since"):
        preparation.prepare("BY", "ADM1", tmp_path)


def test_incomplete_capture_is_not_treated_as_reusable(tmp_path: Path) -> None:
    (tmp_path / "BLR-ADM2-123.geojson").write_text("partial", encoding="utf-8")
    with pytest.raises(ValueError, match="Incomplete or ambiguous"):
        preparation.prepare("BY", "ADM2", tmp_path)


def test_metadata_count_and_review_fields_cannot_be_edited_to_bypass_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        if metadata:
            return json.dumps({**METADATA, "admUnitCount": "2"}).encode()
        return json.dumps(GEOMETRY).encode()

    monkeypatch.setattr(preparation, "_read_url", fetch)
    result = preparation.prepare("BY", "ADM1", tmp_path)
    source = tmp_path / str(result["file_name"])
    manifest = tmp_path / f"{source.name}.manifest.json"
    original = json.loads(manifest.read_text(encoding="utf-8"))
    for tampered in (
        {**original, "inventory_matches_metadata": True},
        {**original, "review_status": "pending"},
    ):
        manifest.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(ValueError, match="Inconsistent"):
            importer.manifest_provenance(
                manifest, source, "BY", "ADM1", acknowledge_inventory_mismatch=True
            )


def test_batch_stages_missing_layers_and_reuses_verified_captures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import prepare_all_geoboundaries as batch

    calls: list[tuple[str, str]] = []

    def capture(country: str, level: str, _output: Path) -> dict[str, object]:
        calls.append((country, level))
        return {
            "country": country,
            "level": level,
            "unit_count": 1,
            "review_status": (
                "inventory_mismatch" if country == "RU" and level == "ADM2" else "pending"
            ),
            "reused": country == "RU" and level == "ADM1",
        }

    monkeypatch.setattr(batch, "prepare", capture)
    reports, errors = batch.prepare_all(tmp_path)
    assert calls == list(batch.LAYERS)
    assert errors == []
    assert len(reports) == 4
    assert reports[1]["review_status"] == "inventory_mismatch"
    assert reports[0]["reused"] is True


def test_batch_reports_failed_layer_without_silencing_remaining_attempts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import prepare_all_geoboundaries as batch

    attempts: list[str] = []

    def capture(country: str, level: str, _output: Path) -> dict[str, object]:
        attempts.append(f"{country}/{level}")
        if country == "RU" and level == "ADM2":
            raise ValueError("provider unavailable")
        return {"country": country, "level": level, "unit_count": 1, "review_status": "pending"}

    monkeypatch.setattr(batch, "prepare", capture)
    reports, errors = batch.prepare_all(tmp_path)
    assert attempts == ["RU/ADM1", "RU/ADM2", "BY/ADM1", "BY/ADM2"]
    assert len(reports) == 3
    assert errors == ["RU/ADM2: provider unavailable"]


def test_existing_capture_requires_matching_adm1_review_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(_url: str, _limit: int, *, metadata: bool) -> bytes:
        return json.dumps(METADATA if metadata else GEOMETRY).encode()

    monkeypatch.setattr(preparation, "_read_url", fetch)
    manifest = preparation.prepare("BY", "ADM1", tmp_path)
    review = tmp_path / f"{manifest['file_name']}.review.json"
    review.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="review does not cover"):
        preparation.prepare("BY", "ADM1", tmp_path)


def test_verifier_retains_provider_count_as_separate_audit_field(tmp_path: Path) -> None:
    from verify_admin_boundaries import advertised_inventory, manifest_summary

    path = tmp_path / "adm2.manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "country": "RU",
                "level": "ADM2",
                "reference_id": "geoboundaries:RUS-ADM2-50074027",
                "unit_count": 2200,
                "advertised_unit_count": 2328,
                "inventory_matches_metadata": False,
            }
        ),
        encoding="utf-8",
    )
    assert manifest_summary(path, "RU", "ADM2")[1] == 2200
    assert advertised_inventory(path, 2200) == 2328
    metadata: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    metadata["inventory_matches_metadata"] = True
    path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="provider inventory"):
        manifest_summary(path, "RU", "ADM2")


def test_staging_prints_download_progress_with_a_bounded_http_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from urllib.request import Request

    geometry_bytes = json.dumps(GEOMETRY).encode() + b" " * (2 * 1024 * 1024)
    metadata_bytes = json.dumps(METADATA).encode()

    class Response:
        def __init__(self, data: bytes) -> None:
            self.data = data
            self.offset = 0
            self.headers = {"Content-Length": str(len(data))}

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def read(self, count: int) -> bytes:
            result = self.data[self.offset : self.offset + count]
            self.offset += len(result)
            return result

    class Opener:
        def open(self, request: Request, *, timeout: int) -> Response:
            assert timeout == 45
            if request.full_url.endswith("/BLR/ADM1/"):
                return Response(metadata_bytes)
            assert request.full_url == METADATA["simplifiedGeometryGeoJSON"]
            return Response(geometry_bytes)

    def fake_opener(*_handlers: object) -> Opener:
        return Opener()

    monkeypatch.setattr(preparation, "build_opener", fake_opener)
    result = preparation.prepare("BY", "ADM1", tmp_path)
    assert result["unit_count"] == 1
    output = capsys.readouterr().err
    assert "BY/ADM1: downloading" in output
    assert "Downloaded 2.0 MiB" in output
    assert "Download completed" in output
