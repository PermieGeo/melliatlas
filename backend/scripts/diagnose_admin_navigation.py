"""Compare saved administrative districts with the running local territory API."""

import argparse
import json
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import TypeAlias
from urllib.parse import quote
from urllib.request import Request, urlopen

RegionRow: TypeAlias = tuple[str, str, int]


@dataclass(frozen=True)
class NavigationIssue:
    region_id: str
    database_count: int
    api_count: int | None
    reason: str


@dataclass(frozen=True)
class NavigationAudit:
    country: str
    regions_checked: int
    database_districts: int
    api_districts: int
    empty_regions: tuple[str, ...]
    issues: tuple[NavigationIssue, ...]


def database_regions(dsn: str, country: str) -> tuple[RegionRow, ...]:
    """Read region/district counts without changing PostGIS contents."""
    import psycopg

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT r.id, r.name, COUNT(d.territory_id)
                   FROM melliatlas_region AS r
                   LEFT JOIN melliatlas_admin_geometry AS d
                     ON d.region_id = r.id AND d.kind = 'district'
                   WHERE r.country_code = %s
                   GROUP BY r.id, r.name ORDER BY r.name, r.id""",
                (country,),
            )
            return tuple((str(row[0]), str(row[1]), int(row[2])) for row in cursor.fetchall())


def local_api_read(path: str) -> object:
    request = Request(f"http://127.0.0.1:8000{path}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def audit_regions(
    country: str,
    regions: Sequence[RegionRow],
    fetch: Callable[[str], object],
    region_id: str | None = None,
) -> NavigationAudit:
    """Validate API identity and compare counts for every selected region."""
    if not regions:
        raise ValueError(f"No seeded regions for {country}")
    expected = {row[0] for row in regions}
    api_regions = fetch(f"/api/v1/territories/regions?country={country}")
    if not isinstance(api_regions, list) or any(
        not isinstance(item, dict)
        or item.get("country") != country
        or item.get("kind") != "region"
        or not isinstance(item.get("id"), str)
        for item in api_regions
    ):
        raise ValueError("API returned an invalid region catalog")
    api_ids = [item["id"] for item in api_regions]
    if len(set(api_ids)) != len(api_ids) or set(api_ids) != expected:
        raise ValueError("API region IDs differ from the seeded database directory")

    if region_id is not None:
        regions = tuple(row for row in regions if row[0] == region_id)
        if not regions:
            raise ValueError("Selected region ID is not part of the country directory")

    issues: list[NavigationIssue] = []
    empty: list[str] = []
    sql_total = 0
    api_total = 0
    for index, (identifier, name, database_count) in enumerate(regions, start=1):
        print(f"[{index}/{len(regions)}] {name} ({identifier})", flush=True)
        sql_total += database_count
        if database_count == 0:
            empty.append(f"{identifier} ({name})")
        try:
            payload = fetch(f"/api/v1/territories/districts?region_id={quote(identifier, safe='')}")
            if not isinstance(payload, list) or any(
                not isinstance(item, dict)
                or item.get("country") != country
                or item.get("kind") != "district"
                or item.get("parent_id") != identifier
                or not isinstance(item.get("id"), str)
                for item in payload
            ):
                raise ValueError("Invalid district response or parent identity")
            district_ids = [item["id"] for item in payload]
            if len(set(district_ids)) != len(district_ids):
                raise ValueError("Duplicate district IDs from API")
            api_count = len(payload)
            api_total += api_count
            if api_count != database_count:
                issues.append(
                    NavigationIssue(identifier, database_count, api_count, "count mismatch")
                )
        except (OSError, ValueError) as exc:
            issues.append(NavigationIssue(identifier, database_count, None, str(exc)))
    return NavigationAudit(country, len(regions), sql_total, api_total, tuple(empty), tuple(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", required=True, choices=("RU", "BY"))
    parser.add_argument("--region-id", help="Inspect only this canonical region ID")
    args = parser.parse_args()
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if not dsn:
        parser.error("MELLIATLAS_DATABASE_URL must point to the imported PostGIS database")
    rows = database_regions(dsn, args.country)
    try:
        result = audit_regions(args.country, rows, local_api_read, args.region_id)
    except (OSError, ValueError) as exc:
        print(f"Navigation diagnosis failed: {exc}")
        return 1
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 2 if result.issues or result.database_districts == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
