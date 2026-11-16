"""Import an explicitly captured public Saturn subject directory by exact names.

The input is a previously saved JSON response from /beemaster/oktmo-subjects.
No network access, implicit fuzzy matching, or destructive remapping is performed.
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path

import psycopg

from melliatlas.sources.providers.saturn.subjects import (
    normalized_subject_name,
    validate_subject_directory,
)

SATURN_SUBJECTS_URI = "https://bee-saturn.ru/backend/beemaster/oktmo-subjects"


def import_subjects(dsn: str, source_file: Path, captured_at: datetime) -> tuple[int, int]:
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError("Capture timestamp must include timezone")
    raw = source_file.read_bytes()
    subjects = validate_subject_directory(raw)
    capture_sha256 = hashlib.sha256(raw).hexdigest()
    inserted = 0
    unmatched = 0
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM melliatlas_region WHERE country_code = 'RU'")
            rows = cursor.fetchall()
            name_to_region = {
                normalized_subject_name(str(name)): str(region_id) for region_id, name in rows
            }
            if len(name_to_region) != len(rows):
                raise ValueError("Ambiguous normalized region names")
            for subject in subjects:
                region_id = name_to_region.get(normalized_subject_name(subject.name))
                if region_id is None:
                    unmatched += 1
                    continue
                cursor.execute(
                    "SELECT subject_id, oktmo_code FROM melliatlas_source_saturn WHERE region_id = %s",
                    (region_id,),
                )
                existing = cursor.fetchone()
                if existing is not None:
                    if tuple(existing) != (subject.id, subject.oktmo_code):
                        raise ValueError(f"Conflicting Saturn mapping for {region_id}")
                    continue
                cursor.execute(
                    """INSERT INTO melliatlas_source_saturn
                       (region_id, country_code, subject_id, oktmo_code, source_uri, capture_sha256, verified_at)
                       VALUES (%s, 'RU', %s, %s, %s, %s, %s)""",
                    (
                        region_id,
                        subject.id,
                        subject.oktmo_code,
                        SATURN_SUBJECTS_URI,
                        capture_sha256,
                        captured_at,
                    ),
                )
                inserted += 1
    print(f"Capture SHA-256: {capture_sha256}")
    return inserted, unmatched


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Import captured Saturn subject IDs")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--captured-at", type=datetime.fromisoformat, required=True)
    args = parser.parse_args()
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if not dsn:
        parser.error("MELLIATLAS_DATABASE_URL is required")
    inserted, unmatched = import_subjects(dsn, args.file, args.captured_at)
    print(f"Saturn mappings inserted: {inserted}; unmatched names requiring review: {unmatched}")


if __name__ == "__main__":
    main()
