"""Review and explicitly approve Smolensk Saturn-to-PostGIS district identities.

By default this command is read-only. A matching label is a proposal, not an
independent verification: the operator must review the printed IDs and approve
one exact capture digest before any row is inserted. Unmatched districts are
never assigned guessed provider identifiers.
"""

import argparse
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeGuard

from melliatlas.sources.providers.saturn.districts import (
    SaturnDistrict,
    district_name_normalizer,
    validate_district_directory,
)
from melliatlas.sources.providers.saturn.http import SATURN_SMOLENSK_DISTRICTS_URL
from melliatlas.territories.api import CountryCode

SMOLENSK_REGION_ID = "ru:region:smo"
SMOLENSK_SUBJECT_ID = 55
SMOLENSK_COUNTRY = CountryCode.RU


@dataclass(frozen=True)
class CanonicalDistrict:
    id: str
    name: str
    name_ru: str | None


@dataclass(frozen=True)
class DistrictMapping:
    district_id: str
    provider_district_code: int
    provider_name: str
    canonical_name: str
    match_method: str


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def parse_overrides(path: Path | None) -> dict[int, str]:
    """Read only explicit source-id-to-canonical-id approvals from a local file."""
    if path is None:
        return {}
    if path.stat().st_size > 16_000:
        raise ValueError("Override file exceeds the review budget")
    raw: object = json.loads(path.read_bytes())
    if not _is_object(raw):
        raise ValueError("Overrides must be a JSON object keyed by Saturn district ID")
    overrides: dict[int, str] = {}
    for key, value in raw.items():
        if not re.fullmatch(r"[1-9][0-9]{0,5}", key) or not isinstance(value, str):
            raise ValueError("Invalid Saturn district override")
        if not value.startswith("ru:district:") or len(value) > 128:
            raise ValueError("Override must identify a canonical RU district")
        overrides[int(key)] = value
    if len(set(overrides.values())) != len(overrides):
        raise ValueError("Two source districts were explicitly mapped to the same canonical ID")
    return overrides


def propose_mappings(
    source: tuple[SaturnDistrict, ...],
    canonical: tuple[CanonicalDistrict, ...],
    overrides: dict[int, str],
) -> tuple[tuple[DistrictMapping, ...], tuple[SaturnDistrict, ...]]:
    """Match only normalized labels or independently reviewed explicit overrides."""
    by_id = {district.id: district for district in canonical}
    if len(by_id) != len(canonical):
        raise ValueError("Duplicate canonical district ID")
    if any(not d.id.startswith("ru:district:") or not d.name.strip() for d in canonical):
        raise ValueError("Invalid canonical district reference")
    known_codes = {district.id for district in source}
    if any(code not in known_codes or target not in by_id for code, target in overrides.items()):
        raise ValueError("Override refers to a missing Saturn or canonical district")

    normalize = district_name_normalizer(SMOLENSK_COUNTRY)
    by_name: dict[str, list[CanonicalDistrict]] = {}
    for district in canonical:
        for label in {district.name, district.name_ru or district.name}:
            by_name.setdefault(normalize(label), []).append(district)

    used: set[str] = set()
    matched: list[DistrictMapping] = []
    unmatched: list[SaturnDistrict] = []
    for item in source:
        explicit_id = overrides.get(item.id)
        method = "operator_override" if explicit_id is not None else "exact_normalized_name"
        if explicit_id is not None:
            target = by_id[explicit_id]
        else:
            # A name shared by multiple canonical rows is never enough to authorize a mapping.
            possible = {
                candidate.id: candidate for candidate in by_name.get(normalize(item.name), [])
            }
            if len(possible) != 1:
                unmatched.append(item)
                continue
            target = next(iter(possible.values()))
        if target.id in used:
            raise ValueError("Two Saturn districts resolve to one canonical district")
        used.add(target.id)
        matched.append(
            DistrictMapping(
                district_id=target.id,
                provider_district_code=item.id,
                provider_name=item.name,
                canonical_name=target.name_ru or target.name,
                match_method=method,
            )
        )
    return tuple(matched), tuple(unmatched)


def _canonical_rows(rows: list[tuple[object, ...]]) -> tuple[CanonicalDistrict, ...]:
    result: list[CanonicalDistrict] = []
    for row in rows:
        if (
            len(row) != 3
            or not isinstance(row[0], str)
            or not isinstance(row[1], str)
            or (row[2] is not None and not isinstance(row[2], str))
        ):
            raise ValueError("Invalid canonical district database row")
        result.append(CanonicalDistrict(row[0], row[1], row[2]))
    return tuple(result)


def run_import(
    dsn: str,
    source: tuple[SaturnDistrict, ...],
    digest: str,
    overrides: dict[int, str],
    *,
    apply: bool,
) -> dict[str, object]:
    """Compare provider identities to one reviewed PostGIS region; write only on approval."""
    import psycopg

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT subject_id FROM melliatlas_source_saturn "
                "WHERE region_id = %s AND country_code = 'RU'",
                (SMOLENSK_REGION_ID,),
            )
            region = cursor.fetchone()
            if region != (SMOLENSK_SUBJECT_ID,):
                raise ValueError(
                    "The database does not contain the reviewed Smolensk subject mapping"
                )
            cursor.execute(
                "SELECT territory_id, name, name_ru FROM melliatlas_admin_geometry "
                "WHERE region_id = %s AND country_code = 'RU' AND kind = 'district' "
                "ORDER BY territory_id",
                (SMOLENSK_REGION_ID,),
            )
            canonical = _canonical_rows(cursor.fetchall())
            if not canonical:
                raise ValueError("Import reviewed Smolensk ADM2 geometry and migration 0006 first")
            matched, unmatched = propose_mappings(source, canonical, overrides)
            if not matched:
                raise ValueError(
                    "No exact district identity matches; review the directory and overrides"
                )
            cursor.execute(
                "SELECT m.district_id, m.provider_district_code FROM "
                "melliatlas_source_saturn_district AS m "
                "JOIN melliatlas_admin_geometry AS g ON g.territory_id = m.district_id "
                "WHERE g.region_id = %s",
                (SMOLENSK_REGION_ID,),
            )
            stored = cursor.fetchall()
            existing: dict[str, int] = {}
            for row in stored:
                if len(row) != 2 or not isinstance(row[0], str) or type(row[1]) is not int:
                    raise ValueError("Invalid stored Saturn district mapping")
                existing[row[0]] = row[1]
            desired = {item.district_id: item.provider_district_code for item in matched}
            if any(
                (district_id in existing and existing[district_id] != code)
                or (code in existing.values() and existing.get(district_id) != code)
                for district_id, code in desired.items()
            ):
                raise ValueError("Captured directory conflicts with an existing reviewed mapping")
            inserted = 0
            if apply:
                approved_at = datetime.now(timezone.utc)
                for mapping in matched:
                    cursor.execute(
                        "INSERT INTO melliatlas_source_saturn_district "
                        "(district_id, provider_district_code, source_uri, verified_at) "
                        "VALUES (%s, %s, %s, %s) ON CONFLICT (district_id) DO NOTHING "
                        "RETURNING district_id",
                        (
                            mapping.district_id,
                            mapping.provider_district_code,
                            SATURN_SMOLENSK_DISTRICTS_URL,
                            approved_at,
                        ),
                    )
                    if cursor.fetchone() is not None:
                        inserted += 1
                    elif mapping.district_id not in existing:
                        raise ValueError(
                            "Concurrent Saturn district mapping change; review and retry"
                        )
    return {
        "subject_id": SMOLENSK_SUBJECT_ID,
        "source_uri": SATURN_SMOLENSK_DISTRICTS_URL,
        "capture_sha256": digest,
        "source_count": len(source),
        "canonical_count": len(canonical),
        "proposed_count": len(matched),
        "unmatched_source": [asdict(item) for item in unmatched],
        "unmatched_canonical": [d.id for d in canonical if d.id not in desired],
        "proposals": [asdict(item) for item in matched],
        "applied": apply,
        "inserted": inserted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--overrides", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approve-sha256")
    args = parser.parse_args()
    if args.apply != (args.approve_sha256 is not None):
        parser.error("--apply requires --approve-sha256; approval is invalid without --apply")
    if not args.file.is_file() or args.file.is_symlink():
        parser.error("Capture must be an existing regular file, not a symlink")
    if args.file.stat().st_size > 64_000:
        parser.error("Captured source file exceeds the district directory limit")
    raw = args.file.read_bytes()
    source = validate_district_directory(raw, country=SMOLENSK_COUNTRY)
    if len(source) < 20:
        parser.error("Smolensk capture is unexpectedly small; review upstream coverage")
    digest = hashlib.sha256(raw).hexdigest()
    if args.apply and args.approve_sha256 != digest:
        parser.error("Approval digest differs from the reviewed capture bytes")
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if not dsn:
        parser.error("MELLIATLAS_DATABASE_URL is required")
    report = run_import(dsn, source, digest, parse_overrides(args.overrides), apply=args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.apply:
        print("Read-only proposal. Review every mapping and unmatched name before applying.")
        print(f"For an approved import, repeat with --apply --approve-sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
