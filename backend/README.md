# Backend

The backend is a Python/FastAPI modular monolith under active implementation. The first slice provides a runnable HTTP application with typed health and OpenAPI contracts. The current territory slice adds typed RU/BY administrative domain contracts, an offline reference validator, an in-memory catalog, and versioned country/region/district/geometry endpoints.

The territory service deliberately starts **without approved real reference data**. Region reads return `503` until a validated snapshot is injected. Test fixtures are incomplete, fictional catalogs and must never be used to claim coverage of Russian federal subjects or Belarusian oblasts. Complete real regional/district inventories, licensed geometries, spatial topology validation in PostGIS, and database persistence remain open requirements.

## Source layout

- `src/melliatlas/api/` owns HTTP composition and file-deserialization boundaries; see its [contract](src/melliatlas/api/contract.md).
- `src/melliatlas/territories/` owns geographic identity, validation, and the in-memory catalog; see its [contract](src/melliatlas/territories/contract.md).
- `scripts/import_reference.py` performs offline validation of a normalized dataset and independent inventory, reporting coverage counts without storing data.
- `tests/` contains contract, unit and architecture checks, using only clearly marked synthetic geography.

See the [repository overview](../README.md) and [specification index](../docs/specs/README.md) for scope. For setup and testing, see [installation](../docs/INSTALLATION.md) and [tests](../docs/TESTS.md).
