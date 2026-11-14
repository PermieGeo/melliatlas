# Backend

The Python backend is being implemented incrementally. Step 1 provides a runnable FastAPI application factory and a typed health/OpenAPI contract; territory catalogs, sources, analysis, persistence and investigations are not yet implemented.

## Source layout

`src/melliatlas/api/` owns the implemented HTTP app composition and its [contract](src/melliatlas/api/contract.md). Other directories remain reserved for subsequent capabilities. `tests/contract/` and `tests/architecture/` contain the initial executable checks.

See the [repository overview](../README.md) and [specification index](../docs/specs/README.md) for the current scope. For verified installation and test commands, see [installation](../docs/INSTALLATION.md) and [tests](../docs/TESTS.md).
