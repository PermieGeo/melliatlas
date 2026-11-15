# Development Installation

## Backend requirements

- Python 3.12 or newer.
- A local virtual environment and an installable development toolchain.
- PostgreSQL/PostGIS will be required in later MVP-01 implementation steps; the initial health endpoint does not use a database.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e './backend[dev]'
```

The install uses only the backend dependencies declared in `backend/pyproject.toml`.

## Local HTTP smoke run

```bash
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000
```

The `uvicorn` command requires an ASGI server. FastAPI's development installation does not necessarily install it; install an ASGI server separately only after its dependency is approved, or run the included FastAPI ASGI tests without starting an external server. No public deployment is configured.

## Optional local reference loading (V03 partial)

The ASGI entrypoint normally starts without territory reference data: reference-dependent reads return `503`. After separately reviewing and approving a licensed normalized snapshot and an independently prepared inventory, supply **both** paths before starting the server:

```bash
export MELLIATLAS_REFERENCE_SNAPSHOT=/path/to/approved-reference.json
export MELLIATLAS_REFERENCE_INVENTORY=/path/to/independent-inventory.json
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000
```

The values above are illustrative paths, not shipped data. Startup reads only those two local files, verifies the reference against the independent inventory and refuses to start on missing, malformed or inconsistent input. It does not fetch sources, select a reference automatically, write to PostGIS, or approve any reference data. Existing applications that pass `territories=` to `create_app()` must not also configure reference file paths. Synthetic unit-test fixtures are incomplete and must not be used as geographic coverage evidence.
