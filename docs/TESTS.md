# Test Commands

Install the backend development dependencies described in [INSTALLATION.md](INSTALLATION.md) before running the full project checks.

Run all configured checks from the repository root:

```bash
bash ./run-tests.sh
```

The runner performs specification/documentation tests, backend pytest, Ruff lint/format checks, and strict Pyright when `backend/pyproject.toml` is present. It fails if required tools are missing; it does not silently skip enabled checks.

For focused initial backend checks:

```bash
python -m pytest -p no:cacheprovider backend/tests/contract backend/tests/architecture
python -m ruff check --no-cache backend
python -m ruff format --check backend
python -m pyright --project backend
```

Current tests cover FastAPI health/OpenAPI, versioned territory endpoints, the synthetic V01 investigation POST/GET path with successful and insufficient-evidence results, rejected malformed and unsupported requests, independent fixture determinism, process-local store isolation and network-free execution, offline territory-reference validation, independent inventory comparisons, WGS84 coordinate checks and Shapely/GEOS polygon topology, idempotent in-memory loading, and architecture import boundaries. These tests use synthetic administrative snapshots; **they do not establish complete real RU/BY coverage or PostGIS topology correctness**. No approved full reference, real provider adapter, PostGIS import, full engine/agent, or browser acceptance test exists yet. V01 tests establish only the provisional, non-durable synthetic backend slice.

To validate externally obtained normalized reference files after verifying permission, provenance, and independent inventories, run from an installed backend environment:

```bash
python backend/scripts/import_reference.py path/to/reference.json path/to/independent-inventory.json
```

This command only validates the local input and prints a report; it does not import into PostGIS or mark a reference approved.

## Architecture import policy

The backend architecture suite validates a fixed, approved capability dependency matrix,
public `api.py` boundaries or explicit `__all__` facades, relative and absolute imports,
and forbidden framework, database, and outbound-client imports. Deliberately invalid import
fixtures verify that the gate detects these violations; permitted imports are tested too.
The import policy and regression cases are owned by `backend/tests/architecture/`.

The policy analyzes static Python imports. It is **not** proof that runtime code cannot
perform network I/O, that a database migration is correct, or that an arbitrary dynamic
import is safe. Fixture network isolation, integration tests, and data validation are
separate acceptance gates. An intentional change to the dependency matrix requires
an architectural review and matching regression tests.

## Formatting and apatch

Run the mutating formatter before read-only checks:

```bash
sh ./run-format.sh
bash ./run-tests.sh
```

For apatch, enable its local FMT command once after applying the formatter setup PATCH:

```bash
python3 -B scripts/enable-apatch-fmt.py
```

The setup script only appends the formatter command to an existing `.apatch/config.yaml`
with configured checks. It stops rather than overriding a different formatter setup.
`FMT` performs safe Ruff fixes and formatting; `CHK` performs validation only.
Install the backend development dependencies before running either command.


## SDD consistency checks

The documentation suite uses PyYAML and JSON Schema Draft 2020-12 (both installed via `backend[dev]`) to validate feature references and the developer-controlled checkpoint. It checks exact `APPROVED` / `AUTHORIZED` / `PENDING` metadata, prevents `verified` without a feature acceptance record, and requires every requirement of the current task to be covered by selected test-inventory entries. An acceptance record needs explicit criterion IDs, evidence file paths and a developer approval reference; no record is generated automatically from passing tests. These checks cannot authenticate the human decision or establish product acceptance.

After each bounded task, review the change against the convergence checklist in the active implementation plan: scope, actual behavior, public contract compatibility, architecture, traceability and unresolved external approvals.

## Optional PostGIS verification (V02 partial)

The `backend/tests/unit/test_postgis_store_unit.py` and `backend/tests/contract/test_investigation_reopen_http.py` tests cover SQL adapter transaction intentions, typed completed-snapshot encoding and an injected fake store. They do **not** prove PostgreSQL/PostGIS execution or restart recovery. Routine `run-tests.sh` does not implicitly open a database.

After explicit developer approval of the PostgreSQL driver, migration privileges and a **disposable dedicated database**, install the approved driver in the backend development environment and provision a database whose name ends in `_test`. Set `MELLIATLAS_TEST_POSTGIS_DSN` in the local shell or secret manager; never commit it to the repository. With the backend and `backend[dev]` installed, run the opt-in verifier:

```bash
python3 -B backend/scripts/verify_postgis_investigations.py
```

The script verifies the actual database name before running SQL, applies the reviewed migration **twice** to check repeatability, inspects the PostGIS extension, required constraints and GiST index, and exercises completed-snapshot persistence. It verifies JSONB/evidence/decision-trace reopening through new service and HTTP instances, exact stored synthetic stop coordinates, SRID 4326 and a `geography`-based metric proximity query. Additional cases exercise UUID immutability, a completed `INSUFFICIENT_EVIDENCE` outcome with null site geometry, a database-rejected timestamp with rollback and subsequent successful write. It deletes only the synthetic UUID records generated during that verification run; **the migration, table and index remain**. Do not point it at a production or shared database, even if its name ends in `_test`.

This verifier is intentionally **not** part of routine `run-tests.sh`: it requires an authorized external database and performs SQL writes. Record the PostGIS version, migration identity, exact verification command and result as acceptance evidence. Until the real check passes and the developer approves the corresponding criteria, `MVP01-BE-A09` and `BE-T040`–`BE-T044` remain pending, regardless of local fake-store or unit test results.

## Optional runtime territory reference startup (V03 partial)

`backend/tests/contract/test_reference_startup.py` verifies paired opt-in local reference loading through ASGI lifespan, unchanged territory HTTP responses, default `503` isolation, missing/corrupt snapshot refusal, independent-inventory mismatches and the `melliatlas.main:app` environment configuration path. Tests use **synthetic incomplete fixtures** to prove wiring and fail-closed behavior; they do not certify real RU/BY region/district completeness or license suitability. The `BE-T001`–`BE-T012` and `BE-T058` real-data oracles remain pending approved inventories and source review.

## Pure fictional ecology screening (V04-01 partial)

`backend/tests/unit/test_ecology_screening.py` checks the typed analyzer/planning boundary: explicit fictional polygon overlap (including the boundary), synthetic exclusion versus non-binding precaution, conservative unknown with absent coverage, stable evidence/rule IDs, candidate-rename independence, deterministic precedence, and invalid input. No live data or network access is involved. These tests do **not** establish a real legal exclusion, complete habitat coverage, agent replanning, successful investigation integration, or acceptance of `MVP01-BE-A06/A07`.
