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
