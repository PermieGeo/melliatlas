# PostGIS Completed Investigation Store Contract — V02 (partial)

`persistence/postgis_store.py` owns `PostgisCompletedInvestigationStore`, which implements the jobs-owned `CompletedInvestigationStore` protocol. A caller injects a DB-API-compatible PostgreSQL connection factory; the adapter does not import a driver, read credentials, open implicit connections at application startup, or install dependencies. Each operation owns and closes its connection and cursor.

`save` accepts only `COMPLETED` snapshots with a domain outcome, inserts the immutable JSONB payload and the selected stop points as an `EPSG:4326` PostGIS `MULTIPOINT` geometry, and commits once. A duplicate UUID cannot overwrite history. A failed insert or commit is rolled back; the jobs service then reports `FAILED` rather than exposing a completed response. `load` returns a validated typed snapshot from a fresh connection or `None` for a missing UUID. Database errors are wrapped as `InvestigationStorageError`, without leaking SQL or credentials through HTTP.

Apply `backend/migrations/0001_completed_investigations.sql` to a separately provisioned PostgreSQL/PostGIS database with extension privileges before use. The migration declares a primary key, JSONB payload, timestamps, SRID-bound geometry, constraints, and a GiST index. Metric proximity operations must use `geography` or an appropriate projected CRS, never raw WGS84 degrees. It stores **fictional selected-site points**, not approved administrative boundaries. A suitable DB driver and a real PostGIS test environment require explicit developer approval. `backend/scripts/verify_postgis_investigations.py` is an opt-in real-database check; fake-driver tests do **not** establish database correctness.

In-process `QUEUED` and `RUNNING` jobs are not durable. Persistence is not enabled in `melliatlas.main:app` by default. Configuring a driver, connection pool, actual schema permissions, reference/territory storage, restart-safe job recovery, migration version management, and production access controls remain separate work. Completed snapshot payloads include the private starting point; database access must be restricted accordingly.


## Optional PostgreSQL region directory

`melliatlas.persistence.regions.PostgresRegionCatalog` supplies both the public
`TerritoryCatalog` interface for first-order region names and the
`SourceTerritoryCodeLookup` interface for provider-specific IDs. SQL I/O uses
parameterized read-only queries and one short-lived injected connection per
operation; the ASGI event loop runs those reads in a worker thread. Errors
never silently downgrade to an empty catalog. The catalog does not import raw
Saturn responses, use network access, or infer geometries/district depth.

Schema: `backend/migrations/0002_region_directory.sql`. Region seed:
`backend/reference/iso3166-2-regions.json`, installed separately before
starting the API via `backend/scripts/bootstrap_regions.py`. The separate
`melliatlas_source_saturn` table stores only reviewed mapping IDs; the seed
contains the Smolensk `55`/`66000000` example confirmed in the dated
independently captured Saturn reference. Later mappings can be imported from
an operator-reviewed, bounded `/oktmo-subjects` JSON capture, with exact-name
matching only. Conflicting mappings fail instead of being overwritten.

Database connections are opt-in through `MELLIATLAS_DATABASE_URL` and the
`postgres` optional dependency; no migration, seeding or fetching occurs on
ordinary API startup. Real Postgres integration checks remain required.


## Reviewed administrative geometry (additive)

`PostgisTerritoryCatalog` extends the independent PostgreSQL region directory
with read-only PostGIS polygons and districts from `melliatlas_admin_geometry`.
That table contains provenance, source shape identity, country code, canonical
parent region, and WGS84 MultiPolygon, but no Saturn identifiers. The importer
runs explicitly outside application startup, checks country and ADM level,
rejects ambiguous ADM1 identities and ADM2 parent assignments, and uses a
transaction per review batch. Country/region independence remains mandatory:
Saturn mappings are resolved only through `melliatlas_source_saturn`. A region
with no approved geometry is still a valid region, but not an analyzable map
boundary. Imported geometry/district coverage is not assumed complete.


### Administrative boundary import integrity

The operator-only staging tool downloads an externally versioned geoBoundaries
layer into files outside the repository. A captured manifest records SHA-256,
source version, country, ADM level, license, observed feature count and any
discrepancy with the provider-advertised inventory. The importer's `--manifest`
option validates these against exact source bytes before opening a database
connection. A mismatched source inventory requires an explicit
`--acknowledge-inventory-mismatch` option after human review, without weakening
other matching, geometry or provenance checks. A repeated insert only counts as equivalent when shape ID,
reference identity, region parent, name, provenance, validity anchor and actual
PostGIS geometry match. Any conflicting row rolls back the batch. The database
verifier counts exact reference IDs, checks spatial/CRS validity and district
parent presence, but does not certify present-day authoritative boundaries.

## Independently reviewed district identity

`PostgresRegionCatalog.find_district_code` reads
`melliatlas_source_saturn_district` created by migration `0005`. This table
is intentionally unseeded. The lookup joins existing canonical district
geometry, its parent region and the separately verified Saturn subject ID;
an absent mapping cannot turn into an unfiltered provider request.

A Smolensk-only operator workflow captures the provider directory using one
bounded read of `beemaster/district/55` and separately previews imported
canonical ADM2 IDs against the captured district IDs and names. The preview
is read-only; insertion requires an explicit capture SHA-256 approval. The
importer accepts only unique one-to-one exact-normalized names or separately
reviewed explicit overrides, checks the subject mapping (`55`) and rejects
conflicting existing rows. Unmatched entries remain unmapped. No mapping
is generated from a geoBoundaries `shapeID` or a guessed name/code, and no
remote lookups occur during application startup or source reads. Without a
successful reviewed import, the existing source route continues to fail closed.

## Optional district display localization

Migration `0006_smolensk_district_names.sql` adds a nullable `name_ru` column
to the existing independent administrative geometry table and seeds only
explicitly listed Smolensk district translations when English names match.
The read-only `PostgisTerritoryCatalog` exposes the optional translation on
`Territory` without changing the original `name`, canonical ID, province,
geometry, reference version or source authority. API consumers choose a locale;
missing translations fall back to source names. This is a UI display field,
not a new verified administrative inventory or Saturn identity.

Source-code lookup dispatch is configured in `source_registry.py` by provider ID and supported country; each entry contains parameterized, reviewed SQL for a concrete mapping table. Unsupported combinations return no mapping without querying PostgreSQL. Provider-specific SQL is never embedded in public `api.py` contracts. Operational weather policy is read from `persistence/weather/config.py`.

## Spatial SQL and weather configuration boundaries

`point_locator.py` owns reviewed PostGIS point-containment queries. It uses
`ST_Covers` to include boundary points and `LIMIT 2` to detect ambiguous
regional or district overlays; multiple results fail rather than selecting
first. Geometry JSON is decoded separately in `geography.py`, while region
rows are validated by column shape in `regions.py`. SQL receives the shared
`WGS84_SRID` instead of embedding an undocumented numeric literal.

`persistence/weather/config.py` reads the optional operator-managed weather
provider rows introduced by `0004` and augmented by `0007`. The public
`WeatherProviderConfig` is a DB-owned value contract, not an HTTP adapter.
Exactly one enabled provider can be selected; malformed rows and multiple
active providers fail closed. The API composition boundary selects an approved
provider-specific forecast adapter and validates its URLs before external I/O.

## Read-only area intersections

`PostgisTerritoryCatalog` optionally implements `TerritoryAreaDistrictLookup` using imported WGS84 ADM1/ADM2 data and a separate, bounded, positive-area ADM2 read. It verifies that the selected region has imported geometry before the query; missing geometry fails closed. This operation is read-only, not proof of independent ADM2 completeness or production-ready saved-place persistence. Its spatial SQL is internal to persistence; clients consume the typed `territories.api` protocol.

## Private saved places (prepared, not exposed)

`PostgisSavedPlaceRepository` implements the `places.api.SavedPlaceRepository` port through explicitly injected PostgreSQL connections. Each operation requires an independently authorized, non-nil owner UUID; a missing or foreign record is indistinguishable, and updates/deletes use optimistic revision checks. Creation and updates require one unambiguous, imported ADM1 boundary containing the WGS84 center. The server derives rectangle geometry from the validated place dimensions; districts and analysis results are not persisted as place identity. Every write commits atomically or rolls back, and infrastructure errors do not expose private coordinates.

Migration `0008_saved_places.sql` creates the owner-scoped table, bounded WGS84 geometries and indexes. It is opt-in and cannot enable any HTTP route by itself. `melliatlas.main:app` does not construct or use this adapter. An authentication/isolation boundary must supply the owner UUID before public CRUD is authorized. The optional test-database smoke check exercises real PostGIS semantics; mock tests alone are insufficient evidence of durability, correctness or access control.
