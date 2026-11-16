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

The optional database path holds **first-order administrative names and IDs**.
Approved boundaries and districts can be imported separately after the region seed. PostgreSQL 15+ is recommended. Install the
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

### Import independent administrative boundaries and districts (manual, reviewed)

MelliAtlas owns the country-scoped region directory separately from external
Saturn IDs. After the `0002` migration and `bootstrap_regions.py` step above,
install the PostGIS extension on the PostgreSQL server and apply the additive
geometry migration:

```bash
psql "$MELLIATLAS_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/0003_administrative_boundaries.sql
```

The first-order region names become available immediately after the independent
seed. Boundaries and the district selector require **separately reviewed**
ADM1/ADM2 GeoJSON from an approved geographic source. An example candidate
is geoBoundaries gbOpen, with provider metadata at:

- `https://www.geoboundaries.org/api/current/gbOpen/RUS/ADM1/`
- `https://www.geoboundaries.org/api/current/gbOpen/RUS/ADM2/`
- `https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM1/`
- `https://www.geoboundaries.org/api/current/gbOpen/BLR/ADM2/`

Inspect each source's collection date, boundaries, attribution and license;
these historical files do **not** establish current administrative authority.
Original source licenses differ by geography: RU is ODbL-sourced and BY is
CC BY-sourced in the published provider metadata. Obtain a **reviewed**
`FeatureCollection` for each country/level and keep the downloaded GeoJSON
outside the repository. The importer recognizes `shapeID`, `shapeName`,
`shapeGroup`, `shapeType` and optional `shapeISO`. ADM1 matches the independent
region identity only by exact ISO code, exact normalized name or a reviewed
operator-supplied `shapeID -> region_id` mapping. Unmatched records fail the
transaction unless `--allow-partial` was explicitly chosen. Never guess
parent regions from numeric Saturn IDs.

Example for an operator-approved RU ADM1 capture:

```bash
python backend/scripts/import_admin_boundaries.py \
  --country RU --level ADM1 \
  --file /path/to/reviewed-RUS-ADM1.geojson \
  --reference-id geoboundaries:RUS-ADM1:reviewed-2026-11 \
  --source-uri https://www.geoboundaries.org/api/current/gbOpen/RUS/ADM1/ \
  --license ODbL-1.0 --valid-on 2017-01-01 \
  --mapping /path/to/reviewed-region-mapping.json
```

`--reference-id` and `--valid-on` above are placeholders: replace them with
the documented source **version** and actual data vintage; never use the
execution date as an invented boundary validity date. A reviewed mapping file
is a JSON object, for example `{"provider-shape-id": "ru:region:smo"}`;
omit `--mapping` if all identities match exactly without review. If using
`--allow-partial`, review the reported unmatched count rather than treating
partial coverage as complete.

Import ADM1 first. Then import the same country's ADM2 file using
`--level ADM2` and the corresponding captured provenance. ADM2 parent regions
are derived **spatially from the imported ADM1 geometry**, only if exactly one
parent covers a representative point and at least 95% of the district polygon.
Otherwise the import refuses ambiguous membership; `--allow-partial` permits
explicitly incomplete coverage. Every import is transactional and checks
existing shape/version conflicts. Repeat the process separately for BY.

The application never downloads or imports boundaries on startup. With
`MELLIATLAS_DATABASE_URL` configured, region names come from the database;
choosing a region whose reviewed geometry is present automatically loads and
fits its polygon in the map. Districts appear only after an approved ADM2
import. If a geometry is missing, the corresponding map analysis remains
disabled with an explicit explanation. No checked-in geoBoundaries datasets,
complete-coverage claims, or unapproved source access are part of this PATCH.

### One-shot Saturn subject-directory capture and mapping review

The independent RU/BY region seed never fetches Saturn. For an explicitly
reviewed, operator-authorized check of the *historically observed* public
endpoint, capture one bounded GET response to a **new local file outside the
repository** (no scheduled collection, credentials or browser automation):

```bash
python backend/scripts/capture_saturn_subjects.py --output /tmp/melliatlas-saturn-subjects.json
```

The command requires a new path, refuses overwrites, caps the response at
256 KiB, requires 80–150 structurally valid and uniquely identified subjects,
and writes the raw capture as a local `0600` file. It prints only entry count,
SHA-256 and the **actual UTC capture timestamp**, not raw region records.
`HTTP 403`, redirects, changed schemas or timeouts fail without a stored file.
The reported 86 subjects in the dated historical research are not a guarantee
of the provider's current availability, contractual stability or completeness.
Do not commit the captured JSON or use it to claim approved reuse rights.

After reviewing the locally captured names and provider codes, supply the
**printed timestamp** to the existing offline importer:

```bash
python backend/scripts/import_saturn_subjects.py --file /tmp/melliatlas-saturn-subjects.json --captured-at 2026-11-16T00:00:00+00:00
```

The timestamp above is an **example only**; replace it with the capture output.
The importer uses existing independent region names for unique exact normalized
matches, retains distinct provider IDs in `melliatlas_source_saturn`, and
rolls back conflicting entries. Unmatched names are counted for human review;
they are never fuzzy-matched or assigned guessed IDs. Capture and import are
explicit operations, never startup behavior. Confirm source access and reuse
permission before real deployment.

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
**Analyze selected area**. The server resolves a verified numeric Saturn subject
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
