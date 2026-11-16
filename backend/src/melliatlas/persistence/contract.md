# PostGIS Completed Investigation Store Contract — V02 (partial)

`PostgisCompletedInvestigationStore` implements the jobs-owned `CompletedInvestigationStore` protocol. A caller injects a DB-API-compatible PostgreSQL connection factory; the adapter does not import a driver, read credentials, open implicit connections at application startup, or install dependencies. Each operation owns and closes its connection and cursor.

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
