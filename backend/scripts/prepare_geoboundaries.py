"""Explicitly download and inspect a pinned geoBoundaries ADM1/ADM2 snapshot.

Nothing is imported into PostGIS by this command. Review the manifest and
administrative identities before using import_admin_boundaries.py.
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from email.message import Message
from http.client import HTTPResponse
from pathlib import Path
from typing import TypeGuard
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from import_admin_boundaries import MAX_BYTES, _features, choose_region, manifest_provenance

COUNTRIES = {"RU": "RUS", "BY": "BLR"}
API_ROOT = "https://www.geoboundaries.org/api/current/gbOpen"
MAX_METADATA_BYTES = 128 * 1024
CHUNK_BYTES = 64 * 1024
GITHUB_PATH = re.compile(r"^/wmgeolab/geoBoundaries/(?:raw|blob)/[a-z0-9]+/releaseData/gbOpen/")
MEDIA_PATH = re.compile(r"^/media/wmgeolab/geoBoundaries/[a-z0-9]+/releaseData/gbOpen/")
RAW_PATH = re.compile(r"^/wmgeolab/geoBoundaries/[a-z0-9]+/releaseData/gbOpen/")


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _required(metadata: dict[str, object], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing geoBoundaries metadata: {key}")
    return value.strip()


def trusted_url(url: str, *, metadata: bool) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        return False
    if parsed.query or parsed.fragment:
        return False
    if metadata:
        return parsed.hostname == "www.geoboundaries.org" and parsed.path.startswith(
            "/api/current/gbOpen/"
        )
    return bool(
        (parsed.hostname == "github.com" and GITHUB_PATH.match(parsed.path))
        or (parsed.hostname == "media.githubusercontent.com" and MEDIA_PATH.match(parsed.path))
        or (parsed.hostname == "raw.githubusercontent.com" and RAW_PATH.match(parsed.path))
    )


class _BoundedRedirects(HTTPRedirectHandler):
    def redirect_request(
        self,
        request: Request,
        fp: HTTPResponse,
        code: int,
        message: str,
        headers: Message,
        newurl: str,
    ) -> Request | None:
        if not trusted_url(newurl, metadata=False):
            raise ValueError("Unexpected download redirect host or path")
        return super().redirect_request(request, fp, code, message, headers, newurl)


def _read_url(url: str, limit: int, *, metadata: bool) -> bytes:
    if not trusted_url(url, metadata=metadata):
        raise ValueError("Untrusted geoBoundaries URL")
    opener = build_opener(_BoundedRedirects())
    request = Request(url, headers={"User-Agent": "MelliAtlas-geography-import/1"})
    with opener.open(request, timeout=45) as response:
        advertised_size = response.headers.get("Content-Length")
        expected_size = (
            int(advertised_size) if advertised_size and advertised_size.isdecimal() else None
        )
        if expected_size is not None and expected_size > limit:
            raise ValueError("geoBoundaries response exceeds the local review limit")
        chunks: list[bytes] = []
        size = 0
        last_report = time.monotonic()
        last_bytes = 0
        while size <= limit:
            chunk = response.read(min(CHUNK_BYTES, limit - size + 1))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise ValueError("geoBoundaries response exceeds the local review limit")
            chunks.append(chunk)
            now = time.monotonic()
            if not metadata and (size - last_bytes >= 2 * 1024 * 1024 or now - last_report >= 3):
                progress = f"{size / (1024 * 1024):.1f} MiB"
                if expected_size:
                    progress += f" / {expected_size / (1024 * 1024):.1f} MiB"
                print(f"  Downloaded {progress}", file=sys.stderr, flush=True)
                last_bytes = size
                last_report = now
        if not metadata:
            print(
                f"  Download completed: {size / (1024 * 1024):.1f} MiB",
                file=sys.stderr,
                flush=True,
            )
    return b"".join(chunks)


def _existing_capture(country: str, level: str, output_dir: Path) -> dict[str, object] | None:
    """Reuse only an intact, unambiguous, digest-verified existing layer."""
    prefix = f"{COUNTRIES[country]}-{level}-"
    artifacts = list(output_dir.glob(f"{prefix}*"))
    if not artifacts:
        return None
    manifests = [path for path in artifacts if path.name.endswith(".geojson.manifest.json")]
    if len(manifests) != 1 or any(path.is_symlink() or not path.is_file() for path in artifacts):
        raise ValueError(
            f"Incomplete or ambiguous {country}/{level} staging files; review manually"
        )
    manifest_path = manifests[0]
    raw: object = json.loads(manifest_path.read_bytes())
    if not _is_object(raw):
        raise ValueError("Existing boundary manifest is not an object")
    name = raw.get("file_name")
    if not isinstance(name, str) or name != manifest_path.name.removesuffix(".manifest.json"):
        raise ValueError("Existing boundary manifest filename does not match its GeoJSON")
    source = output_dir / name
    if not source.is_file() or source.is_symlink():
        raise ValueError("Existing boundary GeoJSON is absent or unsafe")
    manifest_provenance(manifest_path, source, country, level, acknowledge_inventory_mismatch=True)
    if level == "ADM1":
        review = output_dir / f"{name}.review.json"
        if not review.is_file() or review.is_symlink():
            raise ValueError("Existing ADM1 matching review is missing")
        review_data: object = json.loads(review.read_bytes())
        entries = _features(source, country, level)
        if not isinstance(review_data, list) or len(review_data) != len(entries):
            raise ValueError("Existing ADM1 review does not cover the downloaded boundaries")
        reviewed_ids: set[str] = set()
        for item in review_data:
            if not _is_object(item):
                raise ValueError("Invalid ADM1 matching review entry")
            shape_id = item.get("shape_id")
            if not isinstance(shape_id, str):
                raise ValueError("Invalid ADM1 matching review entry")
            reviewed_ids.add(shape_id)
        if reviewed_ids != {shape_id for shape_id, *_ in entries}:
            raise ValueError("Existing ADM1 review does not match downloaded shape IDs")
    size = source.stat().st_size
    if raw.get("size_bytes") != size:
        raise ValueError("Existing boundary file size differs from the manifest")
    print(
        f"{country}/{level}: SKIP existing verified capture "
        f"({name}, {size / (1024 * 1024):.1f} MiB)",
        file=sys.stderr,
        flush=True,
    )
    return {**raw, "reused": True}


def inspect_metadata(country: str, level: str, value: object) -> dict[str, str | int]:
    if not _is_object(value):
        raise ValueError("Unexpected geoBoundaries metadata")
    expected = COUNTRIES[country]
    identifier = _required(value, "boundaryID")
    if (
        value.get("boundaryISO") != expected
        or value.get("boundaryType") != level
        or not re.fullmatch(rf"{expected}-{level}-[0-9]+", identifier)
    ):
        raise ValueError("GeoBoundary identity does not match requested geography")
    count = _required(value, "admUnitCount")
    if not count.isascii() or not count.isdecimal() or not 1 <= int(count) <= 5000:
        raise ValueError("Invalid advertised administrative unit count")
    url = _required(value, "simplifiedGeometryGeoJSON")
    if not trusted_url(url, metadata=False):
        raise ValueError("Untrusted geoBoundaries download URL")
    return {
        "reference_id": f"geoboundaries:{identifier}",
        "source_uri": f"{API_ROOT}/{expected}/{level}/",
        "download_url": url,
        "license": _required(value, "boundaryLicense"),
        "boundary_year": _required(value, "boundaryYearRepresented"),
        "boundary_source": _required(value, "boundarySource"),
        "unit_count": int(count),
    }


def prepare(country: str, level: str, output_dir: Path) -> dict[str, object]:
    if country not in COUNTRIES or level not in {"ADM1", "ADM2"}:
        raise ValueError("Only RU/BY ADM1/ADM2 are supported")
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = _existing_capture(country, level, output_dir)
    if existing is not None:
        return existing
    metadata_url = f"{API_ROOT}/{COUNTRIES[country]}/{level}/"
    raw: object = json.loads(_read_url(metadata_url, MAX_METADATA_BYTES, metadata=True))
    info = inspect_metadata(country, level, raw)
    reference_id = info["reference_id"]
    if not isinstance(reference_id, str):
        raise ValueError("Unexpected source identifier")
    file_name = f"{reference_id.split(':')[-1]}.geojson"
    filename = output_dir / file_name
    manifest_file = output_dir / f"{file_name}.manifest.json"
    review_file = output_dir / f"{file_name}.review.json"
    if any(path.exists() or path.is_symlink() for path in (filename, manifest_file, review_file)):
        raise FileExistsError("Review existing download before running again")
    print(f"{country}/{level}: downloading {file_name}", file=sys.stderr, flush=True)
    contents = _read_url(str(info["download_url"]), MAX_BYTES, metadata=False)
    if contents.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError("Provider returned a Git LFS pointer instead of GeoJSON")
    try:
        with filename.open("xb") as output:
            output.write(contents)
        entries = _features(filename, country, level)
        advertised_count = info["unit_count"]
        if not isinstance(advertised_count, int):
            raise ValueError("Invalid source inventory count")
        inventory_matches = len(entries) == advertised_count
        if not inventory_matches:
            print(
                f"WARNING {country}/{level}: source advertises {advertised_count} units, "
                f"but GeoJSON contains {len(entries)}. Import requires explicit acknowledgement.",
                file=sys.stderr,
                flush=True,
            )
        digest = hashlib.sha256(contents).hexdigest()
        result: dict[str, object] = {
            "schema_version": 1,
            "country": country,
            "level": level,
            "file_name": file_name,
            **info,
            "unit_count": len(entries),
            "advertised_unit_count": advertised_count,
            "inventory_matches_metadata": inventory_matches,
            "sha256": digest,
            "size_bytes": len(contents),
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "review_status": "pending" if inventory_matches else "inventory_mismatch",
        }
        if level == "ADM1":
            seed_path = Path(__file__).resolve().parents[1] / "reference" / "iso3166-2-regions.json"
            seed: object = json.loads(seed_path.read_bytes())
            if not _is_object(seed) or not isinstance(seed.get("regions"), list):
                raise ValueError("Pinned ISO region directory is invalid")
            directory: list[tuple[str, str, str, str]] = []
            for item in seed["regions"]:
                if not _is_object(item):
                    raise ValueError("Invalid pinned ISO subdivision")
                if item.get("country") == country:
                    directory.append(
                        (
                            _required(item, "id"),
                            _required(item, "iso_code"),
                            _required(item, "name"),
                            _required(item, "name_en"),
                        )
                    )
            review: list[dict[str, str | None]] = []
            for shape_id, name, iso, _geometry in entries:
                try:
                    match = choose_region(shape_id, name, iso, {}, directory)
                    issue = "no_exact_match" if match is None else None
                except ValueError:
                    match, issue = None, "conflicting_exact_matches"
                review.append(
                    {
                        "shape_id": shape_id,
                        "shape_name": name,
                        "shape_iso": iso,
                        "exact_match": match,
                        "review_issue": issue,
                    }
                )
            result["unmatched_regions"] = sum(item["exact_match"] is None for item in review)
            with review_file.open("x", encoding="utf-8") as output:
                json.dump(review, output, ensure_ascii=False, indent=2)
                output.write("\n")
        with manifest_file.open("x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        return result
    except BaseException:
        filename.unlink(missing_ok=True)
        manifest_file.unlink(missing_ok=True)
        review_file.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage real ADM1/ADM2 boundaries for review")
    parser.add_argument("--country", choices=sorted(COUNTRIES), required=True)
    parser.add_argument("--level", choices=("ADM1", "ADM2"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.country, args.level, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("reused"):
        print("Existing verified download reused; no network requests were made.")
    if result["review_status"] == "inventory_mismatch":
        print("WARNING: provider inventory differs from GeoJSON; import is blocked by default.")
    print("Review license, territory matches and source vintage before importing into PostGIS.")


if __name__ == "__main__":
    main()
