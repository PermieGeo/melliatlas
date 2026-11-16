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

The table starts empty. For the Smolensk pilot (`ru:region:smo`, Saturn
subject `55`), use the **operator-only two-phase importer** below, after applying
`0006` for the optional Russian district names. No source directory is fetched
at application startup. Review the upstream access and reuse terms first.

1. Capture one bounded HTTPS response from the historically observed
   `GET https://bee-saturn.ru/backend/beemaster/district/55` endpoint to a new
   local file outside the repository. No retries, redirects or repeated polling:

   ```bash
   python backend/scripts/capture_saturn_districts.py \
     --output /tmp/melliatlas-saturn-smolensk-districts.json
   ```

2. Preview the mapping using the already imported ADM2 districts in PostGIS:

   ```bash
   python backend/scripts/import_saturn_districts.py \
     --file /tmp/melliatlas-saturn-smolensk-districts.json
   ```

   The read-only JSON report contains every proposed canonical ID, upstream
   district ID and name, match method, unmatched upstream entries and the
   capture SHA-256. A case/whitespace/`ё` normalization and the explicit
   `муниципальный район` qualifier normalization may suggest exact matches;
   they are **proposals only**. Verify district identity independently before
   accepting the proposal; spelling similarity alone is insufficient.
   Missing or ambiguous names are not inserted.

3. If there are independently verified unmatched districts, you may supply a
   *local, operator-reviewed* overrides JSON whose **keys are the captured
   provider district IDs** and whose values are canonical imported IDs:

   ```json
   {"1524": "ru:district:REPLACE_WITH_VERIFIED_CANONICAL_ID"}
   ```

   Pass it as `--overrides /path/to/reviewed-overrides.json` to both preview and
   apply commands. This is a format illustration, **not a verified mapping**;
   never use this placeholder value or guess a geoBoundaries ID. All overrides
   must refer to IDs present in the captured source and in the selected region.

4. After reviewing the complete preview, explicitly approve the **exact** SHA-256
   printed by the command. The importer checks it again immediately before the
   transaction and inserts only missing pairs. Existing conflicting mappings
   fail without being overwritten:

   ```bash
   CAPTURE_SHA256='paste-reviewed-sha256-here'
   python backend/scripts/import_saturn_districts.py \
     --file /tmp/melliatlas-saturn-smolensk-districts.json \
     --apply --approve-sha256 "$CAPTURE_SHA256"
   ```

   If overrides were used in step 3, supply the same `--overrides` file here.
   The output lists `inserted`, `proposed_count` and unmatched districts. This
   command never inserts fake district codes or changes administrative geometry.

5. Verify the imported records, then restart the backend (or start it with
   `MELLIATLAS_SATURN_LIVE_ENABLED=true`):

   ```bash
   psql "$MELLIATLAS_DATABASE_URL" -c \
     "SELECT district_id, provider_district_code, source_uri FROM melliatlas_source_saturn_district ORDER BY district_id;"
   ```

Select an imported, mapped Smolensk district and press **Analyze**. The server
resolves `district_id` using `PostgresRegionCatalog.find_district_code` and
passes the reviewed numerical provider `district` into the existing bounded
`planapplybees` request. Unmapped districts still fail explicitly (409): there
is **no fallback to a full-region query**. The request remains limited to
100 source entries and a date window of at most one calendar year. A nonempty
response is not evidence of complete coverage or access rights. The live
endpoint's current compatibility cannot be guaranteed by the historical capture.

With `MELLIATLAS_SATURN_LIVE_ENABLED=true`, the UI will reject a district
without an independently reviewed mapping (409), rather than requesting the
whole oblast. The query sends provider `district`, `startDateUpdateMap`, and
`endDateUpdateMap` values: their actual upstream semantics, rights and
completeness require separate confirmation. Without approved mappings or
provider permission, leave the district source read unavailable. The weather
panel does not require a Saturn mapping: it auto-loads the 24-hour forecast
for a validated territory point when live weather is enabled.

## Optional Russian district display names (Smolensk pilot)

After importing reviewed RU ADM2 geometry with migration `0003`, apply the
additive display-name migration before starting a backend that selects
`melliatlas_admin_geometry.name_ru`:

```bash
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f backend/migrations/0006_smolensk_district_names.sql
```

The migration adds an optional `name_ru` column, then backfills a limited list
of Smolensk district names where the original source name matches a reviewed
English spelling. No provider/canonical IDs, original names, source provenance,
geometry or existing non-null translations are rewritten. Unmatched districts
remain in the original source language until independently reviewed; use the
English UI for the original name. This is a temporary localization seed, not a
claim about current administrative status or completeness. Apply `0005`
separately to enable reviewed Saturn district-code mapping; no Saturn codes
are inserted by this localization migration.
