"""Apply all SQL migrations and exercise ASGI startup in an isolated test database.

This opt-in integration check never targets the operator's main database.
It does not fetch external source records or perform HTTP provider requests.
"""

import asyncio
import os
from pathlib import Path
from uuid import uuid4


def assert_test_database(name: object) -> None:
    if not isinstance(name, str) or not name.endswith("_test"):
        raise ValueError("Refusing migrations outside a database whose name ends with _test")


def migration_paths(root: Path) -> tuple[Path, ...]:
    """Select every sequential tracked SQL migration without guessing missing versions."""
    paths = tuple(sorted(root.glob("[0-9][0-9][0-9][0-9]_*.sql")))
    versions = [int(path.name[:4]) for path in paths]
    if not versions or versions != list(range(1, len(versions) + 1)):
        raise ValueError("SQL migration numbers must form a complete sequence starting at 0001")
    return paths


async def _exercise_startup() -> None:
    import httpx

    from melliatlas.main import app

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            health = await client.get("/health")
            if health.status_code != 200 or health.json() != {"status": "ok"}:
                raise RuntimeError("Backend health check failed after migrated startup")
            sources = await client.get("/api/v1/sources?country=RU")
            if sources.status_code != 200:
                raise RuntimeError("Source discovery failed after migrated startup")


def exercise_saved_places(dsn: str) -> None:
    """Verify isolated PostGIS create/reopen/update/ownership/delete using synthetic geometry."""
    import psycopg

    from melliatlas.persistence.postgres import connection_factory
    from melliatlas.persistence.saved_places import PostgisSavedPlaceRepository
    from melliatlas.places.api import SavedPlaceConflict, SavedPlaceDraft, SavedPlaceNotFound
    from melliatlas.territories.api import CountryCode

    suffix = uuid4().hex[:16]
    region_id = f"ru:region:probe{suffix}"
    owner = uuid4()
    another_owner = uuid4()
    repository = PostgisSavedPlaceRepository(connection_factory(dsn))
    # A synthetic polygon in the South Pacific avoids collision with reviewed RU/BY geography.
    try:
        with psycopg.connect(dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO melliatlas_region (
                           id, country_code, iso_3166_2, name, name_en,
                           reference_id, reference_uri, reference_license, valid_on
                       ) VALUES (%s, 'RU', %s, 'Synthetic test only', 'Synthetic test only',
                           'SYNTHETIC-TEST-ONLY', 'https://example.invalid/test', 'TEST-ONLY',
                           CURRENT_DATE)""",
                    (region_id, f"RU-PROBE{suffix.upper()}"),
                )
                cursor.execute(
                    """INSERT INTO melliatlas_admin_geometry (
                           territory_id, country_code, kind, region_id, name, external_shape_id,
                           reference_id, reference_uri, reference_license, valid_on, boundary
                       ) VALUES (%s, 'RU', 'region', %s, 'Synthetic test only', %s,
                           'SYNTHETIC-TEST-ONLY', 'https://example.invalid/test', 'TEST-ONLY',
                           CURRENT_DATE, ST_Multi(ST_MakeEnvelope(-170, -80, -169, -79, 4326)))""",
                    (region_id, region_id, f"probe-{suffix}"),
                )
        draft = SavedPlaceDraft(
            name="Synthetic test apiary",
            country=CountryCode.RU,
            region_id=region_id,
            longitude=-169.5,
            latitude=-79.5,
            width_km=15,
            height_km=15,
        )
        saved = repository.create(owner_id=owner, draft=draft)
        if repository.get(owner_id=owner, place_id=saved.id) != saved:
            raise RuntimeError("Saved place did not survive a new database connection")
        if repository.get(owner_id=another_owner, place_id=saved.id) is not None:
            raise RuntimeError("Saved place leaked across owners")
        updated = repository.update(
            owner_id=owner,
            place_id=saved.id,
            expected_revision=saved.revision,
            draft=SavedPlaceDraft(
                name="Renamed synthetic apiary",
                country=draft.country,
                region_id=draft.region_id,
                longitude=draft.longitude,
                latitude=draft.latitude,
                width_km=draft.width_km,
                height_km=draft.height_km,
            ),
        )
        if updated.revision != 2 or len(repository.list(owner_id=owner)) != 1:
            raise RuntimeError("Saved place revision or owner-scoped list is invalid")
        try:
            repository.delete(owner_id=owner, place_id=saved.id, expected_revision=1)
        except SavedPlaceConflict:
            pass
        else:
            raise RuntimeError("Stale saved-place revision unexpectedly deleted a row")
        try:
            repository.delete(owner_id=another_owner, place_id=saved.id, expected_revision=2)
        except SavedPlaceNotFound:
            pass
        else:
            raise RuntimeError("Another owner unexpectedly deleted a saved place")
        repository.delete(owner_id=owner, place_id=saved.id, expected_revision=2)
        if repository.get(owner_id=owner, place_id=saved.id) is not None:
            raise RuntimeError("Deleted saved place remains readable")
    finally:
        with psycopg.connect(dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM melliatlas_saved_place WHERE owner_id = %s", (owner,))
                cursor.execute(
                    "DELETE FROM melliatlas_admin_geometry WHERE territory_id = %s", (region_id,)
                )
                cursor.execute("DELETE FROM melliatlas_region WHERE id = %s", (region_id,))


def main() -> None:
    dsn = os.environ.get("MELLIATLAS_TEST_POSTGIS_DSN")
    if not dsn:
        raise SystemExit("MELLIATLAS_TEST_POSTGIS_DSN is required")

    import psycopg

    paths = migration_paths(Path(__file__).resolve().parents[1] / "migrations")
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
            assert_test_database(row[0] if row is not None else None)
            for path in paths:
                cursor.execute(path.read_text(encoding="utf-8"))
            cursor.execute("SELECT PostGIS_Version()")
            if cursor.fetchone() is None:
                raise RuntimeError("PostGIS extension is not available")
    # Exercise the real entrypoint and DB-managed Open-Meteo configuration, without live HTTP.
    os.environ["MELLIATLAS_DATABASE_URL"] = dsn
    os.environ["MELLIATLAS_WEATHER_LIVE_ENABLED"] = "true"
    os.environ["MELLIATLAS_SATURN_LIVE_ENABLED"] = "false"
    os.environ["MELLIATLAS_SOURCE_PROVIDER"] = "disabled"
    os.environ.pop("MELLIATLAS_REFERENCE_SNAPSHOT", None)
    os.environ.pop("MELLIATLAS_REFERENCE_INVENTORY", None)
    asyncio.run(_exercise_startup())
    exercise_saved_places(dsn)
    print(
        f"PASS: {len(paths)} migrations, ASGI startup and private saved-place CRUD in test database"
    )


if __name__ == "__main__":
    main()
