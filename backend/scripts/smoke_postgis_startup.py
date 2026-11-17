"""Apply all SQL migrations and exercise ASGI startup in an isolated test database.

This opt-in integration check never targets the operator's main database.
It does not fetch external source records or perform HTTP provider requests.
"""

import asyncio
import os
from pathlib import Path


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
    print(f"PASS: {len(paths)} migrations and ASGI weather-enabled startup in test database")


if __name__ == "__main__":
    main()
