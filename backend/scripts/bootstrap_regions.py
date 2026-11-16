"""Explicit, offline ISO-code region seed for a migrated PostgreSQL database.

No provider network calls; repeat runs validate existing rows without rewriting them.
"""

import os
from pathlib import Path

import psycopg
from pydantic import BaseModel, ConfigDict, Field


class RegionSeed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    country: str
    iso_code: str
    name: str
    name_en: str


class SeedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source: str
    version: str
    source_uri: str
    license: str
    scope_note: str
    regions: list[RegionSeed] = Field(min_length=1)


def seed_regions(dsn: str, dataset: Path) -> tuple[int, int]:
    """Insert and verify immutable canonical regions and the archived Saturn example."""
    document = SeedDocument.model_validate_json(dataset.read_bytes())
    if (document.source, document.version) != ("iso-codes", "4.18.0"):
        raise ValueError("Unexpected seed source or version")
    if len(document.regions) != 90 or {item.country for item in document.regions} != {"RU", "BY"}:
        raise ValueError("Incomplete pinned first-order seed")
    if len({item.id for item in document.regions}) != len(document.regions):
        raise ValueError("Duplicate canonical region IDs")
    expected = {"RU": 83, "BY": 7}
    if any(
        sum(item.country == country for item in document.regions) != count
        for country, count in expected.items()
    ):
        raise ValueError("Unexpected country coverage")
    if not any(
        item.id == "ru:region:smo" and item.name == "Смоленская область"
        for item in document.regions
    ):
        raise ValueError("Archived Saturn mapping requires the canonical Smolensk region")

    inserted = 0
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            for item in document.regions:
                if item.iso_code != f"{item.country}-{item.id.rsplit(':', 1)[-1].upper()}":
                    raise ValueError("Seed ISO and canonical identity mismatch")
                reference_id = f"iso-codes:{document.version}"
                cursor.execute(
                    """SELECT country_code, iso_3166_2, name, name_en, reference_id,
                              reference_uri, reference_license
                       FROM melliatlas_region WHERE id = %s""",
                    (item.id,),
                )
                row = cursor.fetchone()
                expected_row = (
                    item.country,
                    item.iso_code,
                    item.name,
                    item.name_en,
                    reference_id,
                    document.source_uri,
                    document.license,
                )
                if row is None:
                    cursor.execute(
                        """INSERT INTO melliatlas_region
                           (id, country_code, iso_3166_2, name, name_en,
                            reference_id, reference_uri, reference_license, valid_on)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)""",
                        (item.id, *expected_row),
                    )
                    inserted += 1
                elif tuple(row) != expected_row:
                    raise ValueError(f"Conflicting preexisting region seed: {item.id}")
            cursor.execute(
                "SELECT subject_id, oktmo_code FROM melliatlas_source_saturn WHERE region_id = %s",
                ("ru:region:smo",),
            )
            existing = cursor.fetchone()
            if existing is None:
                cursor.execute(
                    """INSERT INTO melliatlas_source_saturn
                       (region_id, country_code, subject_id, oktmo_code, source_uri, verified_at)
                       VALUES (%s, 'RU', %s, %s, %s, %s::timestamptz)""",
                    (
                        "ru:region:smo",
                        55,
                        "66000000",
                        "https://bee-saturn.ru/backend/beemaster/oktmo-subjects",
                        "2026-11-11T00:00:00Z",
                    ),
                )
            elif tuple(existing) != (55, "66000000"):
                raise ValueError("Existing Smolensk Saturn mapping requires review")
    return inserted, len(document.regions)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed pinned RU/BY ISO region directory")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "reference" / "iso3166-2-regions.json",
    )
    args = parser.parse_args()
    dsn = os.environ.get("MELLIATLAS_DATABASE_URL")
    if not dsn:
        parser.error("MELLIATLAS_DATABASE_URL is required")
    inserted, total = seed_regions(dsn, args.dataset)
    print(
        f"Region seed verified: {total} entries, {inserted} newly inserted; Saturn Smolensk mapping confirmed"
    )


if __name__ == "__main__":
    main()
