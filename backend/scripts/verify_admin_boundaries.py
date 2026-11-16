"""Read-only PostGIS inventory verification against reviewed boundary manifests."""

import argparse
import json
import os
import re
from pathlib import Path
from typing import TypeGuard

EXPECTED_REGIONS = {"RU": 83, "BY": 7}


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def manifest_summary(path: Path, country: str, level: str) -> tuple[str, int]:
    document: object = json.loads(path.read_bytes())
    if not _is_object(document):
        raise ValueError("Invalid boundary manifest")
    count = document.get("unit_count")
    reference_id = document.get("reference_id")
    if (
        document.get("schema_version") != 1
        or document.get("country") != country
        or document.get("level") != level
        or type(count) is not int
        or not 1 <= count <= 5000
        or not isinstance(reference_id, str)
        or not re.fullmatch(
            rf"geoboundaries:{'RUS' if country == 'RU' else 'BLR'}-{level}-[0-9]+",
            reference_id,
        )
    ):
        raise ValueError("Boundary manifest does not match the requested country and level")
    return reference_id, count


def verify(
    dsn: str, country: str, adm1_manifest: Path, adm2_manifest: Path
) -> dict[str, int | str | bool]:
    if country not in EXPECTED_REGIONS:
        raise ValueError("Unsupported country")
    first_id, first_count = manifest_summary(adm1_manifest, country, "ADM1")
    second_id, second_count = manifest_summary(adm2_manifest, country, "ADM2")

    import psycopg

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM melliatlas_region WHERE country_code = %s", (country,)
            )
            regions_row = cursor.fetchone()
            cursor.execute(
                """SELECT kind, reference_id, count(*) FROM melliatlas_admin_geometry
                   WHERE country_code = %s GROUP BY kind, reference_id""",
                (country,),
            )
            boundary_rows = cursor.fetchall()
            cursor.execute(
                """SELECT count(*) FROM melliatlas_admin_geometry
                   WHERE country_code = %s AND
                   (NOT ST_IsValid(boundary) OR ST_SRID(boundary) <> 4326
                    OR ST_IsEmpty(boundary))""",
                (country,),
            )
            invalid_row = cursor.fetchone()
            cursor.execute(
                """SELECT count(*) FROM melliatlas_admin_geometry AS d
                   LEFT JOIN melliatlas_admin_geometry AS r
                     ON r.territory_id = d.region_id AND r.kind = 'region'
                   WHERE d.country_code = %s AND d.kind = 'district'
                     AND (r.territory_id IS NULL OR NOT ST_Covers(
                       r.boundary, ST_PointOnSurface(d.boundary)))""",
                (country,),
            )
            detached_row = cursor.fetchone()
    if regions_row is None or invalid_row is None or detached_row is None:
        raise ValueError("PostGIS inventory did not return a valid count")
    totals = {(kind, reference): count for kind, reference, count in boundary_rows}
    actual_first = int(totals.get(("region", first_id), 0))
    actual_second = int(totals.get(("district", second_id), 0))
    other = sum(
        count
        for (kind, reference), count in totals.items()
        if (kind, reference) not in {("region", first_id), ("district", second_id)}
    )
    passed = (
        regions_row[0] == EXPECTED_REGIONS[country]
        and actual_first == first_count
        and actual_second == second_count
        and other == 0
        and invalid_row[0] == 0
        and detached_row[0] == 0
    )
    return {
        "country": country,
        "seed_regions": int(regions_row[0]),
        "adm1_from_manifest": actual_first,
        "adm1_expected": first_count,
        "adm2_from_manifest": actual_second,
        "adm2_expected": second_count,
        "other_geometry_rows": other,
        "invalid_geometry_rows": int(invalid_row[0]),
        "detached_district_rows": int(detached_row[0]),
        "complete_for_source_snapshot": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare imported PostGIS boundaries to manifests")
    parser.add_argument("--country", choices=sorted(EXPECTED_REGIONS), required=True)
    parser.add_argument("--adm1-manifest", type=Path, required=True)
    parser.add_argument("--adm2-manifest", type=Path, required=True)
    args = parser.parse_args()
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if not dsn:
        parser.error("MELLIATLAS_DATABASE_URL is required")
    report = verify(dsn, args.country, args.adm1_manifest, args.adm2_manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["complete_for_source_snapshot"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
