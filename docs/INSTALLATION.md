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
