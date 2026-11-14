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

Current tests cover FastAPI health/OpenAPI, versioned territory endpoints, offline territory-reference validation, independent inventory comparisons, simple WGS84 polygon checks, idempotent in-memory loading, and architecture import boundaries. These tests use synthetic administrative snapshots; **they do not establish complete real RU/BY coverage or PostGIS topology correctness**. No approved full reference, PostGIS import, source adapter, agent, or browser acceptance test exists yet.

To validate externally obtained normalized reference files after verifying permission, provenance, and independent inventories, run from an installed backend environment:

```bash
python backend/scripts/import_reference.py path/to/reference.json path/to/independent-inventory.json
```

This command only validates the local input and prints a report; it does not import into PostGIS or mark a reference approved.

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
