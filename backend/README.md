# Backend

The backend is a Python/FastAPI modular monolith under active implementation. The first slice provides a runnable HTTP application with typed health and OpenAPI contracts. The current territory slice adds typed RU/BY administrative domain contracts, an offline GEOS-backed polygon validator, an in-memory catalog, and versioned country/region/district/geometry endpoints.

An explicitly configured development-only investigation slice adds a fixed offline RU synthetic scenario, a deterministic two-or-more-stop proposal, and `POST`/`GET` investigation endpoints. No provider is active by default; choose `MELLIATLAS_SOURCE_PROVIDER=synthetic` for the offline demo. When enabled, the store is per-application memory. An opt-in PostGIS adapter can durably save completed snapshots after migration and explicit injection; no PostgreSQL driver, DB connection or persistence is configured by default. In-flight background tasks are not durable. It does not supply verified ecological screening, weather, or real site availability. An explicit V04-03 fictional ecology scenario connects the pure `agent` replanner to the same jobs/HTTP boundary and returns a typed observation and decision trace. The V01 scenario remains unchanged. A separate fictional V04-05 treatment scenario now uses offline normalized planned-spraying claims to withhold an intersecting candidate, select an illustrative alternative, and return typed notice dates, product claims and uncertainty. This is not real spraying, drift analysis or placement advice. A bounded V04-06 joint fixture now combines both checks before selecting the final proposed stops and preserves their separate observations. The full source/engine pipeline and real environmental acceptance remain pending.

The territory service remains unconfigured until a validated file snapshot or the optional preseeded PostgreSQL region directory is supplied. Region reads return `503` until a validated snapshot is injected or explicitly loaded at ASGI startup. Test fixtures are incomplete, fictional catalogs and must never be used to claim coverage of Russian federal subjects or Belarusian oblasts. The pinned ISO 3166-2 region-only seed supplies 83 RU and 7 BY entries but not verified complete borders, extra jurisdictions or pilot districts. Independent spatial integration checks remain open requirements. Shapely/GEOS validates local polygon topology but does not prove that boundaries, CRS labels or administrative coverage are correct.

## Source layout

- `src/melliatlas/api/` owns HTTP composition and file-deserialization boundaries; see its [contract](src/melliatlas/api/contract.md).
- `src/melliatlas/territories/` owns geographic identity, validation, and the in-memory catalog; see its [contract](src/melliatlas/territories/contract.md).
- `src/melliatlas/planning/`, `sources/`, and `jobs/` contain narrow public interfaces and synthetic-only tests; each has a capability contract. `sources/providers/saturn/api.py` exports the offline decoder; `sources/providers/saturn/legacy_treatment.py` decodes the historically observed `/planapplybees` treatment-page format into explicit RU fixture-only notice claims; it does not fetch from a provider, store immutable raw pages or prove legal reuse rights.
- `src/melliatlas/sources/providers/synthetic/` implements the explicit offline fixture source; `sources/api.py` contains only the protocol and provider-neutral types.
- `src/melliatlas/analyzers/` contains pure fictional ecology checks and a conservative offline treatment-notice site screening operation (approximate distance, temporal overlap, unknown coverage, no wind model); `planning` owns the separate demo eligibility policy.
- `src/melliatlas/agent/` contains bounded deterministic ecology and treatment-aware fictional planning loops; it uses injected inspectors and never claims real-world eligibility. Its [contract](src/melliatlas/agent/contract.md) explicitly excludes V01 HTTP/jobs integration.
- `src/melliatlas/persistence/` implements optional PostGIS completed-result persistence. The SQL migration is in `migrations/`; driver approval and real PostGIS testing remain required. See its [contract](src/melliatlas/persistence/contract.md).
- `scripts/import_reference.py` performs offline validation of a normalized dataset and independent inventory, reporting coverage counts without storing data. Optional `MELLIATLAS_REFERENCE_SNAPSHOT` and `MELLIATLAS_REFERENCE_INVENTORY` paths load the same normalized documents at ASGI startup, validate them before serving, and populate an isolated in-memory territory catalog. This is not PostGIS import or proof of approved real-world coverage.
- `tests/` contains contract, unit and architecture checks, using only clearly marked synthetic geography.

See the [repository overview](../README.md) and [specification index](../docs/specs/README.md) for scope. For setup and testing, see [installation](../docs/INSTALLATION.md) and [tests](../docs/TESTS.md).

## Experimental real Saturn read

Only if `MELLIATLAS_SATURN_LIVE_ENABLED=true`, the FastAPI composition root
injects a bounded `SaturnPublicTreatmentReader`. The fixed HTTPS transport is
isolated in `api/saturn_http.py`; the decoder remains in `sources/providers/saturn/`.
`GET /api/v1/sources?country=RU` advertises this capability; a manual POST to
`/api/v1/sources/saturn/treatments` reads one public portal page. Country BY
is rejected before transport. A 502 response means the live portal could not
be read or its response failed validation, not that no treatments exist.
Source records are not automatically stored or combined with synthetic plans.
The historical read endpoint and public-use terms still require verification.

For a **single operator-initiated compatibility check**, after independently reviewing
upstream access and reuse terms, run the following from the repository root with
an editable backend installation:

```sh
python backend/scripts/probe_saturn.py --region-code 55
```

Replace `55` with a verified **Saturn upstream subject code** for the target
Russian region; it is not a MelliAtlas territory ID. This command makes at most
one HTTPS page request and prints one JSON summary with the upstream HTTP status
(if available), allowlisted envelope fields, row-shape counts and decoder status.
It does not print or store source records, product names, field IDs, coordinates
or raw response bodies. A nonzero exit status means access, schema, or partial
record verification remains unresolved; a successful parse is **not** evidence
of provider availability elsewhere, complete coverage or permission to ingest.
Do not run it as a scheduled job or increase its call frequency without review.

## Live point weather preview (opt-in)

The `WeatherForecastReader` port is implemented by the bounded Open-Meteo
adapter, with network I/O isolated in `api/weather_http.py`. It requires
`AppSettings.weather_live_enabled=True` or the main-process environment flag
`MELLIATLAS_WEATHER_LIVE_ENABLED=true`. The default is disabled and does not
activate synthetic scenarios. Requests are explicit, 24-hour, UTC and local
point-specific; they do not measure wind at the apiary or estimate pesticide
transport. Open-Meteo free API use is non-commercial and requires attribution.


## Preloaded, provider-independent region directory

Apply `migrations/0002_region_directory.sql` to PostgreSQL and run the explicit
`backend/scripts/bootstrap_regions.py` seed. The optional `postgres` dependency
is required (`pip install -e './backend[dev]'` includes it for development).
Set `MELLIATLAS_DATABASE_URL` before starting the API; without it, the existing
fail-closed reference state remains. Region names, canonical identifiers and
provenance live in `melliatlas_region`, separate from `melliatlas_source_saturn`.
The latter contains only an archived verified mapping for Smolensk initially.
For additional codes, use the one-shot `capture_saturn_subjects.py` command only
when public source access is authorized, review its local JSON output, and then
run the separate offline `import_saturn_subjects.py`. Neither script runs at
application startup. The capture is bounded, exclusive and never committed.
See [installation](../docs/INSTALLATION.md) and the territory/persistence contracts.
