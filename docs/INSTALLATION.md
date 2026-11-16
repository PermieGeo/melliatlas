# Development Installation

Run commands from the repository root unless stated otherwise. Python 3.12+, Node.js 22+, Docker/OrbStack and PostgreSQL `psql` are needed for the full local workflow.

## 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './backend[dev]'
python -m pip install uvicorn
cd web && npm install && cd ..
```

## 2. Start PostgreSQL + PostGIS

For the existing local container:

```bash
docker start melliatlas-postgis
export MELLIATLAS_DATABASE_URL='postgresql://melliatlas:melliatlas_dev@127.0.0.1:5433/melliatlas'
psql "$MELLIATLAS_DATABASE_URL" -c 'SELECT PostGIS_Version();'
```

For a fresh development setup, create the container once (use a local-only password; the example is **not** for deployment):

```bash
docker volume create melliatlas-postgis-data
docker run -d --name melliatlas-postgis --restart unless-stopped \
  -p 127.0.0.1:5433:5432 \
  -e POSTGRES_DB=melliatlas -e POSTGRES_USER=melliatlas \
  -e POSTGRES_PASSWORD=melliatlas_dev \
  -v melliatlas-postgis-data:/var/lib/postgresql/data \
  postgis/postgis:16-3.7
```

Use an unused host port if `5433` belongs to another container. The named volume preserves imported data on restart; do not remove it to troubleshoot connections.

## 3. Initialize database tables

Run once for a new database; these commands are safe to rerun against matching existing data:

```bash
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/0002_region_directory.sql
python backend/scripts/bootstrap_regions.py
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/0003_administrative_boundaries.sql
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/0004_weather_provider_configuration.sql
```

Migration `0001_completed_investigations.sql` is optional and separate from geographic navigation.

## 4. Download administrative boundaries

```bash
export MELLIATLAS_BOUNDARIES_DIR="$HOME/melliatlas-boundaries"
python backend/scripts/prepare_all_geoboundaries.py --output-dir "$MELLIATLAS_BOUNDARIES_DIR"
```

The command downloads only missing RU/BY ADM1/ADM2 files, verifies existing captures and shows progress. It may report `inventory_mismatch` when source counts differ; review the manifest before importing. GeoJSON and manifests stay outside Git.

## 5. Import boundaries

Import each country's **ADM1 before ADM2**. These filenames are from the inspected 2026-11-16 geoBoundaries capture; use the filenames in your downloaded directory if newer IDs are returned.

```bash
python backend/scripts/import_admin_boundaries.py --country RU --level ADM1 \
  --file "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM1-28173009.geojson" \
  --manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM1-28173009.geojson.manifest.json" --valid-on 2017-01-01
python backend/scripts/import_admin_boundaries.py --country RU --level ADM2 \
  --file "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM2-50074027.geojson" \
  --manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM2-50074027.geojson.manifest.json" --valid-on 2017-01-01
python backend/scripts/import_admin_boundaries.py --country BY --level ADM1 \
  --file "$MELLIATLAS_BOUNDARIES_DIR/BLR-ADM1-45462678.geojson" \
  --manifest "$MELLIATLAS_BOUNDARIES_DIR/BLR-ADM1-45462678.geojson.manifest.json" --valid-on 2005-01-01
python backend/scripts/import_admin_boundaries.py --country BY --level ADM2 \
  --file "$MELLIATLAS_BOUNDARIES_DIR/BLR-ADM2-67162791.geojson" \
  --manifest "$MELLIATLAS_BOUNDARIES_DIR/BLR-ADM2-67162791.geojson.manifest.json" --valid-on 2005-01-01
```

Only after reviewing a provider count discrepancy, append `--acknowledge-inventory-mismatch` to the affected command. Never use `--allow-partial` without reviewing unmatched territories. The example dates reflect the source's year, not verified legal effective dates. Imports are transactional and reject conflicting repeats.

## 6. Verify geography and diagnose missing districts

```bash
python backend/scripts/verify_admin_boundaries.py --country RU \
  --adm1-manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM1-28173009.geojson.manifest.json" \
  --adm2-manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM2-50074027.geojson.manifest.json"
python backend/scripts/verify_admin_boundaries.py --country BY \
  --adm1-manifest "$MELLIATLAS_BOUNDARIES_DIR/BLR-ADM1-45462678.geojson.manifest.json" \
  --adm2-manifest "$MELLIATLAS_BOUNDARIES_DIR/BLR-ADM2-67162791.geojson.manifest.json"
```

A complete country-wide inventory **does not** guarantee districts exist under every region. With the backend running (step 7), compare database counts with the live HTTP API:

```bash
python backend/scripts/diagnose_admin_navigation.py --country RU
# Optionally restrict to one region:
python backend/scripts/diagnose_admin_navigation.py --country RU --region-id ru:region:smo
```

The script makes read-only SQL queries and local HTTP requests. `issues` identifies mismatched/invalid API responses; `empty_regions` lists regions with no saved districts. If database and API counts match but the browser does not show districts, inspect the browser Network request to `/api/v1/territories/districts`.

## 7. Run the application

Backend — terminal 1, with `MELLIATLAS_DATABASE_URL` set:

```bash
source .venv/bin/activate
export MELLIATLAS_DATABASE_URL='postgresql://melliatlas:melliatlas_dev@127.0.0.1:5433/melliatlas'
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000 --reload
```

Web — terminal 2:

```bash
cd web
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to port `8000`. Without `MELLIATLAS_DATABASE_URL`, the backend serves region names only (no districts/geometry).

Weather operational configuration is kept in the single `open-meteo` row of
`melliatlas_weather_provider_config`: `enabled`, `timeout_seconds` (1–15),
`max_body_bytes` (1024–100000), and the provider documentation URL (verified
`https://open-meteo.com/` origin). Edit only with a reviewed database update;
there is no public or remote operator configuration endpoint. The migration
is required for database-backed live weather. If `MELLIATLAS_DATABASE_URL`
and `MELLIATLAS_WEATHER_LIVE_ENABLED=true` are configured, settings are read
at ASGI lifespan startup, not during module import. A missing migration prevents
the server from starting in that explicit live-weather mode. Apply the `0004`
migration before restarting; do not delete existing geographic data or turn
on unreviewed fallback settings. Missing database settings fail closed; the source is still disabled unless the explicit environment gate is true.

Optional local-only flags: `MELLIATLAS_SOURCE_PROVIDER=synthetic` enables fictional investigation scenarios; `MELLIATLAS_SATURN_LIVE_ENABLED=true` enables the experimental RU-only manual Saturn read; `MELLIATLAS_WEATHER_LIVE_ENABLED=true` enables a manually requested Open-Meteo forecast. Review source terms before use.

## 8. Checks

```bash
sh ./run-format.sh
sh ./run-tests.sh
```

Use `run-format.sh` before `run-tests.sh`; formatting modifies source files. Manual PostGIS imports and real external-source checks are not performed by the normal test suite.

## Explicit Saturn district mapping after 0003 (W01)

The manual selected-area workflow requires a reviewed, provider-specific
Saturn district identifier. After loading the reviewed administrative
boundaries via migration `0003`, create the empty mapping table:

```bash
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f backend/migrations/0005_saturn_district_mapping.sql
```

For every district that an operator explicitly verified, insert a row into
`melliatlas_source_saturn_district` containing the imported canonical
`district_id`, the **independently observed** upstream `provider_district_code`,
`source_uri`, and `verified_at`. Do not infer upstream IDs from geoBoundaries
shape IDs, names, ISO codes, polygon coordinates or array indexes. Do not
populate fake examples into a real database. The table starts empty on purpose.

With `MELLIATLAS_SATURN_LIVE_ENABLED=true`, the UI will reject a district
without an independently reviewed mapping (409), rather than requesting the
whole oblast. The query sends provider `district`, `startDateUpdateMap`, and
`endDateUpdateMap` values: their actual upstream semantics, rights and
completeness require separate confirmation. Without approved mappings or
provider permission, leave the district source read unavailable. The weather
panel does not require a Saturn mapping: it auto-loads the 24-hour forecast
for a validated territory point when live weather is enabled.
