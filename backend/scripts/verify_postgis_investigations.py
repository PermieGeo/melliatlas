"""Opt-in real PostGIS verification; requires an approved dedicated test database.

Run only after provisioning the test DB, installing an approved psycopg driver,
and setting MELLIATLAS_TEST_POSTGIS_DSN. This script never runs in routine CI.
"""

import os
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from melliatlas.jobs.api import (
    InMemoryInvestigationService,
    InvestigationRequest,
    InvestigationStatus,
    InvestigationStorageError,
)
from melliatlas.persistence.api import PostgisCompletedInvestigationStore
from melliatlas.planning.api import TimeWindow
from melliatlas.sources.api import SYNTHETIC_SCENARIO_ID, SyntheticFixtureProvider
from melliatlas.territories.api import CountryCode


def main() -> None:
    dsn = os.environ.get("MELLIATLAS_TEST_POSTGIS_DSN")
    if not dsn:
        raise SystemExit("MELLIATLAS_TEST_POSTGIS_DSN is required for real PostGIS verification")
    try:
        import psycopg
    except ImportError as error:
        raise SystemExit("Approved psycopg driver must be installed for this check") from error

    def connect():
        return psycopg.connect(dsn)

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
            if row is None or not isinstance(row[0], str) or not row[0].endswith("_test"):
                raise SystemExit("Refusing migration outside a database ending with _test")
            migration = (
                Path(__file__).parents[1] / "migrations" / "0001_completed_investigations.sql"
            ).read_text(encoding="utf-8")
            cursor.execute(migration)

    store = PostgisCompletedInvestigationStore(connect)
    service = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    queued = service.submit(
        InvestigationRequest(
            country=CountryCode.RU,
            territory_id="ru:region:smolensk",
            scenario_id=SYNTHETIC_SCENARIO_ID,
            season=TimeWindow(date(2026, 5, 1), date(2026, 8, 15)),
            starting_point=(32.0, 54.0),
        )
    )
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None and completed.status is InvestigationStatus.COMPLETED
    reopened_service = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    assert reopened_service.get(queued.id) == completed
    assert reopened_service.get(queued.id) == completed
    try:
        store.save(replace(completed, limitations=("Must not overwrite",)))
        raise AssertionError("A duplicate UUID overwrote a completed snapshot")
    except InvestigationStorageError:
        pass
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT ST_SRID(site_points), ST_IsValid(site_points), "
                "ST_NumGeometries(site_points), "
                "ST_DWithin(site_points::geography, "
                "ST_SetSRID(ST_MakePoint(32.0, 54.0), 4326)::geography, 1000) "
                "FROM melliatlas_completed_investigations "
                "WHERE id = %s",
                (queued.id,),
            )
            geometry = cursor.fetchone()
            assert geometry == (4326, True, 3, True)
    bad = replace(
        completed,
        id=completed.id.__class__(int=completed.id.int ^ 1),
        updated_at=completed.created_at - timedelta(days=1),
    )
    try:
        store.save(bad)
        raise AssertionError("Database accepted a completed_at value before created_at")
    except InvestigationStorageError:
        assert store.load(bad.id) is None
    print(
        "PostGIS verification passed: migration, fresh-session reopen, immutability, "
        "rollback, valid SRID 4326 geometry"
    )


if __name__ == "__main__":
    main()
