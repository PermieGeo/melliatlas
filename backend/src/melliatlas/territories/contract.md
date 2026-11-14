# Territory Module Contract

The `territories` module owns canonical RU/BY administrative identity, reference metadata, geometry, and the distinction between **not loaded**, **missing**, and **unsupported depth**. It has no dependencies on HTTP, SQL, or external providers.

## Public interfaces

- `melliatlas.territories.api`: `CountryCode`, `TerritoryKind`, `GeometryStatus`, `Territory`, `ReferenceManifest`, `TerritoryGeometry`, `ReferenceSnapshot`, `ExpectedInventory`, `TerritoryCatalog`, `TerritoryImport`, and typed errors.
- `melliatlas.territories.InMemoryTerritoryCatalog`: a replaceable, non-durable adapter implementing the catalog and import protocols. It accepts exactly one immutable validated reference and must not be mistaken for the planned PostGIS implementation.
- `melliatlas.territories.validation.snapshot_checksum`: SHA-256 of a canonical serialization of normalized territories and geometries. It does not authenticate the original publisher or certify legal applicability.
- `melliatlas.territories.validation.validate_reference`: checks the normalized snapshot against a **separately maintained** reference inventory, country/region/district relationships, dates, metadata, a normalized payload checksum, and WGS84 coordinate/ring invariants with GEOS polygon topology validation.

## Catalog semantics

- Countries RU and BY are identified by their country codes. Canonical region and district IDs use `ru:region:*`, `by:region:*`, `ru:district:*`, and `by:district:*`; each ID prefix must match its `CountryCode` and the administrative parent must belong to that country. Provider IDs must not replace canonical identities.
- Complete first-order catalogs for **both countries** (including the separately administered Minsk city) and complete pilot district catalogs for **Smolensk and Vitebsk regions** must be verified against independent, date-specific inventories. An imported snapshot with a small self-declared inventory is **not evidence of real-world completeness**.
- `list_districts()` raises `CatalogDepthUnsupported` outside the two pilot regions and `TerritoryNotFound` for an unknown ID. An unloaded catalog raises `ReferenceUnavailableError`, rather than returning an empty list that looks complete.
- Repeated import of identical data is idempotent; a different payload is rejected instead of silently replacing an active snapshot. Caller-owned mutable GeoJSON arrays are copied at import and read boundaries.
- WGS84 polygon and multipolygon rings are checked for closure, finite coordinate range, and adjacent duplicate points; Shapely/GEOS validates ring intersections, holes, and interactions between polygon components. Validity here does **not** prove geographic accuracy, correct CRS labeling, complete administrative coverage, or licensed provenance. PostGIS persistence, SRID validation, spatial indexing and integration checks are still required before production acceptance.

## Reference access and limitations

The normalized JSON file loader belongs to the API/administration boundary (`melliatlas.api.reference_loader`); it reads local files and never contacts a public provider. The independent inventory is a separate input. The CLI `backend/scripts/import_reference.py` validates files and prints a report; it does **not** populate PostGIS, expose private coordinates, or approve a dataset.

**Current status:** API contracts, in-memory validated import, and HTTP reads are implemented. No real complete RU/BY inventory, licensed boundary download, approved reference version, or PostGIS adapter has been installed. `MVP01-BE-A02/A03` remain open.

