"""Explicit offline PostGIS import of reviewed ADM1/ADM2 GeoJSON boundaries.

Never resolves provider identifiers or downloads external files during application startup.
The source license, validity year and any ambiguous unit matches require operator review.
"""

import argparse
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import TypeGuard

MAX_BYTES = 150 * 1024 * 1024
MAX_FEATURES = 5000
ISO_COUNTRIES = {"RU": "RUS", "BY": "BLR"}


def _load_json(path: Path) -> object:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Reference file exceeds the review limit")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _object(value: object) -> dict[str, object]:
    if not _is_object(value):
        raise ValueError("Expected a JSON object")
    return value


def _value(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing {label}")
    return value.strip()


def _features(path: Path, country: str, level: str) -> list[tuple[str, str, str | None, str]]:
    document = _object(_load_json(path))
    if document.get("type") != "FeatureCollection" or not _is_list(document.get("features")):
        raise ValueError("Expected a GeoJSON FeatureCollection")
    features = document["features"]
    if not features or len(features) > MAX_FEATURES:
        raise ValueError("Unexpected feature count")
    result: list[tuple[str, str, str | None, str]] = []
    ids: set[str] = set()
    for raw in features:
        feature = _object(raw)
        if feature.get("type") != "Feature":
            raise ValueError("Unexpected GeoJSON feature")
        properties = _object(feature.get("properties"))
        shape_id = _value(properties.get("shapeID"), "shapeID")
        name = _value(properties.get("shapeName"), "shapeName")
        if shape_id in ids or not re.fullmatch(r"[A-Za-z0-9-]{1,96}", shape_id):
            raise ValueError("Duplicate or unsupported shapeID")
        ids.add(shape_id)
        group = _value(properties.get("shapeGroup"), "shapeGroup")
        if group != ISO_COUNTRIES[country]:
            raise ValueError("Country mismatch in reference geometry")
        shape_type = _value(properties.get("shapeType"), "shapeType").replace(" ", "")
        if shape_type != level:
            raise ValueError("Administrative level mismatch")
        geometry = _object(feature.get("geometry"))
        if geometry.get("type") not in ("Polygon", "MultiPolygon") or not isinstance(
            geometry.get("coordinates"), list
        ):
            raise ValueError("Boundary must be a Polygon or MultiPolygon")
        shape_iso = properties.get("shapeISO")
        iso = (
            shape_iso.strip().upper() if isinstance(shape_iso, str) and shape_iso.strip() else None
        )
        result.append(
            (shape_id, name, iso, json.dumps(geometry, ensure_ascii=False, allow_nan=False))
        )
    return result


def _mapping(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    content = _object(_load_json(path))
    mapping: dict[str, str] = {}
    for key, value in content.items():
        if not isinstance(value, str) or not key.strip() or not value.strip():
            raise ValueError("Invalid reviewed mapping")
        mapping[key] = value
    return mapping


def choose_region(
    shape_id: str,
    name: str,
    iso: str | None,
    mapping: dict[str, str],
    directory: list[tuple[str, str, str, str]],
) -> str | None:
    explicit = mapping.get(shape_id)
    candidates = {
        identifier
        for identifier, iso_code, name_ru, name_en in directory
        if (iso is not None and iso == iso_code)
        or name.casefold() in (name_ru.casefold(), name_en.casefold())
    }
    if explicit is not None:
        if explicit not in {row[0] for row in directory}:
            raise ValueError("Reviewed mapping refers to an unknown region")
        if candidates and candidates != {explicit}:
            raise ValueError("Reviewed mapping conflicts with source identity")
        return explicit
    if len(candidates) > 1:
        raise ValueError("Ambiguous region identity; review source mapping")
    return next(iter(candidates), None)


def import_boundaries(
    dsn: str,
    path: Path,
    country: str,
    level: str,
    reference_id: str,
    reference_uri: str,
    license_id: str,
    valid_on: date,
    mapping_path: Path | None = None,
    allow_partial: bool = False,
) -> tuple[int, int, int]:
    if country not in ISO_COUNTRIES or level not in ("ADM1", "ADM2"):
        raise ValueError("Only RU/BY ADM1/ADM2 are supported")
    if not reference_id or not reference_uri.startswith("https://") or not license_id:
        raise ValueError("Source version, HTTPS provenance and license are required")
    features = _features(path, country, level)
    mapping = _mapping(mapping_path)
    used: set[str] = set()
    matched = 0
    skipped = 0
    import psycopg

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, iso_3166_2, name, name_en FROM melliatlas_region "
                "WHERE country_code = %s",
                (country,),
            )
            directory = [(r[0], r[1], r[2], r[3]) for r in cursor.fetchall()]
            if not directory:
                raise ValueError("Seed the independent region directory first")
            for shape_id, name, iso, geometry in features:
                region_id: str | None
                if level == "ADM1":
                    region_id = choose_region(shape_id, name, iso, mapping, directory)
                else:
                    cursor.execute(
                        """WITH candidate AS (
                               SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
                           )
                           SELECT region.territory_id FROM melliatlas_admin_geometry AS region
                           CROSS JOIN candidate
                           WHERE region.country_code = %s AND region.kind = 'region'
                             AND ST_Covers(region.boundary, ST_PointOnSurface(candidate.geom))
                             AND ST_Area(ST_Intersection(region.boundary, candidate.geom))
                                 >= 0.95 * ST_Area(candidate.geom)""",
                        (geometry, country),
                    )
                    candidates = [row[0] for row in cursor.fetchall()]
                    if len(candidates) > 1:
                        raise ValueError("District overlaps multiple reviewed parent regions")
                    region_id = candidates[0] if candidates else None
                if region_id is None:
                    if not allow_partial:
                        raise ValueError(
                            f"Unmatched {level} administrative unit: {shape_id} ({name})"
                        )
                    skipped += 1
                    continue
                if region_id in used and level == "ADM1":
                    raise ValueError("Two boundaries map to the same region")
                used.add(region_id)
                territory_id = (
                    region_id
                    if level == "ADM1"
                    else f"{country.lower()}:district:{shape_id.lower()}"
                )
                cursor.execute(
                    """INSERT INTO melliatlas_admin_geometry
                       (territory_id, country_code, kind, region_id, name, external_shape_id,
                        reference_id, reference_uri, reference_license, valid_on, boundary)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                               ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)))
                       ON CONFLICT (territory_id) DO NOTHING RETURNING territory_id""",
                    (
                        territory_id,
                        country,
                        "region" if level == "ADM1" else "district",
                        region_id,
                        name,
                        shape_id,
                        reference_id,
                        reference_uri,
                        license_id,
                        valid_on,
                        geometry,
                    ),
                )
                if cursor.fetchone() is not None:
                    matched += 1
                else:
                    cursor.execute(
                        """SELECT external_shape_id, reference_id, name, region_id,
                                  reference_uri, reference_license, valid_on,
                                  ST_Equals(boundary,
                                      ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)))
                           FROM melliatlas_admin_geometry WHERE territory_id = %s""",
                        (geometry, territory_id),
                    )
                    existing = cursor.fetchone()
                    if existing != (
                        shape_id,
                        reference_id,
                        name,
                        region_id,
                        reference_uri,
                        license_id,
                        valid_on,
                        True,
                    ):
                        raise ValueError("Existing boundary differs from the reviewed import")
    return matched, len(features), skipped


def manifest_provenance(
    manifest_path: Path, path: Path, country: str, level: str
) -> tuple[str, str, str]:
    """Bind imported file bytes and provenance to the reviewed download manifest."""
    metadata = _object(_load_json(manifest_path))
    if (
        metadata.get("schema_version") != 1
        or metadata.get("country") != country
        or metadata.get("level") != level
        or metadata.get("file_name") != path.name
    ):
        raise ValueError("Manifest identity does not match the requested import")
    expected_digest = _value(metadata.get("sha256"), "sha256")
    if not re.fullmatch(r"[a-f0-9]{64}", expected_digest):
        raise ValueError("Invalid downloaded dataset digest")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Reference file exceeds the review limit")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_digest:
        raise ValueError("Boundary GeoJSON has changed since the reviewed download")
    reference_id = _value(metadata.get("reference_id"), "reference_id")
    reference_uri = _value(metadata.get("source_uri"), "source_uri")
    license_id = _value(metadata.get("license"), "license")
    expected_country = ISO_COUNTRIES[country]
    expected_url = f"https://www.geoboundaries.org/api/current/gbOpen/{expected_country}/{level}/"
    if (
        reference_uri != expected_url
        or not re.fullmatch(rf"geoboundaries:{expected_country}-{level}-[0-9]+", reference_id)
        or metadata.get("unit_count") != len(_features(path, country, level))
    ):
        raise ValueError("Unexpected boundary manifest source or inventory")
    return reference_id, reference_uri, license_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import reviewed country administrative GeoJSON to PostGIS"
    )
    parser.add_argument("--country", choices=sorted(ISO_COUNTRIES), required=True)
    parser.add_argument("--level", choices=("ADM1", "ADM2"), required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--reference-id")
    parser.add_argument("--source-uri")
    parser.add_argument("--license")
    parser.add_argument("--valid-on", type=date.fromisoformat, required=True)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    if args.manifest is not None:
        if any((args.reference_id, args.source_uri, args.license)):
            parser.error("Use either --manifest or explicit provenance fields")
        provenance = manifest_provenance(args.manifest, args.file, args.country, args.level)
    else:
        if not all((args.reference_id, args.source_uri, args.license)):
            parser.error("Provide --manifest or all three provenance fields")
        provenance = (args.reference_id, args.source_uri, args.license)
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if not dsn:
        parser.error("MELLIATLAS_DATABASE_URL is required")
    inserted, total, skipped = import_boundaries(
        dsn,
        args.file,
        args.country,
        args.level,
        provenance[0],
        provenance[1],
        provenance[2],
        args.valid_on,
        args.mapping,
        args.allow_partial,
    )
    print(f"{args.country}/{args.level}: {inserted} inserted; {total} seen; {skipped} unmatched")


if __name__ == "__main__":
    main()
