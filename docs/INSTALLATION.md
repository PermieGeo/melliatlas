# Development Installation

## Backend requirements

- Python 3.12 or newer.
- A local virtual environment and an installable development toolchain.
- PostgreSQL/PostGIS is optional for health and isolated tests, but required for durable preloaded administrative regions.

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

## Preload independent RU/BY regions into PostgreSQL (optional)

The optional database path holds **first-order administrative names and IDs**,
not real polygon boundaries. PostgreSQL 15+ is recommended. Install the
opt-in `postgres` extra (also included in `backend[dev]`) and create a local
database through your normal PostgreSQL administration. The region directory is independent of the older completed-result/PostGIS
migration. Apply `0001` separately only if you also use completed-result
persistence. For a new empty PostgreSQL database, the region setup is:

```bash
python -m pip install -e './backend[postgres]'
export MELLIATLAS_DATABASE_URL='postgresql://user:password@127.0.0.1:5432/melliatlas'
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/0002_region_directory.sql
python backend/scripts/bootstrap_regions.py
export MELLIATLAS_SOURCE_PROVIDER=disabled
export MELLIATLAS_SATURN_LIVE_ENABLED=true
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000 --reload
```

Use your own local credentials and **do not commit connection strings**. Apply migration 0002 and seed once; subsequent runs validate the same entries. The region seed is safe to rerun and rejects
conflicting existing rows. It includes the 83 RU / 7 BY subdivisions identified
in `iso-codes` 4.18.0, and only the archived Smolensk Saturn subject mapping.
No coverage of disputed/other regions, municipal districts or valid borders is
claimed. With no database configured, the previous explicit `503` remains.

To import further Saturn mappings, first obtain and review an authorized JSON
array from the separately documented `GET /backend/beemaster/oktmo-subjects`
endpoint. The importer performs **offline exact-name matching only**:

```bash
python backend/scripts/import_saturn_subjects.py --file /path/to/reviewed-subjects.json --captured-at 2026-11-11T12:00:00+00:00
```

Replace the capture time with its **actual** timestamp. The imported numeric
identifiers are stored separately in `melliatlas_source_saturn`; unmatched
names are not guessed and conflicting mappings reject the transaction. The
ordinary application never fetches region directories from Saturn. Source
access and reuse rights require separate approval.

## Optional local reference loading (V03 partial)

The ASGI entrypoint normally starts without territory reference data: reference-dependent reads return `503`. After separately reviewing and approving a licensed normalized snapshot and an independently prepared inventory, supply **both** paths before starting the server:

```bash
export MELLIATLAS_REFERENCE_SNAPSHOT=/path/to/approved-reference.json
export MELLIATLAS_REFERENCE_INVENTORY=/path/to/independent-inventory.json
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000
```

The values above are illustrative paths, not shipped data. Startup reads only those two local files, verifies the reference against the independent inventory and refuses to start on missing, malformed or inconsistent input. It does not fetch sources, select a reference automatically, write to PostGIS, or approve any reference data. Existing applications that pass `territories=` to `create_app()` must not also configure reference file paths. Synthetic unit-test fixtures are incomplete and must not be used as geographic coverage evidence.


## Beekeeper Web client (W01 partial)

The only browser client lives in `web/`. Node.js 22+ and npm are required. Install backend dependencies first; the API must be started separately at `127.0.0.1:8000`. The FastAPI project does not currently pin a production ASGI runner. An approved local `uvicorn` installation can be used for development.

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the local backend. The first successful npm installation must generate and commit `web/package-lock.json` for reproducible installs. Do not claim `npm ci` or a reproducible build until that lockfile is present. The optional external map tile layer is disabled by default; enable it explicitly if you accept sharing map viewport requests with OpenStreetMap.

See [Web README](../web/README.md) for the synthetic scenario and client-specific verification commands.



### Source-provider selection

The backend defaults to `MELLIATLAS_SOURCE_PROVIDER=disabled`: the public API has no
synthetic scenario enabled, and investigation creation fails closed. To run the
explicit offline demonstration, start the backend with
`MELLIATLAS_SOURCE_PROVIDER=synthetic` in its environment. This is a fixture-only
mode and does not activate real Saturn/network data. An unsupported mode causes
startup to fail instead of silently choosing a provider.

## Experimental RU-only public Saturn preview

The experimental live source is disabled by default and independent of the
offline demonstration provider. For a deliberately user-triggered public portal
request from a local development instance only:

```bash
export MELLIATLAS_SATURN_LIVE_ENABLED=true
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000
```

Use the Web client with country `RU`; the server advertises `saturn` only there.
Select a country and a preloaded region in the left panel, then click
**Read one live page**. The server resolves a verified numeric Saturn subject
code from its separate mapping table; missing mappings return HTTP 409. The request sends one bounded POST to a pinned
legacy public URL; status 403/404, changed response shape or inaccessible site
returns an explicit error, never fabricated data. `BY` never offers or contacts
Saturn. No automatic polling, rate-intensive scanning, scheduled crawling or
plan calculations on the live observations are provided.

The request format is based on older observed portal traffic, not an official
verified current machine-readable read contract. Public website access does
not establish permission to bulk reuse data. Confirm the current API and reuse
conditions before any public deployment. The real source has not been reachable
from this development environment for live acceptance testing.

## Experimental Open-Meteo forecast (explicit opt-in)

For a local non-commercial development preview, activate your Python environment
and start the backend with `MELLIATLAS_WEATHER_LIVE_ENABLED=true`. No synthetic
provider is needed. The Web UI shows the Open-Meteo panel for countries where
the backend advertises it, and requests 24 hours of forecast only after you
select a map point and click the read button. Example:

```bash
export MELLIATLAS_SOURCE_PROVIDER=disabled
export MELLIATLAS_WEATHER_LIVE_ENABLED=true
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000 --reload
```

Saturn remains separately controlled by `MELLIATLAS_SATURN_LIVE_ENABLED=true`
and is RU-only. Both sources are disabled by default. Forecast coordinates
are transmitted to Open-Meteo after the button click, even when the map tile
layer is disabled. Do not enable the free endpoint for commercial deployment
without reviewing the provider's separate commercial terms and attribution.
