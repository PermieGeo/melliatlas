"""Opt-in V02 verification against an explicitly approved PostgreSQL/PostGIS test DB.

This script applies the reviewed migration and temporarily writes synthetic records.
It requires MELLIATLAS_TEST_POSTGIS_DSN and an approved psycopg installation.
Routine project checks never connect to PostgreSQL.
"""

import asyncio
import json
import os
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import httpx

from melliatlas.api.app import create_app
from melliatlas.jobs import (
    InMemoryInvestigationService,
    InvestigationOutcomeKind,
    InvestigationRequest,
    InvestigationSnapshot,
    InvestigationStatus,
    InvestigationStorageError,
)
from melliatlas.persistence.api import PostgisCompletedInvestigationStore
from melliatlas.planning import TimeWindow
from melliatlas.sources.providers.synthetic.api import (
    SYNTHETIC_SCENARIO_ID,
    SyntheticFixtureProvider,
)
from melliatlas.territories.api import CountryCode


def _assert_test_database(database_name: object) -> None:
    if not isinstance(database_name, str) or not database_name.endswith("_test"):
        raise SystemExit("Refusing migration outside a database ending with _test")


def _complete(
    store: PostgisCompletedInvestigationStore,
    season: TimeWindow,
    created_ids: list[UUID],
) -> InvestigationSnapshot:
    service = InMemoryInvestigationService(SyntheticFixtureProvider(), store)
    queued = service.submit(
        InvestigationRequest(
            country=CountryCode.RU,
            territory_id="ru:region:smolensk",
            scenario_id=SYNTHETIC_SCENARIO_ID,
            season=season,
            starting_point=(32.0, 54.0),
        )
    )
    created_ids.append(queued.id)
    service.process(queued.id)
    completed = service.get(queued.id)
    assert completed is not None
    assert completed.status is InvestigationStatus.COMPLETED, completed.diagnostics
    assert completed.outcome is not None
    return completed


async def _check_fresh_http_read(
    store: PostgisCompletedInvestigationStore,
    completed: InvestigationSnapshot,
) -> None:
    app = create_app(investigations=InMemoryInvestigationService(SyntheticFixtureProvider(), store))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get(f"/api/v1/investigations/{completed.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == str(completed.id)
    assert data["status"] == "COMPLETED"
    assert data["outcome"] == completed.outcome.value
    assert data["reference_version"] == completed.reference_version
    assert data["decision_trace"] == list(completed.decision_trace)
    assert [item["id"] for item in data["evidence"]] == [item.id for item in completed.evidence]
    if completed.plan is not None:
        assert [item["site_id"] for item in data["plan"]["stops"]] == [
            item.site_id for item in completed.plan.stops
        ]
    else:
        assert data["plan"] is None


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

    migration = (
        Path(__file__).parents[1] / "migrations" / "0001_completed_investigations.sql"
    ).read_text(encoding="utf-8")

    # Verify the actual database name before executing any schema-changing SQL.
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
            _assert_test_database(row[0] if row is not None else None)
            cursor.execute(migration)
            cursor.execute(migration)
            cursor.execute("SELECT postgis_version()")
            assert cursor.fetchone() is not None
            cursor.execute(
                "SELECT indexdef FROM pg_indexes "
                "WHERE schemaname = current_schema() "
                "AND tablename = 'melliatlas_completed_investigations' "
                "AND indexname = 'melliatlas_completed_investigations_site_points_gist'"
            )
            index = cursor.fetchone()
            assert index is not None and "using gist" in index[0].lower()
            cursor.execute(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid = 'melliatlas_completed_investigations'::regclass"
            )
            constraints = {item[0] for item in cursor.fetchall()}
            assert {
                "completed_investigation_status",
                "completed_investigation_id",
                "completed_investigation_timestamps",
                "completed_investigation_site_points_valid",
            }.issubset(constraints)

    store = PostgisCompletedInvestigationStore(connect)
    created_ids: list[UUID] = []
    try:
        complete = _complete(store, TimeWindow(date(2026, 5, 1), date(2026, 8, 15)), created_ids)
        assert complete.outcome is InvestigationOutcomeKind.PLAN_FOUND
        assert complete.plan is not None and len(complete.plan.stops) == 3
        assert (
            InMemoryInvestigationService(SyntheticFixtureProvider(), store).get(complete.id)
            == complete
        )
        asyncio.run(_check_fresh_http_read(store, complete))

        with psycopg.connect(dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT payload::text, reference_version, created_at, completed_at, "
                    "ST_SRID(site_points), ST_IsValid(site_points), "
                    "ST_NumGeometries(site_points), ST_AsGeoJSON(site_points), "
                    "ST_DWithin(site_points::geography, "
                    "ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, 1000) "
                    "FROM melliatlas_completed_investigations WHERE id = %s",
                    (
                        complete.plan.stops[0].longitude,
                        complete.plan.stops[0].latitude,
                        complete.id,
                    ),
                )
                row = cursor.fetchone()
                assert row is not None
                original_payload = row[0]
                assert json.loads(original_payload)["id"] == str(complete.id)
                assert row[1:7] == (
                    complete.reference_version,
                    complete.created_at,
                    complete.updated_at,
                    4326,
                    True,
                    len(complete.plan.stops),
                )
                geometry = json.loads(row[7])
                assert geometry["type"] == "MultiPoint"
                assert geometry["coordinates"] == [
                    [stop.longitude, stop.latitude] for stop in complete.plan.stops
                ]
                assert row[8] is True

        try:
            store.save(replace(complete, limitations=("Different historical result",)))
        except InvestigationStorageError:
            pass
        else:
            raise AssertionError("Duplicate UUID did not fail")
        with psycopg.connect(dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT payload::text FROM melliatlas_completed_investigations WHERE id = %s",
                    (complete.id,),
                )
                row = cursor.fetchone()
                assert row is not None and row[0] == original_payload

        without_plan = _complete(
            store, TimeWindow(date(2026, 5, 1), date(2026, 5, 20)), created_ids
        )
        assert without_plan.outcome is InvestigationOutcomeKind.INSUFFICIENT_EVIDENCE
        assert without_plan.plan is None
        assert (
            InMemoryInvestigationService(SyntheticFixtureProvider(), store).get(without_plan.id)
            == without_plan
        )
        asyncio.run(_check_fresh_http_read(store, without_plan))
        with psycopg.connect(dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT site_points IS NULL FROM melliatlas_completed_investigations "
                    "WHERE id = %s",
                    (without_plan.id,),
                )
                assert cursor.fetchone() == (True,)

        invalid_id = uuid4()
        created_ids.append(invalid_id)
        invalid = replace(
            complete,
            id=invalid_id,
            updated_at=complete.created_at - timedelta(days=1),
        )
        try:
            store.save(invalid)
        except InvestigationStorageError:
            assert store.load(invalid_id) is None
        else:
            raise AssertionError("Database accepted completed_at earlier than created_at")
        repaired = replace(complete, id=invalid_id)
        store.save(repaired)
        assert store.load(invalid_id) == repaired
    finally:
        # Remove only the fresh UUIDs created by this verification run.
        if created_ids:
            with psycopg.connect(dsn) as connection:
                with connection.cursor() as cursor:
                    for identifier in created_ids:
                        cursor.execute(
                            "DELETE FROM melliatlas_completed_investigations WHERE id = %s",
                            (identifier,),
                        )

    print(
        "PostGIS V02 verification passed: repeatable migration, constraints, GiST, "
        "JSONB and HTTP reopen, SRID-4326 geometry, metric distance, immutable UUID, "
        "insufficient-evidence result, rollback, retry and test-record cleanup"
    )


if __name__ == "__main__":
    main()
