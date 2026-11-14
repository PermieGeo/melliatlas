# Backend

The backend is a Python/FastAPI modular monolith under active implementation. The first slice provides a runnable HTTP application with typed health and OpenAPI contracts. The current territory slice adds typed RU/BY administrative domain contracts, an offline GEOS-backed polygon validator, an in-memory catalog, and versioned country/region/district/geometry endpoints.

A development-only investigation slice adds a fixed offline RU synthetic scenario, a deterministic two-or-more-stop proposal, `POST`/`GET` investigation endpoints, and a per-application in-memory result store. Its background tasks are not durable. It does not supply verified ecological screening, weather, or real site availability. The planned engine and agent remain outside this slice.

The territory service deliberately starts **without approved real reference data**. Region reads return `503` until a validated snapshot is injected. Test fixtures are incomplete, fictional catalogs and must never be used to claim coverage of Russian federal subjects or Belarusian oblasts. Complete real regional/district inventories, licensed geometries, PostGIS persistence and independent spatial integration checks remain open requirements. Shapely/GEOS validates local polygon topology but does not prove that boundaries, CRS labels or administrative coverage are correct.

## Source layout

- `src/melliatlas/api/` owns HTTP composition and file-deserialization boundaries; see its [contract](src/melliatlas/api/contract.md).
- `src/melliatlas/territories/` owns geographic identity, validation, and the in-memory catalog; see its [contract](src/melliatlas/territories/contract.md).
- `src/melliatlas/planning/`, `sources/`, and `jobs/` contain narrow V01 public interfaces and synthetic-only tests; each has a capability contract.
- `scripts/import_reference.py` performs offline validation of a normalized dataset and independent inventory, reporting coverage counts without storing data.
- `tests/` contains contract, unit and architecture checks, using only clearly marked synthetic geography.

See the [repository overview](../README.md) and [specification index](../docs/specs/README.md) for scope. For setup and testing, see [installation](../docs/INSTALLATION.md) and [tests](../docs/TESTS.md).
