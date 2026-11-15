# Backend

The backend is a Python/FastAPI modular monolith under active implementation. The first slice provides a runnable HTTP application with typed health and OpenAPI contracts. The current territory slice adds typed RU/BY administrative domain contracts, an offline GEOS-backed polygon validator, an in-memory catalog, and versioned country/region/district/geometry endpoints.

A development-only investigation slice adds a fixed offline RU synthetic scenario, a deterministic two-or-more-stop proposal, and `POST`/`GET` investigation endpoints. The default store is per-application memory. An opt-in PostGIS adapter can durably save completed snapshots after migration and explicit injection; no PostgreSQL driver, DB connection or persistence is configured by default. In-flight background tasks are not durable. It does not supply verified ecological screening, weather, or real site availability. The planned engine and agent remain outside this slice.

The territory service deliberately starts **without approved real reference data**. Region reads return `503` until a validated snapshot is injected or explicitly loaded at ASGI startup. Test fixtures are incomplete, fictional catalogs and must never be used to claim coverage of Russian federal subjects or Belarusian oblasts. Complete real regional/district inventories, licensed geometries, PostGIS persistence and independent spatial integration checks remain open requirements. Shapely/GEOS validates local polygon topology but does not prove that boundaries, CRS labels or administrative coverage are correct.

## Source layout

- `src/melliatlas/api/` owns HTTP composition and file-deserialization boundaries; see its [contract](src/melliatlas/api/contract.md).
- `src/melliatlas/territories/` owns geographic identity, validation, and the in-memory catalog; see its [contract](src/melliatlas/territories/contract.md).
- `src/melliatlas/planning/`, `sources/`, and `jobs/` contain narrow public interfaces and synthetic-only tests; each has a capability contract.
- `src/melliatlas/analyzers/` contains a pure fictional ecology point-in-polygon check (`find_ecology_overlaps`); `planning` owns the separate demo eligibility policy. Neither is wired into investigations or validated against real restrictions.
- `src/melliatlas/persistence/` implements optional PostGIS completed-result persistence. The SQL migration is in `migrations/`; driver approval and real PostGIS testing remain required. See its [contract](src/melliatlas/persistence/contract.md).
- `scripts/import_reference.py` performs offline validation of a normalized dataset and independent inventory, reporting coverage counts without storing data. Optional `MELLIATLAS_REFERENCE_SNAPSHOT` and `MELLIATLAS_REFERENCE_INVENTORY` paths load the same normalized documents at ASGI startup, validate them before serving, and populate an isolated in-memory territory catalog. This is not PostGIS import or proof of approved real-world coverage.
- `tests/` contains contract, unit and architecture checks, using only clearly marked synthetic geography.

See the [repository overview](../README.md) and [specification index](../docs/specs/README.md) for scope. For setup and testing, see [installation](../docs/INSTALLATION.md) and [tests](../docs/TESTS.md).
