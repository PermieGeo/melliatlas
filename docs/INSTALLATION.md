# Development Installation

## Backend requirements

- Python 3.12 or newer.
- A local virtual environment and an installable development toolchain.
- PostgreSQL/PostGIS is optional for health, the bundled name-only RU/BY region list, and isolated tests; it is required for reviewed administrative boundaries and districts.

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

## Region names without a database

The standard `melliatlas.main:app` entry point loads the pinned `backend/reference/iso3166-2-regions.json` when `MELLIATLAS_DATABASE_URL` is unset. This provides 83 Russian and 7 Belarusian first-order names immediately, even with fictional sources disabled. It does **not** include ADM1 geometry, ADM2 districts, approved present-day coverage, or Saturn region-ID mappings; requesting districts returns `409` and geometry returns `404`. A weather or place analysis needing a boundary remains unavailable. The startup loader rejects a modified, incomplete or inconsistent pinned file instead of silently inventing entries.

To make the area map and district selector useful, configure PostgreSQL/PostGIS and run the explicit migrations, region seed, and reviewed ADM1 then ADM2 imports below. Restart the server after setting `MELLIATLAS_DATABASE_URL`. A configured database that is unavailable or incompletely migrated reports an error; the backend does not hide it by switching silently to the bundled directory.

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
claimed. With no database configured, the pinned name-only directory is used instead of a `503` for region reads.

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

A reproducible, explicit download workflow is available for the published
geoBoundaries `gbOpen` dataset. Run the following **on the machine which can
reach the source**, from the repository root. The commands never access the
database; large geometry files and their review manifests stay outside Git.

```bash
export MELLIATLAS_BOUNDARIES_DIR="$HOME/melliatlas-boundaries"
python backend/scripts/prepare_all_geoboundaries.py --output-dir "$MELLIATLAS_BOUNDARIES_DIR"
```

Run this command from the repository root. It stages **RU ADM1, RU ADM2,
BY ADM1 and BY ADM2** in that order and prints download progress (MiB, and
expected size when available), each layer's status and a final JSON report.
It checks any existing matching dataset **locally before making a network
request**. Intact captures are reused after validating SHA-256, source identity,
file size, feature inventory and the ADM1 review file. Only missing layers are
downloaded; corrupt, incomplete or multiple versions for a layer cause an
explicit error rather than an overwrite. Re-run the exact command after a
network interruption. An interrupted in-memory download of a missing layer
starts that layer over; it does not resume individual HTTP byte ranges. A newer
upstream dataset must be reviewed and staged in a separate directory.

The provider's simplified GeoJSON may not contain the same number of features
as its `admUnitCount` metadata (observed while staging RU ADM2). The command
**does not silently ignore the discrepancy or invent missing districts**:
`unit_count` records the actual downloaded feature count,
`advertised_unit_count` records the source claim and
`review_status: inventory_mismatch` blocks ordinary import. The batch stages
all possible layers and exits **2** if any discrepancy requires review, **1**
if any layer could not be staged, or **0** when no discrepancy was observed.
An exit status of 2 is not a corrupted download: inspect the reported counts
and compare the downloaded dataset with the source before deciding whether a
partial historical snapshot is suitable. No import into PostgreSQL occurs
in this staging command.

Each staged layer writes `<boundaryID>.geojson` and a sibling
`.manifest.json` containing source ID, license, vintage, download URL,
SHA-256, capture time and both counts. ADM1 also writes `.review.json`
containing names, ISO codes and **exact-only proposed** canonical matches.
Review unmatched entries and create a mapping JSON of verified
`shapeID -> region_id` entries if necessary. A staged count mismatch remains
explicitly unapproved: if, after independent review, you choose to import the
available historical subset, pass `--acknowledge-inventory-mismatch` together
with `--manifest` to `import_admin_boundaries.py`. Without that flag the
importer refuses the mismatch before opening a database connection. The flag
acknowledges *only the source inventory discrepancy*, not missing/ambiguous
parent regions or use permissions. Never interpret a matching PostGIS count as
proof of full provider coverage or current administrative boundaries. GitHub
LFS download failures are reported instead of treated as valid GeoJSON.

For example, after reviewing the **current** downloaded manifest and ADM1
matching report, import RU ADM1 and then RU ADM2 with their actual filenames
(the IDs below identify the metadata snapshot inspected on 2026-11-16 and can
change in later upstream releases):

```bash
python backend/scripts/import_admin_boundaries.py --country RU --level ADM1 \
  --file "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM1-28173009.geojson" \
  --manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM1-28173009.geojson.manifest.json" \
  --valid-on 2017-01-01
python backend/scripts/import_admin_boundaries.py --country RU --level ADM2 \
  --file "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM2-50074027.geojson" \
  --manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM2-50074027.geojson.manifest.json" \
  --valid-on 2017-01-01
```

For Belarus use `--country BY`, the captured `BLR-ADM1-*` then `BLR-ADM2-*`
filenames, and a reviewed 2005 vintage (the inspected provider records identify
`BLR-ADM1-45462678` and `BLR-ADM2-67162791`). The example first-of-year
`--valid-on` values are **year-level metadata anchors**, not precise legal
boundary effective dates. Document any separately verified actual effective date
instead of treating the anchor as a verified enactment date.

The manifest path binds an import to the captured file's SHA-256, country,
level, version and advertised feature count. Any discrepancy stops before
connecting to PostgreSQL. To supply reviewed ADM1 matches, add
`--mapping /path/to/reviewed-mapping.json` to that ADM1 import. For districts,
parent regions are identified by spatial containment of the already imported
ADM1 geometry. Ambiguous/missing parents abort the entire transaction; only a
consciously reviewed `--allow-partial` run skips unmatched units. Do not present
such a run as complete district coverage.

After both levels are imported for a country, compare **stored** geometry to
the captured source inventories:

```bash
python backend/scripts/verify_admin_boundaries.py --country RU \
  --adm1-manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM1-28173009.geojson.manifest.json" \
  --adm2-manifest "$MELLIATLAS_BOUNDARIES_DIR/RUS-ADM2-50074027.geojson.manifest.json"
```

The verification uses read-only SQL, requires matching version counts and
reports invalid geometries, orphaned districts, other-version rows and any
advertised-versus-downloaded source inventory discrepancy. A successful
snapshot match does not resolve that provider discrepancy.
A failure means the imported data is incomplete **relative to this source
snapshot**. It does not independently validate current jurisdiction boundaries.
Restart the API with `MELLIATLAS_DATABASE_URL` configured to serve the stored
regions and districts. Import only after reviewing each dataset's provenance,
coverage, terms and regional matching reports.

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

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the local backend. The first successful npm installation must generate and commit `web/package-lock.json` for reproducible installs. Do not claim `npm ci` or a reproducible build until that lockfile is present. The map loads OpenStreetMap tiles automatically (the tile host receives the tile coordinates). The last map center and zoom are stored only in this browser under `melliatlas.map.viewport.v1`; no apiary point is separately persisted. To avoid external map requests, block the tile host or use a separately approved offline map source in a future deployment. Region/district zoom requires the reviewed ADM1/ADM2 data described above.

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

