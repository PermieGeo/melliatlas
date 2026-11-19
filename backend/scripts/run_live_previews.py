#!/usr/bin/env python3
"""Start an explicitly opted-in local API with validated live-source configuration.

This launcher performs read-only database preflight checks. It does not fetch
external provider data, import geography, or approve Saturn district mappings.
"""

import argparse
import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class PreviewReadiness:
    weather_provider: str
    mapped_districts: int


def _database_url() -> str:
    value = os.environ.get("MELLIATLAS_DATABASE_URL", "")
    if not value.strip():
        raise ValueError(
            "Set MELLIATLAS_DATABASE_URL to the initialized local PostGIS database "
            "before enabling live previews"
        )
    return value


def _preflight(dsn: str, region_id: str | None) -> PreviewReadiness:
    """Inspect configured providers and reviewed IDs without external source reads."""
    import psycopg

    from melliatlas.api.composition import compose_weather_reader
    from melliatlas.persistence.postgres import connection_factory
    from melliatlas.persistence.weather.config import read_weather_configuration

    weather = read_weather_configuration(connection_factory(dsn))
    if weather is None:
        raise ValueError(
            "The weather provider row is disabled. Review the provider settings "
            "in PostGIS before enabling the Open-Meteo preview"
        )
    compose_weather_reader(True, weather)

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            if region_id is None:
                cursor.execute("SELECT COUNT(*) FROM melliatlas_source_saturn_district")
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM melliatlas_source_saturn_district AS mapping "
                    "JOIN melliatlas_admin_geometry AS district "
                    "ON district.territory_id = mapping.district_id "
                    "AND district.kind = 'district' "
                    "WHERE district.region_id = %s",
                    (region_id,),
                )
            row = cursor.fetchone()
    if row is None or type(row[0]) is not int:
        raise ValueError("The Saturn district mapping inventory returned an invalid count")
    return PreviewReadiness(weather_provider=weather.provider_id, mapped_districts=row[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region-id",
        help="Report reviewed Saturn mappings for this canonical region (e.g. ru:region:smo)",
    )
    parser.add_argument("--port", type=int, default=8000, help="Local HTTP port (default: 8000)")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Inspect database readiness without starting a server",
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    try:
        dsn = _database_url()
        readiness = _preflight(dsn, args.region_id)
    except ValueError as error:
        print(f"Live preview configuration: {error}", file=sys.stderr)
        print(
            "See docs/INSTALLATION.md for weather migrations 0004/0007 "
            "and the reviewed Saturn district mapping procedure.",
            file=sys.stderr,
        )
        return 2
    except ImportError:
        print(
            "Live preview requires the backend's optional PostgreSQL driver "
            "(install the backend dev dependencies).",
            file=sys.stderr,
        )
        return 2
    except Exception as error:
        # Database driver messages may embed connection credentials; do not print them.
        print(
            f"Live preview database preflight failed ({type(error).__name__}). "
            "Check connectivity and migrations 0004, 0005 and 0007.",
            file=sys.stderr,
        )
        return 2

    print(f"Weather: {readiness.weather_provider} configured for explicit live preview")
    print(
        f"Saturn: {readiness.mapped_districts} reviewed district mappings"
        + (f" in {args.region_id}" if args.region_id else " across all regions")
    )
    if readiness.mapped_districts == 0:
        print(
            "WARNING: Saturn cannot read an unmapped district. Review and approve its "
            "mapping using the operator procedure in docs/INSTALLATION.md.",
            file=sys.stderr,
        )
    if args.check_only:
        return 0

    environment = os.environ.copy()
    environment["MELLIATLAS_SATURN_LIVE_ENABLED"] = "true"
    environment["MELLIATLAS_WEATHER_LIVE_ENABLED"] = "true"
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "melliatlas.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--reload",
    ]
    print("Starting the local API with both live-source flags enabled", flush=True)
    os.execvpe(sys.executable, command, environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
